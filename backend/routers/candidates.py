"""Candidate CRUD endpoints.

Staff list and read every application; an applicant submits one, linked to
their account, and reads only that one.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.db import candidates as store
from backend.models import Application, Candidate, Essay
from backend.routers.guards import ensure_candidate_access, require_role
from backend.security import ALL_ROLES, STAFF_ROLES, Role

router = APIRouter(prefix="/api/candidates", tags=["candidates"])


def load_candidates() -> list[Candidate]:
    return store.list_candidates()


def get_candidate_or_404(candidate_id: str) -> Candidate:
    """Sync: from an `async def` route, call through `run_in_threadpool`."""
    candidate = store.get_candidate(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
    return candidate


# ── Request models ─────────────────────────────────────────────────


class CandidateCreate(BaseModel):
    """Payload for creating a new candidate application."""
    name: str = Field(min_length=1)
    age: int = Field(default=17, ge=14, le=25)
    application: Application
    essay: Essay
    interview_transcript: str = ""
    recommendation_summary: str = ""
    video_link: str = ""
    video_transcript: str = ""


# ── Endpoints ──────────────────────────────────────────────────────


@router.get("/", response_model=list[Candidate])
def list_candidates(_user: dict = Depends(require_role(*STAFF_ROLES))):
    """List all candidates."""
    return load_candidates()


@router.post("/", response_model=Candidate, status_code=201)
def create_candidate(body: CandidateCreate, user: dict = Depends(require_role(Role.APPLICANT))):
    """Submit the caller's application; one per account."""
    try:
        # The id is allocated by the store; this placeholder is never saved.
        return store.create_candidate(Candidate(id="", **body.model_dump()), owner_user_id=user["id"])
    except store.AlreadyApplied:
        raise HTTPException(status_code=409, detail="You have already submitted an application")


@router.get("/{candidate_id}", response_model=Candidate)
def get_candidate(candidate_id: str, user: dict = Depends(require_role(*ALL_ROLES))):
    """Get a single candidate by ID. Applicants: only their own."""
    ensure_candidate_access(user, candidate_id)
    return get_candidate_or_404(candidate_id)
