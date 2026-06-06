"""repositories/comunicacion_repository.py — ComunicacionRepository (C-12).

Tenant-scoped repository for Comunicacion records.
All queries filter by tenant_id and exclude soft-deleted records.

Methods:
  create_bulk            — insert multiple Comunicacion records at once
  get_by_id              — get a single message by PK (tenant-scoped)
  get_lote               — get all active messages for a lote_id
  update_estado          — transition a message to a new state
  aprobar_lote           — mark all Pendiente messages in a lote as approved
  cancelar_lote          — cancel all Pendiente messages in a lote
  get_pendientes_para_worker — SELECT FOR UPDATE SKIP LOCKED, worker use only
  soft_delete            — soft-delete a single message

Design decisions (C-12 design.md D1, D2, D5):
- get_pendientes_para_worker uses SELECT FOR UPDATE SKIP LOCKED to prevent two
  workers from processing the same message concurrently (D1).
- aprobar_lote / cancelar_lote use bulk UPDATE for efficiency (D2).
- No business logic here — state machine validation lives in the service (D5).
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comunicacion import Comunicacion
from app.repositories.base import BaseRepository


class ComunicacionRepository(BaseRepository[Comunicacion]):
    """Tenant-scoped repository for outbound communication queue."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, Comunicacion)

    # ── Bulk creation ─────────────────────────────────────────────────────────

    async def create_bulk(self, records: list[dict[str, Any]]) -> list[Comunicacion]:
        """Insert multiple Comunicacion rows in a single flush.

        tenant_id is always overwritten from the repository instance.
        """
        instances: list[Comunicacion] = []
        for data in records:
            data = {**data, "tenant_id": self._tenant_id}
            instance = Comunicacion(**data)
            self._session.add(instance)
            instances.append(instance)
        await self._session.flush()
        for inst in instances:
            await self._session.refresh(inst)
        return instances

    # ── Single record ─────────────────────────────────────────────────────────

    async def get_by_id(self, id: uuid.UUID) -> Comunicacion | None:
        """Return a single active Comunicacion by PK within the current tenant.

        Alias for BaseRepository.get() — provided for clarity in service code.
        """
        return await self.get(id)

    # ── Lote queries ──────────────────────────────────────────────────────────

    async def get_lote(self, lote_id: uuid.UUID) -> list[Comunicacion]:
        """Return all active messages belonging to lote_id within the current tenant."""
        stmt = select(Comunicacion).where(
            Comunicacion.tenant_id == self._tenant_id,
            Comunicacion.lote_id == lote_id,
            Comunicacion.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ── State transitions ─────────────────────────────────────────────────────

    async def update_estado(
        self,
        comunicacion_id: uuid.UUID,
        nuevo_estado: str,
        *,
        enviado_at: datetime | None = None,
    ) -> Comunicacion | None:
        """Transition a single message to nuevo_estado.

        Does NOT validate state machine legality — that's the service's job.
        Returns the updated instance, or None if not found / wrong tenant.
        """
        instance = await self.get(comunicacion_id)
        if instance is None:
            return None

        instance.estado = nuevo_estado
        instance.updated_at = datetime.now(tz=timezone.utc)
        if enviado_at is not None:
            instance.enviado_at = enviado_at
        self._session.add(instance)
        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    async def aprobar_lote(self, lote_id: uuid.UUID) -> int:
        """Mark all Pendiente messages in lote_id as aprobado=True.

        Returns the number of rows updated.
        Only affects messages in estado=Pendiente (not Cancelado, Enviado, etc.).
        """
        stmt = (
            update(Comunicacion)
            .where(
                Comunicacion.tenant_id == self._tenant_id,
                Comunicacion.lote_id == lote_id,
                Comunicacion.estado == "Pendiente",
                Comunicacion.deleted_at.is_(None),
            )
            .values(
                aprobado=True,
                updated_at=datetime.now(tz=timezone.utc),
            )
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount  # type: ignore[return-value]

    async def cancelar_lote(self, lote_id: uuid.UUID) -> int:
        """Cancel all Pendiente messages in lote_id (estado → Cancelado).

        Returns the number of rows updated.
        Only affects messages in estado=Pendiente.
        """
        stmt = (
            update(Comunicacion)
            .where(
                Comunicacion.tenant_id == self._tenant_id,
                Comunicacion.lote_id == lote_id,
                Comunicacion.estado == "Pendiente",
                Comunicacion.deleted_at.is_(None),
            )
            .values(
                estado="Cancelado",
                updated_at=datetime.now(tz=timezone.utc),
            )
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount  # type: ignore[return-value]

    # ── Worker queue ──────────────────────────────────────────────────────────

    async def get_pendientes_para_worker(
        self, limit: int = 10
    ) -> list[Comunicacion]:
        """SELECT messages ready for dispatch: Pendiente + aprobado=True.

        Uses SELECT FOR UPDATE SKIP LOCKED to prevent concurrent workers
        from processing the same message (D1 in design.md).

        This method is NOT tenant-scoped intentionally: the worker processes
        ALL tenants. The tenant scope is NOT applied here.
        """
        stmt = (
            select(Comunicacion)
            .where(
                Comunicacion.estado == "Pendiente",
                Comunicacion.aprobado.is_(True),
                Comunicacion.deleted_at.is_(None),
            )
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_estado_worker(
        self,
        comunicacion_id: uuid.UUID,
        nuevo_estado: str,
        enviado_at: datetime | None = None,
    ) -> Comunicacion | None:
        """Transition a single message for the worker (not tenant-scoped).

        The worker already has the row locked via SELECT FOR UPDATE SKIP LOCKED.
        """
        stmt = select(Comunicacion).where(Comunicacion.id == comunicacion_id)
        result = await self._session.execute(stmt)
        instance = result.scalar_one_or_none()
        if instance is None:
            return None

        instance.estado = nuevo_estado
        instance.updated_at = datetime.now(tz=timezone.utc)
        if enviado_at is not None:
            instance.enviado_at = enviado_at
        self._session.add(instance)
        await self._session.flush()
        await self._session.refresh(instance)
        return instance
