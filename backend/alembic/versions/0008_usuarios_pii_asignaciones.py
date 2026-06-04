"""Add PII columns to usuarios and create asignaciones table (C-07).

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-04

Changes:
  - Adds PII profile columns to 'usuarios' (all nullable for backward compat):
      nombre, apellidos, dni_cifrado, cuil_cifrado, cbu_cifrado,
      alias_cbu_cifrado, banco, regional, legajo, legajo_profesional, facturador
  - Creates table 'asignaciones': links Usuario ↔ Rol ↔ academic context
      (materia_id, carrera_id, cohorte_id) with temporal validity (desde/hasta)
      and supervisory hierarchy (responsable_id).

Note: FKs to materias, carreras, cohortes require migration 0005 to be applied.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add PII columns to usuarios; create asignaciones table."""

    # ── Add PII profile columns to usuarios ───────────────────────────────────
    op.add_column("usuarios", sa.Column(
        "nombre",
        sa.String(),
        nullable=True,
        comment="First name (plaintext).",
    ))
    op.add_column("usuarios", sa.Column(
        "apellidos",
        sa.String(),
        nullable=True,
        comment="Last name(s) (plaintext).",
    ))
    op.add_column("usuarios", sa.Column(
        "dni_cifrado",
        sa.Text(),
        nullable=True,
        comment="AES-256-GCM encrypted DNI (national ID).",
    ))
    op.add_column("usuarios", sa.Column(
        "cuil_cifrado",
        sa.Text(),
        nullable=True,
        comment="AES-256-GCM encrypted CUIL (tax ID).",
    ))
    op.add_column("usuarios", sa.Column(
        "cbu_cifrado",
        sa.Text(),
        nullable=True,
        comment="AES-256-GCM encrypted CBU (bank account key).",
    ))
    op.add_column("usuarios", sa.Column(
        "alias_cbu_cifrado",
        sa.Text(),
        nullable=True,
        comment="AES-256-GCM encrypted CBU alias.",
    ))
    op.add_column("usuarios", sa.Column(
        "banco",
        sa.String(),
        nullable=True,
        comment="Bank name (plaintext).",
    ))
    op.add_column("usuarios", sa.Column(
        "regional",
        sa.String(),
        nullable=True,
        comment="Institutional delegation / branch (plaintext).",
    ))
    op.add_column("usuarios", sa.Column(
        "legajo",
        sa.String(),
        nullable=True,
        comment="Institutional record number (business attribute, not PK).",
    ))
    op.add_column("usuarios", sa.Column(
        "legajo_profesional",
        sa.String(),
        nullable=True,
        comment="Professional college / registry record number.",
    ))
    op.add_column("usuarios", sa.Column(
        "facturador",
        sa.Boolean(),
        nullable=True,
        comment="True if the user issues invoices (monotributo / etc.).",
    ))

    # ── Create asignaciones table ─────────────────────────────────────────────
    op.create_table(
        "asignaciones",
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
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "rol",
            sa.String(),
            nullable=False,
            comment="ALUMNO | TUTOR | PROFESOR | COORDINADOR | NEXO | ADMIN | FINANZAS",
        ),
        sa.Column(
            "materia_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="FK to materias; NULL for tenant-global roles (ADMIN, FINANZAS).",
        ),
        sa.Column(
            "carrera_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="FK to carreras; NULL when assignment is not carrera-scoped.",
        ),
        sa.Column(
            "cohorte_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="FK to cohortes; NULL when assignment is not cohorte-scoped.",
        ),
        sa.Column(
            "comisiones",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default="{}",
            comment="Comma of comision codes covered by this assignment.",
        ),
        sa.Column(
            "responsable_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="FK to usuarios; the coordinator supervising this assignment.",
        ),
        sa.Column(
            "desde",
            sa.Date(),
            nullable=False,
            comment="Start date of validity.",
        ),
        sa.Column(
            "hasta",
            sa.Date(),
            nullable=True,
            comment="End date of validity; NULL means open-ended (still active).",
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
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_asignaciones_tenant"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], name="fk_asignaciones_usuario"),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"], name="fk_asignaciones_materia"),
        sa.ForeignKeyConstraint(["carrera_id"], ["carreras.id"], name="fk_asignaciones_carrera"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohortes.id"], name="fk_asignaciones_cohorte"),
        sa.ForeignKeyConstraint(["responsable_id"], ["usuarios.id"], name="fk_asignaciones_responsable"),
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    op.create_index(
        "ix_asignaciones_tenant_id",
        "asignaciones",
        ["tenant_id"],
    )
    op.create_index(
        "ix_asignaciones_tenant_usuario",
        "asignaciones",
        ["tenant_id", "usuario_id"],
    )


def downgrade() -> None:
    """Drop asignaciones table and PII columns from usuarios."""
    op.drop_table("asignaciones")

    for col in [
        "nombre", "apellidos", "dni_cifrado", "cuil_cifrado",
        "cbu_cifrado", "alias_cbu_cifrado", "banco", "regional",
        "legajo", "legajo_profesional", "facturador",
    ]:
        op.drop_column("usuarios", col)
