"""Applicants and their artifacts, read and written as API `Candidate`s.

Every function is one unit of work with its own session. Call them directly
from `def` routes; from `async def` routes go through `run_in_threadpool` so the
event loop never waits on the database.
"""

from __future__ import annotations

import re
from collections import defaultdict

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, or_, select

from backend.db.engine import get_engine
from backend.db.tables import Applicant, Artifact, ArtifactKind, User
from backend.models import Application, Candidate, Essay

_LEGACY_REF = re.compile(r"^c-(\d+)$")
_ALLOCATION_ATTEMPTS = 5


class AlreadyApplied(Exception):
    """The user submitting an application already has one."""


# ── Conversion ─────────────────────────────────────────────────────


def _artifacts_from(candidate: Candidate) -> list[Artifact]:
    """Split a candidate's texts into artifact rows; empty texts are not stored."""
    rows = [
        Artifact(kind=ArtifactKind.ESSAY.value, content=candidate.essay.text, prompt=candidate.essay.prompt),
    ]
    if candidate.interview_transcript:
        rows.append(Artifact(kind=ArtifactKind.INTERVIEW_TRANSCRIPT.value, content=candidate.interview_transcript))
    if candidate.recommendation_summary:
        rows.append(Artifact(kind=ArtifactKind.RECOMMENDATION.value, content=candidate.recommendation_summary))
    if candidate.video_transcript or candidate.video_link:
        rows.append(
            Artifact(
                kind=ArtifactKind.VIDEO_TRANSCRIPT.value,
                content=candidate.video_transcript,
                uri=candidate.video_link or None,
            )
        )
    return rows


def _to_candidate(applicant: Applicant, artifacts: list[Artifact]) -> Candidate:
    latest: dict[str, Artifact] = {}
    for artifact in sorted(artifacts, key=lambda a: a.created_at):
        latest[artifact.kind] = artifact

    essay = latest.get(ArtifactKind.ESSAY.value)
    video = latest.get(ArtifactKind.VIDEO_TRANSCRIPT.value)
    interview = latest.get(ArtifactKind.INTERVIEW_TRANSCRIPT.value)
    recommendation = latest.get(ArtifactKind.RECOMMENDATION.value)

    return Candidate(
        id=applicant.legacy_ref or applicant.id,
        name=applicant.name,
        age=applicant.age,
        application=Application.model_validate(applicant.application),
        # word_count is derived from the text, not stored.
        essay=Essay(prompt=essay.prompt or "", text=essay.content) if essay else Essay(prompt="", text=""),
        interview_transcript=interview.content if interview else "",
        recommendation_summary=recommendation.content if recommendation else "",
        video_link=(video.uri or "") if video else "",
        video_transcript=video.content if video else "",
    )


def find_applicant(session: Session, ref: str) -> Applicant | None:
    """Look an applicant up by `c-001`-style ref or by UUID."""
    return session.exec(
        select(Applicant).where(or_(Applicant.legacy_ref == ref, Applicant.id == ref))
    ).first()


def _artifacts_of(session: Session, applicant_ids: list[str]) -> dict[str, list[Artifact]]:
    grouped: dict[str, list[Artifact]] = defaultdict(list)
    if not applicant_ids:
        return grouped
    for artifact in session.exec(select(Artifact).where(col(Artifact.applicant_id).in_(applicant_ids))):
        grouped[artifact.applicant_id].append(artifact)
    return grouped


# ── Reads ──────────────────────────────────────────────────────────


def list_candidates() -> list[Candidate]:
    with Session(get_engine()) as session:
        applicants = session.exec(
            select(Applicant).order_by(col(Applicant.created_at), col(Applicant.legacy_ref))
        ).all()
        artifacts = _artifacts_of(session, [a.id for a in applicants])
        return [_to_candidate(a, artifacts[a.id]) for a in applicants]


def get_candidate(ref: str) -> Candidate | None:
    with Session(get_engine()) as session:
        applicant = find_applicant(session, ref)
        if applicant is None:
            return None
        return _to_candidate(applicant, _artifacts_of(session, [applicant.id])[applicant.id])


def applicant_id_for(ref: str) -> str | None:
    """UUID of the applicant a `c-001`-style ref or UUID points at."""
    with Session(get_engine()) as session:
        applicant = find_applicant(session, ref)
        return applicant.id if applicant else None


def applicant_ids() -> dict[str, str]:
    """Every applicant's public id (`Candidate.id`) -> UUID, in one query."""
    with Session(get_engine()) as session:
        rows = session.exec(select(Applicant.id, Applicant.legacy_ref)).all()
        return {legacy_ref or applicant_id: applicant_id for applicant_id, legacy_ref in rows}


# ── Writes ─────────────────────────────────────────────────────────


def _insert(session: Session, candidate: Candidate, legacy_ref: str | None) -> Applicant:
    applicant = Applicant(
        legacy_ref=legacy_ref,
        name=candidate.name,
        age=candidate.age,
        application=candidate.application.model_dump(mode="json"),
    )
    session.add(applicant)
    session.flush()
    for artifact in _artifacts_from(candidate):
        artifact.applicant_id = applicant.id
        session.add(artifact)
    return applicant


def _next_legacy_ref(session: Session) -> str:
    refs = session.exec(select(Applicant.legacy_ref).where(col(Applicant.legacy_ref).is_not(None))).all()
    numbers = [int(m.group(1)) for r in refs if (m := _LEGACY_REF.match(r))]
    return f"c-{max(numbers, default=0) + 1:03d}"


def _claim(session: Session, owner_user_id: str, applicant_id: str) -> bool:
    """Link the application to its owner, only if they have none yet.

    One conditional UPDATE, so two submissions racing from the same account
    cannot both succeed and leave an orphaned application behind.
    """
    result = session.execute(
        update(User)
        .where(col(User.id) == owner_user_id, col(User.applicant_id).is_(None))
        .values(applicant_id=applicant_id)
    )
    return result.rowcount == 1


def create_candidate(candidate: Candidate, owner_user_id: str | None = None) -> Candidate:
    """Store a new application and return it with its assigned id.

    `candidate.id` is ignored; the next free `c-###` ref is allocated. The
    unique constraint on `legacy_ref` turns a race between two submissions into
    a retry instead of two applicants sharing an id. With `owner_user_id` the
    application is linked to that user in the same transaction; raises
    `AlreadyApplied` if they already have one.
    """
    for _ in range(_ALLOCATION_ATTEMPTS):
        with Session(get_engine()) as session:
            try:
                applicant = _insert(session, candidate, _next_legacy_ref(session))
                if owner_user_id is not None and not _claim(session, owner_user_id, applicant.id):
                    session.rollback()
                    raise AlreadyApplied(owner_user_id)
                session.commit()
            except IntegrityError:
                session.rollback()
                continue
            return _to_candidate(applicant, _artifacts_of(session, [applicant.id])[applicant.id])
    raise RuntimeError("could not allocate a candidate id; retry the request")


def import_candidate(session: Session, candidate: Candidate) -> bool:
    """Insert a seed record under its own id, unless it is already there.

    Used by the seed; the caller owns the transaction. Returns whether a row
    was inserted.
    """
    if find_applicant(session, candidate.id) is not None:
        return False
    _insert(session, candidate, candidate.id)
    return True
