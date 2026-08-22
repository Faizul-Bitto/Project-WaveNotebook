"""Add page_title column to site_settings table

Revision ID: 2026_add_page_title
Revises: 2026_add_favicon_url
Create Date: 2026-08-22 21:36:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2026_add_page_title'
down_revision = '2026_add_favicon_url'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('site_settings', sa.Column('page_title', sa.String(length=255), nullable=True, server_default=None))


def downgrade() -> None:
    op.drop_column('site_settings', 'page_title')
