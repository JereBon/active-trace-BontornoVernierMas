"""api/v1/routers/programas.py — ProgramaMateria endpoints (C-17).

All write endpoints require the 'estructura:gestionar' permission.
Identity and tenant_id always come from the verified JWT (CurrentUser).

Endpoints:
  POST   /v1/programas                   Create a ProgramaMateria
  GET    /v1/programas                   List all active ProgramaMateria for tenant
  GET    /v1/programas/materia/{id}      List programs for a specific materia
  DELETE /v1/programas/{id}              Soft-delete a ProgramaMateria
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import CurrentUser, DBSession
from app.core.permisos import ESTRUCTURA_GESTIONAR
from app.core.rbac import require_permission
from app.repositories.programa_materia import ProgramaMateriaRepository
from app.schemas.programa_materia import ProgramaMateriaCreate, ProgramaMateriaOut

router = APIRouter(
    prefix="/v1/programas",
    tags=["programas"],
)


@router.post(
    "",
    response_model=ProgramaMateriaOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(ESTRUCTURA_GESTIONAR))],
)
async def create_programa(
    body: ProgramaMateriaCreate,
    session: DBSession,
    current_user: CurrentUser,
) -> ProgramaMateriaOut:
    """Create a new ProgramaMateria for the current tenant."""
    repo = ProgramaMateriaRepository(session, current_user.tenant_id)
    programa = await repo.create(body.model_dump())
    await session.commit()
    await session.refresh(programa)
    return ProgramaMateriaOut.model_validate(programa)


@router.get(
    "",
    response_model=list[ProgramaMateriaOut],
    dependencies=[Depends(require_permission(ESTRUCTURA_GESTIONAR))],
)
async def list_programas(
    session: DBSession,
    current_user: CurrentUser,
) -> list[ProgramaMateriaOut]:
    """List all active ProgramaMateria for the current tenant."""
    repo = ProgramaMateriaRepository(session, current_user.tenant_id)
    programas = await repo.list()
    return [ProgramaMateriaOut.model_validate(p) for p in programas]


@router.get(
    "/materia/{materia_id}",
    response_model=list[ProgramaMateriaOut],
    dependencies=[Depends(require_permission(ESTRUCTURA_GESTIONAR))],
)
async def list_programas_by_materia(
    materia_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> list[ProgramaMateriaOut]:
    """List all active ProgramaMateria for a specific materia in this tenant."""
    repo = ProgramaMateriaRepository(session, current_user.tenant_id)
    programas = await repo.list_by_materia(materia_id)
    return [ProgramaMateriaOut.model_validate(p) for p in programas]


@router.delete(
    "/{programa_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(ESTRUCTURA_GESTIONAR))],
)
async def delete_programa(
    programa_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> None:
    """Soft-delete a ProgramaMateria."""
    repo = ProgramaMateriaRepository(session, current_user.tenant_id)
    deleted = await repo.soft_delete(programa_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ProgramaMateria not found")
    await session.commit()
