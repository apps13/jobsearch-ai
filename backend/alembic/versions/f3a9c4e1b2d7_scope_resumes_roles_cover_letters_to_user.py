"""scope resumes, roles, cover_letters to user

Revision ID: f3a9c4e1b2d7
Revises: d29c43815a51
Create Date: 2026-06-15 00:00:00.000001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a9c4e1b2d7'
down_revision: Union[str, Sequence[str], None] = 'd29c43815a51'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    for table in ('resumes', 'roles', 'cover_letters'):
        op.add_column(table, sa.Column('user_id', sa.Integer(), nullable=True))

    # Backfill existing rows to the earliest-created user (single-user data so far).
    op.execute(
        """
        UPDATE resumes SET user_id = (SELECT id FROM users ORDER BY id LIMIT 1)
        WHERE user_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE roles SET user_id = (SELECT id FROM users ORDER BY id LIMIT 1)
        WHERE user_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE cover_letters SET user_id = (SELECT id FROM users ORDER BY id LIMIT 1)
        WHERE user_id IS NULL
        """
    )

    for table in ('resumes', 'roles', 'cover_letters'):
        op.alter_column(table, 'user_id', nullable=False)
        op.create_index(op.f(f'ix_{table}_user_id'), table, ['user_id'])
        op.create_foreign_key(
            f'fk_{table}_user_id_users', table, 'users', ['user_id'], ['id']
        )


def downgrade() -> None:
    """Downgrade schema."""
    for table in ('resumes', 'roles', 'cover_letters'):
        op.drop_constraint(f'fk_{table}_user_id_users', table, type_='foreignkey')
        op.drop_index(op.f(f'ix_{table}_user_id'), table_name=table)
        op.drop_column(table, 'user_id')
