from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from starlette import status

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.logger import logger
from app.core.security import (
    hash_password,
    verify_password,
)

# Import all models so SQLAlchemy can register them
from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.file import File
from app.models.attribute import Attribute
from app.models.attribute_option import AttributeOption
from app.models.product_attribute import ProductAttribute
from app.models.order import Order
from app.models.order_item import OrderItem

# Import routers
from app.apis import auth, category, attribute, attribute_option, product, file
from app.apis.admin import category as admin_category
from app.apis.admin import attribute as admin_attribute
from app.apis.admin import attribute_option as admin_attribute_option
from app.apis.admin import product as admin_product
from app.apis.admin import file as admin_file


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
)


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


# ==========================================================
# Admin Routers
# ==========================================================
app.include_router(admin_category.router)
app.include_router(admin_attribute.router)
app.include_router(admin_attribute_option.router)
app.include_router(admin_product.router)
app.include_router(admin_file.router)


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
