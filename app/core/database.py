"""
Async database engine and session management.

The async engine and session factory are created once at module load.
Individual sessions are created per-request via the get_db dependency.
Never create sessions directly in service or router code.
"""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

logger = logging.getLogger(__name__)

# pool_pre_ping=True checks connections before use — prevents stale connection errors.
engine = create_async_engine(
    settings.database_url,
    echo=settings.is_development,  # log SQL queries in development only
    pool_pre_ping=True,
)

# Session factory — creates new AsyncSession instances on demand.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # prevents lazy-load errors after commit in async code
)


class Base(DeclarativeBase):
    """
    SQLAlchemy declarative base.

    All SQLAlchemy models in the application inherit from this class.
    Import in models.py files: from app.core.database import Base
    """

    pass


async def get_db() -> AsyncGenerator[AsyncSession]:
    """
    FastAPI dependency that provides a database session per request.

    Usage in routers:
        db: AsyncSession = Depends(get_db)

    The session is committed on success, rolled back on error,
    and always closed when the request completes.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Database session rolled back due to exception")
            raise
        finally:
            await session.close()
