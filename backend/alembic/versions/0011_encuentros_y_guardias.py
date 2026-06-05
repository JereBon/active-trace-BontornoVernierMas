"""Create slot_encuentro, instancia_encuentro, guardia tables (C-13).

Revision ID: 0011
Revises: 0009
Create Date: 2026-06-05

Changes:
  - Creates table 'slot_encuentro': recurrence template for synchronous encounters.
  - Creates table 'instancia_encuentro': concrete meeting occurrence (slot-derived or independent).
  - Creates table 'guardia': tutor duty-shift record.

Note: down_revision = "0009" because C-10 (migration 0010) runs in parallel.
This change does NOT depend on 0010.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create slot_encuentro, instancia_encuentro, guardia tables."""

    # ── slot_encuentro ────────────────────────────────────────────────────────
    op.create_table(
        "slot_encuentro",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column(
            "asignacion_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("asignaciones.id", name="fk_slot_encuentro_asignacion"),
            nullable=False,
            comment="Asignacion that owns this slot.",
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materias.id", name="fk_slot_encuentro_materia"),
            nullable=False,
        ),
        sa.Column("titulo", sa.String(), nullable=False),
        sa.Column("hora", sa.String(5), nullable=False, comment="HH:MM format."),
        sa.Column(
            "dia_semana",
            sa.String(10),
            nullable=False,
            comment="Lunes | Martes | Miercoles | Jueves | Viernes | Sabado | Domingo",
        ),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column(
            "cant_semanas",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="0 = fecha_unica mode; > 0 = recurrent.",
        ),
        sa.Column(
            "fecha_unica",
            sa.Date(),
            nullable=True,
            comment="Used when cant_semanas=0 for a one-off encounter.",
        ),
        sa.Column("meet_url", sa.Text(), nullable=True),
        sa.Column("vig_desde", sa.Date(), nullable=True),
        sa.Column("vig_hasta", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_slot_encuentro_tenant_id", "slot_encuentro", ["tenant_id"])
    op.create_index("ix_slot_encuentro_materia_id", "slot_encuentro", ["materia_id"])

    # ── instancia_encuentro ───────────────────────────────────────────────────
    op.create_table(
        "instancia_encuentro",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "slot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("slot_encuentro.id", name="fk_instancia_encuentro_slot"),
            nullable=True,
            comment="NULL when created independently (no slot).",
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materias.id", name="fk_instancia_encuentro_materia"),
            nullable=False,
        ),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("hora", sa.String(5), nullable=False),
        sa.Column("titulo", sa.String(), nullable=False),
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default="Programado",
            comment="Programado | Realizado | Cancelado",
        ),
        sa.Column("meet_url", sa.Text(), nullable=True),
        sa.Column("video_url", sa.Text(), nullable=True),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_instancia_encuentro_tenant_id", "instancia_encuentro", ["tenant_id"])
    op.create_index("ix_instancia_encuentro_materia_id", "instancia_encuentro", ["materia_id"])
    op.create_index("ix_instancia_encuentro_slot_id", "instancia_encuentro", ["slot_id"])
    op.create_index("ix_instancia_encuentro_fecha", "instancia_encuentro", ["fecha"])

    # ── guardia ───────────────────────────────────────────────────────────────
    op.create_table(
        "guardia",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "asignacion_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("asignaciones.id", name="fk_guardia_asignacion"),
            nullable=False,
            comment="Asignacion of who covers the duty shift.",
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materias.id", name="fk_guardia_materia"),
            nullable=False,
        ),
        sa.Column(
            "carrera_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("carreras.id", name="fk_guardia_carrera"),
            nullable=False,
        ),
        sa.Column(
            "cohorte_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cohortes.id", name="fk_guardia_cohorte"),
            nullable=False,
        ),
        sa.Column(
            "dia",
            sa.String(10),
            nullable=False,
            comment="Lunes | Martes | Miercoles | Jueves | Viernes | Sabado | Domingo",
        ),
        sa.Column("horario", sa.String(20), nullable=False, comment="Range e.g. '14:00-14:45'."),
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default="Pendiente",
            comment="Pendiente | Realizada | Cancelada",
        ),
        sa.Column("comentarios", sa.Text(), nullable=True),
        sa.Column(
            "creada_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_guardia_tenant_id", "guardia", ["tenant_id"])
    op.create_index("ix_guardia_materia_id", "guardia", ["materia_id"])
    op.create_index("ix_guardia_asignacion_id", "guardia", ["asignacion_id"])


def downgrade() -> None:
    """Drop guardia, instancia_encuentro, slot_encuentro tables."""
    op.drop_table("guardia")
    op.drop_table("instancia_encuentro")
    op.drop_table("slot_encuentro")
