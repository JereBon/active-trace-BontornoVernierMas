"""repositories/audit_log.py — Append-only repository for AuditLog (C-05).

Design decisions (design.md D1):
  AuditLogRepository is append-only by contract:
    - create()          : the only write operation allowed.
    - list_by_tenant()  : tenant-scoped read, ordered by fecha_hora DESC.
    - update()          : raises NotImplementedError — audit logs are immutable.
    - soft_delete()     : raises NotImplementedError — audit logs are never deleted.

  We do NOT inherit BaseRepository because BaseRepository exposes update() and
  soft_delete() as valid operations.  AuditLogRepository implements only the
  subset of operations that are contractually allowed.

  The 'TenantScopedMixin' contract (every query scoped to tenant_id) is
  maintained manually in each read method.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditLogRepository:
    """Append-only repository for AuditLog.

    Constructor args:
        session   — open AsyncSession for the current unit-of-work.
        tenant_id — UUID of the current tenant (from verified JWT).

    Public interface:
        create(data)         -> AuditLog   (only write operation)
        list_by_tenant(...)  -> list[AuditLog]
        update(...)          -> raises NotImplementedError
        soft_delete(...)     -> raises NotImplementedError
    """

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    # ── Reads ─────────────────────────────────────────────────────────────────

    async def list_by_tenant(
        self,
        *,
        actor_id: uuid.UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Return audit log entries for the current tenant, newest first.

        Args:
            actor_id: Optional filter — only entries for this actor.
            limit:    Maximum rows to return (default 100).
            offset:   Skip this many rows (for pagination).

        Returns:
            List of AuditLog instances ordered by fecha_hora DESC.
        """
        stmt = (
            select(AuditLog)
            .where(AuditLog.tenant_id == self._tenant_id)
            .order_by(AuditLog.fecha_hora.desc())
            .limit(limit)
            .offset(offset)
        )
        if actor_id is not None:
            stmt = stmt.where(AuditLog.actor_id == actor_id)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ── Write ─────────────────────────────────────────────────────────────────

    async def create(self, data: dict[str, Any]) -> AuditLog:
        """Persist a new audit log entry.

        tenant_id is always sourced from the repository instance (the JWT),
        never from the data dict — any tenant_id in data is overwritten.
        fecha_hora defaults to now(UTC) via server_default if not provided.

        Args:
            data: Dict of column values.  tenant_id will be overwritten.

        Returns:
            Persisted AuditLog instance.
        """
        payload = {**data, "tenant_id": self._tenant_id}
        # Ensure fecha_hora is set in Python if not supplied (server_default
        # fires after flush, but we want it visible within the current session)
        if "fecha_hora" not in payload:
            payload["fecha_hora"] = datetime.now(tz=timezone.utc)

        entry = AuditLog(**payload)
        self._session.add(entry)
        await self._session.flush()
        await self._session.refresh(entry)
        return entry

    # ── Disabled mutations (append-only contract) ─────────────────────────────

    async def update(self, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
        """AuditLog records are immutable. This method always raises."""
        raise NotImplementedError(
            "AuditLog is append-only: update() is not permitted."
        )

    async def soft_delete(self, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
        """AuditLog records are never deleted. This method always raises."""
        raise NotImplementedError(
            "AuditLog is append-only: soft_delete() is not permitted."
        )

    async def delete(self, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
        """AuditLog records are never deleted. This method always raises."""
        raise NotImplementedError(
            "AuditLog is append-only: delete() is not permitted."
        )
