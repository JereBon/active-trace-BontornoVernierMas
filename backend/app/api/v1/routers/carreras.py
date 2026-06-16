"""api/v1/routers/carreras.py — Carrera endpoints (C-06: estructura-academica).

All endpoints require the 'estructura:gestionar' permission.
Identity and tenant_id always come from the verified JWT (CurrentUser).
No business logic lives here — only HTTP translation → service calls.

Endpoints:
  POST   /v1/carreras           Create a new Carrera
  GET    /v1/carreras           List all active Carreras
  GET    /v1/carreras/{id}      Get a single Carrera
  PATCH  /v1/carreras/{id}      Update a Carrera
  DELETE /v1/carreras/{id}      Soft-delete a Carrera
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencies import CurrentUser, DBSession
from app.core.exceptions import AppError
from app.core.permisos import ESTRUCTURA_GESTIONAR
from app.core.rbac import require_permission
from app.schemas.carrera import CarreraCreate, CarreraOut, CarreraUpdate
from app.services.carrera import CarreraService

router = APIRouter(
    prefix="/v1/carreras",
    tags=["carreras"],
    dependencies=[Depends(require_permission(ESTRUCTURA_GESTIONAR))],
)


@router.post("", response_model=CarreraOut, status_code=status.HTTP_201_CREATED)
async def create_carrera(
    body: CarreraCreate,
    session: DBSession,
    current_user: CurrentUser,
) -> CarreraOut:
    """Create a new Carrera within the current tenant."""
    svc = CarreraService(session, current_user.tenant_id)
    carrera = await svc.create(body)
    await session.commit()
    return CarreraOut.model_validate(carrera)


@router.get("", response_model=list[CarreraOut])
async def list_carreras(
    session: DBSession,
    current_user: CurrentUser,
) -> list[CarreraOut]:
    """List all active Carreras for the current tenant."""
    svc = CarreraService(session, current_user.tenant_id)
    carreras = await svc.list()
    return [CarreraOut.model_validate(c) for c in carreras]


@router.get("/{carrera_id}", response_model=CarreraOut)
async def get_carrera(
    carrera_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> CarreraOut:
    """Get a single active Carrera by ID."""
    svc = CarreraService(session, current_user.tenant_id)
    carrera = await svc.get(carrera_id)
    return CarreraOut.model_validate(carrera)


@router.patch("/{carrera_id}", response_model=CarreraOut)
async def update_carrera(
    carrera_id: uuid.UUID,
    body: CarreraUpdate,
    session: DBSession,
    current_user: CurrentUser,
) -> CarreraOut:
    """Update fields on an existing Carrera."""
    svc = CarreraService(session, current_user.tenant_id)
    carrera = await svc.update(carrera_id, body)
    await session.commit()
    return CarreraOut.model_validate(carrera)


@router.delete("/{carrera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_carrera(
    carrera_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> None:
    """Soft-delete a Carrera (sets deleted_at; never removes from DB)."""
    svc = CarreraService(session, current_user.tenant_id)
    await svc.soft_delete(carrera_id)
    await session.commit()
