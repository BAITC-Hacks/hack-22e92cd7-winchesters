"""Committee/admin-only FAIR-09 historical evaluation endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from backend.db.engine import get_engine
from backend.db.tables import AuditLogEntry, ModelRun, ModelRunStatus
from backend.evals.historical import build_model_card, build_report
from backend.routers.guards import require_role
from backend.security import Role

router = APIRouter(prefix="/api/fairness/historical", tags=["fairness-historical"], dependencies=[Depends(require_role(Role.COMMITTEE, Role.ADMIN))])


class HistoricalIngest(BaseModel):
    records: list[dict[str, Any]] = Field(min_length=1)
    prompt_id: str = "historical-prompt-frozen"
    model_id: str = "historical-model-frozen"
    rubric_id: str = "historical-rubric-frozen"
    split_seed: int = 8009


@router.post("/ingest")
def ingest(payload: HistoricalIngest, user: dict[str, Any] = Depends(require_role(Role.COMMITTEE, Role.ADMIN))):
    try:
        report = build_report(records=payload.records, prompt_id=payload.prompt_id, model_id=payload.model_id, rubric_id=payload.rubric_id, split_seed=payload.split_seed)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    with Session(get_engine()) as session:
        session.add(ModelRun(stage="historical_ingest", model=payload.model_id, status=ModelRunStatus.OK.value, output=report))
        session.add(AuditLogEntry(actor_user_id=user["id"], action="historical_evaluation_ingest", object_type="evaluation", object_id=report["manifest"]["fixture_or_data_hash"], after={"report_mode": "historical", "holdout_sealed": True}))
        session.commit()
    return report


@router.get("/report")
def report() -> dict[str, Any]:
    with Session(get_engine()) as session:
        run = session.exec(select(ModelRun).where(ModelRun.stage == "historical_ingest").order_by(ModelRun.created_at.desc())).first()
    if run is None:
        raise HTTPException(status_code=404, detail="No historical evaluation has been ingested")
    return run.output


@router.get("/model-card")
def model_card() -> dict[str, Any]:
    with Session(get_engine()) as session:
        run = session.exec(select(ModelRun).where(ModelRun.stage == "historical_ingest").order_by(ModelRun.created_at.desc())).first()
    if run is None:
        raise HTTPException(status_code=404, detail="No historical evaluation has been ingested")
    return build_model_card(run.output)