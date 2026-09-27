"""Committee signatures on the decision memo (COM-05).

The table first shipped by editing revision 0003 in place, so databases
already at 0003 never got it and the decision memo failed with "no such
table". It lives here instead; `if_not_exists` covers databases created from
that edited 0003.

committee_signatures is append-only, like the other committee tables.

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-27 12:00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TRIGGERS = [
    """CREATE TRIGGER IF NOT EXISTS trg_committee_signatures_no_update BEFORE UPDATE ON committee_signatures
    BEGIN SELECT RAISE(ABORT, 'committee_signatures is append-only'); END""",
    """CREATE TRIGGER IF NOT EXISTS trg_committee_signatures_no_delete BEFORE DELETE ON committee_signatures
    WHEN EXISTS (SELECT 1 FROM applicants WHERE id = OLD.applicant_id)
    BEGIN SELECT RAISE(ABORT, 'committee_signatures is append-only'); END""",
]


def upgrade() -> None:
    op.create_table('committee_signatures',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('applicant_id', sa.String(length=36), nullable=False),
    sa.Column('role', sa.String(length=32), nullable=False),
    sa.Column('signer_user_id', sa.String(length=36), nullable=False),
    sa.Column('signer_name', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['applicant_id'], ['applicants.id'], name=op.f('fk_committee_signatures_applicant_id_applicants'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['signer_user_id'], ['users.id'], name=op.f('fk_committee_signatures_signer_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_committee_signatures')),
    if_not_exists=True,
    )
    op.create_index('ix_committee_signatures_applicant_id', 'committee_signatures', ['applicant_id'], unique=False, if_not_exists=True)
    if op.get_bind().dialect.name == "sqlite":
        for statement in _TRIGGERS:
            op.execute(statement)


def downgrade() -> None:
    # Dropping the table drops its triggers.
    op.drop_index('ix_committee_signatures_applicant_id', table_name='committee_signatures')
    op.drop_table('committee_signatures')
