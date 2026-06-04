"""models/fecha_academica.py — FechaAcademica model (C-17).

Calendarización de instancias evaluativas dentro de un período académico.
Cada fila representa una fecha concreta de evaluación (parcial, TP, coloquio,
recuperatorio) para una materia y cohorte del tenant.

Design decisions:
  - TipoEvaluacion es un enum Python mapeado al tipo nativo Postgres.
  - numero permite distinguir 1er y 2do parcial, etc.
  - periodo es texto libre (ej: '2026-1') para no acoplarse a tablas de períodos.
  - Soft delete via deleted_at (TenantScopedMixin).
"""

import enum
import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantScopedMixin


class TipoEvaluacion(str, enum.Enum):
    """Tipo de instancia evaluativa.

    Stored as native PG enum 'tipoevaluacion' (created in migration 0006).
    """

    PARCIAL = "PARCIAL"
    TP = "TP"
    COLOQUIO = "COLOQUIO"
    RECUPERATORIO = "RECUPERATORIO"


class FechaAcademica(Base, TenantScopedMixin):
    """Instancia evaluativa del calendario académico del tenant.

    Rules:
      - materia_id y cohorte_id son obligatorios.
      - tipo + numero identifican una instancia (ej: 1er Parcial, 2do Parcial).
      - periodo es un string como '2026-1' para el cuatrimestre.
    """

    __tablename__ = "fecha_academica"

    materia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materias.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    cohorte_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cohortes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    tipo: Mapped[TipoEvaluacion] = mapped_column(
        Enum(
            TipoEvaluacion,
            name="tipoevaluacion",
            create_type=False,
        ),
        nullable=False,
        comment="PARCIAL | TP | COLOQUIO | RECUPERATORIO",
    )
    numero: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Número de instancia (ej: 1 = 1er parcial, 2 = 2do parcial).",
    )
    periodo: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Cuatrimestre/año de la instancia (ej: '2026-1').",
    )
    fecha: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Fecha exacta de la evaluación.",
    )
    titulo: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Título descriptivo (ej: '1er Parcial Prog. I').",
    )
