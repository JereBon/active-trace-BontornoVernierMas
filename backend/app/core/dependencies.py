"""core/dependencies.py — FastAPI dependency providers.

C-01 implements: get_db (async DB session per request).
C-03 implements: get_current_user (JWT verification, identity from token).

Reserved slots (filled by future changes):
  - get_tenant        → C-02 (resolve tenant from JWT claims)
  - require_permission → C-04 (RBAC enforcement)

Design rule: identity ALWAYS comes from the verified JWT token, never
from URL params, request body, or headers supplied by the client.
"""

import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError
from app.core.security import decode_access_token
from app.models.usuario import Usuario

# OAuth2 scheme — token extracted from Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a single async DB session for the duration of a request.

    Opens a session, yields it, and closes it in the finally block to
    guarantee the connection is returned to the pool even on exceptions
    (prevents connection leaks).

    Note: imports app.core.database at call time (not module import time) so
    that the module-level async_session_factory variable is read after it has
    been set by create_engine_and_session() during application lifespan.
    """
    from app.core.database import async_session_factory  # read at call time

    assert async_session_factory is not None, (
        "Database not initialized. Call create_engine_and_session() at startup."
    )
    session = async_session_factory()
    try:
        yield session
    finally:
        await session.close()


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Usuario:
    """Resolve the authenticated user from the Bearer JWT.

    Identity is derived EXCLUSIVELY from the verified JWT — never from
    request parameters, body, or any other client-supplied data.

    Args:
        token:   Raw JWT string extracted from the Authorization header.
        session: Database session for the user lookup.

    Returns:
        The active Usuario corresponding to the verified JWT claims.

    Raises:
        HTTPException 401: Token is missing, invalid, expired, or the user
                           no longer exists / is inactive.
    """
    from fastapi import HTTPException, status

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(token)
    except AuthError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Reject challenge tokens — they must NOT grant access to protected endpoints
    if payload.get("type") == "2fa_challenge":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Challenge token cannot be used to access protected resources",
            headers={"WWW-Authenticate": "Bearer"},
        )

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Lookup the user in DB to confirm existence and activo status
    from sqlalchemy import select

    try:
        user_id = uuid.UUID(sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        )

    stmt = select(Usuario).where(
        Usuario.id == user_id,
        Usuario.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    usuario = result.scalar_one_or_none()

    if usuario is None or not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return usuario


# Convenience type aliases for routers
DBSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[Usuario, Depends(get_current_user)]
