"""services/salario_grilla_service.py — SalarioGrillaService (C-18, Task 4.4).

Manages the salary grid (ABM for SalarioBase and SalarioPlus) with tenant scope.
All persistence goes through the repository layer (D3).
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.salario_base import SalarioBase
from app.models.salario_plus import SalarioPlus
from app.repositories.salario_base import SalarioBaseRepository
from app.repositories.salario_plus import SalarioPlusRepository


class SalarioGrillaService:
    """ABM for salary grid records (Base and Plus) with tenant isolation."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._base_repo = SalarioBaseRepository(session, tenant_id)
        self._plus_repo = SalarioPlusRepository(session, tenant_id)

    # ── SalarioBase ABM ───────────────────────────────────────────────────────

    async def listar_base(self) -> list[SalarioBase]:
        """Return all active SalarioBase records for the tenant."""
        return await self._base_repo.list()

    async def crear_base(self, data: dict[str, Any]) -> SalarioBase:
        """Persist a new SalarioBase record."""
        record = await self._base_repo.crear(data)
        await self._session.commit()
        return record

    async def actualizar_base(
        self, id: uuid.UUID, data: dict[str, Any]
    ) -> SalarioBase | None:
        """Update an existing SalarioBase record."""
        record = await self._base_repo.actualizar(id, data)
        await self._session.commit()
        return record

    async def eliminar_base(self, id: uuid.UUID) -> bool:
        """Soft-delete a SalarioBase record."""
        result = await self._base_repo.eliminar(id)
        await self._session.commit()
        return result

    # ── SalarioPlus ABM ───────────────────────────────────────────────────────

    async def listar_plus(self) -> list[SalarioPlus]:
        """Return all active SalarioPlus records for the tenant."""
        return await self._plus_repo.list()

    async def crear_plus(self, data: dict[str, Any]) -> SalarioPlus:
        """Persist a new SalarioPlus record."""
        record = await self._plus_repo.crear(data)
        await self._session.commit()
        return record

    async def actualizar_plus(
        self, id: uuid.UUID, data: dict[str, Any]
    ) -> SalarioPlus | None:
        """Update an existing SalarioPlus record."""
        record = await self._plus_repo.actualizar(id, data)
        await self._session.commit()
        return record

    async def eliminar_plus(self, id: uuid.UUID) -> bool:
        """Soft-delete a SalarioPlus record."""
        result = await self._plus_repo.eliminar(id)
        await self._session.commit()
        return result
