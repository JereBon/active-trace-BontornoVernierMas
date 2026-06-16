"""Create calificacion and umbral_materia tables (C-10).

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-05

Changes:
  - Creates table 'calificacion': stores a student's grade for an evaluable
      activity. Unique per (tenant_id, entrada_padron_id, actividad).
      `aprobado` is stored denormalized (computed by the service layer).
  - Creates table 'umbral_materia': stores the passing threshold for a
      docente's assignment in a materia. Unique per (tenant_id, asignacion_id,
      materia_id). Default umbral_pct = 60 (RN-03).
  - Seeds new permissions: calificaciones:importar (already present in permisos
      catalogue from C-04) and calificaciones:umbral.

Note: requires migrations 0008 (usuarios) and 0009 (entrada_padron, asignaciones) applied.
"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# ── New permissions for this migration ───────────────────────────────────────
_CAL_PERMISOS: list[tuple[str, str]] = [
    ("calificaciones:importar", "Importar calificaciones desde archivo LMS"),
    ("calificaciones:umbral", "Configurar umbral de aprobación por materia"),
]

# Role → new permissions to add
_CAL_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "PROFESOR": ["calificaciones:importar", "calificaciones:umbral"],
    "COORDINADOR": ["calificaciones:importar", "calificaciones:umbral"],
    "ADMIN": ["calificaciones:importar", "calificaciones:umbral"],
}

# revision identifiers
revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create calificacion and umbral_materia tables."""

    # ── Create calificacion ───────────────────────────────────────────────────
    op.create_table(
        "calificacion",
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
        ),
        sa.Column(
            "entrada_padron_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="FK to entrada_padron; identifies the student for this grade.",
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="FK to materias; denormalized for efficient materia-scoped queries.",
        ),
        sa.Column(
            "actividad",
            sa.String(),
            nullable=False,
            comment="Activity name from LMS column header (without '(Real)' suffix).",
        ),
        sa.Column(
            "nota_numerica",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
            comment="Numeric grade; NULL when the activity uses a textual scale.",
        ),
        sa.Column(
            "nota_textual",
            sa.String(),
            nullable=True,
            comment="Textual grade value (e.g. 'Satisfactorio'); NULL when numeric.",
        ),
        sa.Column(
            "aprobado",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="Derived by service: True if passing threshold is met.",
        ),
        sa.Column(
            "origen",
            sa.String(),
            nullable=False,
            server_default=sa.text("'Importado'"),
            comment="Source of the grade: Importado | Manual.",
        ),
        sa.Column(
            "importado_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Timestamp when the grade was last imported/set.",
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
        ),
        # FK constraints
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="fk_calificacion_tenant"
        ),
        sa.ForeignKeyConstraint(
            ["entrada_padron_id"],
            ["entrada_padron.id"],
            name="fk_calificacion_entrada_padron",
        ),
        sa.ForeignKeyConstraint(
            ["materia_id"], ["materias.id"], name="fk_calificacion_materia"
        ),
        # Unique constraint
        sa.UniqueConstraint(
            "tenant_id",
            "entrada_padron_id",
            "actividad",
            name="uq_calificacion_entrada_actividad",
        ),
    )

    # Indexes for calificacion
    op.create_index(
        "ix_calificacion_tenant_materia",
        "calificacion",
        ["tenant_id", "materia_id"],
    )
    op.create_index(
        "ix_calificacion_entrada_padron",
        "calificacion",
        ["entrada_padron_id", "tenant_id"],
    )

    # ── Create umbral_materia ─────────────────────────────────────────────────
    op.create_table(
        "umbral_materia",
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
        ),
        sa.Column(
            "asignacion_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="FK to asignaciones; which docente assignment this threshold belongs to.",
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="FK to materias; which materia this threshold applies to.",
        ),
        sa.Column(
            "umbral_pct",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("60"),
            comment="Minimum percentage to consider a numeric grade as passing (RN-03).",
        ),
        sa.Column(
            "valores_aprobatorios",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'"),
            comment="List of textual grade values that count as passing (RN-02).",
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
        ),
        # FK constraints
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="fk_umbral_materia_tenant"
        ),
        sa.ForeignKeyConstraint(
            ["asignacion_id"],
            ["asignaciones.id"],
            name="fk_umbral_materia_asignacion",
        ),
        sa.ForeignKeyConstraint(
            ["materia_id"], ["materias.id"], name="fk_umbral_materia_materia"
        ),
        # Unique constraint
        sa.UniqueConstraint(
            "tenant_id",
            "asignacion_id",
            "materia_id",
            name="uq_umbral_materia_asignacion",
        ),
    )

    # Indexes for umbral_materia
    op.create_index(
        "ix_umbral_materia_tenant_asignacion",
        "umbral_materia",
        ["tenant_id", "asignacion_id"],
    )

    # ── Seed new calificaciones permissions for all existing tenants ──────────
    _seed_calificaciones_permissions(op.get_bind())


