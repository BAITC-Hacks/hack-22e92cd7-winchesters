"""Committee/admin-only FAIR-12 held-out evaluation endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from backend.db.engine import get_engine
from backend.db.tables import AuditLogEntry, ModelRun, ModelRunStatus
from backend.evals.historical import build_report, compare_reports, replay_report
from backend.routers.guards import require_role
from backend.security import Role

router = APIRouter(prefix="/api/fairness/heldout", tags=["fairness-heldout"], dependencies=[Depends(require_role(Role.COMMITTEE, Role.ADMIN))])


class HeldoutIngest(BaseModel):
    records: list[dict[str, Any]] = Field(min_length=1)
    prompt_id: str = "historical-prompt-frozen"
    model_id: str = "historical-model-frozen"
    rubric_id: str = "historical-rubric-frozen"
    split_seed: int = 8009


def _latest() -> ModelRun | None:
    with Session(get_engine()) as session:
        return session.exec(select(ModelRun).where(ModelRun.stage == "fair12_heldout").order_by(ModelRun.created_at.desc())).first()


@router.post("/ingest")
def ingest(payload: HeldoutIngest, user: dict[str, Any] = Depends(require_role(Role.COMMITTEE, Role.ADMIN))):
    try:
        report = build_report(records=payload.records, prompt_id=payload.prompt_id, model_id=payload.model_id, rubric_id=payload.rubric_id, split_seed=payload.split_seed)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    with Session(get_engine()) as session:
        session.add(ModelRun(stage="fair12_heldout", model=payload.model_id, status=ModelRunStatus.OK.value, output=report))
        session.add(AuditLogEntry(actor_user_id=user["id"], action="heldout_evaluation_run", object_type="evaluation", object_id=report["manifest"]["evaluation_data_hash"], after={"report_mode": "historical", "holdout_sealed": True, "production_invariance": report["production_invariance"]}))
        session.commit()
    return report


@router.get("/report")
def report() -> dict[str, Any]:
    run = _latest()
    if run is None:
        raise HTTPException(status_code=404, detail="No held-out evaluation has been ingested")
    return run.output


@router.get("/reproduce")
def reproduce(user: dict[str, Any] = Depends(require_role(Role.COMMITTEE, Role.ADMIN))) -> dict[str, Any]:
    """Replay every saved rating and compare the complete report byte-for-byte."""
    run = _latest()
    if run is None:
        raise HTTPException(status_code=404, detail="No held-out evaluation has been ingested")
    try:
        replayed = replay_report(run.output)
        comparison = compare_reports(run.output, replayed)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    with Session(get_engine()) as session:
        session.add(AuditLogEntry(
            actor_user_id=user["id"],
            action="heldout_reproducibility_check",
            object_type="evaluation",
            object_id=comparison["expected_hash"],
            after={"byte_identical": comparison["byte_identical"], "mismatch_count": len(comparison["mismatches"])},
        ))
        session.commit()
    bundle = run.output["reproducibility"]
    return {
        "status": "reproduced" if comparison["byte_identical"] else "mismatch",
        "ratings_recomputed": bundle["rating_count"],
        "frozen_hashes": bundle["frozen_hashes"],
        "provenance": {
            "requested_mode": "replay",
            "effective_mode": "replay",
            "fallback_used": False,
            "fallback_reason": None,
            "live_result": None,
            "cached_result": {"source": "saved_ratings", "report_mode": run.output["manifest"]["report_mode"]},
            "fallback_result": None,
        },
        "source_provenance": run.output["provenance"],
        "production_invariance": run.output["production_invariance"],
        **comparison,
    }