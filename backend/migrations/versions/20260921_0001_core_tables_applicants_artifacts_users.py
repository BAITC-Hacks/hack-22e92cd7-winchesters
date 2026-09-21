"""Core tables: applicants, artifacts, users (FND-04, PR 1).

Revision ID: 0001
Revises: (none, first migration)
Create Date: 2026-09-21 14:39:54.075396
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0001'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('applicants',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('legacy_ref', sa.String(length=16), nullable=True),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('age', sa.Integer(), nullable=False),
    sa.Column('application', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_applicants')),
    sa.UniqueConstraint('legacy_ref', name=op.f('uq_applicants_legacy_ref'))
    )
    op.create_table('artifacts',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('applicant_id', sa.String(length=36), nullable=False),
    sa.Column('kind', sa.String(length=32), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('prompt', sa.Text(), nullable=True),
    sa.Column('uri', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['applicant_id'], ['applicants.id'], name=op.f('fk_artifacts_applicant_id_applicants'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_artifacts'))
    )
    with op.batch_alter_table('artifacts', schema=None) as batch_op:
        batch_op.create_index('ix_artifacts_applicant_kind', ['applicant_id', 'kind'], unique=False)

    op.create_table('users',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('email', sa.String(length=320), nullable=False),
    sa.Column('password_hash', sa.Text(), nullable=False),
    sa.Column('full_name', sa.Text(), nullable=False),
    sa.Column('role', sa.String(length=16), nullable=False),
    sa.Column('applicant_id', sa.String(length=36), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['applicant_id'], ['applicants.id'], name=op.f('fk_users_applicant_id_applicants'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    sa.UniqueConstraint('email', name=op.f('uq_users_email'))
    )


def downgrade() -> None:
    op.drop_table('users')
    with op.batch_alter_table('artifacts', schema=None) as batch_op:
        batch_op.drop_index('ix_artifacts_applicant_kind')

    op.drop_table('artifacts')
    op.drop_table('applicants')
