"""The rest of the schema: evidence ledger, model runs, versions, committee
overrides, audit log, protected attributes, consents (FND-04, PR 2).

Ledger columns come from the LED-03 contract (backend/ledger/schema.py),
protected_attributes from LED-01 (backend/scoring/protected_attributes.py).

evidence_items, committee_overrides and audit_log are append-only, enforced
by the triggers at the bottom of upgrade(). Their SQL is written out here
rather than imported, so this revision creates the same thing forever. Any
later migration that rebuilds one of those tables in batch mode must recreate
its triggers; backend/migrations/env.py fails the migration if it does not.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-21 17:42:06
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0003'
down_revision: str | Sequence[str] | None = '0002'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Append-only. UPDATE is always rejected. DELETE is rejected while the row's
# applicant still exists, so erasing an applicant (ON DELETE CASCADE) still
# works: SQLite runs the cascade after the parent row is gone. audit_log has no
# applicant and no exception.
_APPEND_ONLY_TRIGGERS = [
    """CREATE TRIGGER trg_evidence_items_no_update BEFORE UPDATE ON evidence_items
    BEGIN SELECT RAISE(ABORT, 'evidence_items is append-only'); END""",
    """CREATE TRIGGER trg_evidence_items_no_delete BEFORE DELETE ON evidence_items
    WHEN EXISTS (SELECT 1 FROM applicants WHERE id = OLD.applicant_id)
    BEGIN SELECT RAISE(ABORT, 'evidence_items is append-only'); END""",
    """CREATE TRIGGER trg_committee_overrides_no_update BEFORE UPDATE ON committee_overrides
    BEGIN SELECT RAISE(ABORT, 'committee_overrides is append-only'); END""",
    """CREATE TRIGGER trg_committee_overrides_no_delete BEFORE DELETE ON committee_overrides
    WHEN EXISTS (SELECT 1 FROM applicants WHERE id = OLD.applicant_id)
    BEGIN SELECT RAISE(ABORT, 'committee_overrides is append-only'); END""",
    """CREATE TRIGGER trg_committee_signatures_no_update BEFORE UPDATE ON committee_signatures
    BEGIN SELECT RAISE(ABORT, 'committee_signatures is append-only'); END""",
    """CREATE TRIGGER trg_committee_signatures_no_delete BEFORE DELETE ON committee_signatures
    WHEN EXISTS (SELECT 1 FROM applicants WHERE id = OLD.applicant_id)
    BEGIN SELECT RAISE(ABORT, 'committee_signatures is append-only'); END""",
    """CREATE TRIGGER trg_audit_log_no_update BEFORE UPDATE ON audit_log
    BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END""",
    """CREATE TRIGGER trg_audit_log_no_delete BEFORE DELETE ON audit_log
    BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END""",
]


def upgrade() -> None:
    op.create_table('prompt_versions',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('version', sa.String(length=32), nullable=False),
    sa.Column('content_hash', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_prompt_versions')),
    sa.UniqueConstraint('version', name=op.f('uq_prompt_versions_version'))
    )
    op.create_table('rubric_versions',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('version', sa.String(length=32), nullable=False),
    sa.Column('content_hash', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_rubric_versions')),
    sa.UniqueConstraint('version', name=op.f('uq_rubric_versions_version'))
    )
    op.create_table('consents',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('applicant_id', sa.String(length=36), nullable=False),
    sa.Column('kind', sa.String(length=32), nullable=False),
    sa.Column('given_by', sa.String(length=32), nullable=False),
    sa.Column('version', sa.String(length=32), nullable=False),
    sa.Column('given_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('withdrawn_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['applicant_id'], ['applicants.id'], name=op.f('fk_consents_applicant_id_applicants'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_consents'))
    )
    with op.batch_alter_table('consents', schema=None) as batch_op:
        batch_op.create_index('ix_consents_applicant_id', ['applicant_id'], unique=False)

    op.create_table('model_runs',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('applicant_id', sa.String(length=36), nullable=True),
    sa.Column('stage', sa.String(length=16), nullable=False),
    sa.Column('model', sa.String(length=64), nullable=False),
    sa.Column('prompt_version_id', sa.String(length=36), nullable=True),
    sa.Column('rubric_version_id', sa.String(length=36), nullable=True),
    sa.Column('status', sa.String(length=8), nullable=False),
    sa.Column('output', sa.JSON(none_as_null=True), nullable=True),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("(status = 'ok' AND output IS NOT NULL) OR (status = 'failed' AND error IS NOT NULL)", name=op.f('ck_model_runs_status_payload')),
    sa.CheckConstraint("status IN ('ok', 'failed')", name=op.f('ck_model_runs_status_values')),
    sa.ForeignKeyConstraint(['applicant_id'], ['applicants.id'], name=op.f('fk_model_runs_applicant_id_applicants'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['prompt_version_id'], ['prompt_versions.id'], name=op.f('fk_model_runs_prompt_version_id_prompt_versions'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['rubric_version_id'], ['rubric_versions.id'], name=op.f('fk_model_runs_rubric_version_id_rubric_versions'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_model_runs'))
    )
    with op.batch_alter_table('model_runs', schema=None) as batch_op:
        batch_op.create_index('ix_model_runs_applicant_id', ['applicant_id'], unique=False)

    op.create_table('protected_attributes',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('applicant_id', sa.String(length=36), nullable=False),
    sa.Column('school_type', sa.String(length=32), nullable=False),
    sa.Column('application_language', sa.String(length=16), nullable=False),
    sa.Column('languages_spoken', sa.JSON(), nullable=False),
    sa.Column('region', sa.String(length=64), nullable=False),
    sa.Column('settlement_type', sa.String(length=16), nullable=False),
    sa.Column('foundation_eligible', sa.Boolean(), nullable=True),
    sa.Column('gender', sa.String(length=16), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['applicant_id'], ['applicants.id'], name=op.f('fk_protected_attributes_applicant_id_applicants'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_protected_attributes')),
    sa.UniqueConstraint('applicant_id', name=op.f('uq_protected_attributes_applicant_id'))
    )
    op.create_table('audit_log',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('actor_user_id', sa.String(length=36), nullable=True),
    sa.Column('action', sa.String(length=64), nullable=False),
    sa.Column('object_type', sa.String(length=32), nullable=False),
    sa.Column('object_id', sa.String(length=36), nullable=False),
    sa.Column('before', sa.JSON(none_as_null=True), nullable=True),
    sa.Column('after', sa.JSON(none_as_null=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], name=op.f('fk_audit_log_actor_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_log'))
    )
    with op.batch_alter_table('audit_log', schema=None) as batch_op:
        batch_op.create_index('ix_audit_log_object', ['object_type', 'object_id'], unique=False)

    op.create_table('committee_overrides',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('applicant_id', sa.String(length=36), nullable=False),
    sa.Column('competency', sa.String(length=32), nullable=False),
    sa.Column('from_level', sa.String(length=16), nullable=True),
    sa.Column('to_level', sa.String(length=16), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['applicant_id'], ['applicants.id'], name=op.f('fk_committee_overrides_applicant_id_applicants'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_committee_overrides_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_committee_overrides'))
    )
    with op.batch_alter_table('committee_overrides', schema=None) as batch_op:
        batch_op.create_index('ix_committee_overrides_applicant_competency', ['applicant_id', 'competency'], unique=False)

    op.create_table('committee_signatures',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('applicant_id', sa.String(length=36), nullable=False),
    sa.Column('role', sa.String(length=32), nullable=False),
    sa.Column('signer_user_id', sa.String(length=36), nullable=False),
    sa.Column('signer_name', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['applicant_id'], ['applicants.id'], name=op.f('fk_committee_signatures_applicant_id_applicants'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['signer_user_id'], ['users.id'], name=op.f('fk_committee_signatures_signer_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_committee_signatures'))
    )
    with op.batch_alter_table('committee_signatures', schema=None) as batch_op:
        batch_op.create_index('ix_committee_signatures_applicant_id', ['applicant_id'], unique=False)

    op.create_table('competency_scores',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('applicant_id', sa.String(length=36), nullable=False),
    sa.Column('competency', sa.String(length=32), nullable=False),
    sa.Column('level', sa.String(length=16), nullable=True),
    sa.Column('rule_applied', sa.String(length=8), nullable=False),
    sa.Column('reserved_for_humans', sa.Boolean(), nullable=False),
    sa.Column('contrastive', sa.Text(), nullable=False),
    sa.Column('probe_question', sa.Text(), nullable=False),
    sa.Column('flags', sa.JSON(), nullable=False),
    sa.Column('schema_version', sa.String(length=16), nullable=False),
    sa.Column('rubric_version_id', sa.String(length=36), nullable=False),
    sa.Column('prompt_version_id', sa.String(length=36), nullable=False),
    sa.Column('model_judge', sa.String(length=64), nullable=False),
    sa.Column('model_extract', sa.String(length=64), nullable=False),
    sa.Column('extract_run_id', sa.String(length=36), nullable=True),
    sa.Column('rate_run_id', sa.String(length=36), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['applicant_id'], ['applicants.id'], name=op.f('fk_competency_scores_applicant_id_applicants'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['extract_run_id'], ['model_runs.id'], name=op.f('fk_competency_scores_extract_run_id_model_runs'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['prompt_version_id'], ['prompt_versions.id'], name=op.f('fk_competency_scores_prompt_version_id_prompt_versions'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['rate_run_id'], ['model_runs.id'], name=op.f('fk_competency_scores_rate_run_id_model_runs'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['rubric_version_id'], ['rubric_versions.id'], name=op.f('fk_competency_scores_rubric_version_id_rubric_versions'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_competency_scores'))
    )
    with op.batch_alter_table('competency_scores', schema=None) as batch_op:
        batch_op.create_index('ix_competency_scores_applicant_competency', ['applicant_id', 'competency'], unique=False)

    op.create_table('ratings',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('competency_score_id', sa.String(length=36), nullable=False),
    sa.Column('applicant_id', sa.String(length=36), nullable=False),
    sa.Column('indicator_id', sa.String(length=64), nullable=False),
    sa.Column('observed_level', sa.String(length=16), nullable=False),
    sa.Column('note', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['applicant_id'], ['applicants.id'], name=op.f('fk_ratings_applicant_id_applicants'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['competency_score_id'], ['competency_scores.id'], name=op.f('fk_ratings_competency_score_id_competency_scores'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_ratings'))
    )
    with op.batch_alter_table('ratings', schema=None) as batch_op:
        batch_op.create_index('ix_ratings_competency_score_id', ['competency_score_id'], unique=False)

    op.create_table('evidence_items',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('rating_id', sa.String(length=36), nullable=False),
    sa.Column('applicant_id', sa.String(length=36), nullable=False),
    sa.Column('quote', sa.Text(), nullable=False),
    sa.Column('source', sa.String(length=32), nullable=False),
    sa.Column('source_ref', sa.String(length=36), nullable=True),
    sa.Column('char_start', sa.Integer(), nullable=False),
    sa.Column('char_end', sa.Integer(), nullable=False),
    sa.Column('atola', sa.String(length=16), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('verified', sa.Boolean(), nullable=False),
    sa.Column('indicator_hint', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['applicant_id'], ['applicants.id'], name=op.f('fk_evidence_items_applicant_id_applicants'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['rating_id'], ['ratings.id'], name=op.f('fk_evidence_items_rating_id_ratings'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['source_ref'], ['artifacts.id'], name=op.f('fk_evidence_items_source_ref_artifacts'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_evidence_items'))
    )
    with op.batch_alter_table('evidence_items', schema=None) as batch_op:
        batch_op.create_index('ix_evidence_items_rating_id', ['rating_id'], unique=False)

    for statement in _APPEND_ONLY_TRIGGERS:
        op.execute(statement)


def downgrade() -> None:
    # Dropping a table drops its triggers.
    with op.batch_alter_table('evidence_items', schema=None) as batch_op:
        batch_op.drop_index('ix_evidence_items_rating_id')

    op.drop_table('evidence_items')
    with op.batch_alter_table('ratings', schema=None) as batch_op:
        batch_op.drop_index('ix_ratings_competency_score_id')

    op.drop_table('ratings')
    with op.batch_alter_table('competency_scores', schema=None) as batch_op:
        batch_op.drop_index('ix_competency_scores_applicant_competency')

    op.drop_table('competency_scores')
    with op.batch_alter_table('committee_overrides', schema=None) as batch_op:
        batch_op.drop_index('ix_committee_overrides_applicant_competency')

    op.drop_table('committee_overrides')
    with op.batch_alter_table('committee_signatures', schema=None) as batch_op:
        batch_op.drop_index('ix_committee_signatures_applicant_id')

    op.drop_table('committee_signatures')
    with op.batch_alter_table('audit_log', schema=None) as batch_op:
        batch_op.drop_index('ix_audit_log_object')

    op.drop_table('audit_log')
    op.drop_table('protected_attributes')
    with op.batch_alter_table('model_runs', schema=None) as batch_op:
        batch_op.drop_index('ix_model_runs_applicant_id')

    op.drop_table('model_runs')
    with op.batch_alter_table('consents', schema=None) as batch_op:
        batch_op.drop_index('ix_consents_applicant_id')

    op.drop_table('consents')
    op.drop_table('rubric_versions')
    op.drop_table('prompt_versions')
