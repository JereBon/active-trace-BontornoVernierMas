"""repositories/encuentro.py — Encuentro repositories (C-13).

SlotEncuentroRepository:
  - create_slot  — persist SlotEncuentro
  - create_instancias  — bulk create InstanciaEncuentro rows

InstanciaEncuentroRepository:
  - list_by_materia_slot  — list instances for a materia, optionally filtered by slot
  - list_for_admin  — list all instances for the tenant (with optional materia filter)

All queries are scoped to tenant_id and exclude soft-deleted records.
"""

import uuid
from typing import Any

from sqlalchemy import and_, select

from app.models.encuentro import InstanciaEncuentro, SlotEncuentro
from app.repositories.base import BaseRepository


class SlotEncuentroRepository(BaseRepository[SlotEncuentro]):
    """Tenant-scoped repository for SlotEncuentro records."""

    def __init__(self, session, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, SlotEncuentro)


class InstanciaEncuentroRepository(BaseRepository[InstanciaEncuentro]):
    """Tenant-scoped repository for InstanciaEncuentro records."""

    def __init__(self, session, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, InstanciaEncuentro)

    async def list_by_materia_slot(
        self,
        materia_id: uuid.UUID,
        asignacion_id: uuid.UUID | None = None,
    ) -> list[InstanciaEncuentro]:
        """Return active instances for a materia within the current tenant.

        Optionally scoped to instances whose slot belongs to a given asignacion.
        If asignacion_id is None, returns all instances for the materia.
        """
        if asignacion_id is not None:
            # Join through slot to filter by asignacion_id
            stmt = (
                select(InstanciaEncuentro)
                .join(
                    SlotEncuentro,
                    and_(
                        SlotEncuentro.id == InstanciaEncuentro.slot_id,
                        SlotEncuentro.deleted_at.is_(None),
                    ),
                    isouter=True,
                )
                .where(
                    InstanciaEncuentro.tenant_id == self._tenant_id,
                    InstanciaEncuentro.materia_id == materia_id,
                    InstanciaEncuentro.deleted_at.is_(None),
                    and_(
                        InstanciaEncuentro.slot_id.is_(None)
                        | (SlotEncuentro.asignacion_id == asignacion_id)
                    ),
                )
                .order_by(InstanciaEncuentro.fecha.asc())
            )
        else:
            stmt = (
                select(InstanciaEncuentro)
                .where(
                    InstanciaEncuentro.tenant_id == self._tenant_id,
                    InstanciaEncuentro.materia_id == materia_id,
                    InstanciaEncuentro.deleted_at.is_(None),
                )
                .order_by(InstanciaEncuentro.fecha.asc())
            )

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_for_admin(
        self,
        materia_id: uuid.UUID | None = None,
    ) -> list[InstanciaEncuentro]:
        """Return all active instances for the current tenant.

        Args:
            materia_id: optional filter by materia.
        """
        conditions: list[Any] = [
            InstanciaEncuentro.tenant_id == self._tenant_id,
            InstanciaEncuentro.deleted_at.is_(None),
        ]
        if materia_id is not None:
            conditions.append(InstanciaEncuentro.materia_id == materia_id)

        stmt = (
            select(InstanciaEncuentro)
            .where(and_(*conditions))
            .order_by(InstanciaEncuentro.fecha.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
