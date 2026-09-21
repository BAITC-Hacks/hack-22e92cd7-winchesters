"""Candidate CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.db import candidates as store
from backend.models import Application, Candidate, Essay

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
def list_candidates():
    """List all candidates."""
    return load_candidates()


@router.post("/", response_model=Candidate, status_code=201)
def create_candidate(body: CandidateCreate):
    """Create a new candidate from an application form submission."""
    # The id is allocated by the store; this placeholder is never saved.
    return store.create_candidate(Candidate(id="", **body.model_dump()))


@router.get("/{candidate_id}", response_model=Candidate)
def get_candidate(candidate_id: str):
    """Get a single candidate by ID."""
    return get_candidate_or_404(candidate_id)
