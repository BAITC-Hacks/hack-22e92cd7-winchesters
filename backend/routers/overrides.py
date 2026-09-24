"""Committee override ledger (COM-01).

Committee and admin only: the whole router carries the guard. A committee
member changes one competency's BARS level with a mandatory reason code; the
change is appended, never written over the AI's level, and the history shows
who changed what from what to what, and when.

Replaces `POST /api/scoring/override`, which rewrote a cached 0–100 dimension
score in place with no record.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator

from backend.db import overrides as store
from backend.db.candidates import applicant_id_for
from backend.db.overrides import NOTE_REQUIRED, REASON_LABELS, ReasonCode
from backend.ledger.schema import Competency, Level
from backend.routers.guards import require_role
from backend.security import Role

router = APIRouter(
    prefix="/api/overrides",
    tags=["overrides"],
    dependencies=[Depends(require_role(Role.COMMITTEE, Role.ADMIN))],
)


# ── Models ─────────────────────────────────────────────────────────


class ReasonCodeOut(BaseModel):
    code: ReasonCode
    label: str
    note_required: bool


class OverrideCreate(BaseModel):
    competency: Competency
    to_level: Level
    reason_code: ReasonCode
    note: str = Field("", max_length=1000)
    # The AI level the card showed. Only used when the server has no stored
    # competency score to take it from (until LED-11, always).
    ai_level: Level | None = None

    @model_validator(mode="after")
    def _note_when_required(self) -> OverrideCreate:
        self.note = self.note.strip()
        if self.reason_code in NOTE_REQUIRED and not self.note:
            raise ValueError(f"reason code '{self.reason_code.value}' needs a note")
        return self


class Author(BaseModel):
    id: str
    full_name: str
    role: str


class OverrideOut(BaseModel):
    id: str
    competency: str
    from_level: str | None
    to_level: str
    reason_code: str | None
    note: str
    ai_level: str | None
    ai_level_source: str
    author: Author
    created_at: datetime


class OverrideHistory(BaseModel):
    candidate_id: str
    overrides: list[OverrideOut]


# ── Routes ─────────────────────────────────────────────────────────


def _applicant_or_404(candidate_id: str) -> str:
    applicant_id = applicant_id_for(candidate_id)
    if applicant_id is None:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
    return applicant_id


# Declared before `/{candidate_id}`, which would otherwise take it as an id.
@router.get("/reason-codes", response_model=list[ReasonCodeOut])
def reason_codes():
    return [
        ReasonCodeOut(code=code, label=REASON_LABELS[code], note_required=code in NOTE_REQUIRED) for code in ReasonCode
    ]


@router.get("/{candidate_id}", response_model=OverrideHistory)
def history(candidate_id: str):
    """Every override for the candidate, oldest first."""
    return OverrideHistory(candidate_id=candidate_id, overrides=store.list_overrides(_applicant_or_404(candidate_id)))


@router.post("/{candidate_id}", response_model=OverrideOut, status_code=201)
def create(
    candidate_id: str,
    body: OverrideCreate,
    user: dict[str, Any] = Depends(require_role(Role.COMMITTEE, Role.ADMIN)),
):
    applicant_id = _applicant_or_404(candidate_id)
    try:
        override_id = store.record_override(
            applicant_id=applicant_id,
            competency=body.competency.value,
            to_level=body.to_level.value,
            reason_code=body.reason_code,
            note=body.note,
            user_id=user["id"],
            reported_ai_level=body.ai_level.value if body.ai_level else None,
        )
    except store.NoChange as exc:
        raise HTTPException(status_code=409, detail=f"No change: {exc}") from exc
    return next(o for o in store.list_overrides(applicant_id) if o["id"] == override_id)
