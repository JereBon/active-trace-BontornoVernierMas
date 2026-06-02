"""Tests for GET /health endpoint.

TDD cycle:
  RED  (5.1) — this file written BEFORE health.py and main.py exist
  GREEN (5.2) — implement health.py router → tests pass
  TRIANGULATE (5.3) — add DB-down case
"""

import pytest
from httpx import AsyncClient


class TestHealthEndpointUp:
    """Scenario: La aplicación está viva y DB alcanzable."""

    @pytest.mark.asyncio
    async def test_health_returns_200(self, async_client: AsyncClient):
        """GET /health responds 200 OK when the app is running."""
        response = await async_client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_response_is_json(self, async_client: AsyncClient):
        """GET /health returns a JSON body."""
        response = await async_client.get("/health")
        assert response.headers["content-type"].startswith("application/json")

    @pytest.mark.asyncio
    async def test_health_has_status_field(self, async_client: AsyncClient):
        """Response JSON includes a 'status' field."""
        response = await async_client.get("/health")
        body = response.json()
        assert "status" in body

    @pytest.mark.asyncio
    async def test_health_status_is_ok(self, async_client: AsyncClient):
        """Response JSON has status == 'ok' when app is healthy."""
        response = await async_client.get("/health")
        body = response.json()
        assert body["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health_has_database_field(self, async_client: AsyncClient):
        """Response JSON includes a 'database' readiness field."""
        response = await async_client.get("/health")
        body = response.json()
        assert "database" in body

    @pytest.mark.asyncio
    async def test_health_database_is_up_when_db_reachable(
        self, async_client: AsyncClient
    ):
        """Scenario: Base de datos alcanzable — database field is 'up'."""
        response = await async_client.get("/health")
        body = response.json()
        # When connected to the real test DB, database should be 'up'
        assert body["database"] == "up"


class TestHealthEndpointDbDown:
    """Scenario: Base de datos inalcanzable — endpoint degrades gracefully."""

    @pytest.mark.asyncio
    async def test_health_returns_200_when_db_down(
        self, monkeypatch, async_client: AsyncClient
    ):
        """GET /health still returns 200 even when DB is unreachable.

        Simulates DB failure by patching the router's execute call.
        The process must NOT crash — it degrades to database: 'down'.
        """
        from unittest.mock import AsyncMock, patch
        from sqlalchemy.exc import OperationalError

        # Patch at the session level to simulate DB failure
        with patch(
            "app.api.v1.routers.health.check_db",
            new_callable=AsyncMock,
            return_value=False,
        ):
            response = await async_client.get("/health")

        assert response.status_code == 200
        body = response.json()
        assert body["database"] == "down"
        # App must still report its own status
        assert body["status"] == "ok"
