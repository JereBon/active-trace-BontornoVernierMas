"""services/materia.py — MateriaService (C-06: estructura-academica).

Business logic for Materia CRUD.

Design:
  - create() checks (tenant_id, codigo) uniqueness → ConflictError if duplicate.
  - update() revalidates uniqueness when codigo changes.
  - soft_delete() returns NotFoundError if not found.
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.materia import Materia
from app.repositories.materia import MateriaRepository
from app.schemas.materia import MateriaCreate, MateriaUpdate


class MateriaService:
    """Service layer for Materia operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._repo = MateriaRepository(session, tenant_id)

    async def create(self, data: MateriaCreate) -> Materia:
        """Create a new Materia.

        Raises:
            ConflictError: if (tenant_id, codigo) already exists.
        """
        existing = await self._repo.get_by_codigo(data.codigo)
        if existing is not None:
            raise ConflictError(f"Materia con codigo '{data.codigo}' ya existe en este tenant")

        return await self._repo.create(
            {
                "codigo": data.codigo,
                "nombre": data.nombre,
                "estado": data.estado.value,
            }
        )

    async def list(self) -> list[Materia]:
        """Return all active Materias for the current tenant."""
        return await self._repo.list()

    async def get(self, materia_id: uuid.UUID) -> Materia:
        """Return a single active Materia.

        Raises:
            NotFoundError: if not found or belongs to another tenant.
        """
        materia = await self._repo.get(materia_id)
        if materia is None:
            raise NotFoundError(f"Materia {materia_id} no encontrada")
        return materia

    async def update(self, materia_id: uuid.UUID, data: MateriaUpdate) -> Materia:
        """Update fields on an existing Materia.

        Raises:
            NotFoundError: if the Materia doesn't exist.
            ConflictError: if the new codigo collides with another active Materia.
        """
        await self.get(materia_id)

        update_dict: dict[str, Any] = {}
        if data.codigo is not None:
            existing = await self._repo.get_by_codigo(data.codigo)
            if existing is not None and existing.id != materia_id:
                raise ConflictError(f"Materia con codigo '{data.codigo}' ya existe en este tenant")
            update_dict["codigo"] = data.codigo
        if data.nombre is not None:
            update_dict["nombre"] = data.nombre
        if data.estado is not None:
            update_dict["estado"] = data.estado.value

        updated = await self._repo.update(materia_id, update_dict)
        if updated is None:
            raise NotFoundError(f"Materia {materia_id} no encontrada")
        return updated

    async def soft_delete(self, materia_id: uuid.UUID) -> None:
        """Soft-delete a Materia.

        Raises:
            NotFoundError: if the Materia doesn't exist.
        """
        deleted = await self._repo.soft_delete(materia_id)
        if not deleted:
            raise NotFoundError(f"Materia {materia_id} no encontrada")
