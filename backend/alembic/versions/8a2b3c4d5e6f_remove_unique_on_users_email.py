"""remove unique constraint on users.email

Revision ID: 8a2b3c4d5e6f
Revises: 6f1d0aa3f842
Create Date: 2026-08-24 06:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a2b3c4d5e6f'
down_revision: Union[str, Sequence[str], None] = '6f1d0aa3f842'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove the unique constraint on users.email so multiple users can share an email."""
    op.drop_index('ix_users_email', table_name='users')
    op.create_index('ix_users_email', 'users', ['email'], unique=False)


def downgrade() -> None:
    """Re-add the unique constraint on users.email."""
    op.drop_index('ix_users_email', table_name='users')
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
