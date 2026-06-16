"""Create programa_materia and fecha_academica tables (C-17).

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-04

Creates two tables:
  - programa_materia : programa oficial de una materia por carrera/cohorte
  - fecha_academica  : instancias evaluativas del calendario académico

Both tables use soft delete (deleted_at) and tenant_id isolation.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create programa_materia and fecha_academica tables."""

    # ── programa_materia ──────────────────────────────────────────────────────
    op.create_table(
        "programa_materia",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materias.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "carrera_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("carreras.id", ondelete="RESTRICT"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "cohorte_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cohortes.id", ondelete="RESTRICT"),
            nullable=True,
            index=True,
        ),
        sa.Column("titulo", sa.String(), nullable=False),
        sa.Column("referencia_archivo", sa.String(), nullable=True),
        sa.Column(
            "vigente",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("publicado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── fecha_academica ───────────────────────────────────────────────────────
    # Create enum type for tipo_evaluacion (IF NOT EXISTS — idempotent)
    op.execute(
        "DO $$ BEGIN "
        "  CREATE TYPE tipoevaluacion AS ENUM ('PARCIAL', 'TP', 'COLOQUIO', 'RECUPERATORIO'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; "
        "END $$;"
    )

    op.create_table(
        "fecha_academica",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materias.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "cohorte_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cohortes.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "tipo",
            postgresql.ENUM(
                "PARCIAL",
                "TP",
                "COLOQUIO",
                "RECUPERATORIO",
                name="tipoevaluacion",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("periodo", sa.String(), nullable=False, comment="ej: 2026-1"),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("titulo", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Drop fecha_academica and programa_materia tables."""
    op.drop_table("fecha_academica")
    postgresql.ENUM(name="tipoevaluacion").drop(op.get_bind(), checkfirst=True)
    op.drop_table("programa_materia")
