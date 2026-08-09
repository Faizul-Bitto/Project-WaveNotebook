"""Add hotline_number to site_settings

Revision ID: 2025_add_hotline_number
Revises: 2025_add_chat_settings
Create Date: 2025-01-01 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2025_add_hotline_number'
down_revision = '2025_add_chat_settings'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('site_settings', sa.Column('hotline_number', sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column('site_settings', 'hotline_number')
