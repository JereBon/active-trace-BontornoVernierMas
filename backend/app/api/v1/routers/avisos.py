"""api/v1/routers/avisos.py — Aviso endpoints (C-15: avisos-y-acknowledgment).

Identity and tenant_id always come from the verified JWT (CurrentUser).

Endpoints:
  POST   /v1/avisos           Create (publish) a new Aviso
  GET    /v1/avisos           List active Avisos visible to the current user
  POST   /v1/avisos/{id}/ack  Acknowledge (confirm reading) an Aviso
  GET    /v1/avisos/{id}/acks List all acknowledgments (admin view)
  PATCH  /v1/avisos/{id}      Soft-delete or toggle activo flag
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import CurrentUser, DBSession
from app.core.permisos import AVISOS_CONFIRMAR, AVISOS_PUBLICAR
from app.core.rbac import require_permission
from app.repositories.aviso_repository import AvisoRepository
from app.schemas.aviso import AvisoAckOut, AvisoCreate, AvisoOut, AvisoPatch

router = APIRouter(
    prefix="/v1/avisos",
    tags=["avisos"],
)


@router.post(
    "",
    response_model=AvisoOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(AVISOS_PUBLICAR))],
)
async def create_aviso(
    body: AvisoCreate,
    session: DBSession,
    current_user: CurrentUser,
) -> AvisoOut:
    """Publish a new Aviso within the current tenant."""
    repo = AvisoRepository(session, current_user.tenant_id)
    aviso = await repo.create_aviso(
        publicado_por=current_user.id,
        data=body.model_dump(),
    )
    await session.commit()
    await session.refresh(aviso)
    return AvisoOut.model_validate(aviso)


@router.get(
    "",
    response_model=list[AvisoOut],
)
async def list_avisos(
    session: DBSession,
    current_user: CurrentUser,
) -> list[AvisoOut]:
    """Return active Avisos visible to the current user (filtered by scope/vigencia)."""
    repo = AvisoRepository(session, current_user.tenant_id)
    roles: list[str] = getattr(current_user, "roles", []) or []
    avisos = await repo.list_vigentes(
        usuario_id=current_user.id,
        roles=roles,
    )
    return [AvisoOut.model_validate(a) for a in avisos]


@router.post(
    "/{aviso_id}/ack",
    response_model=AvisoAckOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission(AVISOS_CONFIRMAR))],
)
async def ack_aviso(
    aviso_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> AvisoAckOut:
    """Acknowledge (confirm reading) an Aviso. Idempotent: repeated calls return 200."""
    repo = AvisoRepository(session, current_user.tenant_id)
    aviso = await repo.get_aviso(aviso_id)
    if aviso is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aviso not found")
    ack = await repo.create_ack(aviso_id=aviso_id, usuario_id=current_user.id)
    await session.commit()
    await session.refresh(ack)
    return AvisoAckOut.model_validate(ack)


@router.get(
    "/{aviso_id}/acks",
    response_model=list[AvisoAckOut],
    dependencies=[Depends(require_permission(AVISOS_PUBLICAR))],
)
async def list_acks(
    aviso_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> list[AvisoAckOut]:
    """List all acknowledgments for an Aviso. Requires avisos:publicar."""
    repo = AvisoRepository(session, current_user.tenant_id)
    aviso = await repo.get_aviso(aviso_id)
    if aviso is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aviso not found")
    acks = await repo.list_acks(aviso_id)
    return [AvisoAckOut.model_validate(a) for a in acks]


@router.patch(
    "/{aviso_id}",
    response_model=AvisoOut,
    dependencies=[Depends(require_permission(AVISOS_PUBLICAR))],
)
async def patch_aviso(
    aviso_id: uuid.UUID,
    body: AvisoPatch,
    session: DBSession,
    current_user: CurrentUser,
) -> AvisoOut:
    """Toggle activo (soft delete) on an Aviso. Requires avisos:publicar."""
    repo = AvisoRepository(session, current_user.tenant_id)
    aviso = await repo.patch_aviso(aviso_id, body.model_dump())
    if aviso is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aviso not found")
    await session.commit()
    await session.refresh(aviso)
    return AvisoOut.model_validate(aviso)
