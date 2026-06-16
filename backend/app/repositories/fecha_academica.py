"""repositories/fecha_academica.py — FechaAcademicaRepository (C-17).

All queries are scoped to tenant_id and exclude soft-deleted records.
Extends BaseRepository with a list_by_materia lookup.
"""

import uuid

from sqlalchemy import select

from app.models.fecha_academica import FechaAcademica
from app.repositories.base import BaseRepository


class FechaAcademicaRepository(BaseRepository[FechaAcademica]):
    """Tenant-scoped repository for FechaAcademica records."""

    def __init__(self, session, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, FechaAcademica)

    async def list_by_materia(self, materia_id: uuid.UUID) -> list[FechaAcademica]:
        """Return all active FechaAcademica entries for a specific materia in this tenant.

        Excludes soft-deleted records.
        """
        stmt = select(FechaAcademica).where(
            FechaAcademica.tenant_id == self._tenant_id,
            FechaAcademica.materia_id == materia_id,
            FechaAcademica.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
