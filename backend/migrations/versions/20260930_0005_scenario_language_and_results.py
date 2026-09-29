"""Scenarios replace the teaching challenge's 0-100 scores (INP-04).

A scenario is now answered in a chosen language (en / ru / kk) and its result
is one competency rating on the same BARS rules as the essays, not clarity or
empathy points. `feynman_sessions` keeps holding the conversations and the
attempt limit, with the language added; results go to `scenario_results`.
`feynman_scores` is left in place, unread, so no stored row is lost.

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-30 12:00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("feynman_sessions") as batch:
        batch.add_column(sa.Column("language", sa.String(length=8), nullable=False, server_default="en"))
    op.create_table('scenario_results',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('session_id', sa.String(length=36), nullable=False),
    sa.Column('applicant_id', sa.String(length=36), nullable=False),
    sa.Column('competency', sa.String(length=64), nullable=False),
    sa.Column('rating', sa.JSON(), nullable=False),
    sa.Column('source', sa.String(length=16), nullable=False),
    sa.Column('model', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['applicant_id'], ['applicants.id'], name=op.f('fk_scenario_results_applicant_id_applicants'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['session_id'], ['feynman_sessions.id'], name=op.f('fk_scenario_results_session_id_feynman_sessions'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_scenario_results')),
    sa.UniqueConstraint('session_id', name=op.f('uq_scenario_results_session_id')),
    )
    op.create_index('ix_scenario_results_applicant_id', 'scenario_results', ['applicant_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_scenario_results_applicant_id', table_name='scenario_results')
    op.drop_table('scenario_results')
    with op.batch_alter_table("feynman_sessions") as batch:
        batch.drop_column("language")
