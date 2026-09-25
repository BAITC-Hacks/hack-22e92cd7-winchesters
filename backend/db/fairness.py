"""Audit records from the database (FAIR-07): background joined to levels.

The one place `protected_attributes` meets `competency_scores`, and only to
hand plain records to `backend.scoring.fairness_audit`. An applicant's level
per competency is the latest `competency_scores` row, the same rule the ledger
uses. Applicants without a `protected_attributes` row are left out: the audit
groups by declared background, and there is none to group by.

Until LED-11 writes competency scores this returns an empty list, and the audit
says so rather than showing anything.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlmodel import Session, col, select

from backend.db.engine import get_engine
from backend.db.tables import CompetencyScore, ProtectedAttributesRecord

_ATTRIBUTE_FIELDS = (
    "region",
    "settlement_type",
    "school_type",
    "application_language",
    "foundation_eligible",
    "gender",
)


def load_audit_records() -> list[dict]:
    """[{applicant_ref, attributes, levels}] for every applicant with both."""
    with Session(get_engine()) as session:
        attributes = {row.applicant_id: row for row in session.exec(select(ProtectedAttributesRecord))}
        if not attributes:
            return []
        scores = session.exec(
            select(CompetencyScore)
            .where(col(CompetencyScore.applicant_id).in_(list(attributes)))
            .order_by(col(CompetencyScore.created_at), text("competency_scores.rowid"))
        )
        levels: dict[str, dict[str, str | None]] = {}
        for score in scores:  # oldest first, so the latest row per competency wins
            levels.setdefault(score.applicant_id, {})[score.competency] = score.level

    return [
        {
            "applicant_ref": applicant_id,
            "attributes": {field: getattr(attributes[applicant_id], field) for field in _ATTRIBUTE_FIELDS},
            "levels": applicant_levels,
        }
        for applicant_id, applicant_levels in sorted(levels.items())
    ]
