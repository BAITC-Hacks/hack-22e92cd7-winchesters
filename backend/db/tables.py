"""Core tables (FND-04, PR 1): applicants, artifacts, users.

These are storage rows, not the API contract. Routers and the scoring pipeline
keep speaking `backend.models.Candidate`; `backend.db.candidates` converts
between the two. That keeps this PR out of the shared `models.py`, and keeps
the ledger schema (LED-03) free to reshape the API without a storage rewrite.

The rest of the schema (FND-04, PR 2) follows below: the evidence ledger with
its columns taken from LED-03 (backend/ledger/schema.py), model runs, the
committee's overrides, the audit log, and the background attributes LED-01
keeps out of scoring.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, CheckConstraint, Column, DateTime, ForeignKey, Index, String, Text
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
    New kinds (scenario, test) are added here. `kind` is a plain string column
    with no CHECK constraint, so a new kind needs no migration.
    """

    ESSAY = "essay"
    WRITTEN_PRESENTATION = "written_presentation"
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


# ── Teaching challenge (INP-03, storage half) ──────────────────────


class FeynmanStatus(str, Enum):
    ACTIVE = "active"
    # Quiz and scorer calls are in flight. Claimed with a conditional UPDATE so
    # a double-clicked Finish scores the session once.
    SCORING = "scoring"
    FINISHED = "finished"
    # Left open when the applicant started another attempt.
    ABANDONED = "abandoned"


class FeynmanSession(SQLModel, table=True):
    """One attempt at the teaching challenge. Every row counts against
    `settings.FEYNMAN_MAX_ATTEMPTS`, whatever its status: each start costs a
    model call, and finishing is not the only way to learn the questions."""

    __tablename__ = "feynman_sessions"
    __table_args__ = (Index("ix_feynman_sessions_applicant_id", "applicant_id"),)

    id: str = Field(default_factory=_uuid, sa_column=Column(String(36), primary_key=True))
    applicant_id: str = Field(
        sa_column=Column(String(36), ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    )
    # Who started it; only they may continue or finish it.
    user_id: str = Field(sa_column=Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False))
    topic_id: str = Field(sa_column=Column(String(32), nullable=False))
    # The conversation as sent to the model: [{"role", "content"}, ...].
    messages: list[dict[str, str]] = Field(sa_column=Column(JSON, nullable=False))
    exchange_count: int = Field(default=0, nullable=False)
    status: str = Field(default=FeynmanStatus.ACTIVE.value, sa_column=Column(String(16), nullable=False))
    created_at: datetime = _created_at()
    finished_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))


