from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override sqlalchemy.url with runtime settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all models so they're registered with Base.metadata
from app.models.order import Order  # noqa: E402, F401
from app.models.order_item import OrderItem  # noqa: E402, F401
from app.models.product import Product  # noqa: E402, F401
from app.models.product_variant import ProductVariant  # noqa: E402, F401
from app.models.user import User  # noqa: E402, F401
from app.models.category import Category  # noqa: E402, F401
from app.models.attribute import Attribute  # noqa: E402, F401
from app.models.attribute_option import AttributeOption  # noqa: E402, F401
from app.models.product_attribute import ProductAttribute  # noqa: E402, F401
from app.models.product_attribute_option import ProductAttributeOption  # noqa: E402, F401
from app.models.file import File  # noqa: E402, F401
from app.models.banner import Banner  # noqa: E402, F401
from app.models.cart_item import CartItem  # noqa: E402, F401
from app.models.contact import Contact  # noqa: E402, F401
from app.models.site_settings import SiteSettings  # noqa: E402, F401
from app.models.expense import Expense  # noqa: E402, F401
from app.models.expense_type import ExpenseType  # noqa: E402, F401
from app.models.payment_by import PaymentBy  # noqa: E402, F401
from app.models.payment_method import PaymentMethod  # noqa: E402, F401
from app.models.discount import Discount  # noqa: E402, F401
from app.models.discount_scope import DiscountScope  # noqa: E402, F401
from app.models.bundle_rule import BundleRule  # noqa: E402, F401
from app.models.bundle_slab import BundleSlab  # noqa: E402, F401
from app.models.bogo_rule import BogoRule  # noqa: E402, F401
from app.models.discount_usage import DiscountUsage  # noqa: E402, F401

from app.core.database import Base

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()