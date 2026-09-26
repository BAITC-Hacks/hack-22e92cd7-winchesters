"""Committee/admin-only FAIR-12 held-out evaluation endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from backend.db.engine import get_engine
from backend.db.tables import AuditLogEntry, ModelRun, ModelRunStatus
from backend.evals.historical import build_report
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