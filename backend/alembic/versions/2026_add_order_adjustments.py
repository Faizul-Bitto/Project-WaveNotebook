"""Add order_adjustments table for manual admin discounts

Revision ID: 2026_add_order_adjustments
Revises: 2026_add_order_item_bonus
Create Date: 2026-08-17 00:20:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2026_add_order_adjustments'
down_revision = '2026_add_order_item_bonus'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'order_adjustments',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('order_id', sa.Integer,
                  sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('admin_user_id', sa.Integer,
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('adjustment_type', sa.String(50), nullable=False,
                  server_default='manual_discount'),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('reason', sa.Text, nullable=True,
                  comment='Admin-provided reason for the adjustment'),
        sa.Column('before_total', sa.Numeric(10, 2), nullable=True),
        sa.Column('after_total', sa.Numeric(10, 2), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('order_adjustments')