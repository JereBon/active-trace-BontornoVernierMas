"""models/calificacion.py — Calificacion model (C-10: calificaciones-y-umbral).

Stores a student's grade for an evaluable activity in a materia.
The `aprobado` field is derived by the CalificacionService before persisting
(not a DB-computed column) for testability and to support recalculation
when the threshold changes.

Design decisions (C-10 design.md D1):
- aprobado is stored denormalized for efficient reads in C-11.
- nota_numerica and nota_textual are both nullable; at least one must be set
  (enforced at the service level, not the DB level).
- origen is stored as a plain string (Importado | Manual) for simplicity.
- Unique constraint: (tenant_id, entrada_padron_id, actividad) — one grade
  per student per activity per tenant. upsert_bulk respects this.
- Inherits TenantScopedMixin: id, tenant_id, created_at, updated_at, deleted_at.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantScopedMixin


class Calificacion(Base, TenantScopedMixin):
    """One grade record for a student activity in a materia.

    Rules:
      - aprobado is derived by CalificacionService; not computed by the DB.
      - Unique per (tenant_id, entrada_padron_id, actividad).
      - Soft delete: deleted_at IS NULL means active.
    """

    __tablename__ = "calificacion"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "entrada_padron_id",
            "actividad",
            name="uq_calificacion_entrada_actividad",
        ),
    )

    entrada_padron_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="FK to entrada_padron; identifies the student for this grade.",
    )

    materia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="FK to materias; denormalized for efficient materia-scoped queries.",
    )

    actividad: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Activity name from LMS column header (without '(Real)' suffix).",
    )

    nota_numerica: Mapped[float | None] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=True,
        default=None,
        comment="Numeric grade; NULL when the activity uses a textual scale.",
    )

    nota_textual: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        default=None,
        comment="Textual grade value (e.g. 'Satisfactorio'); NULL when numeric.",
    )

    aprobado: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Derived by service: True if nota_numerica>=umbral OR nota_textual in approved set.",
    )

    origen: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="Importado",
        comment="Source of the grade: Importado | Manual.",
    )

    importado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the grade was last imported/set.",
    )

    finalizado_lms: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="FALSE",
        comment="True when LMS reports the student finalised the activity but no grade is present (RN-07).",
    )
