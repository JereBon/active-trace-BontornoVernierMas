"""repositories/salario_plus.py — SalarioPlusRepository (C-18).

All queries are scoped to tenant_id via BaseRepository. Business rule D4:
when multiple records overlap for the same (grupo, rol, periodo), the one
with the most recent 'desde' wins (deterministic).
"""

import uuid
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.salario_plus import SalarioPlus
from app.repositories.base import BaseRepository


class SalarioPlusRepository(BaseRepository[SalarioPlus]):
    """Tenant-scoped CRUD + vigencia lookup for SalarioPlus records."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, SalarioPlus)

    async def get_vigente(
        self,
        grupo: str,
        rol: str,
        ini_mes: date,
        fin_mes: date,
    ) -> SalarioPlus | None:
        """Return the single SalarioPlus record vigente for (grupo, rol, period).

        Vigencia: desde <= fin_mes AND (hasta IS NULL OR hasta >= ini_mes).
        If multiple records match, the one with the most recent 'desde' wins.

        Returns None if no vigente record exists (no Plus for this group/rol/period).
        """
        stmt = (
            select(SalarioPlus)
            .where(
                SalarioPlus.tenant_id == self._tenant_id,
                SalarioPlus.deleted_at.is_(None),
                SalarioPlus.grupo == grupo,
                SalarioPlus.rol == rol,
                SalarioPlus.desde <= fin_mes,
                (SalarioPlus.hasta.is_(None)) | (SalarioPlus.hasta >= ini_mes),
            )
            .order_by(SalarioPlus.desde.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def crear(self, data: dict[str, Any]) -> SalarioPlus:
        """Persist a new SalarioPlus record with tenant scope."""
        return await self.create(data)

    async def actualizar(self, id: uuid.UUID, data: dict[str, Any]) -> SalarioPlus | None:
        """Update an existing SalarioPlus record."""
        return await self.update(id, data)

    async def eliminar(self, id: uuid.UUID) -> bool:
        """Soft-delete a SalarioPlus record."""
        return await self.soft_delete(id)
