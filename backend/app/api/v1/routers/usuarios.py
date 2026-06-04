"""api/v1/routers/usuarios.py — Usuario and profile endpoints (C-07).

Identity and tenant_id always come from the verified JWT (CurrentUser).

Endpoints:
  POST   /v1/users           Create user (requires usuarios:gestionar)
  GET    /v1/users           List all users (requires usuarios:gestionar)
  GET    /v1/users/{id}      Get user details (requires usuarios:gestionar)
  PUT    /v1/users/{id}      Update user profile (requires usuarios:gestionar)
  PUT    /v1/users/{id}/deactivate  Deactivate user (requires usuarios:gestionar)
  GET    /v1/me              Get own profile (authenticated only, no special permission)
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import CurrentUser, DBSession
from app.core.exceptions import NotFoundError
from app.core.permisos import USUARIOS_GESTIONAR
from app.core.rbac import require_permission
from app.schemas.usuario import UsuarioCreate, UsuarioListItem, UsuarioOut, UsuarioUpdate
from app.services.usuario import UsuarioService

router = APIRouter(
    prefix="/v1",
    tags=["usuarios"],
)


# ── Protected endpoints (require usuarios:gestionar) ─────────────────────────

@router.post(
    "/users",
    response_model=UsuarioOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(USUARIOS_GESTIONAR))],
)
async def create_usuario(
    body: UsuarioCreate,
    session: DBSession,
    current_user: CurrentUser,
) -> UsuarioOut:
    """Create a new usuario in the current tenant."""
    svc = UsuarioService(session, current_user.tenant_id)
    data = await svc.crear_usuario(body)
    await session.commit()
    return UsuarioOut(**data)


@router.get(
    "/users",
    response_model=list[UsuarioListItem],
    dependencies=[Depends(require_permission(USUARIOS_GESTIONAR))],
)
async def list_usuarios(
    session: DBSession,
    current_user: CurrentUser,
) -> list[UsuarioListItem]:
    """List all active usuarios in the current tenant."""
    svc = UsuarioService(session, current_user.tenant_id)
    users = await svc.listar_usuarios()
    return [UsuarioListItem(**u) for u in users]


@router.get(
    "/users/{usuario_id}",
    response_model=UsuarioOut,
    dependencies=[Depends(require_permission(USUARIOS_GESTIONAR))],
)
async def get_usuario(
    usuario_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> UsuarioOut:
    """Get a single usuario by ID."""
    svc = UsuarioService(session, current_user.tenant_id)
    try:
        data = await svc.obtener_usuario(usuario_id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario not found")
    return UsuarioOut(**data)


@router.put(
    "/users/{usuario_id}",
    response_model=UsuarioOut,
    dependencies=[Depends(require_permission(USUARIOS_GESTIONAR))],
)
async def update_usuario(
    usuario_id: uuid.UUID,
    body: UsuarioUpdate,
    session: DBSession,
    current_user: CurrentUser,
) -> UsuarioOut:
    """Update a usuario's profile fields."""
    svc = UsuarioService(session, current_user.tenant_id)
    try:
        data = await svc.actualizar_usuario(usuario_id, body)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario not found")
    await session.commit()
    return UsuarioOut(**data)


@router.put(
    "/users/{usuario_id}/deactivate",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(USUARIOS_GESTIONAR))],
)
async def deactivate_usuario(
    usuario_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> None:
    """Deactivate (soft-disable) a usuario."""
    svc = UsuarioService(session, current_user.tenant_id)
    try:
        await svc.desactivar_usuario(usuario_id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario not found")
    await session.commit()


# ── Own profile (authenticated only, no special permission required) ──────────

@router.get(
    "/me",
    response_model=UsuarioOut,
)
async def get_me(
    session: DBSession,
    current_user: CurrentUser,
) -> UsuarioOut:
    """Return the authenticated user's own profile.

    Identity is always from the verified JWT — never from a request param.
    """
    svc = UsuarioService(session, current_user.tenant_id)
    try:
        data = await svc.obtener_perfil_propio(current_user.user_id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario not found")
    return UsuarioOut(**data)
