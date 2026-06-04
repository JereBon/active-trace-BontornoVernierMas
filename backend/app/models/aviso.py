"""models/aviso.py — Aviso model (C-15: avisos-y-acknowledgment).

Aviso represents an institutional notice published by COORDINADOR/ADMIN for a tenant.

Design decisions:
  - Soft delete via `activo` flag (domain concept: a deactivated notice is a
    business state, not just a technical tombstone). deleted_at from
    TenantScopedMixin is intentionally unused for Aviso.
  - `scope` stored as String (not native PG ENUM) to allow future values
    (MATERIA, COHORTE) without a DDL migration to the ENUM type.
  - `publicado_por` references Usuario.id; stored as plain UUID (no FK
    constraint declared at ORM level) to avoid circular imports across modules.
  - `vig_hasta` is NOT NULL — open-ended notices are not allowed (RN-18).
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantScopedMixin


class AvisoScope(str, enum.Enum):
    """Audience scope for an Aviso.

    TODOS  — visible to all authenticated users in the tenant.
    ROL    — visible only to users with a specific role (scope_valor = role code).
    USUARIO — visible only to a specific user (scope_valor = usuario UUID str).
    """

    TODOS = "TODOS"
    ROL = "ROL"
    USUARIO = "USUARIO"


class Aviso(Base, TenantScopedMixin):
    """Institutional notice published within a tenant.

    Rules:
      - activo=True means the notice is live; activo=False is soft-deleted.
      - Visibility is controlled by vig_desde / vig_hasta window (RN-18).
      - Audience segmentation is controlled by scope / scope_valor (RN-20).
    """

    __tablename__ = "avisos"

    titulo: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Short title of the notice.",
    )
    cuerpo: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Full body text of the notice.",
    )
    scope: Mapped[str] = mapped_column(
        String,
        nullable=False,
        server_default=AvisoScope.TODOS.value,
        comment="Audience scope: TODOS | ROL | USUARIO",
    )
    scope_valor: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        comment="When scope=ROL: role code. When scope=USUARIO: usuario UUID str.",
    )
    vig_desde: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Visibility start datetime (inclusive).",
    )
    vig_hasta: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Visibility end datetime (inclusive). Must be > vig_desde.",
    )
    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="False = soft-deleted (hidden from all users).",
    )
    publicado_por: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="user_id of the actor who published the notice (from JWT).",
    )
