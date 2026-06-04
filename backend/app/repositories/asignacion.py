"""repositories/asignacion.py — AsignacionRepository (C-07).

All queries are scoped to tenant_id and exclude soft-deleted records.

Methods:
  create               — persist a new Asignacion
  list_by_usuario      — all (including expired) for a user in this tenant
  get_vigentes_by_usuario — only active assignments (hasta IS NULL OR hasta >= today)
"""

import uuid
from datetime import date

from sqlalchemy import or_, select

from app.models.asignacion import Asignacion
from app.repositories.base import BaseRepository


class AsignacionRepository(BaseRepository[Asignacion]):
    """Tenant-scoped repository for Asignacion records."""

    def __init__(self, session, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, Asignacion)

    async def list_by_usuario(self, usuario_id: uuid.UUID) -> list[Asignacion]:
        """Return all (including expired) assignments for a user in this tenant.

        Excludes soft-deleted records.
        """
        stmt = select(Asignacion).where(
            Asignacion.tenant_id == self._tenant_id,
            Asignacion.usuario_id == usuario_id,
            Asignacion.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_vigentes_by_usuario(
        self,
        usuario_id: uuid.UUID,
        reference_date: date | None = None,
    ) -> list[Asignacion]:
        """Return only active (vigentes) assignments for a user in this tenant.

        An assignment is vigente when: hasta IS NULL OR hasta >= reference_date.
        Excludes soft-deleted records.

        Args:
            usuario_id:      UUID of the user.
            reference_date:  Date to check vigencia against (default: today).
        """
        if reference_date is None:
            reference_date = date.today()

        stmt = select(Asignacion).where(
            Asignacion.tenant_id == self._tenant_id,
            Asignacion.usuario_id == usuario_id,
            Asignacion.deleted_at.is_(None),
            Asignacion.desde <= reference_date,
            or_(
                Asignacion.hasta.is_(None),
                Asignacion.hasta >= reference_date,
            ),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
