"""Attribute-grouped fairness audit (FAIR-07).

Committee and admin only: the response joins self-declared background to
levels, which is exactly what an interviewer or applicant must not browse.

`source=synthetic` (the default until LED-11 stores real levels) audits a
generated cohort and says so in the body; `source=db` audits whatever
`protected_attributes` × `competency_scores` holds, which today is nothing.
The numbers match `python -m backend.scoring.fairness_audit` for the same
source and seeds.
"""

from __future__ import annotations

from functools import cache
from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from backend.db.fairness import load_audit_records
from backend.routers.guards import require_role
from backend.scoring import fairness_audit, synthetic_cohort
from backend.security import Role

router = APIRouter(
    prefix="/api/fairness",
    tags=["fairness"],
    dependencies=[Depends(require_role(Role.COMMITTEE, Role.ADMIN))],
)


class GroupOut(BaseModel):
    group: str
    n: int
    share_of_pool: float
    levels: dict[str, int]
    high_rate: float
    no_evidence_rate: float
    impact_ratio: float | None
    ci_low: float | None
    ci_high: float | None
    is_reference: bool
    state: Literal["ok", "review_needed", "not_enough_data"]
    review_reason: Literal["below_threshold", "interval_crosses_threshold"] | None


class CellOut(BaseModel):
    competency: str
    pool: int
    reference_group: str | None
    groups: list[GroupOut]


class DimensionOut(BaseModel):
    dimension: str
    undeclared: int
    competencies: list[CellOut]


class MethodOut(BaseModel):
    outcome: str
    reference: str
    interval: str
    bootstrap_seed: int
    n_bootstrap: int
    review_threshold: float
    min_group_n: int
    min_group_share: float


class SyntheticOut(BaseModel):
    cohort_seed: int
    size: int
    planted_effects: list[dict[str, str]]
    notice: str


class AuditOut(BaseModel):
    source: Literal["synthetic", "db"]
    applicants: int
    applicants_with_levels: int
    input_hash: str
    method: MethodOut
    competencies: list[str]
    dimensions: list[DimensionOut]
    synthetic: SyntheticOut | None = None


SYNTHETIC_NOTICE = (
    "Synthetic data: generated profiles, no real applicants. "
    "It demonstrates the method, not evidence about the scorer."
)


@cache
def _synthetic_report() -> dict:
    """Fixed seeds, so the same every time: computed once per process."""
    report = fairness_audit.run_audit(synthetic_cohort.generate(), source="synthetic")
    report["synthetic"] = {
        "cohort_seed": synthetic_cohort.DEFAULT_SEED,
        "size": synthetic_cohort.DEFAULT_SIZE,
        "planted_effects": list(synthetic_cohort.PLANTED_EFFECTS),
        "notice": SYNTHETIC_NOTICE,
    }
    return report


@router.get("/audit", response_model=AuditOut)
def audit(source: Literal["synthetic", "db"] = Query("synthetic")):
    if source == "synthetic":
        return _synthetic_report()
    return fairness_audit.run_audit(load_audit_records(), source="db")
