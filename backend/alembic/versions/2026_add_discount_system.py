"""Create discount system tables

Revision ID: 2026_add_discount_system
Revises: 2026_add_order_email
Create Date: 2026-08-16 20:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2026_add_discount_system'
down_revision = '2026_add_order_email'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- discounts ---
    op.create_table(
        'discounts',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('type', sa.String(50), nullable=False,
                  comment='percentage | flat | bundle | bogo | free_shipping'),
        sa.Column('value_type', sa.String(20), nullable=True,
                  comment='percentage | flat  (NULL for bundle, bogo, free_shipping)'),
        sa.Column('value', sa.Numeric(10, 2), nullable=True,
                  comment='percentage (0-100) or flat amount'),
        sa.Column('max_discount_cap', sa.Numeric(10, 2), nullable=True,
                  comment='Cap total discount for percentage discounts (optional)'),
        sa.Column('start_date', sa.DateTime, nullable=False),
        sa.Column('end_date', sa.DateTime, nullable=True,
                  comment='NULL means unlimited time'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # --- discount_scopes ---
    op.create_table(
        'discount_scopes',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('discount_id', sa.Integer,
                  sa.ForeignKey('discounts.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('scope_type', sa.String(20), nullable=False,
                  comment='product | category'),
        sa.Column('scope_id', sa.Integer, nullable=False),
    )

    # --- bundle_rules ---
    op.create_table(
        'bundle_rules',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('discount_id', sa.Integer,
                  sa.ForeignKey('discounts.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('bundle_type', sa.String(20), nullable=False,
                  comment='quantity | combo'),
        sa.Column('required_products', sa.Text, nullable=True,
                  comment='JSON array of product IDs for combo bundles'),
        sa.Column('free_shipping', sa.Boolean, nullable=False, server_default=sa.false()),
    )

    # --- bundle_slabs ---
    op.create_table(
        'bundle_slabs',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('bundle_rule_id', sa.Integer,
                  sa.ForeignKey('bundle_rules.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('min_quantity', sa.Integer, nullable=False),
        sa.Column('value_type', sa.String(20), nullable=False,
                  comment='percentage | flat'),
        sa.Column('value', sa.Numeric(10, 2), nullable=False),
    )

    # --- bogo_rules ---
    op.create_table(
        'bogo_rules',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('discount_id', sa.Integer,
                  sa.ForeignKey('discounts.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('product_id', sa.Integer,
                  sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('buy_quantity', sa.Integer, nullable=False),
        sa.Column('get_quantity', sa.Integer, nullable=False),
        sa.Column('get_discount_percent', sa.Numeric(10, 2), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # --- discount_usage ---
    op.create_table(
        'discount_usage',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('discount_id', sa.Integer,
                  sa.ForeignKey('discounts.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('order_id', sa.Integer,
                  sa.ForeignKey('orders.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('applied_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # Add discount tracking columns to existing tables
    op.add_column('orders', sa.Column('total_discount',
        sa.Numeric(10, 2), nullable=False, server_default='0'))
    op.add_column('order_items', sa.Column('discount_amount',
        sa.Numeric(10, 2), nullable=False, server_default='0'))
    op.add_column('orders', sa.Column('discount_snapshot',
        sa.Text, nullable=False, server_default='{}'))


def downgrade() -> None:
    op.drop_column('orders', 'discount_snapshot')
    op.drop_column('order_items', 'discount_amount')
    op.drop_column('orders', 'total_discount')
    op.drop_table('discount_usage')
    op.drop_table('bogo_rules')
    op.drop_table('bundle_slabs')
    op.drop_table('bundle_rules')
    op.drop_table('discount_scopes')
    op.drop_table('discounts')
