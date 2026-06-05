"""models/guardia.py — Guardia model (C-13).

Guardia represents a tutor duty-shift record (E11 in knowledge-base/04_modelo_de_datos.md).

Design decisions (C-13 design.md):
  D1 — asignacion_id links to the Asignacion of who covers the shift.
  D3 — estado stored as String (not PG ENUM) for DDL flexibility.
  D9 — Inherits TenantScopedMixin for multi-tenancy and soft delete.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantScopedMixin


class Guardia(Base, TenantScopedMixin):
    """Tutor duty-shift record.

    Rules:
      - estado: Pendiente | Realizada | Cancelada
      - Soft-deleted via deleted_at (TenantScopedMixin).
    """

    __tablename__ = "guardia"

    asignacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("asignaciones.id", name="fk_guardia_asignacion"),
        nullable=False,
        index=True,
        comment="Asignacion of who covers the duty shift.",
    )
    materia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materias.id", name="fk_guardia_materia"),
        nullable=False,
        index=True,
    )
    carrera_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("carreras.id", name="fk_guardia_carrera"),
        nullable=False,
    )
    cohorte_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cohortes.id", name="fk_guardia_cohorte"),
        nullable=False,
    )
    dia: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Lunes | Martes | Miercoles | Jueves | Viernes | Sabado | Domingo",
    )
    horario: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Range e.g. '14:00-14:45'.",
    )
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Pendiente",
        server_default="Pendiente",
        comment="Pendiente | Realizada | Cancelada",
    )
    comentarios: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    creada_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the guardia was registered.",
    )
