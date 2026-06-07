"""repositories/factura.py — FacturaRepository (C-18).

All queries are scoped to tenant_id via BaseRepository.
Supports CRUD + filter by estado/usuario/periodo + state transition to Abonada.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.factura import EstadoFactura, Factura
from app.repositories.base import BaseRepository


class FacturaRepository(BaseRepository[Factura]):
    """Tenant-scoped repository for Factura records."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, Factura)

    async def listar(
        self,
        usuario_id: uuid.UUID | None = None,
        periodo: str | None = None,
        estado: str | None = None,
    ) -> list[Factura]:
        """Return active Factura records, optionally filtered."""
        stmt = (
            select(Factura)
            .where(
                Factura.tenant_id == self._tenant_id,
                Factura.deleted_at.is_(None),
            )
        )
        if usuario_id is not None:
            stmt = stmt.where(Factura.usuario_id == usuario_id)
        if periodo is not None:
            stmt = stmt.where(Factura.periodo == periodo)
        if estado is not None:
            stmt = stmt.where(Factura.estado == estado)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def crear(self, data: dict[str, Any]) -> Factura:
        """Persist a new Factura record."""
        return await self.create(data)

    async def actualizar(self, id: uuid.UUID, data: dict[str, Any]) -> Factura | None:
        """Update an existing Factura record."""
        return await self.update(id, data)

    async def cambiar_estado(
        self,
        id: uuid.UUID,
        nuevo_estado: str,
    ) -> Factura | None:
        """Transition a Factura to a new estado; sets abonada_at when Abonada."""
        factura = await self.get(id)
        if factura is None:
            return None

        now = datetime.now(tz=timezone.utc)
        update_data: dict[str, Any] = {
            "estado": nuevo_estado,
            "updated_at": now,
        }
        if nuevo_estado == EstadoFactura.Abonada.value and factura.abonada_at is None:
            update_data["abonada_at"] = now

        return await self.update(id, update_data)

    async def eliminar(self, id: uuid.UUID) -> bool:
        """Soft-delete a Factura record."""
        return await self.soft_delete(id)
