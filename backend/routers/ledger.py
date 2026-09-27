"""Committee/admin read access to persisted evidence ledgers (LED-11).

Every response is a stored snapshot. Nothing here calls a model: a candidate
without a snapshot gets 404, never a live rebuild. Snapshots are written by
`python -m backend.ledger.cache` and loaded by `python -m backend.db init`.

Interviewers are left out on purpose: the ledger carries levels, and the
interviewer pre-brief withholds them.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool

from backend.db import ledger as ledger_store
from backend.ledger import versions
from backend.ledger.rubric import COMPETENCY_ORDER, RUBRIC
from backend.ledger.schema import CandidateLedger
from backend.routers.candidates import get_candidate_or_404
from backend.routers.guards import require_role
from backend.security import Role

router = APIRouter(prefix="/api/ledger", tags=["ledger"], dependencies=[Depends(require_role(Role.COMMITTEE, Role.ADMIN))])


@router.get("")
async def list_ledgers() -> list[CandidateLedger]:
    return await run_in_threadpool(ledger_store.list_ledgers)


@router.get("/rubric")
def rubric_status() -> dict[str, Any]:
    """Which rubric the ledgers are built under, and which scales are still drafts (LED-13)."""
    version, digest = versions.current()["rubric"]
    return {
        "version": version,
        "content_hash": digest,
        "locked": versions.known_hash("rubric", version) == digest,
        "competencies": [
            {"competency": c.value, "label": RUBRIC[c].label, "provisional": RUBRIC[c].provisional, "ai_may_rate": RUBRIC[c].ai_may_rate}
            for c in COMPETENCY_ORDER
        ],
    }


@router.get("/{candidate_id}")
async def get_ledger(candidate_id: str) -> CandidateLedger:
    await run_in_threadpool(get_candidate_or_404, candidate_id)
    ledger = await run_in_threadpool(ledger_store.load_ledger, candidate_id)
    if ledger is None:
        raise HTTPException(status_code=404, detail="No evidence ledger has been built for this candidate yet")
    return ledger
