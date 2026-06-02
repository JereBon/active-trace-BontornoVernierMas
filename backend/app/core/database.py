"""core/database.py — Async SQLAlchemy 2.0 engine, session factory, and Base.

Design decisions (D3):
- Single async engine per process, created at startup via lifespan.
- async_sessionmaker with expire_on_commit=False to avoid lazy-load errors
  after commit (important for async where lazy loads would fail).
- One session per request via dependency injection (get_db in dependencies.py).
- Sessions MUST NOT be shared between requests.
"""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


# Module-level variables; populated by create_engine_and_session().
# Using None as sentinel so callers that import before lifespan setup
# get an AttributeError rather than a silent failure.
engine: AsyncEngine | None = None
async_session_factory: async_sessionmaker[AsyncSession] | None = None


def create_engine_and_session(database_url: str) -> None:
    """Initialize the async engine and session factory.

    Called once during application startup (lifespan). Idempotent: calling
    it again overwrites the module globals (useful in tests).
    """
    global engine, async_session_factory

    engine = create_async_engine(
        database_url,
        echo=False,  # set True for SQL debug logging
        pool_pre_ping=True,  # verifies connections before checkout
    )
    async_session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def dispose_engine() -> None:
    """Dispose the engine pool on shutdown (called from lifespan teardown)."""
    global engine
    if engine is not None:
        await engine.dispose()
        engine = None
