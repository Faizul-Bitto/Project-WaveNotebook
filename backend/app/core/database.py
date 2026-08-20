from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# Initialize database engine with connection pool settings.
# pool_pre_ping: validates connections before use, automatically
#   reconnecting if the server has closed them (common with NeonDB's
#   serverless pooler which drops idle connections).
# pool_recycle: forces connection recycling every 300 seconds (5 min)
#   to stay ahead of NeonDB's idle connection timeout.
# pool_size / max_overflow: keep a modest pool since NeonDB's pooler
#   already multiplexes connections server-side.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10,
)

# Create database session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Base class for ORM models
class Base(DeclarativeBase):
    pass
