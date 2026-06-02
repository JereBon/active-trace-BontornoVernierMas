"""tests/conftest.py — Shared pytest fixtures for the activia-trace backend.

Fixtures provided:
  - settings_env      : sets env vars for Settings (session-scoped)
  - app               : FastAPI application instance (function-scoped)
  - async_client      : httpx AsyncClient against the test app (function-scoped)
  - db_session        : AsyncSession against test DB (function-scoped)
  - test_session_factory: async_sessionmaker for test DB (session-scoped)

Database: uses a REAL PostgreSQL test database (DATABASE_URL_TEST env var).
No mocking of the DB — per project rules, smoke tests hit the real DB.
"""

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import create_engine_and_session


# ─── Environment helpers ─────────────────────────────────────────────────────


def _get_test_database_url() -> str:
    """Return the test DB URL, falling back to a sensible local default."""
    return os.environ.get(
        "DATABASE_URL_TEST",
        "postgresql+asyncpg://activia:changeme@localhost:5432/activia_trace_test",
    )


# ─── Session-scoped: test engine ─────────────────────────────────────────────


@pytest.fixture(scope="session")
def test_database_url() -> str:
    return _get_test_database_url()


@pytest.fixture(scope="session")
def test_session_factory(test_database_url: str) -> async_sessionmaker[AsyncSession]:
    """Initialize the engine once per test session against the test DB."""
    create_engine_and_session(test_database_url)
    from app.core import database as db_module
    assert db_module.async_session_factory is not None
    return db_module.async_session_factory


# ─── Function-scoped: DB session ─────────────────────────────────────────────


@pytest_asyncio.fixture
async def db_session(test_session_factory: async_sessionmaker[AsyncSession]) -> AsyncSession:
    """Provide an open AsyncSession for a single test, closed afterwards."""
    async with test_session_factory() as session:
        yield session


# ─── Function-scoped: FastAPI app + httpx client ─────────────────────────────


@pytest.fixture
def app(test_database_url: str, monkeypatch):
    """FastAPI app wired to the test database."""
    # Provide required env vars so Settings can instantiate
    monkeypatch.setenv("DATABASE_URL", test_database_url)
    monkeypatch.setenv("DATABASE_URL_TEST", test_database_url)
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-32-characters-ok!")
    monkeypatch.setenv("ENCRYPTION_KEY", "test-encryption-key-32-chars-ok!")

    # Reset the settings singleton so it re-reads from the patched env
    from app.core.config import _reset_settings
    _reset_settings()

    from app.main import create_application
    return create_application()


@pytest_asyncio.fixture
async def async_client(app) -> AsyncClient:
    """httpx AsyncClient pointing at the test FastAPI app via ASGI transport.

    Uses anyio lifespan management to trigger FastAPI's startup/shutdown hooks.
    """
    from asgi_lifespan import LifespanManager

    async with LifespanManager(app) as manager:
        async with AsyncClient(
            transport=ASGITransport(app=manager.app),
            base_url="http://testserver",
        ) as client:
            yield client