class FeynmanScoreRecord(SQLModel, table=True):
    """The scorer's verdict on one finished session. Written once, never edited."""

    __tablename__ = "feynman_scores"
    __table_args__ = (Index("ix_feynman_scores_applicant_id", "applicant_id"),)

    id: str = Field(default_factory=_uuid, sa_column=Column(String(36), primary_key=True))
    session_id: str = Field(
        sa_column=Column(
            String(36), ForeignKey("feynman_sessions.id", ondelete="CASCADE"), unique=True, nullable=False
        )
    )
    applicant_id: str = Field(
        sa_column=Column(String(36), ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    )
    clarity: float = Field(nullable=False)
    patience: float = Field(nullable=False)
    empathy: float = Field(nullable=False)
    adaptability: float = Field(nullable=False)
    quiz_transfer_score: float = Field(nullable=False)
    overall_score: float = Field(nullable=False)
    summary: str = Field(sa_column=Column(Text, nullable=False))
    # [{"question", "answer", "confident"}, ...] as shown to the committee.
    quiz_answers: list[dict[str, Any]] = Field(sa_column=Column(JSON, nullable=False))
    # Which model judged, so a score can be traced after MODEL_JUDGE changes.
    model: str = Field(sa_column=Column(String(64), nullable=False))
    created_at: datetime = _created_at()


# ── Versions (FND-04, PR 2) ────────────────────────────────────────


class RubricVersion(SQLModel, table=True):
    """A rubric a score was computed under (`CandidateLedger.rubric_version`).

    The rubric itself stays in backend/ledger/rubric.py. The hash is what makes
    the version string honest: two scores stamped "provisional-0.1" are only
    comparable if the rubric behind them was the same.
    """

    __tablename__ = "rubric_versions"

    id: str = Field(default_factory=_uuid, sa_column=Column(String(36), primary_key=True))
    version: str = Field(sa_column=Column(String(32), unique=True, nullable=False))
    # sha256 hex of the rubric content.
    content_hash: str = Field(sa_column=Column(String(64), nullable=False))
    created_at: datetime = _created_at()


class PromptVersion(SQLModel, table=True):
    """The prompts a ledger was built with (`CandidateLedger.prompt_version`).

    One version covers every stage of a pipeline run, as in the ledger; which
    stage a call belonged to is recorded on the model run.
    """

    __tablename__ = "prompt_versions"

    id: str = Field(default_factory=_uuid, sa_column=Column(String(36), primary_key=True))
    version: str = Field(sa_column=Column(String(32), unique=True, nullable=False))
    # sha256 hex of the prompt templates.
    content_hash: str = Field(sa_column=Column(String(64), nullable=False))
    created_at: datetime = _created_at()


# ── Model runs ─────────────────────────────────────────────────────


class ModelRunStatus(str, Enum):
    OK = "ok"
    # The call failed or its reply did not parse. Recorded as such, never as a
    # zero score: a missing answer and a low answer are different facts.
    FAILED = "failed"


class ModelRun(SQLModel, table=True):
    """One model call and what came back, whatever its shape.

    `output` is generic JSON so one table serves the ledger stages, the teaching
    challenge and whatever comes next, without a table per output shape. The
    checks make a failed run impossible to read as a result: an ok run must
    carry output, a failed one must say why.
    """

    __tablename__ = "model_runs"
    __table_args__ = (
        Index("ix_model_runs_applicant_id", "applicant_id"),
        CheckConstraint("status IN ('ok', 'failed')", name="status_values"),
        CheckConstraint(
            "(status = 'ok' AND output IS NOT NULL) OR (status = 'failed' AND error IS NOT NULL)",
            name="status_payload",
        ),
    )

    id: str = Field(default_factory=_uuid, sa_column=Column(String(36), primary_key=True))
    # Empty for a call about no applicant (an eval harness run, say).
    applicant_id: str | None = Field(
        default=None, sa_column=Column(String(36), ForeignKey("applicants.id", ondelete="CASCADE"))
    )
    # extract | rate | chat | ...; free text so a new stage needs no migration.
    stage: str = Field(sa_column=Column(String(16), nullable=False))
    model: str = Field(sa_column=Column(String(64), nullable=False))
    prompt_version_id: str | None = Field(
        default=None, sa_column=Column(String(36), ForeignKey("prompt_versions.id", ondelete="RESTRICT"))
    )
    rubric_version_id: str | None = Field(
        default=None, sa_column=Column(String(36), ForeignKey("rubric_versions.id", ondelete="RESTRICT"))
    )
    status: str = Field(sa_column=Column(String(8), nullable=False))
    # none_as_null: without it SQLAlchemy stores Python None as the JSON text
    # 'null', which is NOT NULL to SQLite and would slip past the check above.
    output: Any = Field(default=None, sa_column=Column(JSON(none_as_null=True)))
    error: str | None = Field(default=None, sa_column=Column(Text))
    created_at: datetime = _created_at()


# ── Evidence ledger (LED-03) ───────────────────────────────────────
#
# One row per `CompetencyRating`, per `IndicatorRating` and per `EvidenceItem`,
# nested the way the contract nests them. Columns mirror the contract's fields
# by name; tests/test_db_schema.py fails when the two drift apart. Enums are
# stored as their string values; the contract validates them.


class CompetencyScore(SQLModel, table=True):
    """One of the nine blocks for one applicant, as the committee card shows it.

    Also carries the ledger's header fields (schema, rubric and prompt version,
    models), because there is no ledger row: an applicant's ledger is the
    latest score per competency. A re-score adds rows.
    """

    __tablename__ = "competency_scores"
    __table_args__ = (Index("ix_competency_scores_applicant_competency", "applicant_id", "competency"),)

    id: str = Field(default_factory=_uuid, sa_column=Column(String(36), primary_key=True))
    applicant_id: str = Field(
        sa_column=Column(String(36), ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    )
    competency: str = Field(sa_column=Column(String(32), nullable=False))
    # Empty when the rubric reserves the competency for humans.
    level: str | None = Field(default=None, sa_column=Column(String(16)))
    rule_applied: str = Field(default="", sa_column=Column(String(8), nullable=False))
    reserved_for_humans: bool = Field(default=False, nullable=False)
    contrastive: str = Field(default="", sa_column=Column(Text, nullable=False))
    probe_question: str = Field(default="", sa_column=Column(Text, nullable=False))
    # [AttentionFlag, ...]. Flags route to a human and never move a number, so
    # nothing queries into them.
    flags: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    schema_version: str = Field(sa_column=Column(String(16), nullable=False))
    rubric_version_id: str = Field(
        sa_column=Column(String(36), ForeignKey("rubric_versions.id", ondelete="RESTRICT"), nullable=False)
    )
    prompt_version_id: str = Field(
        sa_column=Column(String(36), ForeignKey("prompt_versions.id", ondelete="RESTRICT"), nullable=False)
    )
    model_judge: str = Field(sa_column=Column(String(64), nullable=False))
    model_extract: str = Field(sa_column=Column(String(64), nullable=False))
    # The two calls behind this row. Empty until llm.py records runs.
    extract_run_id: str | None = Field(
        default=None, sa_column=Column(String(36), ForeignKey("model_runs.id", ondelete="SET NULL"))
    )
    rate_run_id: str | None = Field(
        default=None, sa_column=Column(String(36), ForeignKey("model_runs.id", ondelete="SET NULL"))
    )
    created_at: datetime = _created_at()


class Rating(SQLModel, table=True):
    """One behavioural indicator within a competency score (`IndicatorRating`)."""

    __tablename__ = "ratings"
    __table_args__ = (Index("ix_ratings_competency_score_id", "competency_score_id"),)

    id: str = Field(default_factory=_uuid, sa_column=Column(String(36), primary_key=True))
    competency_score_id: str = Field(
        sa_column=Column(String(36), ForeignKey("competency_scores.id", ondelete="CASCADE"), nullable=False)
    )
    applicant_id: str = Field(
        sa_column=Column(String(36), ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    )
    indicator_id: str = Field(sa_column=Column(String(64), nullable=False))
    observed_level: str = Field(sa_column=Column(String(16), nullable=False))
    note: str = Field(default="", sa_column=Column(Text, nullable=False))
    created_at: datetime = _created_at()


class EvidenceItemRecord(SQLModel, table=True):
    """One quote attached to one indicator rating (`EvidenceItem`).

    Append-only (see APPEND_ONLY_TABLES): a quote is what a level was defended
    with, and a defence that can be edited afterwards is not one. Rows go only
    when their applicant is deleted.
    """

    __tablename__ = "evidence_items"
    __table_args__ = (Index("ix_evidence_items_rating_id", "rating_id"),)

    id: str = Field(default_factory=_uuid, sa_column=Column(String(36), primary_key=True))
    rating_id: str = Field(
        sa_column=Column(String(36), ForeignKey("ratings.id", ondelete="CASCADE"), nullable=False)
    )
    # Also what the delete trigger checks: a row may be deleted only once its
    # applicant row is gone, i.e. as part of erasing the applicant.
    applicant_id: str = Field(
        sa_column=Column(String(36), ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    )
    quote: str = Field(sa_column=Column(Text, nullable=False))
    source: str = Field(sa_column=Column(String(32), nullable=False))
    # The artifact the quote was taken from; the contract's "" is stored as NULL.
    source_ref: str | None = Field(
        default=None, sa_column=Column(String(36), ForeignKey("artifacts.id", ondelete="CASCADE"))
    )
    char_start: int = Field(default=-1, nullable=False)
    char_end: int = Field(default=-1, nullable=False)
    atola: str = Field(default="none", sa_column=Column(String(16), nullable=False))
    status: str = Field(default="present", sa_column=Column(String(16), nullable=False))
    verified: bool = Field(default=False, nullable=False)
    indicator_hint: str = Field(default="", sa_column=Column(String(64), nullable=False))
    created_at: datetime = _created_at()


class CommitteeSignatureRecord(SQLModel, table=True):
    """One append-only signature in a committee decision workflow."""

    __tablename__ = "committee_signatures"
    __table_args__ = (Index("ix_committee_signatures_applicant_id", "applicant_id"),)

    id: str = Field(default_factory=_uuid, sa_column=Column(String(36), primary_key=True))
    applicant_id: str = Field(
        sa_column=Column(String(36), ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    )
    role: str = Field(sa_column=Column(String(32), nullable=False))
    signer_user_id: str = Field(
        sa_column=Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    )
    signer_name: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = _created_at()


# ── Committee and audit ────────────────────────────────────────────


class CommitteeOverrideRecord(SQLModel, table=True):
    """A human changing a competency level. Append-only.

    The AI's row in competency_scores is never touched; the effective level is
    the latest override, else the AI level. `from_level` is what the committee
    saw when overriding, so the record stands on its own after a re-score.
    """

    __tablename__ = "committee_overrides"
    __table_args__ = (Index("ix_committee_overrides_applicant_competency", "applicant_id", "competency"),)

    id: str = Field(default_factory=_uuid, sa_column=Column(String(36), primary_key=True))
    applicant_id: str = Field(
        sa_column=Column(String(36), ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    )
    competency: str = Field(sa_column=Column(String(32), nullable=False))
    # Empty for a competency reserved for humans, which has no AI level.
    from_level: str | None = Field(default=None, sa_column=Column(String(16)))
    to_level: str = Field(sa_column=Column(String(16), nullable=False))
    reason: str = Field(sa_column=Column(Text, nullable=False))
    # RESTRICT, not SET NULL: SET NULL is an UPDATE, which the append-only
    # trigger rejects, and who overrode must outlive the account anyway.
    user_id: str = Field(
        sa_column=Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    )
    created_at: datetime = _created_at()


class AuditLogEntry(SQLModel, table=True):
    """Who did what to which object. Append-only, with no exception.

    No foreign key to applicants on purpose: erasing an applicant must leave
    the record that the erasure happened. `object_id` is therefore a plain
    string, and before/after must not carry applicant text.
    """

    __tablename__ = "audit_log"
    __table_args__ = (Index("ix_audit_log_object", "object_type", "object_id"),)

    id: str = Field(default_factory=_uuid, sa_column=Column(String(36), primary_key=True))
    # Empty for actions the system takes on its own (a retention job).
    actor_user_id: str | None = Field(
        default=None, sa_column=Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"))
    )
    action: str = Field(sa_column=Column(String(64), nullable=False))
    object_type: str = Field(sa_column=Column(String(32), nullable=False))
    object_id: str = Field(sa_column=Column(String(36), nullable=False))
    before: Any = Field(default=None, sa_column=Column(JSON(none_as_null=True)))
    after: Any = Field(default=None, sa_column=Column(JSON(none_as_null=True)))
    created_at: datetime = _created_at()


# Tables whose rows are never updated or deleted, enforced by SQLite triggers
# created in migration 0003. A batch-mode rebuild (copy, drop, rename) drops a
# table's triggers along with the old table; backend/migrations/env.py refuses
# to finish a migration that leaves one of these tables without them.
APPEND_ONLY_TABLES = ("evidence_items", "committee_overrides", "committee_signatures", "audit_log")


def append_only_trigger_names(table: str) -> tuple[str, str]:
    return (f"trg_{table}_no_update", f"trg_{table}_no_delete")


# ── Background and consent ─────────────────────────────────────────


class ProtectedAttributesRecord(SQLModel, table=True):
    """Self-declared background, for audits only (LED-01, `ProtectedAttributes`).

    Nothing references this table: no rating, score or run may join to it, and
    the scoring path never reads it. A fairness audit joins it to scores by
    applicant_id, outside the pipeline.
    """

    __tablename__ = "protected_attributes"

    id: str = Field(default_factory=_uuid, sa_column=Column(String(36), primary_key=True))
    applicant_id: str = Field(
        sa_column=Column(
            String(36), ForeignKey("applicants.id", ondelete="CASCADE"), unique=True, nullable=False
        )
    )
    school_type: str = Field(default="", sa_column=Column(String(32), nullable=False))
    application_language: str = Field(default="", sa_column=Column(String(16), nullable=False))
    languages_spoken: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    region: str = Field(default="", sa_column=Column(String(64), nullable=False))
    settlement_type: str = Field(default="", sa_column=Column(String(16), nullable=False))
    foundation_eligible: bool | None = Field(default=None)
    gender: str = Field(default="", sa_column=Column(String(16), nullable=False))
    created_at: datetime = _created_at()


class Consent(SQLModel, table=True):
    """One consent given for one purpose. Withdrawing sets `withdrawn_at`."""

    __tablename__ = "consents"
    __table_args__ = (Index("ix_consents_applicant_id", "applicant_id"),)

    id: str = Field(default_factory=_uuid, sa_column=Column(String(36), primary_key=True))
    applicant_id: str = Field(
        sa_column=Column(String(36), ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    )
    # data_processing | video_processing | ai_preassessment
    kind: str = Field(sa_column=Column(String(32), nullable=False))
    # applicant | legal_representative (under-18s, FND-09)
    given_by: str = Field(sa_column=Column(String(32), nullable=False))
    # Version of the consent text that was shown.
    version: str = Field(sa_column=Column(String(32), nullable=False))
    given_at: datetime = _created_at()
    withdrawn_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
