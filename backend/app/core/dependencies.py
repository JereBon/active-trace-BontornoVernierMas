"""core/dependencies.py — FastAPI dependency providers.

C-01 implements: get_db (async DB session per request).
C-03 implements: get_current_user (JWT verification, identity from token).
C-04 extends:    get_current_user now resolves effective permissions via RBAC.

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
from app.core.schemas import UsuarioAutenticado
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
) -> UsuarioAutenticado:
    """Resolve the authenticated user and their effective RBAC permissions.

    C-04 extension: after verifying the JWT and loading the Usuario row,
    this dependency also resolves permisos_efectivos via UsuarioRolRepository
    and returns a UsuarioAutenticado object.

    Identity is derived EXCLUSIVELY from the verified JWT — never from
    request parameters, body, or any other client-supplied data.

    Args:
        token:   Raw JWT string extracted from the Authorization header.
        session: Database session for the user + permission lookup.

    Returns:
        UsuarioAutenticado with user_id, tenant_id, roles, permisos_efectivos.

    Raises:
        HTTPException 401: Token is missing, invalid, expired, or the user
                           no longer exists / is inactive.
    """
    from fastapi import HTTPException, status
    from sqlalchemy import select

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

    try:
        user_id = uuid.UUID(sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        )

    # Lookup the user in DB to confirm existence and activo status
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

    # ── C-04: resolve effective permissions ───────────────────────────────────
    from app.repositories.usuario_rol import UsuarioRolRepository  # avoid cycle

    repo = UsuarioRolRepository(session, usuario.tenant_id)
    permisos_efectivos = await repo.get_permisos_efectivos(usuario.id)

    # Resolve role codes for the user (active assignments only)
    from sqlalchemy import and_, or_
    from datetime import date
    from app.models.usuario_rol import UsuarioRol
    from app.models.rol import Rol

    today = date.today()
    roles_stmt = (
        select(Rol.codigo)
        .join(UsuarioRol, UsuarioRol.rol_id == Rol.id)
        .where(
            UsuarioRol.usuario_id == usuario.id,
            UsuarioRol.tenant_id == usuario.tenant_id,
            UsuarioRol.deleted_at.is_(None),
            UsuarioRol.vig_desde <= today,
            or_(
                UsuarioRol.vig_hasta.is_(None),
                UsuarioRol.vig_hasta >= today,
            ),
        )
        .distinct()
    )
    roles_result = await session.execute(roles_stmt)
    roles = list(roles_result.scalars().all())

    return UsuarioAutenticado(
        user_id=usuario.id,
        tenant_id=usuario.tenant_id,
        roles=roles,
        permisos_efectivos=permisos_efectivos,
    )


# Convenience type aliases for routers
DBSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[UsuarioAutenticado, Depends(get_current_user)]
