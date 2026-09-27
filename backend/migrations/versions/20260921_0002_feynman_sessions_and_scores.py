"""Teaching challenge sessions and scores (INP-03, storage half, PR 4).

Replaces the in-memory `_sessions` and `_score_cache` in
backend/routers/feynman.py, which lost every session and score on restart and
let an applicant start as many attempts as they liked.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-21 18:00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0002'
down_revision: str | Sequence[str] | None = '0001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('feynman_sessions',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('applicant_id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('topic_id', sa.String(length=32), nullable=False),
    sa.Column('messages', sa.JSON(), nullable=False),
    sa.Column('exchange_count', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['applicant_id'], ['applicants.id'], name=op.f('fk_feynman_sessions_applicant_id_applicants'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_feynman_sessions_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_feynman_sessions'))
    )
    with op.batch_alter_table('feynman_sessions', schema=None) as batch_op:
        batch_op.create_index('ix_feynman_sessions_applicant_id', ['applicant_id'], unique=False)

    op.create_table('feynman_scores',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('session_id', sa.String(length=36), nullable=False),
    sa.Column('applicant_id', sa.String(length=36), nullable=False),
    sa.Column('clarity', sa.Float(), nullable=False),
    sa.Column('patience', sa.Float(), nullable=False),
    sa.Column('empathy', sa.Float(), nullable=False),
    sa.Column('adaptability', sa.Float(), nullable=False),
    sa.Column('quiz_transfer_score', sa.Float(), nullable=False),
    sa.Column('overall_score', sa.Float(), nullable=False),
    sa.Column('summary', sa.Text(), nullable=False),
    sa.Column('quiz_answers', sa.JSON(), nullable=False),
    sa.Column('model', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['applicant_id'], ['applicants.id'], name=op.f('fk_feynman_scores_applicant_id_applicants'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['session_id'], ['feynman_sessions.id'], name=op.f('fk_feynman_scores_session_id_feynman_sessions'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_feynman_scores')),
    sa.UniqueConstraint('session_id', name=op.f('uq_feynman_scores_session_id'))
    )
    with op.batch_alter_table('feynman_scores', schema=None) as batch_op:
        batch_op.create_index('ix_feynman_scores_applicant_id', ['applicant_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('feynman_scores', schema=None) as batch_op:
        batch_op.drop_index('ix_feynman_scores_applicant_id')

    op.drop_table('feynman_scores')
    with op.batch_alter_table('feynman_sessions', schema=None) as batch_op:
        batch_op.drop_index('ix_feynman_sessions_applicant_id')

    op.drop_table('feynman_sessions')
