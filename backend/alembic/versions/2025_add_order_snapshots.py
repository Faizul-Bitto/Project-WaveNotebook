"""Add snapshot columns to orders and order_items for backup when user/product deleted

Revision ID: 2025_add_order_snapshots
Revises: (initial)
Create Date: 2025-06-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2025_add_order_snapshots'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Add snapshot columns as nullable (MySQL can't default TEXT columns)
    op.add_column('orders', sa.Column('user_snapshot', sa.Text(), nullable=True))
    op.add_column('order_items', sa.Column('product_snapshot', sa.Text(), nullable=True))
    op.add_column('order_items', sa.Column('variant_snapshot', sa.Text(), nullable=True))

    # 2) Backfill existing rows with '{}'
    op.execute("UPDATE orders SET user_snapshot = '{}' WHERE user_snapshot IS NULL")
    op.execute("UPDATE order_items SET product_snapshot = '{}' WHERE product_snapshot IS NULL")
    op.execute("UPDATE order_items SET variant_snapshot = '{}' WHERE variant_snapshot IS NULL")

    # 3) Alter to NOT NULL
    op.alter_column('orders', 'user_snapshot', existing_type=sa.Text(), nullable=False)
    op.alter_column('order_items', 'product_snapshot', existing_type=sa.Text(), nullable=False)
    op.alter_column('order_items', 'variant_snapshot', existing_type=sa.Text(), nullable=False)

    # 4) Orders: drop FK, make user_id nullable, re-add FK with SET NULL
    op.drop_constraint('orders_ibfk_1', 'orders', type_='foreignkey')
    op.alter_column('orders', 'user_id', existing_type=sa.Integer(), nullable=True)
    op.create_foreign_key(
        'fk_orders_user_id_users',
        'orders',
        'users',
        ['user_id'],
        ['id'],
        ondelete='SET NULL',
    )

    # 5) Order items: drop FK, make product_id nullable, re-add FK with SET NULL
    op.drop_constraint('order_items_ibfk_2', 'order_items', type_='foreignkey')
    op.alter_column('order_items', 'product_id', existing_type=sa.Integer(), nullable=True)
    op.create_foreign_key(
        'fk_order_items_product_id_products',
        'order_items',
        'products',
        ['product_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    # Order items: revert product_id to NOT NULL, restore CASCADE FK, drop snapshot columns
    op.drop_constraint('fk_order_items_product_id_products', 'order_items', type_='foreignkey')
    op.alter_column('order_items', 'product_id', existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key(
        'order_items_ibfk_2',
        'order_items',
        'products',
        ['product_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.drop_column('order_items', 'variant_snapshot')
    op.drop_column('order_items', 'product_snapshot')

    # Orders: revert user_id to NOT NULL, restore CASCADE FK, drop snapshot column
    op.drop_constraint('fk_orders_user_id_users', 'orders', type_='foreignkey')
    op.alter_column('orders', 'user_id', existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key(
        'orders_ibfk_1',
        'orders',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.drop_column('orders', 'user_snapshot')