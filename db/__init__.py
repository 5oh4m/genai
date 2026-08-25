"""
Database engine, session factory, and lifecycle management for AEGIS-AI.
Uses async SQLAlchemy with asyncpg for PostgreSQL.
"""

import os
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///aegis_ai.db",
)

engine = create_async_engine(DATABASE_URL, echo=False, pool_size=5, max_overflow=10)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all AEGIS-AI ORM models."""
    pass


async def get_session() -> AsyncSession:
    """FastAPI dependency: yields an async DB session."""
    async with async_session_factory() as session:
        yield session


async def init_db():
    """Create all tables. Called once at startup."""
    async with engine.begin() as conn:
        from db.models import AttackAttempt, DefenseRound  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Dispose of the connection pool. Called at shutdown."""
    await engine.dispose()
