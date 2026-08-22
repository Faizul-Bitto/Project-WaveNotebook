"""Add favicon_url column to site_settings table

Revision ID: 2026_add_favicon_url
Revises: 2026_add_shipping_charges
Create Date: 2026-08-22 21:17:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2026_add_favicon_url'
down_revision = '2026_add_shipping_charges'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('site_settings', sa.Column('favicon_url', sa.String(length=500), nullable=True, server_default=None))


def downgrade() -> None:
    op.drop_column('site_settings', 'favicon_url')
