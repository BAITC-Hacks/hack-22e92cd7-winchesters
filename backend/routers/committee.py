"""Committee decision memo endpoints (COM-04)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from fastapi.concurrency import run_in_threadpool

from backend.committee_memo import build_decision_memo, render_pdf
from backend.ledger.pipeline import build_ledger
from backend.routers.candidates import get_candidate_or_404
from backend.routers.guards import require_role
from backend.security import Role

router = APIRouter(prefix="/api/committee", tags=["committee"], dependencies=[Depends(require_role(Role.COMMITTEE, Role.ADMIN))])


async def _memo(candidate_id: str) -> dict:
    candidate = await run_in_threadpool(get_candidate_or_404, candidate_id)
    return build_decision_memo(candidate_id, await build_ledger(candidate))


@router.get("/decision-memo/{candidate_id}")
async def decision_memo(candidate_id: str) -> dict:
    return await _memo(candidate_id)


@router.get("/decision-memo/{candidate_id}/pdf")
async def decision_memo_pdf(candidate_id: str) -> Response:
    memo = await _memo(candidate_id)
    return Response(content=render_pdf(memo), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="decision-memo-{candidate_id}.pdf"'})