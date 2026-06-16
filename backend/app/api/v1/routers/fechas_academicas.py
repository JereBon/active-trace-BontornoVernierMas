"""api/v1/routers/fechas_academicas.py — FechaAcademica endpoints (C-17).

All write endpoints require the 'estructura:gestionar' permission.
Identity and tenant_id always come from the verified JWT (CurrentUser).

Endpoints:
  POST   /v1/fechas-academicas           Create a FechaAcademica
  GET    /v1/fechas-academicas           List all active FechaAcademica (optionally filtered by materia_id)
  DELETE /v1/fechas-academicas/{id}      Soft-delete a FechaAcademica
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import CurrentUser, DBSession
from app.core.permisos import ESTRUCTURA_GESTIONAR
from app.core.rbac import require_permission
from app.repositories.fecha_academica import FechaAcademicaRepository
from app.schemas.fecha_academica import FechaAcademicaCreate, FechaAcademicaOut

router = APIRouter(
    prefix="/v1/fechas-academicas",
    tags=["fechas-academicas"],
)


@router.post(
    "",
    response_model=FechaAcademicaOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(ESTRUCTURA_GESTIONAR))],
)
async def create_fecha_academica(
    body: FechaAcademicaCreate,
    session: DBSession,
    current_user: CurrentUser,
) -> FechaAcademicaOut:
    """Create a new FechaAcademica for the current tenant."""
    repo = FechaAcademicaRepository(session, current_user.tenant_id)
    data = body.model_dump()
    fecha = await repo.create(data)
    await session.commit()
    await session.refresh(fecha)
    return FechaAcademicaOut.model_validate(fecha)


@router.get(
    "",
    response_model=list[FechaAcademicaOut],
    dependencies=[Depends(require_permission(ESTRUCTURA_GESTIONAR))],
)
async def list_fechas_academicas(
    session: DBSession,
    current_user: CurrentUser,
    materia_id: Optional[uuid.UUID] = Query(default=None, description="Filter by materia UUID"),
) -> list[FechaAcademicaOut]:
    """List all active FechaAcademica for the current tenant.

    Optionally filter by materia_id query parameter.
    """
    repo = FechaAcademicaRepository(session, current_user.tenant_id)
    if materia_id is not None:
        fechas = await repo.list_by_materia(materia_id)
    else:
        fechas = await repo.list()
    return [FechaAcademicaOut.model_validate(f) for f in fechas]


@router.delete(
    "/{fecha_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(ESTRUCTURA_GESTIONAR))],
)
async def delete_fecha_academica(
    fecha_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> None:
    """Soft-delete a FechaAcademica."""
    repo = FechaAcademicaRepository(session, current_user.tenant_id)
    deleted = await repo.soft_delete(fecha_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FechaAcademica not found")
    await session.commit()
