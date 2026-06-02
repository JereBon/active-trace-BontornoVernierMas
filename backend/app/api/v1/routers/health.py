"""api/v1/routers/health.py — GET /health endpoint.

Spec (health-check):
- Returns 200 OK with JSON: {"status": "ok", "database": "<up|down>"}
- Verifies DB readiness by executing SELECT 1 via get_db dependency.
- Degrades gracefully: database: "down" if DB unreachable, process stays up.

Design (D4): liveness + readiness in one endpoint for simplicity.
Splitting into /health/live vs /health/ready is an additive change for later.
"""

import logging

from fastapi import APIRouter, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


async def check_db(session: AsyncSession) -> bool:
    """Execute SELECT 1 to verify DB connectivity. Returns True if reachable."""
    try:
        await session.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("DB health check failed", extra={"error": str(exc)})
        return False


@router.get("/health")
async def health_check(request: Request) -> dict:
    """Liveness + readiness health check.

    Returns:
        {"status": "ok", "database": "up"} when fully healthy.
        {"status": "ok", "database": "down"} when DB is unreachable.
    """
    from app.core.database import async_session_factory

    db_status = "down"
    if async_session_factory is not None:
        async with async_session_factory() as session:
            db_ok = await check_db(session)
            db_status = "up" if db_ok else "down"

    return {"status": "ok", "database": db_status}
