"""Committee/admin-only FAIR-05 evaluation results."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session

from backend.db import model_runs
from backend.db.engine import get_engine
from backend.db.tables import AuditLogEntry, ModelRunStatus
from backend import llm
from backend.evals.harness import cached_report, live_report
from backend.routers.guards import require_role
from backend.security import Role

router = APIRouter(
    prefix="/api/fairness",
    tags=["fairness-evaluation"],
    dependencies=[Depends(require_role(Role.COMMITTEE, Role.ADMIN))],
)


def _record_provenance(actor_id: str, report: dict[str, Any]) -> None:
    model_runs.record_model_run(
        stage="eval_harness",
        model=report["model_id"],
        status=ModelRunStatus.OK.value,
        output={
            "fixture_hash": report["fixture_hash"],
            "prompt_id": report["prompt_id"],
            "rubric_id": report["rubric_id"],
            "metrics": {k: report[k] for k in ("level_flip_rate", "repeat_consistency", "cross_lingual_agreement")},
        },
    )
    with Session(get_engine()) as session:
        session.add(AuditLogEntry(actor_user_id=actor_id, action="fairness_evaluation_run", object_type="evaluation", object_id=report["fixture_hash"], after={"status": report["status"], "prompt_id": report["prompt_id"], "model_id": report["model_id"], "fixture_hash": report["fixture_hash"], "seed": report["seed"]}))
        session.commit()


@router.get("/evaluation")
async def evaluation(live: bool = Query(False), user: dict[str, Any] = Depends(require_role(Role.COMMITTEE, Role.ADMIN))):
    if live:
        try:
            report = await live_report()
        except Exception as error:
            report = cached_report()
            report["status"] = "fallback_demo"
            report["model_id"] = "cached-baseline-demo"
            report["fallback_reason"] = (
                "no model API key on this server" if isinstance(error, llm.ModelUnavailable) else "the live model call failed"
            )
    else:
        report = cached_report()
    await run_in_threadpool(_record_provenance, user["id"], report)
    return report
