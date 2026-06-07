"""Create liquidaciones tables and add categoria_clave to materias (C-18).

Revision ID: 0017
Revises: 0016
Create Date: 2026-06-07

Changes:
  - Creates table 'salario_base': base salary per role with date-range validity.
  - Creates table 'salario_plus': bonus salary per (grupo, rol) with date-range validity.
  - Creates table 'liquidaciones': per-docente salary record per (cohorte, periodo).
  - Creates table 'facturas': invoice submitted by facturante docentes.
  - ALTER TABLE materias ADD COLUMN categoria_clave VARCHAR NULL.

All new tables inherit TenantScopedMixin columns:
  id (UUID PK), tenant_id (UUID NOT NULL), created_at, updated_at, deleted_at.

Downgrade:
  - Drop the 4 new tables.
  - DROP COLUMN categoria_clave from materias.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0017"
down_revision: Union[str, tuple[str, ...], None] = "0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Common TenantScopedMixin columns reused across tables
_TENANT_COLS = [
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
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
        comment="Record creation timestamp.",
    ),
    sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
        comment="Record last-update timestamp.",
    ),
    sa.Column(
        "deleted_at",
        sa.DateTime(timezone=True),
        nullable=True,
        comment="Soft-delete timestamp; NULL = active.",
    ),
]


def upgrade() -> None:
    conn = op.get_bind()

    # ── 1. salario_base ───────────────────────────────────────────────────────
    if not conn.execute(
        sa.text("SELECT 1 FROM information_schema.tables WHERE table_name='salario_base'")
    ).fetchone():
        op.create_table(
            "salario_base",
            *_TENANT_COLS,
            sa.Column(
                "rol",
                sa.String,
                nullable=False,
                comment="Role code (e.g. PROFESOR, TUTOR, NEXO).",
            ),
            sa.Column(
                "monto",
                sa.Numeric(precision=12, scale=2),
                nullable=False,
                comment="Base salary amount.",
            ),
            sa.Column(
                "desde",
                sa.Date,
                nullable=False,
                comment="First date this record is valid (inclusive).",
            ),
            sa.Column(
                "hasta",
                sa.Date,
                nullable=True,
                comment="Last date this record is valid; NULL = open-ended.",
            ),
            sa.Column(
                "descripcion",
                sa.String,
                nullable=True,
                comment="Optional note about this salary entry.",
            ),
        )
        op.create_index("ix_salario_base_tenant_id", "salario_base", ["tenant_id"])
        op.create_index("ix_salario_base_rol", "salario_base", ["rol"])

    # ── 2. salario_plus ───────────────────────────────────────────────────────
    if not conn.execute(
        sa.text("SELECT 1 FROM information_schema.tables WHERE table_name='salario_plus'")
    ).fetchone():
        op.create_table(
            "salario_plus",
            *_TENANT_COLS,
            sa.Column(
                "grupo",
                sa.String,
                nullable=False,
                comment="Category key matching Materia.categoria_clave.",
            ),
            sa.Column(
                "rol",
                sa.String,
                nullable=False,
                comment="Role code this plus applies to.",
            ),
            sa.Column(
                "descripcion",
                sa.String,
                nullable=True,
                comment="Optional label for this plus entry.",
            ),
            sa.Column(
                "monto",
                sa.Numeric(precision=12, scale=2),
                nullable=False,
                comment="Plus amount per commission unit.",
            ),
            sa.Column(
                "desde",
                sa.Date,
                nullable=False,
                comment="First date this record is valid (inclusive).",
            ),
            sa.Column(
                "hasta",
                sa.Date,
                nullable=True,
                comment="Last date this record is valid; NULL = open-ended.",
            ),
        )
        op.create_index("ix_salario_plus_tenant_id", "salario_plus", ["tenant_id"])
        op.create_index("ix_salario_plus_grupo", "salario_plus", ["grupo"])
        op.create_index("ix_salario_plus_rol", "salario_plus", ["rol"])

    # ── 3. liquidaciones ──────────────────────────────────────────────────────
    if not conn.execute(
        sa.text("SELECT 1 FROM information_schema.tables WHERE table_name='liquidaciones'")
    ).fetchone():
        op.create_table(
            "liquidaciones",
            *_TENANT_COLS,
            sa.Column(
                "cohorte_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("cohortes.id", name="fk_liquidaciones_cohorte"),
                nullable=False,
                comment="FK → cohortes.id",
            ),
            sa.Column(
                "periodo",
                sa.String(7),
                nullable=False,
                comment="Billing period AAAA-MM.",
            ),
            sa.Column(
                "usuario_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("usuarios.id", name="fk_liquidaciones_usuario"),
                nullable=False,
                comment="FK → usuarios.id — the docente.",
            ),
            sa.Column(
                "rol",
                sa.String,
                nullable=False,
                comment="Role at calculation time.",
            ),
            sa.Column(
                "comisiones",
                postgresql.ARRAY(sa.Text),
                nullable=False,
                server_default="{}",
                comment="Snapshot of commission codes.",
            ),
            sa.Column(
                "monto_base",
                sa.Numeric(precision=12, scale=2),
                nullable=False,
                comment="Base salary component.",
            ),
            sa.Column(
                "monto_plus",
                sa.Numeric(precision=12, scale=2),
                nullable=False,
                comment="Accumulated plus component.",
            ),
            sa.Column(
                "total",
                sa.Numeric(precision=12, scale=2),
                nullable=False,
                comment="monto_base + monto_plus.",
            ),
            sa.Column(
                "es_nexo",
                sa.Boolean,
                nullable=False,
                server_default="false",
                comment="True when docente holds NEXO role.",
            ),
            sa.Column(
                "excluido_por_factura",
                sa.Boolean,
                nullable=False,
                server_default="false",
                comment="True when Usuario.facturador=True at calculation time.",
            ),
            sa.Column(
                "estado",
                sa.String,
                nullable=False,
                server_default="Abierta",
                comment="Abierta | Cerrada (immutable once Cerrada).",
            ),
        )
        op.create_index("ix_liquidaciones_tenant_id", "liquidaciones", ["tenant_id"])
        op.create_index("ix_liquidaciones_cohorte_id", "liquidaciones", ["cohorte_id"])
        op.create_index("ix_liquidaciones_usuario_id", "liquidaciones", ["usuario_id"])
        op.create_index("ix_liquidaciones_periodo", "liquidaciones", ["periodo"])

    # ── 4. facturas ───────────────────────────────────────────────────────────
    if not conn.execute(
        sa.text("SELECT 1 FROM information_schema.tables WHERE table_name='facturas'")
    ).fetchone():
        op.create_table(
            "facturas",
            *_TENANT_COLS,
            sa.Column(
                "usuario_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("usuarios.id", name="fk_facturas_usuario"),
                nullable=False,
                comment="FK → usuarios.id — the docente who submitted the invoice.",
            ),
            sa.Column(
                "periodo",
                sa.String(7),
                nullable=False,
                comment="Billing period AAAA-MM.",
            ),
            sa.Column(
                "detalle",
                sa.Text,
                nullable=True,
                comment="Free-form description.",
            ),
            sa.Column(
                "referencia_archivo",
                sa.String,
                nullable=True,
                comment="Reference to the uploaded file (filename/path).",
            ),
            sa.Column(
                "tamano_kb",
                sa.Numeric(precision=10, scale=2),
                nullable=True,
                comment="File size in kilobytes.",
            ),
            sa.Column(
                "estado",
                sa.String,
                nullable=False,
                server_default="Pendiente",
                comment="Pendiente | Abonada.",
            ),
            sa.Column(
                "cargada_at",
                sa.DateTime(timezone=True),
                nullable=True,
                comment="Timestamp when invoice was uploaded.",
            ),
            sa.Column(
                "abonada_at",
                sa.DateTime(timezone=True),
                nullable=True,
                comment="Timestamp when invoice was marked as paid.",
            ),
        )
        op.create_index("ix_facturas_tenant_id", "facturas", ["tenant_id"])
        op.create_index("ix_facturas_usuario_id", "facturas", ["usuario_id"])
        op.create_index("ix_facturas_periodo", "facturas", ["periodo"])

    # ── 5. ALTER TABLE materias ADD COLUMN categoria_clave ────────────────────
    col_exists = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name='materias' AND column_name='categoria_clave'"
        )
    ).fetchone()

    if not col_exists:
        op.add_column(
            "materias",
            sa.Column(
                "categoria_clave",
                sa.String,
                nullable=True,
                comment="Plus group key (e.g. 'PROG'); NULL = no Plus generated.",
            ),
        )


def downgrade() -> None:
    conn = op.get_bind()

    # Drop categoria_clave from materias
    col_exists = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name='materias' AND column_name='categoria_clave'"
        )
    ).fetchone()
    if col_exists:
        op.drop_column("materias", "categoria_clave")

    # Drop tables in reverse FK order
    for table in ("facturas", "liquidaciones", "salario_plus", "salario_base"):
        exists = conn.execute(
            sa.text(f"SELECT 1 FROM information_schema.tables WHERE table_name='{table}'")
        ).fetchone()
        if exists:
            op.drop_table(table)
