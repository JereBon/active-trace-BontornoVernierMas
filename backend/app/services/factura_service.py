"""services/factura_service.py — FacturaService (C-18, Task 4.5).

Manages invoice lifecycle: creation, listing, and Pendiente→Abonada transition.
All persistence via FacturaRepository; never touches DB directly.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.factura import EstadoFactura, Factura
from app.repositories.factura import FacturaRepository


class FacturaService:
    """ABM + state transition for Factura records with tenant isolation."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._repo = FacturaRepository(session, tenant_id)

    async def listar(
        self,
        usuario_id: uuid.UUID | None = None,
        periodo: str | None = None,
        estado: str | None = None,
    ) -> list[Factura]:
        """Return active Factura records, optionally filtered."""
        return await self._repo.listar(
            usuario_id=usuario_id,
            periodo=periodo,
            estado=estado,
        )

    async def crear(self, data: dict[str, Any]) -> Factura:
        """Persist a new Factura in Pendiente state.

        Sets cargada_at to now if not provided.
        """
        if "cargada_at" not in data:
            data = {**data, "cargada_at": datetime.now(tz=timezone.utc)}
        record = await self._repo.crear(data)
        await self._session.commit()
        return record

    async def actualizar(self, id: uuid.UUID, data: dict[str, Any]) -> Factura:
        """Update an existing Factura record. Raises NotFoundError if not found."""
        record = await self._repo.actualizar(id, data)
        if record is None:
            raise NotFoundError(f"Factura {id} not found.", code="factura_not_found")
        await self._session.commit()
        return record

    async def cambiar_estado(self, id: uuid.UUID, nuevo_estado: str) -> Factura:
        """Transition a Factura to a new estado.

        Sets abonada_at when transitioning to Abonada (if not already set).
        Raises NotFoundError if the Factura does not exist in this tenant.
        """
        record = await self._repo.cambiar_estado(id, nuevo_estado)
        if record is None:
            raise NotFoundError(f"Factura {id} not found.", code="factura_not_found")
        await self._session.commit()
        return record

    async def eliminar(self, id: uuid.UUID) -> bool:
        """Soft-delete a Factura. Returns True if found and deleted."""
        result = await self._repo.eliminar(id)
        await self._session.commit()
        return result
