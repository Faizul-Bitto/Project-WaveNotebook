"""Add whatsapp_number and messenger_url to site_settings

Revision ID: 2025_add_chat_settings
Revises: 2024_add_footer_settings
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2025_add_chat_settings'
down_revision = '2024_add_footer_settings'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('site_settings', sa.Column('whatsapp_number', sa.String(length=50), nullable=True))
    op.add_column('site_settings', sa.Column('messenger_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('site_settings', 'messenger_url')
    op.drop_column('site_settings', 'whatsapp_number')
