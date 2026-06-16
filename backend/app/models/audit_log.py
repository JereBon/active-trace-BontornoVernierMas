"""models/audit_log.py — AuditLog model (C-05: audit-log).

Design decisions (design.md):
  D1: AuditLog does NOT inherit TenantScopedMixin. That mixin adds
      created_at, updated_at, and deleted_at — none of which belong on an
      append-only immutable log. We define only the columns needed.
  D5: actor_impersonado_id is always explicit: NULL when no impersonation
      is active, non-NULL with the impersonated user's UUID otherwise.

The table has no deleted_at. Soft-delete is meaningless for an audit log:
records are NEVER modified or removed, by design and by contract.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuditLog(Base):
    """Immutable audit log entry.

    Every significant action in the system persists exactly one row here.
    The repository layer enforces append-only: update() and delete() raise
    NotImplementedError.

    Columns:
        id                  — UUID PK, auto-generated.
        tenant_id           — UUID of the tenant where the action occurred.
        fecha_hora          — UTC timestamp of the action (server-side NOW()).
        actor_id            — UUID of the real user who performed the action.
        actor_impersonado_id— UUID of the impersonated user (NULL if none).
        accion              — Action code string (e.g. "CALIFICACIONES_IMPORTAR").
        detalle             — JSONB blob with action-specific context.
        filas_afectadas     — Number of records affected (0 if not applicable).
        ip                  — Client IP address (string).
        user_agent          — HTTP User-Agent string.
    """

    __tablename__ = "audit_logs"

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
    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    actor_impersonado_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        default=None,
    )
    accion: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    detalle: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=None,
    )
    filas_afectadas: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    ip: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="unknown",
    )
    user_agent: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
