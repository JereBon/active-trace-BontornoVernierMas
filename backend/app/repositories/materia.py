"""repositories/materia.py — MateriaRepository (C-06: estructura-academica).

Extends BaseRepository with a lookup by (tenant_id, codigo) for uniqueness
validation before insert/update.
"""

import uuid

from sqlalchemy import select

from app.models.materia import Materia
from app.repositories.base import BaseRepository


class MateriaRepository(BaseRepository[Materia]):
    """Tenant-scoped repository for Materia records."""

    def __init__(self, session, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, Materia)

    async def get_by_codigo(self, codigo: str) -> Materia | None:
        """Return the active Materia with the given codigo for the current tenant.

        Returns None if not found or soft-deleted.
        Used to check uniqueness before create/update.
        """
        stmt = select(Materia).where(
            Materia.tenant_id == self._tenant_id,
            Materia.codigo == codigo,
            Materia.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
