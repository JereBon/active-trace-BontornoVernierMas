"""core/dependencies.py — FastAPI dependency providers.

C-01 implements: get_db (async DB session per request).

RESERVED slots (filled by future changes):
  - get_current_user  → C-03 (JWT verification, identity from token)
  - get_tenant        → C-02 (resolve tenant from JWT claims)
  - require_permission → C-04 (RBAC enforcement)

Design rule: identity ALWAYS comes from the verified JWT token, never
from URL params, request body, or headers supplied by the client.
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a single async DB session for the duration of a request.

    Opens a session, yields it, and closes it in the finally block to
    guarantee the connection is returned to the pool even on exceptions
    (prevents connection leaks).
    """
    assert async_session_factory is not None, (
        "Database not initialized. Call create_engine_and_session() at startup."
    )
    session = async_session_factory()
    try:
        yield session
    finally:
        await session.close()


# Convenience type alias for routers
DBSession = Annotated[AsyncSession, Depends(get_db)]

# ─── RESERVED SLOTS ──────────────────────────────────────────────────────────
# The following dependencies are intentionally absent in C-01.
# They will be implemented in the indicated future changes.
#
#   async def get_current_user(...)  → C-03 (auth/JWT)
#   async def get_tenant(...)        → C-02 (tenancy resolution)
#   async def require_permission(...)→ C-04 (RBAC / fail-closed 403)
