"""Committee decision memo endpoints (COM-04)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.concurrency import run_in_threadpool

from backend.committee_memo import build_decision_memo, render_pdf
from backend.db import ledger as ledger_store
from backend.db import signatures as signature_store
from backend.routers.candidates import get_candidate_or_404
from backend.routers.guards import require_role
from backend.security import Role

router = APIRouter(prefix="/api/committee", tags=["committee"], dependencies=[Depends(require_role(Role.COMMITTEE, Role.ADMIN))])


async def _memo(candidate_id: str, locale: str = "ru") -> dict:
    await run_in_threadpool(get_candidate_or_404, candidate_id)
    ledger = await run_in_threadpool(ledger_store.load_ledger, candidate_id)
    if ledger is None:
        raise HTTPException(status_code=409, detail="No persisted ledger is available for this candidate")
    memo = build_decision_memo(candidate_id, ledger, locale=locale)
    memo["signatures"] = await run_in_threadpool(signature_store.list_signatures, candidate_id)
    return memo


@router.get("/decision-memo/{candidate_id}")
async def decision_memo(candidate_id: str, locale: str = Query("ru", pattern="^(ru|kk)$")) -> dict:
    return await _memo(candidate_id, locale)


@router.get("/decision-memo/{candidate_id}/pdf")
async def decision_memo_pdf(candidate_id: str, locale: str = Query("ru", pattern="^(ru|kk)$")) -> Response:
    memo = await _memo(candidate_id, locale)
    return Response(content=render_pdf(memo, locale=locale), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="decision-memo-{candidate_id}-{locale}.pdf"'})


@router.post("/decision-memo/{candidate_id}/signatures/{role}", status_code=201)
async def sign_decision_memo(
    candidate_id: str,
    role: str,
    user: dict = Depends(require_role(Role.COMMITTEE, Role.ADMIN)),
) -> dict:
    if role not in {"chair", "member"}:
        raise HTTPException(status_code=422, detail="Signature role must be chair or member")
    await _memo(candidate_id)
    try:
        await run_in_threadpool(signature_store.record_signature, candidate_id, role, user["id"])
    except signature_store.SignatureAlreadyRecorded as exc:
        raise HTTPException(status_code=409, detail=f"Signature already recorded for {exc}") from exc
    return {"status": "signed", "role": role}