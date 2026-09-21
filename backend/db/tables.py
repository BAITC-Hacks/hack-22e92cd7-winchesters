"""Core tables (FND-04, PR 1): applicants, artifacts, users.

These are storage rows, not the API contract. Routers and the scoring pipeline
keep speaking `backend.models.Candidate`; `backend.db.candidates` converts
between the two. That keeps this PR out of the shared `models.py`, and keeps
the ledger schema (LED-03) free to reshape the API without a storage rewrite.

The rest of the schema (model_runs, evidence_items, ratings, ...) lands in
PR 2 with its columns taken from LED-03.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, String, Text
from sqlmodel import Field, SQLModel

# Every constraint gets a deterministic name. SQLite migrations rebuild tables
# in batch mode, and Alembic can only drop or alter a constraint it can name;
# an unnamed unique constraint becomes impossible to change later.
SQLModel.metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


def _created_at() -> Any:
    return Field(default_factory=_now, sa_column=Column(DateTime(timezone=True), nullable=False))


class ArtifactKind(str, Enum):
    """What an applicant submitted. One row per submission.

    Must stay aligned with the evidence `source` vocabulary LED-03 defines:
    an evidence quote points at an artifact, and the ledger names its source.
    New kinds (written_presentation for INP-01, scenario, test) are added here.
    """

    ESSAY = "essay"
    INTERVIEW_TRANSCRIPT = "interview_transcript"
    VIDEO_TRANSCRIPT = "video_transcript"
    RECOMMENDATION = "recommendation"


class Applicant(SQLModel, table=True):
    __tablename__ = "applicants"

    # UUID from day one: FND-07 exposes it everywhere, and nothing about an
    # applicant should be guessable from their id.
    id: str = Field(default_factory=_uuid, sa_column=Column(String(36), primary_key=True))
    # The `c-001` ids the frontend and the demo script still use. Unique, so
    # two concurrent registrations can no longer mint the same one.
    legacy_ref: str | None = Field(default=None, sa_column=Column(String(16), unique=True))
    name: str = Field(sa_column=Column(Text, nullable=False))
    age: int = Field(nullable=False)
    # Education, activities, projects, languages, skills, as submitted. Stays a
    # document until LED-01 moves school type / region / language into
    # protected_attributes (PR 2); promoting columns before that would put
    # demographic proxies into the schema we are about to remove them from.
    application: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    created_at: datetime = _created_at()


class Artifact(SQLModel, table=True):
    """Applicant-supplied text, one row per submission.

    Rows are never edited: evidence items will quote an artifact by character
    span, and a span is only meaningful against the exact text the model saw.
    A resubmission is a new row; the latest per kind is current.
    """

    __tablename__ = "artifacts"
    __table_args__ = (Index("ix_artifacts_applicant_kind", "applicant_id", "kind"),)

    id: str = Field(default_factory=_uuid, sa_column=Column(String(36), primary_key=True))
    applicant_id: str = Field(
        sa_column=Column(String(36), ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    )
    kind: str = Field(sa_column=Column(String(32), nullable=False))
    content: str = Field(sa_column=Column(Text, nullable=False))
    # Essay question, when the artifact answers one.
    prompt: str | None = Field(default=None, sa_column=Column(Text))
    # Where the original lives (video link), when the text is derived from it.
    uri: str | None = Field(default=None, sa_column=Column(Text))
    created_at: datetime = _created_at()


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=_uuid, sa_column=Column(String(36), primary_key=True))
    email: str = Field(sa_column=Column(String(320), unique=True, nullable=False))
    password_hash: str = Field(sa_column=Column(Text, nullable=False))
    full_name: str = Field(sa_column=Column(Text, nullable=False))
    # applicant | interviewer | committee | admin (backend.security.Role). The
    # guards in backend/routers/guards.py read it from here on every request.
    role: str = Field(default="applicant", sa_column=Column(String(16), nullable=False))
    applicant_id: str | None = Field(
        default=None,
        sa_column=Column(String(36), ForeignKey("applicants.id", ondelete="SET NULL")),
    )
    created_at: datetime = _created_at()
