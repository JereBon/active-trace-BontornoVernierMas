"""models/version_padron.py — VersionPadron model (C-09: padron-ingesta-moodle).

Tracks a versioned snapshot of the padrón (student roster) for a given
materia × cohorte combination. Only one version can be active per
(tenant_id, materia_id, cohorte_id) at a time — enforced via a partial
unique index at the DB level (see migration 0009).

Design decisions (C-09 design.md):
- activa: explicit boolean flag, not derived. The activation transition
  (deactivate old → activate new) is atomic within a transaction.
- Soft delete: deleted_at IS NULL means active. The partial unique
  constraint includes deleted_at IS NULL so a soft-deleted version does
  not block a new upload.
- cargado_at tracks when the upload occurred (business timestamp).
  created_at tracks when the row was inserted (technical timestamp).
- Inherits TenantScopedMixin: id, tenant_id, created_at, updated_at, deleted_at.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantScopedMixin


class VersionPadron(Base, TenantScopedMixin):
    """A versioned padrón snapshot for a materia×cohorte pair.

    Rules:
      - Only one VersionPadron with activa=True per (tenant_id, materia_id, cohorte_id).
      - Activating a new version atomically deactivates the previous one.
      - Versions are never hard-deleted (soft delete via deleted_at).
    """

    __tablename__ = "version_padron"

    materia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materias.id", name="fk_version_padron_materia"),
        nullable=False,
        index=True,
        comment="FK to materias; scopes this version to a specific subject.",
    )

    cohorte_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cohortes.id", name="fk_version_padron_cohorte"),
        nullable=False,
        index=True,
        comment="FK to cohortes; scopes this version to a specific cohort.",
    )

    cargado_por: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", name="fk_version_padron_cargado_por"),
        nullable=False,
        comment="FK to usuarios; who uploaded this version.",
    )

    cargado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when this version was created (business timestamp).",
    )

    activa: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="True if this is the currently active version for (tenant, materia, cohorte).",
    )
