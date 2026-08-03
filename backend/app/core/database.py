from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# Initialize database engine
engine = create_engine(settings.DATABASE_URL)

# Create database session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Base class for ORM models
class Base(DeclarativeBase):
    pass
