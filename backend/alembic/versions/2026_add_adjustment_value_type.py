"""Add value_type column to order_adjustments

Revision ID: 2026_add_adjustment_value_type
Revises: 2026_add_spend_based_discount
Create Date: 2026-08-17 20:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2026_add_adjustment_value_type'
down_revision = '2026_add_order_adjustments'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'order_adjustments',
        sa.Column(
            'value_type',
            sa.String(20),
            nullable=True,
            server_default='flat',
            comment='flat | percentage',
        ),
    )


def downgrade() -> None:
    op.drop_column('order_adjustments', 'value_type')