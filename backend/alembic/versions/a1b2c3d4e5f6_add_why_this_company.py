"""add why_this_company and make cover_letter/fit_analysis nullable

Revision ID: a1b2c3d4e5f6
Revises: f3a9c4e1b2d7
Create Date: 2026-06-16 00:00:00.000001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f3a9c4e1b2d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('cover_letters', sa.Column('why_this_company', sa.Text(), nullable=True))
    op.alter_column('cover_letters', 'cover_letter', existing_type=sa.JSON(), nullable=True)
    op.alter_column('cover_letters', 'fit_analysis', existing_type=sa.JSON(), nullable=True)


def downgrade() -> None:
    op.alter_column('cover_letters', 'fit_analysis', existing_type=sa.JSON(), nullable=False)
    op.alter_column('cover_letters', 'cover_letter', existing_type=sa.JSON(), nullable=False)
    op.drop_column('cover_letters', 'why_this_company')
