"""repositories/carrera.py — CarreraRepository (C-06: estructura-academica).

Extends BaseRepository with a lookup by (tenant_id, codigo) for uniqueness
validation before insert.  All standard CRUD ops (create, list, get, update,
soft_delete) are inherited from BaseRepository with tenant isolation built in.
"""

import uuid

from sqlalchemy import select

from app.models.carrera import Carrera
from app.repositories.base import BaseRepository


class CarreraRepository(BaseRepository[Carrera]):
    """Tenant-scoped repository for Carrera records.

    Inherits get, list, create, update, soft_delete from BaseRepository.
    All operations automatically filter by tenant_id and deleted_at IS NULL.
    """

    def __init__(self, session, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, Carrera)

    async def get_by_codigo(self, codigo: str) -> Carrera | None:
        """Return the active Carrera with the given codigo for the current tenant.

        Returns None if not found or soft-deleted.
        Used to check uniqueness before create/update.
        """
        stmt = select(Carrera).where(
            Carrera.tenant_id == self._tenant_id,
            Carrera.codigo == codigo,
            Carrera.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
