"""Committee overrides (COM-01): a human changing a competency level, on record.

Nothing here updates or deletes. An override is a new `committee_overrides`
row plus an `audit_log` row, written in one transaction, and the AI's level is
never touched: the effective level is the latest override, else the AI level.
The triggers from migration 0003 reject UPDATE and DELETE on both tables, so
this is the only shape a change can take.

`from_level` is what the committee saw when overriding (the previous override,
else the AI level), so each row reads on its own: "was normal, now high".
The AI level at that moment goes into the audit row next to it, with where it
came from: `ledger` when a `competency_scores` row exists, `client` when the
card was rendered from something else (until LED-11, the LED-03 fixture).

Every function is one unit of work with its own session.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy import text
from sqlmodel import Session, col, select

from backend.db.engine import get_engine
from backend.db.tables import AuditLogEntry, CommitteeOverrideRecord, CompetencyScore, User

AUDIT_OBJECT_TYPE = "committee_override"
AUDIT_ACTION = "committee_override.create"


class ReasonCode(str, Enum):
    """Why the committee changed a level. Draft vocabulary, to be replaced by
    the methodology owner's list; codes are stable, labels are display."""

    EVIDENCE_MISSED = "evidence_missed"
    EVIDENCE_MISREAD = "evidence_misread"
    RUBRIC_MISAPPLIED = "rubric_misapplied"
    INTERVIEW_EVIDENCE = "interview_evidence"
    HUMAN_RATED = "human_rated"
    OTHER = "other"


REASON_LABELS: dict[ReasonCode, str] = {
    ReasonCode.EVIDENCE_MISSED: "AI missed evidence that is in the material",
    ReasonCode.EVIDENCE_MISREAD: "AI misread or over-weighted a quote",
    ReasonCode.RUBRIC_MISAPPLIED: "BARS anchor applied incorrectly",
    ReasonCode.INTERVIEW_EVIDENCE: "Evidence from the interview",
    ReasonCode.HUMAN_RATED: "Competency rated by a human (no AI level)",
    ReasonCode.OTHER: "Other (explain in the note)",
}

# Codes that say nothing on their own; the note is where the reason is.
NOTE_REQUIRED = frozenset({ReasonCode.OTHER})


class LevelSource(str, Enum):
    LEDGER = "ledger"  # latest competency_scores row
    CLIENT = "client"  # what the card showed; the server had no row to check
    NONE = "none"  # neither: nothing to compare against


class NoChange(ValueError):
    """The requested level is already the effective one."""


# The `reason` column holds "code" or "code: note". No migration for a
# separate column (decided for COM-01); `parse_reason` is the only reader.
def format_reason(code: ReasonCode, note: str) -> str:
    return f"{code.value}: {note}" if note else code.value


def parse_reason(reason: str) -> tuple[str | None, str]:
    """(code, note). A reason that does not start with a known code keeps the
    whole text as the note and no code, rather than guessing one."""
    head, sep, tail = reason.partition(":")
    try:
        return ReasonCode(head.strip()).value, tail.strip() if sep else ""
    except ValueError:
        return None, reason


def _aware(value: datetime) -> datetime:
    # SQLite hands timestamps back without their zone; they were written as UTC.
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _history(session: Session, applicant_id: str, competency: str | None = None):
    query = select(CommitteeOverrideRecord).where(col(CommitteeOverrideRecord.applicant_id) == applicant_id)
    if competency is not None:
        query = query.where(col(CommitteeOverrideRecord.competency) == competency)
    # rowid breaks ties between rows written within one clock tick.
    return query.order_by(col(CommitteeOverrideRecord.created_at), text("committee_overrides.rowid"))


def _ai_level(session: Session, applicant_id: str, competency: str, reported: str | None) -> tuple[str | None, LevelSource]:
    row = session.exec(
        select(CompetencyScore)
        .where(col(CompetencyScore.applicant_id) == applicant_id, col(CompetencyScore.competency) == competency)
        .order_by(col(CompetencyScore.created_at).desc())
    ).first()
    if row is not None:
        # The stored AI level wins over whatever the client says it showed.
        return row.level, LevelSource.LEDGER
    if reported is not None:
        return reported, LevelSource.CLIENT
    return None, LevelSource.NONE


# ── Writes ─────────────────────────────────────────────────────────


def record_override(
    *,
    applicant_id: str,
    competency: str,
    to_level: str,
    reason_code: ReasonCode,
    note: str,
    user_id: str,
    reported_ai_level: str | None = None,
) -> str:
    """Append one override and its audit row; return the override id.

    Raises NoChange when `to_level` is already the effective level: an
    override that changes nothing would still read as a decision in the memo.
    """
    with Session(get_engine()) as session:
        ai_level, source = _ai_level(session, applicant_id, competency, reported_ai_level)
        previous = session.exec(_history(session, applicant_id, competency)).all()
        from_level = previous[-1].to_level if previous else ai_level
        if from_level == to_level:
            raise NoChange(f"{competency} is already {to_level}")

        override = CommitteeOverrideRecord(
            applicant_id=applicant_id,
            competency=competency,
            from_level=from_level,
            to_level=to_level,
            reason=format_reason(reason_code, note),
            user_id=user_id,
        )
        session.add(override)
        session.flush()
        # The note stays out of the audit log: it is free text and may quote
        # the applicant, and the audit log outlives an erasure.
        session.add(
            AuditLogEntry(
                actor_user_id=user_id,
                action=AUDIT_ACTION,
                object_type=AUDIT_OBJECT_TYPE,
                object_id=override.id,
                before={"level": from_level, "ai_level": ai_level, "ai_level_source": source.value},
                after={
                    "level": to_level,
                    "applicant_id": applicant_id,
                    "competency": competency,
                    "reason_code": reason_code.value,
                },
            )
        )
        session.commit()
        return override.id


# ── Reads ──────────────────────────────────────────────────────────


def list_overrides(applicant_id: str) -> list[dict[str, Any]]:
    """Every override for the applicant, oldest first, with author and the AI
    level recorded at the time."""
    with Session(get_engine()) as session:
        rows = session.exec(_history(session, applicant_id)).all()
        if not rows:
            return []
        ids = [r.id for r in rows]
        audits = {
            a.object_id: a
            for a in session.exec(
                select(AuditLogEntry).where(
                    col(AuditLogEntry.object_type) == AUDIT_OBJECT_TYPE, col(AuditLogEntry.object_id).in_(ids)
                )
            )
        }
        users = {u.id: u for u in session.exec(select(User).where(col(User.id).in_({r.user_id for r in rows})))}

        history = []
        for r in rows:
            code, note = parse_reason(r.reason)
            before = (audits[r.id].before if r.id in audits else None) or {}
            author = users.get(r.user_id)
            history.append(
                {
                    "id": r.id,
                    "competency": r.competency,
                    "from_level": r.from_level,
                    "to_level": r.to_level,
                    "reason_code": code,
                    "note": note,
                    "ai_level": before.get("ai_level"),
                    "ai_level_source": before.get("ai_level_source", LevelSource.NONE.value),
                    "author": {
                        "id": r.user_id,
                        "full_name": author.full_name if author else "",
                        "role": author.role if author else "",
                    },
                    "created_at": _aware(r.created_at),
                }
            )
        return history
