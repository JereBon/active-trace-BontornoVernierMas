"""models/base.py — Declarative base and TenantScopedMixin for all ORM models.

Design decisions:
- Single DeclarativeBase (Base) that all models inherit from.
- TenantScopedMixin provides common columns: id, tenant_id, created_at,
  updated_at, deleted_at. Inherited by every domain entity except Tenant itself.
- Soft delete pattern: deleted_at IS NULL means "active"; never hard DELETE.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class EstadoEntidad(str, enum.Enum):
    """Shared active/inactive state for domain catalog entities.

    Used by Carrera, Cohorte, Materia and any future catalog entity.
    Stored as a plain string in the DB (not a native PG enum) so migrations
    are simpler and the column is inspectable without enum catalog changes.
    """

    Activa = "Activa"
    Inactiva = "Inactiva"


class Base(DeclarativeBase):
    """Single declarative base for all ORM models in activia-trace."""


class TenantScopedMixin:
    """Mixin that adds tenant-scoped common columns to every domain entity.

    All domain models MUST inherit this mixin (except Tenant itself, which is
    the isolation root and has no tenant_id reference).

    Columns added:
      id          — UUID primary key, auto-generated via uuid4
      tenant_id   — UUID FK to tenants.id, NOT NULL (enforced at DB level)
      created_at  — timestamp, auto-set on INSERT via server default
      updated_at  — timestamp, auto-set on INSERT and updated on every UPDATE
      deleted_at  — nullable timestamp; NULL = active, non-NULL = soft-deleted
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
