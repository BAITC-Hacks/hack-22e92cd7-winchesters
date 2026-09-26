"""Read and write the persisted LED-11 evidence ledger snapshot."""

from __future__ import annotations

import hashlib
from typing import Any

from sqlmodel import Session, col, select

from backend.db.candidates import applicant_id_for
from backend.db.engine import get_engine
from backend.db.tables import CompetencyScore, EvidenceItemRecord, PromptVersion, Rating, RubricVersion
from backend.ledger.schema import CandidateLedger


def _version(session: Session, model: type[PromptVersion] | type[RubricVersion], value: str) -> str:
    row = session.exec(select(model).where(col(model.version) == value)).first()
    if row is None:
        row = model(version=value, content_hash=hashlib.sha256(value.encode("utf-8")).hexdigest())
        session.add(row)
        session.flush()
    return row.id


def save_ledger(candidate_ref: str, ledger: CandidateLedger) -> None:
    """Append one complete ledger snapshot for an applicant."""
    applicant_id = applicant_id_for(candidate_ref)
    if applicant_id is None:
        raise ValueError(f"candidate {candidate_ref} does not exist")
    with Session(get_engine()) as session:
        rubric_id = _version(session, RubricVersion, ledger.rubric_version)
        prompt_id = _version(session, PromptVersion, ledger.prompt_version)
        for competency in ledger.competencies:
            score = CompetencyScore(
                applicant_id=applicant_id, competency=competency.competency.value,
                level=competency.level.value if competency.level else None,
                rule_applied=competency.rule_applied, reserved_for_humans=competency.reserved_for_humans,
                contrastive=competency.contrastive, probe_question=competency.probe_question,
                flags=[flag.model_dump(mode="json") for flag in competency.flags],
                schema_version=ledger.schema_version, rubric_version_id=rubric_id, prompt_version_id=prompt_id,
                model_judge=ledger.model_judge, model_extract=ledger.model_extract,
            )
            session.add(score)
            session.flush()
            for indicator in competency.indicators:
                rating = Rating(
                    competency_score_id=score.id, applicant_id=applicant_id,
                    indicator_id=indicator.indicator_id, observed_level=indicator.observed_level.value,
                    note=indicator.note,
                )
                session.add(rating)
                session.flush()
                for evidence in indicator.evidence:
                    session.add(EvidenceItemRecord(
                        rating_id=rating.id, applicant_id=applicant_id, quote=evidence.quote,
                        source=evidence.source.value, source_ref=None, char_start=evidence.char_start,
                        char_end=evidence.char_end, atola=evidence.atola.value, status=evidence.status.value,
                        verified=evidence.verified, indicator_hint=evidence.indicator_hint,
                    ))
        session.commit()


def load_ledger(candidate_ref: str) -> CandidateLedger | None:
    """Return the latest persisted snapshot, never a live rebuild."""
    applicant_id = applicant_id_for(candidate_ref)
    if applicant_id is None:
        return None
    with Session(get_engine()) as session:
        scores = session.exec(
            select(CompetencyScore).where(col(CompetencyScore.applicant_id) == applicant_id)
            .order_by(col(CompetencyScore.created_at).desc())
        ).all()
        latest: dict[str, CompetencyScore] = {}
        for score in scores:
            latest.setdefault(score.competency, score)
        if not latest:
            return None
        score_ids = [score.id for score in latest.values()]
        ratings = session.exec(select(Rating).where(col(Rating.competency_score_id).in_(score_ids))).all()
        rating_ids = [rating.id for rating in ratings]
        evidence = session.exec(select(EvidenceItemRecord).where(col(EvidenceItemRecord.rating_id).in_(rating_ids))).all() if rating_ids else []
        evidence_by_rating: dict[str, list[EvidenceItemRecord]] = {}
        for item in evidence:
            evidence_by_rating.setdefault(item.rating_id, []).append(item)
        ratings_by_score: dict[str, list[Rating]] = {}
        for rating in ratings:
            ratings_by_score.setdefault(rating.competency_score_id, []).append(rating)
        first = next(iter(latest.values()))
        rubric = session.get(RubricVersion, first.rubric_version_id)
        prompt = session.get(PromptVersion, first.prompt_version_id)
        competencies: list[dict[str, Any]] = []
        for score in sorted(latest.values(), key=lambda value: value.competency):
            competencies.append({
                "competency": score.competency,
                "indicators": [{
                    "indicator_id": rating.indicator_id, "observed_level": rating.observed_level,
                    "evidence": [{
                        "quote": item.quote, "source": item.source, "source_ref": item.source_ref or "",
                        "char_start": item.char_start, "char_end": item.char_end, "atola": item.atola,
                        "status": item.status, "verified": item.verified, "indicator_hint": item.indicator_hint,
                    } for item in evidence_by_rating.get(rating.id, [])],
                    "note": rating.note, "capped_reason": "",
                } for rating in ratings_by_score.get(score.id, [])],
                "level": score.level, "rule_applied": score.rule_applied,
                "reserved_for_humans": score.reserved_for_humans, "contrastive": score.contrastive,
                "probe_question": score.probe_question, "flags": score.flags, "atola_present": [],
            })
        return CandidateLedger(
            applicant_ref=candidate_ref, schema_version=first.schema_version,
            rubric_version=rubric.version if rubric else "unknown", model_judge=first.model_judge,
            model_extract=first.model_extract, prompt_version=prompt.version if prompt else "unknown",
            competencies=competencies,
        )