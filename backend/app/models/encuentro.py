"""models/encuentro.py — SlotEncuentro + InstanciaEncuentro models (C-13).

SlotEncuentro: recurrence template for synchronous encounters (E9).
InstanciaEncuentro: concrete meeting occurrence, slot-derived or independent (E10).

Design decisions (C-13 design.md):
  D1 — SlotEncuentro.asignacion_id links to the Asignacion that owns the slot.
  D2 — InstanciaEncuentro.slot_id is nullable: one-off instances have no slot.
  D3 — Estado stored as String, not PG ENUM, for DDL flexibility.
  D9 — Both tables inherit TenantScopedMixin for multi-tenancy and soft delete.
"""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantScopedMixin


class SlotEncuentro(Base, TenantScopedMixin):
    """Recurrence template for synchronous encounters.

    Rules:
      - cant_semanas > 0: generate that many weekly InstanciaEncuentro rows.
      - cant_semanas == 0: use fecha_unica for a single one-off instance.
      - Soft-deleted via deleted_at (TenantScopedMixin).
    """

    __tablename__ = "slot_encuentro"

    asignacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("asignaciones.id", name="fk_slot_encuentro_asignacion"),
        nullable=False,
        index=True,
        comment="Asignacion that owns this slot.",
    )
    materia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materias.id", name="fk_slot_encuentro_materia"),
        nullable=False,
        index=True,
    )
    titulo: Mapped[str] = mapped_column(String, nullable=False)
    hora: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
        comment="HH:MM format.",
    )
    dia_semana: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Lunes | Martes | Miercoles | Jueves | Viernes | Sabado | Domingo",
    )
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    cant_semanas: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="0 = fecha_unica mode; >0 = recurrent.",
    )
    fecha_unica: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        default=None,
        comment="Used when cant_semanas=0 for a one-off encounter.",
    )
    meet_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    vig_desde: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    vig_hasta: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)


class InstanciaEncuentro(Base, TenantScopedMixin):
    """Concrete meeting occurrence derived from a slot or created independently.

    Rules:
      - estado: Programado | Realizado | Cancelado
      - slot_id is NULL for independently-created instances.
      - video_url is populated after the meeting (recording link).
    """

    __tablename__ = "instancia_encuentro"

    slot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("slot_encuentro.id", name="fk_instancia_encuentro_slot"),
        nullable=True,
        default=None,
        index=True,
        comment="NULL when created independently.",
    )
    materia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materias.id", name="fk_instancia_encuentro_materia"),
        nullable=False,
        index=True,
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    hora: Mapped[str] = mapped_column(String(5), nullable=False)
    titulo: Mapped[str] = mapped_column(String, nullable=False)
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Programado",
        server_default="Programado",
        comment="Programado | Realizado | Cancelado",
    )
    meet_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    video_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
