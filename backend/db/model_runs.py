"""Model runs (FND-04, PR 3): what a model call returned, or why it did not.

Replaces the routers' in-memory result caches. A run is written once and never
changed: a re-score is a new row, and "the current result" is the latest ok
run for that applicant and stage. A failed call is its own row with the error,
so an outage is visible as an outage and never reads as a low score.

Every function is one unit of work with its own session; from `async def`
routes call them through `run_in_threadpool`.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlmodel import Session, col, select

from backend.db.engine import get_engine
from backend.db.tables import ModelRun, ModelRunStatus, PromptVersion, RubricVersion

logger = logging.getLogger(__name__)


def _version_id(session: Session, table: type[PromptVersion] | type[RubricVersion], version: str | None) -> str | None:
    """The row id for a version string, or None if it is not registered.

    An unknown version is not created here: a version row carries the hash of
    the content it names, and a row made up from a bare string would claim a
    hash nobody computed.
    """
    if version is None:
        return None
    row_id = session.exec(select(table.id).where(col(table.version) == version)).first()
    if row_id is None:
        logger.warning("%s %r is not registered; model run stored without it", table.__tablename__, version)
    return row_id


# ── Writes ─────────────────────────────────────────────────────────


def record_model_run(
    *,
    stage: str,
    model: str,
    status: str,
    output: Any = None,
    error: str | None = None,
    applicant_id: str | None = None,
    prompt_version: str | None = None,
    rubric_version: str | None = None,
) -> str:
    """Store one model call and return the run's id.

    `applicant_id` is the applicant's UUID, not a `c-001` ref. `status` is
    "ok" with `output`, or "failed" with `error`; the table's checks reject
    anything else, and this rejects it first with a readable message.
    """
    status = ModelRunStatus(status).value
    if status == ModelRunStatus.OK.value and output is None:
        raise ValueError("an ok model run needs an output")
    if status == ModelRunStatus.FAILED.value and not error:
        raise ValueError("a failed model run needs an error")

    with Session(get_engine()) as session:
        run = ModelRun(
            applicant_id=applicant_id,
            stage=stage,
            model=model,
            prompt_version_id=_version_id(session, PromptVersion, prompt_version),
            rubric_version_id=_version_id(session, RubricVersion, rubric_version),
            status=status,
            output=output,
            error=error,
        )
        session.add(run)
        session.commit()
        return run.id


# ── Reads ──────────────────────────────────────────────────────────


def _latest_ok(stage: str):
    return (
        select(ModelRun)
        .where(col(ModelRun.stage) == stage, col(ModelRun.status) == ModelRunStatus.OK.value)
        .order_by(col(ModelRun.created_at).desc())
    )


def latest_ok_output(applicant_id: str, stage: str) -> dict[str, Any] | None:
    """Output of the applicant's most recent ok run at this stage, if any.

    A later failed run does not hide an earlier ok one: a re-score that timed
    out leaves the previous result standing.
    """
    with Session(get_engine()) as session:
        run = session.exec(_latest_ok(stage).where(col(ModelRun.applicant_id) == applicant_id)).first()
        return run.output if run else None


def latest_ok_outputs(stage: str) -> dict[str, dict[str, Any]]:
    """Applicant UUID -> output of their most recent ok run at this stage.

    Applicants without an ok run are absent, not mapped to an empty result.
    """
    latest: dict[str, dict[str, Any]] = {}
    with Session(get_engine()) as session:
        for run in session.exec(_latest_ok(stage).where(col(ModelRun.applicant_id).is_not(None))):
            # Newest first, so the first run seen per applicant wins.
            latest.setdefault(run.applicant_id, run.output)
    return latest
