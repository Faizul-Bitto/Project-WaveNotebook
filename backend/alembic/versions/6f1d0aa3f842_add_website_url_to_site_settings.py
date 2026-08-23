"""add website_url to site_settings

Revision ID: 6f1d0aa3f842
Revises: 
Create Date: 2026-08-24 04:01:44.397646

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f1d0aa3f842'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "site_settings",
        sa.Column("website_url", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("site_settings", "website_url")
