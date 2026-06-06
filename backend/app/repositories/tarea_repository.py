"""repositories/tarea_repository.py — TareaRepository and ComentarioTareaRepository (C-16).

All queries are scoped to tenant_id and exclude soft-deleted records.

Methods (TareaRepository):
  list_mis_tareas        — tasks where asignado_a = current user, with optional filters
  list_todas             — admin view: all tenant tasks with optional filters
  get_comentarios        — ordered comment thread for a tarea

Methods (ComentarioTareaRepository):
  list_for_tarea         — ordered comments for a given tarea_id
"""

import uuid
from datetime import date
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import and_, select

from app.models.tarea import ComentarioTarea, Tarea
from app.repositories.base import BaseRepository

if TYPE_CHECKING:
    from app.schemas.tarea import TareaFilter


class TareaRepository(BaseRepository[Tarea]):
    """Tenant-scoped repository for Tarea records."""

    def __init__(self, session, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, Tarea)

    async def list_mis_tareas(
        self,
        asignado_a: uuid.UUID,
        filters: "TareaFilter",
    ) -> list[Tarea]:
        """Return active tasks assigned to the given user within the current tenant.

        Args:
            asignado_a: UUID of the user whose tasks to fetch.
            filters: Optional TareaFilter for additional filtering.
        """
        conditions: list[Any] = [
            Tarea.tenant_id == self._tenant_id,
            Tarea.deleted_at.is_(None),
            Tarea.asignado_a == asignado_a,
        ]

        if filters.estado is not None:
            conditions.append(Tarea.estado == filters.estado)
        if filters.materia_id is not None:
            conditions.append(Tarea.materia_id == filters.materia_id)

        stmt = (
            select(Tarea)
            .where(and_(*conditions))
            .order_by(Tarea.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_todas(
        self,
        filters: "TareaFilter",
    ) -> list[Tarea]:
        """Return all active tasks for the current tenant with optional filters.

        Admin-only view: all tasks regardless of assignee.

        Args:
            filters: Optional TareaFilter with estado, asignado_a, materia_id.
        """
        conditions: list[Any] = [
            Tarea.tenant_id == self._tenant_id,
            Tarea.deleted_at.is_(None),
        ]

        if filters.estado is not None:
            conditions.append(Tarea.estado == filters.estado)
        if filters.asignado_a is not None:
            conditions.append(Tarea.asignado_a == filters.asignado_a)
        if filters.materia_id is not None:
            conditions.append(Tarea.materia_id == filters.materia_id)

        stmt = (
            select(Tarea)
            .where(and_(*conditions))
            .order_by(Tarea.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class ComentarioTareaRepository(BaseRepository[ComentarioTarea]):
    """Tenant-scoped repository for ComentarioTarea records."""

    def __init__(self, session, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, ComentarioTarea)

    async def list_for_tarea(self, tarea_id: uuid.UUID) -> list[ComentarioTarea]:
        """Return all active comments for a tarea in chronological order.

        Args:
            tarea_id: UUID of the tarea whose comments to fetch.

        Returns:
            List of ComentarioTarea ordered by created_at ASC (oldest first).
        """
        stmt = (
            select(ComentarioTarea)
            .where(
                ComentarioTarea.tenant_id == self._tenant_id,
                ComentarioTarea.deleted_at.is_(None),
                ComentarioTarea.tarea_id == tarea_id,
            )
            .order_by(ComentarioTarea.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
