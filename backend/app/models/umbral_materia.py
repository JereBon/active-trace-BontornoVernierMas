"""models/umbral_materia.py — UmbralMateria model (C-10: calificaciones-y-umbral).

Stores the passing threshold for a docente's assignments in a materia.
One record per (tenant_id, asignacion_id, materia_id). Changing this value
triggers a recalculation of `aprobado` on all existing Calificacion records
for that asignacion×materia pair.

Design decisions (C-10 design.md D4):
- Unique constraint on (tenant_id, asignacion_id, materia_id) ensures one
  threshold per docente per materia.
- umbral_pct default = 60 (RN-03).
- valores_aprobatorios is stored as a TEXT array (PostgreSQL native) for
  textual grade approval configuration. Future: configurable per tenant.
- Inherits TenantScopedMixin: id, tenant_id, created_at, updated_at, deleted_at.
"""

import uuid

from sqlalchemy import Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantScopedMixin

_DEFAULT_UMBRAL_PCT = 60


class UmbralMateria(Base, TenantScopedMixin):
    """Passing threshold for a docente's assignment in a materia.

    Rules:
      - One record per (tenant_id, asignacion_id, materia_id).
      - Changing umbral_pct triggers recalculation in CalificacionService.
      - Default umbral_pct = 60 (RN-03).
    """

    __tablename__ = "umbral_materia"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "asignacion_id",
            "materia_id",
            name="uq_umbral_materia_asignacion",
        ),
    )

    asignacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="FK to asignaciones; which docente assignment this threshold belongs to.",
    )

    materia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="FK to materias; which materia this threshold applies to.",
    )

    umbral_pct: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=_DEFAULT_UMBRAL_PCT,
        server_default=str(_DEFAULT_UMBRAL_PCT),
        comment="Minimum percentage to consider a numeric grade as passing (RN-03).",
    )

    valores_aprobatorios: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        default=list,
        server_default="{}",
        comment="List of textual grade values that count as passing (RN-02).",
    )
