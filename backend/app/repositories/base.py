"""repositories/base.py — Generic tenant-scoped repository for SQLAlchemy 2.0 async.

Design decisions:
- BaseRepository[T] always scopes queries to tenant_id (extracted from JWT at
  router level and passed via constructor). A query without tenant scope is
  impossible via this repository — see D-03 in design.md.
- Soft delete: deleted_at IS NULL => active; BaseRepository never emits DELETE.
- All read operations (get, list) automatically apply:
    WHERE tenant_id = :tenant_id AND deleted_at IS NULL
- update() sets updated_at explicitly because server-side onupdate triggers
  only fire on UPDATE statements when the column is not included in the SET;
  we set it manually to guarantee the value is current within the session.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import TenantScopedMixin

T = TypeVar("T", bound=TenantScopedMixin)


class BaseRepository(Generic[T]):
    """Generic async repository that enforces tenant isolation on every query.

    Constructor arguments:
      session    — open AsyncSession for the current request/unit-of-work
      tenant_id  — UUID of the current tenant (from verified JWT)
      model      — SQLAlchemy mapped class to operate on (must use TenantScopedMixin)

    Public methods:
      get(id)              -> T | None
      list(**filters)      -> list[T]
      create(data)         -> T
      update(id, data)     -> T | None
      soft_delete(id)      -> bool
    """

    def __init__(
        self,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        model: type[T],
    ) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._model = model

    # ── Reads ─────────────────────────────────────────────────────────────────

    async def get(self, id: uuid.UUID) -> T | None:
        """Return a single active record by PK within the current tenant.

        Returns None if the record doesn't exist, belongs to another tenant,
        or has been soft-deleted.
        """
        stmt = (
            select(self._model)
            .where(
                self._model.id == id,
                self._model.tenant_id == self._tenant_id,
                self._model.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, **filters: Any) -> list[T]:
        """Return all active records for the current tenant, optionally filtered.

        Keyword arguments are translated to equality filters on the model columns.
        Raises AttributeError if a filter key is not a valid model column.
        """
        stmt = (
            select(self._model)
            .where(
                self._model.tenant_id == self._tenant_id,
                self._model.deleted_at.is_(None),
            )
        )
        for key, value in filters.items():
            column = getattr(self._model, key)
            stmt = stmt.where(column == value)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ── Writes ────────────────────────────────────────────────────────────────

    async def create(self, data: dict[str, Any]) -> T:
        """Persist a new record, automatically setting tenant_id.

        The tenant_id is always sourced from the repository instance (the JWT),
        never from the data dict — any tenant_id in data is overwritten.
        """
        data = {**data, "tenant_id": self._tenant_id}
        instance = self._model(**data)
        self._session.add(instance)
        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    async def update(self, id: uuid.UUID, data: dict[str, Any]) -> T | None:
        """Update an existing active record within the current tenant.

        Returns the updated instance, or None if not found / not in tenant.
        Prevents overwriting tenant_id or id from the data dict.
        """
        instance = await self.get(id)
        if instance is None:
            return None

        # Protect immutable fields
        data.pop("id", None)
        data.pop("tenant_id", None)

        for key, value in data.items():
            setattr(instance, key, value)

        # Explicitly update updated_at so it's visible within the current session
        # (server-side onupdate only reflects after a round-trip to the DB)
        instance.updated_at = datetime.now(tz=timezone.utc)

        self._session.add(instance)
        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    async def soft_delete(self, id: uuid.UUID) -> bool:
        """Soft-delete a record by setting deleted_at = now().

        Returns True if the record was found and marked deleted, False otherwise.
        NEVER emits a DELETE SQL statement.
        """
        instance = await self.get(id)
        if instance is None:
            return False

        instance.deleted_at = datetime.now(tz=timezone.utc)
        self._session.add(instance)
        await self._session.flush()
        return True
