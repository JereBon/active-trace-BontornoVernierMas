"""Create evaluaciones, reservas_evaluacion, resultado_evaluacion tables (C-14).

Revision ID: 0015
Revises: 0014
Create Date: 2026-06-06

Changes:
  - Creates table 'evaluaciones': E14 from KB §04. Stores coloquio/exam calls
    with tenant isolation, soft delete, materia/cohorte FK, cupos tracking,
    and estado state machine (Abierta | Cerrada | Cancelada).
  - Creates table 'reservas_evaluacion': student bookings. Each booking
    decrements cupos_disponibles on the parent Evaluacion. Unique constraint
    prevents duplicate Activa reservations per (alumno_id, evaluacion_id).
  - Creates table 'resultados_evaluacion': exam outcomes. Unique constraint
    prevents duplicate results per (alumno_id, evaluacion_id).
  - Seeds permissions: evaluaciones:gestionar, evaluaciones:resultado.
    (evaluaciones:reservar was seeded by migration 0003.)
  - Indexes on tenant_id, materia_id, cohorte_id, estado for evaluaciones;
    on tenant_id, evaluacion_id, alumno_id for reservas and resultados.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0015"
down_revision: Union[str, tuple[str, ...], None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ── 1. Create evaluaciones table (idempotent) ─────────────────────────────
    evaluaciones_exists = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables WHERE table_name='evaluaciones'"
        )
    ).fetchone()

    if not evaluaciones_exists:
        op.create_table(
            "evaluaciones",
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
                comment="FK → tenants.id — row-level tenant isolation.",
            ),
            sa.Column(
                "materia_id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
                comment="FK → materias.id.",
            ),
            sa.Column(
                "cohorte_id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
                comment="FK → cohortes.id.",
            ),
            sa.Column(
                "tipo",
                sa.String(length=30),
                nullable=False,
                server_default="Coloquio",
                comment="Parcial | TP | Coloquio | Recuperatorio",
            ),
            sa.Column(
                "instancia",
                sa.String(length=255),
                nullable=False,
                comment="Free-text label, e.g. 'Coloquio Final'.",
            ),
            sa.Column(
                "dias_disponibles",
                sa.Integer(),
                nullable=False,
                comment="Days the enrollment window stays open.",
            ),
            sa.Column(
                "cupos_disponibles",
                sa.Integer(),
                nullable=False,
                comment="Remaining reservation slots.",
            ),
            sa.Column(
                "estado",
                sa.String(length=20),
                nullable=False,
                server_default="Abierta",
                comment="Abierta | Cerrada | Cancelada",
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
                comment="Soft delete timestamp. NULL = active.",
            ),
            sa.ForeignKeyConstraint(
                ["materia_id"],
                ["materias.id"],
                name="fk_evaluacion_materia",
            ),
            sa.ForeignKeyConstraint(
                ["cohorte_id"],
                ["cohortes.id"],
                name="fk_evaluacion_cohorte",
            ),
        )

        op.create_index("ix_evaluaciones_tenant_id", "evaluaciones", ["tenant_id"])
        op.create_index("ix_evaluaciones_materia_id", "evaluaciones", ["materia_id"])
        op.create_index("ix_evaluaciones_cohorte_id", "evaluaciones", ["cohorte_id"])
        op.create_index("ix_evaluaciones_estado", "evaluaciones", ["estado"])

    # ── 2. Create reservas_evaluacion table (idempotent) ──────────────────────
    reservas_exists = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables WHERE table_name='reservas_evaluacion'"
        )
    ).fetchone()

    if not reservas_exists:
        op.create_table(
            "reservas_evaluacion",
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
                comment="FK → tenants.id — row-level tenant isolation.",
            ),
            sa.Column(
                "evaluacion_id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
                comment="FK → evaluaciones.id.",
            ),
            sa.Column(
                "alumno_id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
                comment="FK → usuarios.id — the student booking.",
            ),
            sa.Column(
                "fecha_hora",
                sa.DateTime(timezone=True),
                nullable=False,
                comment="Chosen slot datetime.",
            ),
            sa.Column(
                "estado",
                sa.String(length=20),
                nullable=False,
                server_default="Activa",
                comment="Activa | Cancelada",
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
                comment="Soft delete timestamp. NULL = active.",
            ),
            sa.ForeignKeyConstraint(
                ["evaluacion_id"],
                ["evaluaciones.id"],
                name="fk_reserva_evaluacion",
            ),
            sa.ForeignKeyConstraint(
                ["alumno_id"],
                ["usuarios.id"],
                name="fk_reserva_alumno",
            ),
            # No DB-level unique constraint on (alumno_id, evaluacion_id):
            # a student may re-book after cancelling (allowed business flow).
            # Application layer enforces "only one Activa per student/evaluacion".

        )

        op.create_index("ix_reservas_evaluacion_tenant_id", "reservas_evaluacion", ["tenant_id"])
        op.create_index("ix_reservas_evaluacion_evaluacion_id", "reservas_evaluacion", ["evaluacion_id"])
        op.create_index("ix_reservas_evaluacion_alumno_id", "reservas_evaluacion", ["alumno_id"])
        op.create_index("ix_reservas_evaluacion_estado", "reservas_evaluacion", ["estado"])

    # ── 3. Create resultados_evaluacion table (idempotent) ────────────────────
    resultados_exists = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables WHERE table_name='resultados_evaluacion'"
        )
    ).fetchone()

    if not resultados_exists:
        op.create_table(
            "resultados_evaluacion",
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
                comment="FK → tenants.id — row-level tenant isolation.",
            ),
            sa.Column(
                "evaluacion_id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
                comment="FK → evaluaciones.id.",
            ),
            sa.Column(
                "alumno_id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
                comment="FK → usuarios.id — evaluated student.",
            ),
            sa.Column(
                "aprobado",
                sa.Boolean(),
                nullable=False,
                comment="True if the student passed.",
            ),
            sa.Column(
                "nota_final",
                sa.String(length=100),
                nullable=True,
                comment="Numeric or qualitative final grade.",
            ),
            sa.Column(
                "observaciones",
                sa.Text(),
                nullable=True,
                comment="Optional examiner notes.",
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
                comment="Soft delete timestamp. NULL = active.",
            ),
            sa.ForeignKeyConstraint(
                ["evaluacion_id"],
                ["evaluaciones.id"],
                name="fk_resultado_evaluacion",
            ),
            sa.ForeignKeyConstraint(
                ["alumno_id"],
                ["usuarios.id"],
                name="fk_resultado_alumno",
            ),
            sa.UniqueConstraint(
                "alumno_id",
                "evaluacion_id",
                "tenant_id",
                name="uq_resultado_alumno_evaluacion",
            ),
        )

        op.create_index("ix_resultados_evaluacion_tenant_id", "resultados_evaluacion", ["tenant_id"])
        op.create_index("ix_resultados_evaluacion_evaluacion_id", "resultados_evaluacion", ["evaluacion_id"])
        op.create_index("ix_resultados_evaluacion_alumno_id", "resultados_evaluacion", ["alumno_id"])

    # ── 4. Seed permissions (idempotent, one row per tenant per permiso) ────────
    # evaluaciones:gestionar and evaluaciones:resultado — seed per tenant.
    # evaluaciones:reservar was seeded in migration 0003 (RBAC).
    import uuid as _uuid

    tenants = conn.execute(sa.text("SELECT id FROM tenants")).fetchall()
    for codigo, descripcion in [
        ("evaluaciones:gestionar", "Gestionar convocatorias de coloquios (crear, editar, listar, resultados)"),
        ("evaluaciones:resultado", "Registrar resultados de evaluaciones"),
    ]:
        for (tenant_id,) in tenants:
            existing = conn.execute(
                sa.text("SELECT 1 FROM permisos WHERE codigo = :codigo AND tenant_id = :tid"),
                {"codigo": codigo, "tid": str(tenant_id)},
            ).fetchone()
            if not existing:
                conn.execute(
                    sa.text(
                        "INSERT INTO permisos (id, tenant_id, codigo, descripcion, created_at, updated_at) "
                        "VALUES (:id, :tid, :codigo, :descripcion, now(), now())"
                    ),
                    {
                        "id": str(_uuid.uuid4()),
                        "tid": str(tenant_id),
                        "codigo": codigo,
                        "descripcion": descripcion,
                    },
                )


def downgrade() -> None:
    conn = op.get_bind()

    # Drop indexes and table resultados_evaluacion
    for idx in [
        "ix_resultados_evaluacion_alumno_id",
        "ix_resultados_evaluacion_evaluacion_id",
        "ix_resultados_evaluacion_tenant_id",
    ]:
        idx_exists = conn.execute(
            sa.text("SELECT 1 FROM pg_indexes WHERE indexname = :name"),
            {"name": idx},
        ).fetchone()
        if idx_exists:
            op.drop_index(idx, table_name="resultados_evaluacion")

    resultados_exists = conn.execute(
        sa.text("SELECT 1 FROM information_schema.tables WHERE table_name='resultados_evaluacion'")
    ).fetchone()
    if resultados_exists:
        op.drop_table("resultados_evaluacion")

    # Drop indexes and table reservas_evaluacion
    for idx in [
        "ix_reservas_evaluacion_estado",
        "ix_reservas_evaluacion_alumno_id",
        "ix_reservas_evaluacion_evaluacion_id",
        "ix_reservas_evaluacion_tenant_id",
    ]:
        idx_exists = conn.execute(
            sa.text("SELECT 1 FROM pg_indexes WHERE indexname = :name"),
            {"name": idx},
        ).fetchone()
        if idx_exists:
            op.drop_index(idx, table_name="reservas_evaluacion")

    reservas_exists = conn.execute(
        sa.text("SELECT 1 FROM information_schema.tables WHERE table_name='reservas_evaluacion'")
    ).fetchone()
    if reservas_exists:
        op.drop_table("reservas_evaluacion")

    # Drop indexes and table evaluaciones
    for idx in [
        "ix_evaluaciones_estado",
        "ix_evaluaciones_cohorte_id",
        "ix_evaluaciones_materia_id",
        "ix_evaluaciones_tenant_id",
    ]:
        idx_exists = conn.execute(
            sa.text("SELECT 1 FROM pg_indexes WHERE indexname = :name"),
            {"name": idx},
        ).fetchone()
        if idx_exists:
            op.drop_index(idx, table_name="evaluaciones")

    evaluaciones_exists = conn.execute(
        sa.text("SELECT 1 FROM information_schema.tables WHERE table_name='evaluaciones'")
    ).fetchone()
    if evaluaciones_exists:
        op.drop_table("evaluaciones")

    # Note: permissions seeded here are intentionally NOT removed in downgrade
    # to avoid breaking role assignments that may reference them.
