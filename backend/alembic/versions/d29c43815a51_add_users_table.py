"""add users table

Revision ID: d29c43815a51
Revises: c1ce25249d18
Create Date: 2026-06-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd29c43815a51'
down_revision: Union[str, Sequence[str], None] = 'c1ce25249d18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    user_status = sa.Enum('pending', 'approved', 'rejected', name='user_status')
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('picture', sa.String(length=1024), nullable=True),
    sa.Column('provider', sa.String(length=50), nullable=False),
    sa.Column('provider_user_id', sa.String(length=255), nullable=False),
    sa.Column('status', user_status, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    sa.Enum(name='user_status').drop(op.get_bind())
