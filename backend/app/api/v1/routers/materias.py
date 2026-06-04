"""api/v1/routers/materias.py — Materia endpoints (C-06: estructura-academica).

All endpoints require the 'estructura:gestionar' permission.
Identity and tenant_id always come from the verified JWT (CurrentUser).

Endpoints:
  POST   /v1/materias           Create a new Materia
  GET    /v1/materias           List all active Materias
  GET    /v1/materias/{id}      Get a single Materia
  PATCH  /v1/materias/{id}      Update a Materia
  DELETE /v1/materias/{id}      Soft-delete a Materia
"""

import uuid

from fastapi import APIRouter, Depends, status

from app.core.dependencies import CurrentUser, DBSession
from app.core.permisos import ESTRUCTURA_GESTIONAR
from app.core.rbac import require_permission
from app.schemas.materia import MateriaCreate, MateriaOut, MateriaUpdate
from app.services.materia import MateriaService

router = APIRouter(
    prefix="/v1/materias",
    tags=["materias"],
    dependencies=[Depends(require_permission(ESTRUCTURA_GESTIONAR))],
)


@router.post("", response_model=MateriaOut, status_code=status.HTTP_201_CREATED)
async def create_materia(
    body: MateriaCreate,
    session: DBSession,
    current_user: CurrentUser,
) -> MateriaOut:
    """Create a new Materia within the current tenant."""
    svc = MateriaService(session, current_user.tenant_id)
    materia = await svc.create(body)
    await session.commit()
    return MateriaOut.model_validate(materia)


@router.get("", response_model=list[MateriaOut])
async def list_materias(
    session: DBSession,
    current_user: CurrentUser,
) -> list[MateriaOut]:
    """List all active Materias for the current tenant."""
    svc = MateriaService(session, current_user.tenant_id)
    materias = await svc.list()
    return [MateriaOut.model_validate(m) for m in materias]


@router.get("/{materia_id}", response_model=MateriaOut)
async def get_materia(
    materia_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> MateriaOut:
    """Get a single active Materia by ID."""
    svc = MateriaService(session, current_user.tenant_id)
    materia = await svc.get(materia_id)
    return MateriaOut.model_validate(materia)


@router.patch("/{materia_id}", response_model=MateriaOut)
async def update_materia(
    materia_id: uuid.UUID,
    body: MateriaUpdate,
    session: DBSession,
    current_user: CurrentUser,
) -> MateriaOut:
    """Update fields on an existing Materia."""
    svc = MateriaService(session, current_user.tenant_id)
    materia = await svc.update(materia_id, body)
    await session.commit()
    return MateriaOut.model_validate(materia)


@router.delete("/{materia_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_materia(
    materia_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> None:
    """Soft-delete a Materia."""
    svc = MateriaService(session, current_user.tenant_id)
    await svc.soft_delete(materia_id)
    await session.commit()
