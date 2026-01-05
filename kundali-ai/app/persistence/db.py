from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.config import settings

# ─────────────────────────────────────────────────────────────
# Base for ORM models (REQUIRED for Alembic)
# ─────────────────────────────────────────────────────────────

Base = declarative_base()

# ─────────────────────────────────────────────────────────────
# Database Engine
# ─────────────────────────────────────────────────────────────

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,          # SQL logs only in debug
    pool_pre_ping=True,           # avoids stale connections
)

# ─────────────────────────────────────────────────────────────
# Session Factory
# ─────────────────────────────────────────────────────────────

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,       # VERY IMPORTANT
    autoflush=False,
    autocommit=False,
)

# ─────────────────────────────────────────────────────────────
# Dependency for FastAPI
# ─────────────────────────────────────────────────────────────

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields an async database session.

    Usage:
        db: AsyncSession = Depends(get_db_session)
    """
    async with AsyncSessionLocal() as session:
        yield session
