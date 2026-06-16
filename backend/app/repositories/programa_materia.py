"""repositories/programa_materia.py — ProgramaMateriaRepository (C-17).

Extends BaseRepository with a list_by_materia lookup for retrieving all
programs of a given materia within the current tenant.

All queries automatically filter by tenant_id and exclude soft-deleted records
via the BaseRepository base class.
"""

import uuid

from sqlalchemy import select

from app.models.programa_materia import ProgramaMateria
from app.repositories.base import BaseRepository


class ProgramaMateriaRepository(BaseRepository[ProgramaMateria]):
    """Tenant-scoped repository for ProgramaMateria records."""

    def __init__(self, session, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, ProgramaMateria)

    async def list_by_materia(self, materia_id: uuid.UUID) -> list[ProgramaMateria]:
        """Return all active programs for a specific materia within the current tenant.

        Excludes soft-deleted records.
        """
        stmt = select(ProgramaMateria).where(
            ProgramaMateria.tenant_id == self._tenant_id,
            ProgramaMateria.materia_id == materia_id,
            ProgramaMateria.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
