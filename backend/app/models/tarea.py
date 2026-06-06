"""models/tarea.py — Tarea and ComentarioTarea models (C-16).

Tarea represents an internal task assigned between team members (E12 in KB §04).
ComentarioTarea represents a comment thread on a task.

Design decisions:
  D1 — asignado_a and asignado_por are FK → usuarios.id (both tracked for delegation).
  D2 — estado stored as String (not PG ENUM) for DDL flexibility.
  D3 — contexto_id is nullable UUID with no FK constraint (domain-agnostic reference).
  D4 — materia_id is nullable: tasks can be institutional (not tied to a materia).
  D5 — Inherits TenantScopedMixin for multi-tenancy and soft delete.
  D6 — ComentarioTarea ordered by created_at ASC for chronological thread.
"""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantScopedMixin


class Tarea(Base, TenantScopedMixin):
    """Internal task assigned between team members.

    Rules:
      - estado: Pendiente | En_progreso | Resuelta | Cancelada
      - asignado_por is preserved even after delegation (never overwritten).
      - Soft-deleted via deleted_at (TenantScopedMixin).
      - materia_id is nullable for institutional-level tasks.
      - contexto_id is nullable domain reference (no FK constraint).
    """

    __tablename__ = "tareas"

    titulo: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Short title of the task.",
    )
    descripcion: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="Full description of the task.",
    )
    asignado_a: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", name="fk_tarea_asignado_a"),
        nullable=False,
        index=True,
        comment="FK → usuarios.id — who must resolve the task.",
    )
    asignado_por: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", name="fk_tarea_asignado_por"),
        nullable=False,
        index=True,
        comment="FK → usuarios.id — who originally assigned the task (preserved on delegation).",
    )
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Pendiente",
        server_default="Pendiente",
        comment="Pendiente | En_progreso | Resuelta | Cancelada",
    )
    materia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materias.id", name="fk_tarea_materia"),
        nullable=True,
        default=None,
        index=True,
        comment="FK → materias.id — nullable for institutional-level tasks.",
    )
    contexto_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        default=None,
        comment="Optional reference to another domain entity (no FK constraint).",
    )


class ComentarioTarea(Base, TenantScopedMixin):
    """Comment on a Tarea, forming a chronological thread.

    Rules:
      - Ordered by created_at ASC for chronological display.
      - Soft-deleted via deleted_at (TenantScopedMixin).
    """

    __tablename__ = "comentarios_tarea"

    tarea_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tareas.id", name="fk_comentario_tarea"),
        nullable=False,
        index=True,
        comment="FK → tareas.id — the task this comment belongs to.",
    )
    autor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", name="fk_comentario_autor"),
        nullable=False,
        index=True,
        comment="FK → usuarios.id — who wrote the comment.",
    )
    contenido: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Comment text content.",
    )
