"""Tests for app/main.py — FastAPI application startup.

TDD cycle:
  RED  (5.4) — this file written BEFORE main.py exists
  GREEN (5.5) — implement main.py → tests pass
"""

import pytest
from httpx import AsyncClient


class TestAppStartup:
    """Scenario: La app FastAPI se instancia/arranca sin error."""

    def test_create_application_returns_fastapi_instance(self, monkeypatch):
        """create_application() returns a FastAPI app without raising."""
        from fastapi import FastAPI

        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)

        import importlib
        import app.core.config as config_module
        importlib.reload(config_module)

        from app.main import create_application

        application = create_application()
        assert isinstance(application, FastAPI)

    @pytest.mark.asyncio
    async def test_app_lifespan_starts_without_error(self, async_client: AsyncClient):
        """The app processes at least one request after startup — lifespan ran OK."""
        response = await async_client.get("/health")
        # Any non-500 response proves the app started (lifespan ran without crashing)
        assert response.status_code < 500

    def test_health_router_registered(self, monkeypatch):
        """The /health route is registered on the app."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)

        import importlib
        import app.core.config as config_module
        importlib.reload(config_module)

        from app.main import create_application

        application = create_application()
        paths = [route.path for route in application.routes]
        assert "/health" in paths
