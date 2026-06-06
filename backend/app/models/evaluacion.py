"""models/evaluacion.py — Evaluacion, ReservaEvaluacion, ResultadoEvaluacion (C-14).

E14 from knowledge-base/04_modelo_de_datos.md.

Design decisions:
  - Evaluacion represents a coloquio/exam call: materia, cohorte, instancia name,
    dias_disponibles (window for enrollment), cupos_disponibles, and estado.
  - ReservaEvaluacion tracks a student's booking: alumno_id, evaluacion_id,
    fecha_hora chosen, estado Activa | Cancelada.
  - ResultadoEvaluacion records the outcome: aprobado boolean, nota, observaciones.
  - All three tables use TenantScopedMixin (id, tenant_id, created_at,
    updated_at, deleted_at) — soft delete enforced.
  - Enums stored as plain String (not native PG ENUM) for simpler migrations.
  - No ORM-level FK constraints on tenant_id to avoid circular imports; the
    constraint is enforced in the migration DDL.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantScopedMixin


class EstadoEvaluacion(str, enum.Enum):
    """Lifecycle state of a coloquio call."""

    Abierta = "Abierta"
    Cerrada = "Cerrada"
    Cancelada = "Cancelada"


class EstadoReserva(str, enum.Enum):
    """Lifecycle state of a student booking."""

    Activa = "Activa"
    Cancelada = "Cancelada"


class TipoEvaluacionColoquio(str, enum.Enum):
    """Type of evaluation for coloquio module (from E14 KB).

    Named TipoEvaluacionColoquio to avoid conflict with TipoEvaluacion
    in fecha_academica.py (which uses uppercase values for a PG native enum).
    Stored as plain String (not PG ENUM) for simpler migrations.
    """

    Parcial = "Parcial"
    TP = "TP"
    Coloquio = "Coloquio"
    Recuperatorio = "Recuperatorio"


class Evaluacion(Base, TenantScopedMixin):
    """Coloquio/exam call: defines when and how many students can book.

    Rules:
      - (tenant_id, materia_id, cohorte_id, instancia) should be unique to avoid
        duplicate calls — enforced via unique index in migration.
      - cupos_disponibles decremented on ReservaEvaluacion creation (Activa).
      - estado transitions: Abierta → Cerrada | Cancelada (never back to Abierta).
    """

    __tablename__ = "evaluaciones"

    materia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="FK → materias.id",
    )
    cohorte_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="FK → cohortes.id",
    )
    tipo: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        server_default=TipoEvaluacionColoquio.Coloquio.value,
        comment="Parcial | TP | Coloquio | Recuperatorio",
    )
    instancia: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Free-text label, e.g. 'Coloquio Final'.",
    )
    dias_disponibles: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Number of days the enrollment window stays open.",
    )
    cupos_disponibles: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Maximum number of active reservations allowed.",
    )
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=EstadoEvaluacion.Abierta.value,
        comment="Abierta | Cerrada | Cancelada",
    )


class ReservaEvaluacion(Base, TenantScopedMixin):
    """Student booking for a specific Evaluacion.

    Rules:
      - Only one Activa reservation per (alumno_id, evaluacion_id) — enforced by
        unique index in migration.
      - Creating an Activa reservation decrements cupos_disponibles on Evaluacion.
      - Cancelling (estado → Cancelada) restores one cupo.
      - fecha_hora is the student-selected slot (within the evaluacion window).
    """

    __tablename__ = "reservas_evaluacion"

    evaluacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="FK → evaluaciones.id",
    )
    alumno_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="FK → usuarios.id — must be ALUMNO role.",
    )
    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Chosen slot datetime for the coloquio.",
    )
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=EstadoReserva.Activa.value,
        comment="Activa | Cancelada",
    )


class ResultadoEvaluacion(Base, TenantScopedMixin):
    """Outcome record for an alumno in a specific Evaluacion.

    Rules:
      - One result per (alumno_id, evaluacion_id) — enforced by unique index.
      - aprobado is set explicitly by the coordinator/admin registering the result.
      - nota_final is a free-text field (may be numeric or qualitative).
      - observaciones is optional additional context.
    """

    __tablename__ = "resultados_evaluacion"

    evaluacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="FK → evaluaciones.id",
    )
    alumno_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="FK → usuarios.id — the evaluated student.",
    )
    aprobado: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="True if the student passed the evaluation.",
    )
    nota_final: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Numeric or qualitative final grade.",
    )
    observaciones: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional notes from the examiner.",
    )
