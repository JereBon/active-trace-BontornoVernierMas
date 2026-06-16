"""repositories/guardia.py — GuardiaRepository (C-13).

All queries are scoped to tenant_id and exclude soft-deleted records.

Methods:
  list_with_filters  — list guardias with optional filters
"""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import and_, select

from app.models.guardia import Guardia
from app.repositories.base import BaseRepository

if TYPE_CHECKING:
    from app.schemas.guardia import GuardiaFilter


class GuardiaRepository(BaseRepository[Guardia]):
    """Tenant-scoped repository for Guardia records."""

    def __init__(self, session, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, Guardia)

    async def list_with_filters(self, filters: "GuardiaFilter") -> list[Guardia]:
        """Return guardias for the current tenant with optional filters.

        Args:
            filters: GuardiaFilter with optional materia_id, asignacion_id,
                     carrera_id, cohorte_id, estado.
        """
        conditions: list[Any] = [
            Guardia.tenant_id == self._tenant_id,
            Guardia.deleted_at.is_(None),
        ]

        if filters.materia_id is not None:
            conditions.append(Guardia.materia_id == filters.materia_id)
        if filters.asignacion_id is not None:
            conditions.append(Guardia.asignacion_id == filters.asignacion_id)
        if filters.carrera_id is not None:
            conditions.append(Guardia.carrera_id == filters.carrera_id)
        if filters.cohorte_id is not None:
            conditions.append(Guardia.cohorte_id == filters.cohorte_id)
        if filters.estado is not None:
            conditions.append(Guardia.estado == filters.estado)

        stmt = (
            select(Guardia)
            .where(and_(*conditions))
            .order_by(Guardia.creada_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
