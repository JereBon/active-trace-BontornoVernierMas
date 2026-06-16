"""api/v1/routers/cohortes.py — Cohorte endpoints (C-06: estructura-academica).

All endpoints require the 'estructura:gestionar' permission.
Identity and tenant_id always come from the verified JWT (CurrentUser).

Endpoints:
  POST   /v1/cohortes           Create a new Cohorte
  GET    /v1/cohortes           List all active Cohortes
  GET    /v1/cohortes/{id}      Get a single Cohorte
  PATCH  /v1/cohortes/{id}      Update a Cohorte
  DELETE /v1/cohortes/{id}      Soft-delete a Cohorte
"""

import uuid

from fastapi import APIRouter, Depends, status

from app.core.dependencies import CurrentUser, DBSession
from app.core.permisos import ESTRUCTURA_GESTIONAR
from app.core.rbac import require_permission
from app.schemas.cohorte import CohorteCreate, CohorteOut, CohorteUpdate
from app.services.cohorte import CohorteService

router = APIRouter(
    prefix="/v1/cohortes",
    tags=["cohortes"],
    dependencies=[Depends(require_permission(ESTRUCTURA_GESTIONAR))],
)


@router.post("", response_model=CohorteOut, status_code=status.HTTP_201_CREATED)
async def create_cohorte(
    body: CohorteCreate,
    session: DBSession,
    current_user: CurrentUser,
) -> CohorteOut:
    """Create a new Cohorte within the current tenant."""
    svc = CohorteService(session, current_user.tenant_id)
    cohorte = await svc.create(body)
    await session.commit()
    return CohorteOut.model_validate(cohorte)


@router.get("", response_model=list[CohorteOut])
async def list_cohortes(
    session: DBSession,
    current_user: CurrentUser,
) -> list[CohorteOut]:
    """List all active Cohortes for the current tenant."""
    svc = CohorteService(session, current_user.tenant_id)
    cohortes = await svc.list()
    return [CohorteOut.model_validate(c) for c in cohortes]


@router.get("/{cohorte_id}", response_model=CohorteOut)
async def get_cohorte(
    cohorte_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> CohorteOut:
    """Get a single active Cohorte by ID."""
    svc = CohorteService(session, current_user.tenant_id)
    cohorte = await svc.get(cohorte_id)
    return CohorteOut.model_validate(cohorte)


@router.patch("/{cohorte_id}", response_model=CohorteOut)
async def update_cohorte(
    cohorte_id: uuid.UUID,
    body: CohorteUpdate,
    session: DBSession,
    current_user: CurrentUser,
) -> CohorteOut:
    """Update fields on an existing Cohorte."""
    svc = CohorteService(session, current_user.tenant_id)
    cohorte = await svc.update(cohorte_id, body)
    await session.commit()
    return CohorteOut.model_validate(cohorte)


@router.delete("/{cohorte_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cohorte(
    cohorte_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> None:
    """Soft-delete a Cohorte."""
    svc = CohorteService(session, current_user.tenant_id)
    await svc.soft_delete(cohorte_id)
    await session.commit()
