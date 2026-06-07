"""repositories/salario_base.py — SalarioBaseRepository (C-18).

All queries are scoped to tenant_id via BaseRepository. Business rule D4:
when multiple records overlap for the same (rol, periodo), the one with
the most recent 'desde' is returned (deterministic tie-break).

Vigencia predicate for period AAAA-MM with first day = ini_mes, last day = fin_mes:
  desde <= fin_mes AND (hasta IS NULL OR hasta >= ini_mes)
"""

import uuid
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.salario_base import SalarioBase
from app.repositories.base import BaseRepository


class SalarioBaseRepository(BaseRepository[SalarioBase]):
    """Tenant-scoped CRUD + vigencia lookup for SalarioBase records."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, SalarioBase)

    async def get_vigente(
        self,
        rol: str,
        ini_mes: date,
        fin_mes: date,
    ) -> SalarioBase | None:
        """Return the single SalarioBase record vigente for (rol, period).

        Vigencia: desde <= fin_mes AND (hasta IS NULL OR hasta >= ini_mes).
        If multiple records match (overlap), the one with the most recent
        'desde' wins (D4 — deterministic).

        Returns None if no vigente record exists for this (rol, period).
        """
        stmt = (
            select(SalarioBase)
            .where(
                SalarioBase.tenant_id == self._tenant_id,
                SalarioBase.deleted_at.is_(None),
                SalarioBase.rol == rol,
                SalarioBase.desde <= fin_mes,
                (SalarioBase.hasta.is_(None)) | (SalarioBase.hasta >= ini_mes),
            )
            .order_by(SalarioBase.desde.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def listar_por_rol(self, rol: str) -> list[SalarioBase]:
        """Return all active SalarioBase records for a given rol (any period)."""
        return await self.list(rol=rol)

    async def crear(self, data: dict[str, Any]) -> SalarioBase:
        """Persist a new SalarioBase record with tenant scope."""
        return await self.create(data)

    async def actualizar(self, id: uuid.UUID, data: dict[str, Any]) -> SalarioBase | None:
        """Update an existing SalarioBase record."""
        return await self.update(id, data)

    async def eliminar(self, id: uuid.UUID) -> bool:
        """Soft-delete a SalarioBase record."""
        return await self.soft_delete(id)
