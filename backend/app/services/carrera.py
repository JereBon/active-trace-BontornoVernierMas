"""services/carrera.py — CarreraService (C-06: estructura-academica).

Business logic for Carrera CRUD. Validates uniqueness before insert/update and
delegates all DB access to CarreraRepository. Never touches DB directly.

Design:
  - create() checks (tenant_id, codigo) uniqueness → ConflictError if duplicate.
  - update() revalidates uniqueness when codigo changes.
  - soft_delete() delegates to repo; returns NotFoundError if not found.
  - No hard DELETE emitted (append-only audit trail).
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.carrera import Carrera
from app.repositories.carrera import CarreraRepository
from app.schemas.carrera import CarreraCreate, CarreraUpdate


class CarreraService:
    """Service layer for Carrera operations.

    Instantiated per-request with the active DB session and tenant context
    (sourced from the verified JWT via the router dependency).
    """

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._repo = CarreraRepository(session, tenant_id)

    async def create(self, data: CarreraCreate) -> Carrera:
        """Create a new Carrera.

        Raises:
            ConflictError: if (tenant_id, codigo) already exists.
        """
        existing = await self._repo.get_by_codigo(data.codigo)
        if existing is not None:
            raise ConflictError(f"Carrera con codigo '{data.codigo}' ya existe en este tenant")

        return await self._repo.create(
            {
                "codigo": data.codigo,
                "nombre": data.nombre,
                "estado": data.estado.value,
            }
        )

    async def list(self) -> list[Carrera]:
        """Return all active Carreras for the current tenant."""
        return await self._repo.list()

    async def get(self, carrera_id: uuid.UUID) -> Carrera:
        """Return a single active Carrera.

        Raises:
            NotFoundError: if not found or belongs to another tenant.
        """
        carrera = await self._repo.get(carrera_id)
        if carrera is None:
            raise NotFoundError(f"Carrera {carrera_id} no encontrada")
        return carrera

    async def update(self, carrera_id: uuid.UUID, data: CarreraUpdate) -> Carrera:
        """Update fields on an existing Carrera.

        Raises:
            NotFoundError: if the Carrera doesn't exist.
            ConflictError: if the new codigo collides with another active Carrera.
        """
        # Verify existence first
        await self.get(carrera_id)

        update_dict: dict[str, Any] = {}
        if data.codigo is not None:
            existing = await self._repo.get_by_codigo(data.codigo)
            if existing is not None and existing.id != carrera_id:
                raise ConflictError(f"Carrera con codigo '{data.codigo}' ya existe en este tenant")
            update_dict["codigo"] = data.codigo
        if data.nombre is not None:
            update_dict["nombre"] = data.nombre
        if data.estado is not None:
            update_dict["estado"] = data.estado.value

        updated = await self._repo.update(carrera_id, update_dict)
        if updated is None:
            raise NotFoundError(f"Carrera {carrera_id} no encontrada")
        return updated

    async def soft_delete(self, carrera_id: uuid.UUID) -> None:
        """Soft-delete a Carrera.

        Raises:
            NotFoundError: if the Carrera doesn't exist.
        """
        deleted = await self._repo.soft_delete(carrera_id)
        if not deleted:
            raise NotFoundError(f"Carrera {carrera_id} no encontrada")
