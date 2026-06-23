"""add generation cap and auto-approve users

Revision ID: b7e2d4f9a1c3
Revises: a1b2c3d4e5f6
Create Date: 2026-06-23 00:00:00.000001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7e2d4f9a1c3'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('generation_limit', sa.Integer(), nullable=False, server_default='5'))
    op.add_column('users', sa.Column('generations_used', sa.Integer(), nullable=False, server_default='0'))

    # Backfill usage from real history so the cap reflects past generations, not zero.
    op.execute(
        """
        UPDATE users SET generations_used = sub.cnt
        FROM (SELECT user_id, COUNT(*) AS cnt FROM cover_letters GROUP BY user_id) sub
        WHERE users.id = sub.user_id
        """
    )

    # Auto-approve everyone currently stuck pending.
    op.execute("UPDATE users SET status = 'approved' WHERE status = 'pending'")
    op.alter_column('users', 'status', server_default='approved')


def downgrade() -> None:
    op.alter_column('users', 'status', server_default='pending')
    op.drop_column('users', 'generations_used')
    op.drop_column('users', 'generation_limit')
