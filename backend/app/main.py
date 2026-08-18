from contextlib import asynccontextmanager
from time import perf_counter
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from sqlalchemy import text
from starlette import status

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.logger import logger
from app.core.security import (
    hash_password,
    verify_password,
)
from app.services.file_storage import check_storage_connection

# Import all models so SQLAlchemy can register them
from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.file import File
from app.models.attribute import Attribute
from app.models.attribute_option import AttributeOption
from app.models.product_attribute import ProductAttribute
from app.models.product_attribute_option import ProductAttributeOption
from app.models.product_variant import ProductVariant
from app.models.cart_item import CartItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.banner import Banner
from app.models.site_settings import SiteSettings
from app.models.expense import Expense
from app.models.expense_type import ExpenseType
from app.models.payment_by import PaymentBy
from app.models.payment_method import PaymentMethod
from app.models.discount import Discount
from app.models.discount_scope import DiscountScope
from app.models.bundle_rule import BundleRule
from app.models.bundle_slab import BundleSlab
from app.models.bogo_rule import BogoRule
from app.models.discount_usage import DiscountUsage
from app.models.order_adjustment import OrderAdjustment
from app.models.shipping_charge import ShippingCharge

# Import routers
from app.apis import auth, category, attribute, attribute_option, product, file, order, cart, lookup, banner, discount
from app.apis import settings as site_settings
from app.apis.admin import category as admin_category
from app.apis.admin import attribute as admin_attribute
from app.apis.admin import attribute_option as admin_attribute_option
from app.apis.admin import product as admin_product
from app.apis.admin import variant as admin_variant
from app.apis.admin import file as admin_file
from app.apis.admin import order as admin_order
from app.apis.admin import user as admin_user
from app.apis.admin import expense as admin_expense
from app.apis.admin import expense as admin_expense  # noqa: F811  (duplicate import preserved per existing code)
from app.apis.admin import banner as admin_banner
from app.apis.admin import settings as admin_settings
from app.apis.admin import discount as admin_discount
from app.apis.admin import shipping_charge as admin_shipping_charge
from app.apis import shipping_charge


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events.
    """

    startup_time = perf_counter()

    try:

        # ==========================================================
        # Check Database Connection
        # ==========================================================
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        logger.info("✅ Database Connected Successfully")

        # ==========================================================
        # Check File Storage Connection
        # ==========================================================
        if check_storage_connection():
            logger.info(
                f"✅ File Storage Connected Successfully | "
                f"Provider={settings.FILE_STORAGE_PROVIDER.upper()}"
            )
        else:
            logger.warning(
                f"⚠️ File Storage Connection Failed | "
                f"Provider={settings.FILE_STORAGE_PROVIDER.upper()} | "
                f"Check credentials in .env"
            )

        # ==========================================================
        # Synchronize Database Tables
        # ==========================================================
        Base.metadata.create_all(bind=engine)

        logger.info("📦 Database Tables Synchronized")

        # ==========================================================
        # Default Admin Setup
        # ==========================================================
        db = SessionLocal()

        try:

            # Find the default admin
            admin_user = db.query(User).filter(User.role == "admin").first()

            if admin_user:

                updated = False

                # Update phone number
                if admin_user.phone_number != settings.DEFAULT_ADMIN_PHONE_NUMBER:
                    admin_user.phone_number = settings.DEFAULT_ADMIN_PHONE_NUMBER
                    updated = True

                # Update email
                if admin_user.email != settings.DEFAULT_ADMIN_EMAIL:
                    admin_user.email = settings.DEFAULT_ADMIN_EMAIL
                    updated = True

                # Update password
                if not verify_password(
                    settings.DEFAULT_ADMIN_PASSWORD,
                    admin_user.password,
                ):

                    admin_user.password = hash_password(settings.DEFAULT_ADMIN_PASSWORD)

                    updated = True

                if updated:
                    db.commit()
                    db.refresh(admin_user)

                    logger.info("🔄 Default Admin Updated Successfully")

                else:
                    logger.info("👤 Default Admin Already Up-to-Date")

            else:
                admin_user = User(
                    phone_number=settings.DEFAULT_ADMIN_PHONE_NUMBER,
                    email=settings.DEFAULT_ADMIN_EMAIL,
                    password=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                    role="admin",
                )

                db.add(admin_user)
                db.commit()
                db.refresh(admin_user)

                logger.info("✅ Default Admin Created Successfully")

        finally:
            db.close()

        # ==========================================================
        # Startup Completed
        # ==========================================================
        elapsed = perf_counter() - startup_time

        logger.info("🚀 Wave Notebook API Started")

        if elapsed < 1:
            logger.info(f"⚡ Startup Time: {elapsed * 1000:.2f} ms")
        else:
            logger.info(f"⚡ Startup Time: {elapsed:.2f} s")

    except Exception:
        logger.exception("❌ Failed to Start Application")

    yield

    # ==========================================================
    # Application Shutdown
    # ==========================================================
    logger.info("🛑 Wave Notebook API Shutdown")


app = FastAPI(
    title="Wave Notebook API",
    version="1.0.0",
    lifespan=lifespan,
    swagger_ui_parameters={
        "tryItOutEnabled": True,  # Show input controls (file pickers) by default
    },
)


def custom_openapi() -> Dict[str, Any]:
    """
    Generate OpenAPI schema with file fields rendered as binary.

    FastAPI 0.141.x generates `contentMediaType: application/octet-stream`
    for UploadFile fields, which Swagger UI does not render as a file picker.
    This conversion replaces it with `format: binary` so Swagger UI shows
    a proper file upload input.
    """
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        openapi_version="3.0.2",
    )

    # Convert file fields from contentMediaType to format: binary
    # so Swagger UI renders a file picker
    def fix_file_fields(obj: Any):
        if isinstance(obj, dict):
            # If this is a file field (has contentMediaType)
            if "contentMediaType" in obj:
                obj["format"] = "binary"
                obj.pop("contentMediaType", None)
            for key, value in obj.items():
                fix_file_fields(value)
        elif isinstance(obj, list):
            for item in obj:
                fix_file_items(item)

    def fix_file_items(item: Any):
        if isinstance(item, dict):
            fix_file_fields(item)
        elif isinstance(item, list):
            for sub in item:
                fix_file_items(sub)

    fix_file_fields(schema)

    # Inline multipart/form-data request body schemas so Swagger UI
    # renders file pickers directly (avoids $ref resolution issues)
    for path, methods in schema.get("paths", {}).items():
        for method, detail in methods.items():
            if not isinstance(detail, dict):
                continue
            request_body = detail.get("requestBody", {})
            content = request_body.get("content", {})
            if "multipart/form-data" in content:
                media = content["multipart/form-data"]
                schema_ref = media.get("schema", {})
                if "$ref" in schema_ref:
                    ref_name = schema_ref["$ref"].split("/")[-1]
                    resolved = (
                        schema.get("components", {})
                        .get("schemas", {})
                        .get(ref_name)
                    )
                    if resolved:
                        media["schema"] = resolved

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi


# ==========================================================
# CORS Middleware
# ==========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================================
# User Routers
# ==========================================================

app.include_router(auth.router)
app.include_router(category.router)
app.include_router(attribute.router)
app.include_router(attribute_option.router)
app.include_router(product.router)
app.include_router(file.router)
app.include_router(order.router)
app.include_router(cart.router)
app.include_router(lookup.router)
app.include_router(banner.router)
app.include_router(site_settings.router)
app.include_router(discount.router)


# ==========================================================
# Admin Routers
# ==========================================================
app.include_router(admin_category.router)
app.include_router(admin_attribute.router)
app.include_router(admin_attribute_option.router)
app.include_router(admin_product.router)
app.include_router(admin_variant.router)
app.include_router(admin_file.router)
app.include_router(admin_order.router)
app.include_router(admin_user.router)
app.include_router(admin_banner.router)
app.include_router(admin_settings.router)
app.include_router(admin_expense.router)
app.include_router(admin_discount.router)
app.include_router(admin_shipping_charge.router)
app.include_router(shipping_charge.router)


# ==========================================================
# API Health
# ==========================================================
@app.get(
    "/healthy",
    tags=["API Health"],
    status_code=status.HTTP_200_OK,
)
async def health_check():
    """
    Health check endpoint.

    Used to verify API availability.
    """

    return {
        "status": "Healthy",
    }