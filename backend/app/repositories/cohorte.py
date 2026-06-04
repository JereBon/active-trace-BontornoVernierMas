"""repositories/cohorte.py — CohorteRepository (C-06: estructura-academica).

Extends BaseRepository with a lookup by (tenant_id, carrera_id, nombre) for
uniqueness validation.  The carrera_id cross-tenant check is enforced at the
service layer (not here) to maintain clean separation of concerns.
"""

import uuid

from sqlalchemy import select

from app.models.cohorte import Cohorte
from app.repositories.base import BaseRepository


class CohorteRepository(BaseRepository[Cohorte]):
    """Tenant-scoped repository for Cohorte records."""

    def __init__(self, session, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, Cohorte)

    async def get_by_nombre(
        self,
        carrera_id: uuid.UUID,
        nombre: str,
    ) -> Cohorte | None:
        """Return the active Cohorte matching (tenant_id, carrera_id, nombre).

        Used to check uniqueness before create/update.
        Returns None if not found or soft-deleted.
        """
        stmt = select(Cohorte).where(
            Cohorte.tenant_id == self._tenant_id,
            Cohorte.carrera_id == carrera_id,
            Cohorte.nombre == nombre,
            Cohorte.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_carrera(self, carrera_id: uuid.UUID) -> list[Cohorte]:
        """Return all active Cohortes for the given carrera within the tenant."""
        return await self.list(carrera_id=carrera_id)
