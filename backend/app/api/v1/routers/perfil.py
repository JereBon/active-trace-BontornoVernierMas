"""api/v1/routers/perfil.py — Own profile endpoints (C-20: perfil-y-mensajeria-interna).

Identity and tenant_id ALWAYS come from the verified JWT (CurrentUser).
CUIL is read-only; PATCH /api/perfil rejects the 'cuil' field with 422.

Endpoints:
  GET   /v1/perfil   — view own profile (authenticated only)
  PATCH /v1/perfil   — update own editable profile fields (authenticated only)
"""

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import CurrentUser, DBSession
from app.core.exceptions import NotFoundError
from app.schemas.perfil import PerfilOut, PerfilUpdate
from app.services.perfil_service import PerfilService

router = APIRouter(
    prefix="/v1/perfil",
    tags=["perfil"],
)


@router.get(
    "",
    response_model=PerfilOut,
    summary="Get own profile (F11.1)",
)
async def get_perfil(
    session: DBSession,
    current_user: CurrentUser,
) -> PerfilOut:
    """Return the authenticated user's own profile.

    Identity is always from the verified JWT — never from a request parameter.
    """
    svc = PerfilService(session, current_user.tenant_id)
    try:
        data = await svc.obtener_perfil(current_user.user_id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil not found")
    return PerfilOut(**data)


@router.patch(
    "",
    response_model=PerfilOut,
    summary="Update own profile (F11.1) — CUIL is read-only",
)
async def patch_perfil(
    body: PerfilUpdate,
    session: DBSession,
    current_user: CurrentUser,
) -> PerfilOut:
    """Update editable fields of the authenticated user's profile.

    CUIL is read-only and must NOT be sent in the request body.
    extra='forbid' on PerfilUpdate ensures unknown fields (including cuil)
    return 422 Unprocessable Entity automatically.

    Identity is always from the verified JWT — never from a request parameter.
    """
    svc = PerfilService(session, current_user.tenant_id)
    try:
        data = await svc.actualizar_perfil(current_user.user_id, body)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil not found")
    await session.commit()
    return PerfilOut(**data)
