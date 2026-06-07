"""repositories/auditoria_repository.py — Read-only analytics repository (C-19).

Design decisions (C-19 design.md):
  D1 — This repository is separate from AuditLogRepository (which is append-only
       by contract from C-05).  Mixing analytic reads into the write-side repo
       would violate single-responsibility.  Names are intentionally distinct:
         AuditLogRepository  → write side (C-05)
         AuditoriaRepository → read/analytics side (C-19)
  D2 — Scope filtering (COORDINADOR vs ADMIN) is handled in the Service layer.
       This repo only knows: "if actor_id is passed, filter by it".
  D3 — Uses func.date_trunc('day', ...) for day-level aggregation (PostgreSQL).
  D5 — /comunicaciones reads from the 'comunicaciones' table, not audit_logs.
  D6 — All queries are tenant-scoped by default.

All methods are async and read-only.  No add(), flush(), or commit() here.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import cast, func, select, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.comunicacion import Comunicacion


class AuditoriaRepository:
    """Read-only analytics repository for audit_logs and comunicaciones.

    Constructor args:
        session   — open AsyncSession for the current unit-of-work.
        tenant_id — UUID of the current tenant (from verified JWT).

    Public interface (all read-only):
        acciones_por_dia(...)          -> list[dict]
        interacciones_por_docente(...) -> list[dict]
        interacciones_por_materia(...) -> list[dict]
        log_paginado(...)              -> tuple[list[AuditLog], int]
        comunicaciones_por_docente(...) -> list[dict]
    """

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    # ── acciones_por_dia ──────────────────────────────────────────────────────

    async def acciones_por_dia(
        self,
        *,
        actor_id: uuid.UUID | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[dict]:
        """Return action counts grouped by calendar day (UTC).

        Args:
            actor_id:    If set, only count actions by this actor.
            fecha_desde: Include only entries on or after this date (UTC day).
            fecha_hasta: Include only entries on or before this date (UTC day).

        Returns:
            List of dicts with keys: fecha (date), total (int).
            Ordered by fecha ASC.
        """
        day_col = func.date_trunc("day", AuditLog.fecha_hora).label("fecha")

        stmt = (
            select(day_col, func.count().label("total"))
            .where(AuditLog.tenant_id == self._tenant_id)
            .group_by(day_col)
            .order_by(day_col)
        )

        if actor_id is not None:
            stmt = stmt.where(AuditLog.actor_id == actor_id)

        if fecha_desde is not None:
            fecha_desde_dt = datetime(
                fecha_desde.year, fecha_desde.month, fecha_desde.day
            )
            stmt = stmt.where(AuditLog.fecha_hora >= fecha_desde_dt)

        if fecha_hasta is not None:
            # Include the full end day
            import datetime as dt_module
            fecha_hasta_dt = datetime(
                fecha_hasta.year, fecha_hasta.month, fecha_hasta.day
            ) + dt_module.timedelta(days=1)
            stmt = stmt.where(AuditLog.fecha_hora < fecha_hasta_dt)

        result = await self._session.execute(stmt)
        rows = result.all()
        return [
            {"fecha": row.fecha.date() if hasattr(row.fecha, "date") else row.fecha, "total": row.total}
            for row in rows
        ]

    # ── interacciones_por_docente ─────────────────────────────────────────────

    async def interacciones_por_docente(
        self,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> list[dict]:
        """Return action counts grouped by actor_id.

        Args:
            actor_id: If set, only return counts for this actor.

        Returns:
            List of dicts with keys: actor_id (UUID), total (int).
            Ordered by total DESC.
        """
        stmt = (
            select(AuditLog.actor_id, func.count().label("total"))
            .where(AuditLog.tenant_id == self._tenant_id)
            .group_by(AuditLog.actor_id)
            .order_by(func.count().desc())
        )

        if actor_id is not None:
            stmt = stmt.where(AuditLog.actor_id == actor_id)

        result = await self._session.execute(stmt)
        rows = result.all()
        return [{"actor_id": row.actor_id, "total": row.total} for row in rows]

    # ── interacciones_por_materia ─────────────────────────────────────────────

    async def interacciones_por_materia(
        self,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> list[dict]:
        """Return action counts grouped by actor_id × materia_id (from JSONB detalle).

        materia_id is extracted with detalle->>'materia_id'; may be NULL.

        Args:
            actor_id: If set, only return counts for this actor.

        Returns:
            List of dicts with keys: actor_id (UUID), materia_id (UUID | None),
            total (int).  Ordered by total DESC.
        """
        materia_col = func.cast(
            AuditLog.detalle["materia_id"].astext, PG_UUID(as_uuid=True)
        ).label("materia_id")

        stmt = (
            select(AuditLog.actor_id, materia_col, func.count().label("total"))
            .where(AuditLog.tenant_id == self._tenant_id)
            .group_by(AuditLog.actor_id, materia_col)
            .order_by(func.count().desc())
        )

        if actor_id is not None:
            stmt = stmt.where(AuditLog.actor_id == actor_id)

        result = await self._session.execute(stmt)
        rows = result.all()
        return [
            {
                "actor_id": row.actor_id,
                "materia_id": row.materia_id,
                "total": row.total,
            }
            for row in rows
        ]

    # ── log_paginado ─────────────────────────────────────────────────────────

    async def log_paginado(
        self,
        *,
        actor_id: uuid.UUID | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        accion: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        """Return a paginated, filtered list of AuditLog entries.

        Args:
            actor_id:    Filter by actor.
            fecha_desde: Include entries on or after this date.
            fecha_hasta: Include entries on or before this date (inclusive).
            accion:      Filter by exact action code.
            limit:       Max rows (default 200).
            offset:      Skip rows for pagination.

        Returns:
            Tuple (items, total) where total is the count before pagination.
        """
        base = select(AuditLog).where(AuditLog.tenant_id == self._tenant_id)

        if actor_id is not None:
            base = base.where(AuditLog.actor_id == actor_id)
        if accion is not None:
            base = base.where(AuditLog.accion == accion)
        if fecha_desde is not None:
            fecha_desde_dt = datetime(
                fecha_desde.year, fecha_desde.month, fecha_desde.day
            )
            base = base.where(AuditLog.fecha_hora >= fecha_desde_dt)
        if fecha_hasta is not None:
            import datetime as dt_module
            fecha_hasta_dt = datetime(
                fecha_hasta.year, fecha_hasta.month, fecha_hasta.day
            ) + dt_module.timedelta(days=1)
            base = base.where(AuditLog.fecha_hora < fecha_hasta_dt)

        # Count query (no pagination)
        count_stmt = select(func.count()).select_from(base.subquery())
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        # Data query with pagination
        data_stmt = (
            base.order_by(AuditLog.fecha_hora.desc())
            .limit(limit)
            .offset(offset)
        )
        data_result = await self._session.execute(data_stmt)
        items = list(data_result.scalars().all())

        return items, total

    # ── comunicaciones_por_docente ────────────────────────────────────────────

    async def comunicaciones_por_docente(
        self,
        *,
        docente_id: uuid.UUID | None = None,
    ) -> list[dict]:
        """Return communication counts by estado for each docente (enviado_por).

        Args:
            docente_id: If set, only return counts for this docente.

        Returns:
            List of dicts with keys:
              docente_id, pendiente, enviando, enviado, error, cancelado.
        """
        stmt = (
            select(
                Comunicacion.enviado_por.label("docente_id"),
                Comunicacion.estado,
                func.count().label("cnt"),
            )
            .where(
                Comunicacion.tenant_id == self._tenant_id,
                Comunicacion.deleted_at.is_(None),
            )
            .group_by(Comunicacion.enviado_por, Comunicacion.estado)
        )

        if docente_id is not None:
            stmt = stmt.where(Comunicacion.enviado_por == docente_id)

        result = await self._session.execute(stmt)
        rows = result.all()

        # Pivot: aggregate by docente_id
        pivot: dict[uuid.UUID, dict] = {}
        for row in rows:
            did = row.docente_id
            if did not in pivot:
                pivot[did] = {
                    "docente_id": did,
                    "pendiente": 0,
                    "enviando": 0,
                    "enviado": 0,
                    "error": 0,
                    "cancelado": 0,
                }
            estado_lower = row.estado.lower()
            if estado_lower in pivot[did]:
                pivot[did][estado_lower] = row.cnt

        return list(pivot.values())
