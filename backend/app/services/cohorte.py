"""services/cohorte.py — CohorteService (C-06: estructura-academica).

Business logic for Cohorte CRUD.

Design:
  - create() validates that the referenced carrera_id exists within the tenant
    (cross-tenant FK protection at service layer) → NotFoundError if missing.
  - create() checks (tenant_id, carrera_id, nombre) uniqueness → ConflictError.
  - soft_delete() returns NotFoundError if the record doesn't exist.
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.cohorte import Cohorte
from app.repositories.carrera import CarreraRepository
from app.repositories.cohorte import CohorteRepository
from app.schemas.cohorte import CohorteCreate, CohorteUpdate


class CohorteService:
    """Service layer for Cohorte operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._repo = CohorteRepository(session, tenant_id)
        self._carrera_repo = CarreraRepository(session, tenant_id)

    async def _assert_carrera_in_tenant(self, carrera_id: uuid.UUID) -> None:
        """Raise NotFoundError if carrera_id is not visible in the current tenant."""
        carrera = await self._carrera_repo.get(carrera_id)
        if carrera is None:
            raise NotFoundError(f"Carrera {carrera_id} no encontrada en este tenant")

    async def create(self, data: CohorteCreate) -> Cohorte:
        """Create a new Cohorte.

        Raises:
            NotFoundError: if carrera_id not found in the current tenant.
            ConflictError: if (tenant_id, carrera_id, nombre) already exists.
        """
        await self._assert_carrera_in_tenant(data.carrera_id)

        existing = await self._repo.get_by_nombre(data.carrera_id, data.nombre)
        if existing is not None:
            raise ConflictError(
                f"Cohorte '{data.nombre}' ya existe para la carrera {data.carrera_id} en este tenant"
            )

        return await self._repo.create(
            {
                "carrera_id": data.carrera_id,
                "nombre": data.nombre,
                "anio": data.anio,
                "vig_desde": data.vig_desde,
                "vig_hasta": data.vig_hasta,
                "estado": data.estado.value,
            }
        )

    async def list(self) -> list[Cohorte]:
        """Return all active Cohortes for the current tenant."""
        return await self._repo.list()

    async def get(self, cohorte_id: uuid.UUID) -> Cohorte:
        """Return a single active Cohorte.

        Raises:
            NotFoundError: if not found or belongs to another tenant.
        """
        cohorte = await self._repo.get(cohorte_id)
        if cohorte is None:
            raise NotFoundError(f"Cohorte {cohorte_id} no encontrada")
        return cohorte

    async def update(self, cohorte_id: uuid.UUID, data: CohorteUpdate) -> Cohorte:
        """Update fields on an existing Cohorte.

        Raises:
            NotFoundError: if the Cohorte doesn't exist.
            ConflictError: if the new nombre collides within the same carrera.
        """
        current = await self.get(cohorte_id)

        update_dict: dict[str, Any] = {}
        if data.nombre is not None:
            # Check uniqueness with new nombre against current carrera_id
            existing = await self._repo.get_by_nombre(current.carrera_id, data.nombre)
            if existing is not None and existing.id != cohorte_id:
                raise ConflictError(
                    f"Cohorte '{data.nombre}' ya existe para la carrera {current.carrera_id}"
                )
            update_dict["nombre"] = data.nombre
        if data.anio is not None:
            update_dict["anio"] = data.anio
        if data.vig_desde is not None:
            update_dict["vig_desde"] = data.vig_desde
        if "vig_hasta" in data.model_fields_set:
            update_dict["vig_hasta"] = data.vig_hasta
        if data.estado is not None:
            update_dict["estado"] = data.estado.value

        updated = await self._repo.update(cohorte_id, update_dict)
        if updated is None:
            raise NotFoundError(f"Cohorte {cohorte_id} no encontrada")
        return updated

    async def soft_delete(self, cohorte_id: uuid.UUID) -> None:
        """Soft-delete a Cohorte.

        Raises:
            NotFoundError: if the Cohorte doesn't exist.
        """
        deleted = await self._repo.soft_delete(cohorte_id)
        if not deleted:
            raise NotFoundError(f"Cohorte {cohorte_id} no encontrada")
