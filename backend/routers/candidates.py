"""Candidate CRUD endpoints."""

from __future__ import annotations

import json
import os
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.models import Application, Candidate, Essay

router = APIRouter(prefix="/api/candidates", tags=["candidates"])

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "candidates.json")
_candidates_cache: list[Candidate] | None = None


def _load_candidates() -> list[Candidate]:
    global _candidates_cache
    if _candidates_cache is not None:
        return _candidates_cache
    with open(_DATA_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    _candidates_cache = [Candidate(**c) for c in raw]
    return _candidates_cache


def _save_candidates(candidates: list[Candidate]) -> None:
    with open(_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump([c.model_dump() for c in candidates], f, ensure_ascii=False, indent=2)


def _get_candidate(candidate_id: str) -> Candidate:
    candidates = _load_candidates()
    for c in candidates:
        if c.id == candidate_id:
            return c
    raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")


# ── Request models ─────────────────────────────────────────────────


class CandidateCreate(BaseModel):
    """Payload for creating a new candidate application."""
    name: str = Field(min_length=1)
    age: int = Field(default=17, ge=14, le=25)
    application: Application
    essay: Essay
    interview_transcript: str = ""
    recommendation_summary: str = ""


# ── Endpoints ──────────────────────────────────────────────────────


@router.get("/", response_model=list[Candidate])
def list_candidates():
    """List all candidates."""
    return _load_candidates()


@router.post("/", response_model=Candidate, status_code=201)
def create_candidate(body: CandidateCreate):
    """Create a new candidate from an application form submission."""
    candidates = _load_candidates()
    # Generate unique ID based on highest existing ID to avoid collisions
    existing_nums = []
    for c in candidates:
        try:
            existing_nums.append(int(c.id.split("-")[1]))
        except (IndexError, ValueError):
            pass
    next_num = max(existing_nums, default=0) + 1
    new_id = f"c-{next_num:03d}"

    candidate = Candidate(
        id=new_id,
        name=body.name,
        age=body.age,
        application=body.application,
        essay=body.essay,
        interview_transcript=body.interview_transcript,
        recommendation_summary=body.recommendation_summary,
    )

    candidates.append(candidate)
    _save_candidates(candidates)
    return candidate


@router.get("/{candidate_id}", response_model=Candidate)
def get_candidate(candidate_id: str):
    """Get a single candidate by ID."""
    return _get_candidate(candidate_id)
