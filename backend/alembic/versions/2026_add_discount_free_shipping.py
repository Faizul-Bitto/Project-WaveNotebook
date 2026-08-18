"""add free_shipping to discounts

Revision ID: 2026_add_discount_free_shipping
Revises: 2026_add_spend_based_discount
Create Date: 2026-08-17 02:39:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '2026_add_discount_free_shipping'
down_revision = '2026_add_spend_based_discount'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'discounts',
        sa.Column('free_shipping', sa.Boolean(), nullable=False, server_default=sa.text('0')),
    )


def downgrade():
    op.drop_column('discounts', 'free_shipping')
