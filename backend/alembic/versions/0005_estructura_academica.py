"""Create estructura academica tables: carreras, cohortes, materias (C-06).

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-04

Creates three tables:
  - carreras   : academic programs per tenant
  - cohortes   : cohorts (student intakes) per carrera
  - materias   : subject catalog per tenant

Unique constraints:
  - (tenant_id, codigo)              on carreras (partial: deleted_at IS NULL)
  - (tenant_id, carrera_id, nombre)  on cohortes (partial: deleted_at IS NULL)
  - (tenant_id, codigo)              on materias (partial: deleted_at IS NULL)

Note: estructura:gestionar permission and ADMIN role assignment are already
seeded by 0003_rbac.py which includes this permission in _ALL_PERMISOS and
_ROLE_PERMISSIONS['ADMIN']. No extra seeding required here.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create carreras, cohortes, materias tables."""

    # ── carreras ──────────────────────────────────────────────────────────────
    op.create_table(
        "carreras",
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
        sa.Column("codigo", sa.String(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column(
            "estado",
            sa.String(),
            nullable=False,
            server_default="Activa",
            comment="Activa | Inactiva",
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
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Partial unique index: (tenant_id, codigo) where deleted_at IS NULL
    op.create_index(
        "uq_carreras_tenant_codigo_active",
        "carreras",
        ["tenant_id", "codigo"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── cohortes ──────────────────────────────────────────────────────────────
    op.create_table(
        "cohortes",
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
            "carrera_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("carreras.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("anio", sa.Integer(), nullable=False),
        sa.Column("vig_desde", sa.Date(), nullable=False),
        sa.Column("vig_hasta", sa.Date(), nullable=True),
        sa.Column(
            "estado",
            sa.String(),
            nullable=False,
            server_default="Activa",
            comment="Activa | Inactiva",
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
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Partial unique index: (tenant_id, carrera_id, nombre) where deleted_at IS NULL
    op.create_index(
        "uq_cohortes_tenant_carrera_nombre_active",
        "cohortes",
        ["tenant_id", "carrera_id", "nombre"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── materias ──────────────────────────────────────────────────────────────
    op.create_table(
        "materias",
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
        sa.Column("codigo", sa.String(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column(
            "estado",
            sa.String(),
            nullable=False,
            server_default="Activa",
            comment="Activa | Inactiva",
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
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Partial unique index: (tenant_id, codigo) where deleted_at IS NULL
    op.create_index(
        "uq_materias_tenant_codigo_active",
        "materias",
        ["tenant_id", "codigo"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    """Drop estructura academica tables in reverse FK order."""
    op.drop_index("uq_materias_tenant_codigo_active", table_name="materias")
    op.drop_table("materias")
    op.drop_index(
        "uq_cohortes_tenant_carrera_nombre_active", table_name="cohortes"
    )
    op.drop_table("cohortes")
    op.drop_index("uq_carreras_tenant_codigo_active", table_name="carreras")
    op.drop_table("carreras")
