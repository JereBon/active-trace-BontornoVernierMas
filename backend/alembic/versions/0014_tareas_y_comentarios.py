"""Create tareas and comentarios_tarea tables (C-16).

Revision ID: 0014
Revises: 0013
Create Date: 2026-06-06

Changes:
  - Creates table 'tareas': E12 from KB §04. Stores internal tasks with
    tenant isolation, soft delete, estado state machine, asignado_a / asignado_por
    (both preserved for delegation traceability), optional materia_id and contexto_id.
  - Creates table 'comentarios_tarea': ComentarioTarea from KB §04. Stores
    chronological comment threads on tasks.
  - Seeds permission: tareas:gestionar (if not already present).
  - Indexes on tenant_id, asignado_a, asignado_por, estado for tareas;
    on tenant_id, tarea_id for comentarios_tarea.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0014"
down_revision: Union[str, tuple[str, ...], None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ── 1. Create tareas table (idempotent) ────────────────────────────────────
    tareas_exists = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables WHERE table_name='tareas'"
        )
    ).fetchone()

    if not tareas_exists:
        op.create_table(
            "tareas",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                nullable=False,
                comment="Internal UUID primary key.",
            ),
            sa.Column(
                "tenant_id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
                comment="FK → tenants.id — enforces row-level tenant isolation.",
            ),
            sa.Column(
                "titulo",
                sa.String(length=255),
                nullable=False,
                comment="Short title of the task.",
            ),
            sa.Column(
                "descripcion",
                sa.Text(),
                nullable=True,
                comment="Full description of the task.",
            ),
            sa.Column(
                "asignado_a",
                postgresql.UUID(as_uuid=True),
                nullable=False,
                comment="FK → usuarios.id — who must resolve the task.",
            ),
            sa.Column(
                "asignado_por",
                postgresql.UUID(as_uuid=True),
                nullable=False,
                comment="FK → usuarios.id — who originally assigned the task (preserved on delegation).",
            ),
            sa.Column(
                "estado",
                sa.String(length=20),
                nullable=False,
                server_default="Pendiente",
                comment="State machine: Pendiente | En_progreso | Resuelta | Cancelada.",
            ),
            sa.Column(
                "materia_id",
                postgresql.UUID(as_uuid=True),
                nullable=True,
                comment="FK → materias.id — nullable for institutional-level tasks.",
            ),
            sa.Column(
                "contexto_id",
                postgresql.UUID(as_uuid=True),
                nullable=True,
                comment="Optional reference to another domain entity (no FK constraint).",
            ),
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
            sa.Column(
                "deleted_at",
                sa.DateTime(timezone=True),
                nullable=True,
                comment="Soft delete timestamp. NULL = active; non-NULL = deleted.",
            ),
            sa.ForeignKeyConstraint(
                ["asignado_a"],
                ["usuarios.id"],
                name="fk_tarea_asignado_a",
            ),
            sa.ForeignKeyConstraint(
                ["asignado_por"],
                ["usuarios.id"],
                name="fk_tarea_asignado_por",
            ),
            sa.ForeignKeyConstraint(
                ["materia_id"],
                ["materias.id"],
                name="fk_tarea_materia",
            ),
        )

        op.create_index("ix_tareas_tenant_id", "tareas", ["tenant_id"])
        op.create_index("ix_tareas_asignado_a", "tareas", ["asignado_a"])
        op.create_index("ix_tareas_asignado_por", "tareas", ["asignado_por"])
        op.create_index("ix_tareas_estado", "tareas", ["estado"])
        op.create_index("ix_tareas_materia_id", "tareas", ["materia_id"])

    # ── 2. Create comentarios_tarea table (idempotent) ─────────────────────────
    comentarios_exists = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables WHERE table_name='comentarios_tarea'"
        )
    ).fetchone()

    if not comentarios_exists:
        op.create_table(
            "comentarios_tarea",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                nullable=False,
                comment="Internal UUID primary key.",
            ),
            sa.Column(
                "tenant_id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
                comment="FK → tenants.id — enforces row-level tenant isolation.",
            ),
            sa.Column(
                "tarea_id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
                comment="FK → tareas.id — the task this comment belongs to.",
            ),
            sa.Column(
                "autor_id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
                comment="FK → usuarios.id — who wrote the comment.",
            ),
            sa.Column(
                "contenido",
                sa.Text(),
                nullable=False,
                comment="Comment text content.",
            ),
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
            sa.Column(
                "deleted_at",
                sa.DateTime(timezone=True),
                nullable=True,
                comment="Soft delete timestamp. NULL = active; non-NULL = deleted.",
            ),
            sa.ForeignKeyConstraint(
                ["tarea_id"],
                ["tareas.id"],
                name="fk_comentario_tarea",
            ),
            sa.ForeignKeyConstraint(
                ["autor_id"],
                ["usuarios.id"],
                name="fk_comentario_autor",
            ),
        )

        op.create_index("ix_comentarios_tarea_tenant_id", "comentarios_tarea", ["tenant_id"])
        op.create_index("ix_comentarios_tarea_tarea_id", "comentarios_tarea", ["tarea_id"])
        op.create_index("ix_comentarios_tarea_autor_id", "comentarios_tarea", ["autor_id"])

    # Note: tareas:gestionar permission was already seeded by migration 0003 (RBAC).
    # No additional seeding required here.


def downgrade() -> None:
    conn = op.get_bind()

    # Drop indexes and table comentarios_tarea
    for idx in [
        "ix_comentarios_tarea_autor_id",
        "ix_comentarios_tarea_tarea_id",
        "ix_comentarios_tarea_tenant_id",
    ]:
        idx_exists = conn.execute(
            sa.text("SELECT 1 FROM pg_indexes WHERE indexname = :name"),
            {"name": idx},
        ).fetchone()
        if idx_exists:
            op.drop_index(idx, table_name="comentarios_tarea")

    comentarios_exists = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables WHERE table_name='comentarios_tarea'"
        )
    ).fetchone()
    if comentarios_exists:
        op.drop_table("comentarios_tarea")

    # Drop indexes and table tareas
    for idx in [
        "ix_tareas_materia_id",
        "ix_tareas_estado",
        "ix_tareas_asignado_por",
        "ix_tareas_asignado_a",
        "ix_tareas_tenant_id",
    ]:
        idx_exists = conn.execute(
            sa.text("SELECT 1 FROM pg_indexes WHERE indexname = :name"),
            {"name": idx},
        ).fetchone()
        if idx_exists:
            op.drop_index(idx, table_name="tareas")

    tareas_exists = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables WHERE table_name='tareas'"
        )
    ).fetchone()
    if tareas_exists:
        op.drop_table("tareas")

    # Note: tareas:gestionar was seeded by migration 0003 — do NOT remove it here.