def _seed_calificaciones_permissions(conn: sa.engine.Connection) -> None:
    """Add calificaciones:importar and calificaciones:umbral to existing tenants.

    Idempotent: uses ON CONFLICT DO NOTHING for all inserts.
    Assigns permissions to PROFESOR, COORDINADOR, and ADMIN roles.
    """
    tenant_ids = [
        r[0]
        for r in conn.execute(
            sa.text("SELECT id FROM tenants")
        ).fetchall()
    ]

    for tenant_id in tenant_ids:
        # Insert new permissions (idempotent)
        permiso_rows = [
            {
                "id": uuid.uuid4(),
                "tenant_id": tenant_id,
                "codigo": codigo,
                "descripcion": desc,
            }
            for codigo, desc in _CAL_PERMISOS
        ]
        conn.execute(
            sa.text(
                """
                INSERT INTO permisos (id, tenant_id, codigo, descripcion,
                                      created_at, updated_at, deleted_at)
                VALUES (:id, :tenant_id, :codigo, :descripcion,
                        now(), now(), NULL)
                ON CONFLICT (tenant_id, codigo) DO NOTHING
                """
            ),
            permiso_rows,
        )

        # Fetch all permisos for this tenant (including new ones)
        permisos_db = conn.execute(
            sa.text(
                "SELECT id, codigo FROM permisos WHERE tenant_id = :tid AND deleted_at IS NULL"
            ),
            {"tid": tenant_id},
        ).fetchall()
        permiso_by_codigo: dict[str, uuid.UUID] = {r.codigo: r.id for r in permisos_db}

        # Fetch roles for this tenant
        roles_db = conn.execute(
            sa.text(
                "SELECT id, codigo FROM roles WHERE tenant_id = :tid AND deleted_at IS NULL"
            ),
            {"tid": tenant_id},
        ).fetchall()
        rol_by_codigo: dict[str, uuid.UUID] = {r.codigo: r.id for r in roles_db}

        # Insert rol_permiso associations for the new permissions
        rp_rows = []
        for rol_codigo, permisos_codigos in _CAL_ROLE_PERMISSIONS.items():
            rol_id = rol_by_codigo.get(rol_codigo)
            if rol_id is None:
                continue
            for permiso_codigo in permisos_codigos:
                permiso_id = permiso_by_codigo.get(permiso_codigo)
                if permiso_id is None:
                    continue
                rp_rows.append(
                    {
                        "id": uuid.uuid4(),
                        "tenant_id": tenant_id,
                        "rol_id": rol_id,
                        "permiso_id": permiso_id,
                    }
                )

        if rp_rows:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO rol_permisos (id, tenant_id, rol_id, permiso_id, created_at)
                    VALUES (:id, :tenant_id, :rol_id, :permiso_id, now())
                    ON CONFLICT (tenant_id, rol_id, permiso_id) DO NOTHING
                    """
                ),
                rp_rows,
            )


def downgrade() -> None:
    """Drop calificacion and umbral_materia tables."""
    op.drop_table("calificacion")
    op.drop_table("umbral_materia")
