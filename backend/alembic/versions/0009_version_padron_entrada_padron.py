"""Create version_padron and entrada_padron tables (C-09).

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-04

Changes:
  - Creates table 'version_padron': versioned padrón per (tenant, materia, cohorte).
      Only one version can be active per (tenant_id, materia_id, cohorte_id) at a time.
      Partial unique constraint enforces this at DB level.
  - Creates table 'entrada_padron': one row per student in a version.
      usuario_id is nullable: students without an account are allowed.
      email_cifrado stores AES-256-GCM encrypted email.

Note: requires migrations 0005 (materias, cohortes) and 0008 (usuarios) to be applied.
"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# ── New permissions for this migration ───────────────────────────────────────
_PADRON_PERMISOS: list[tuple[str, str]] = [
    ("padron:leer", "Ver versiones del padrón de alumnos"),
    ("padron:cargar", "Cargar padrón de alumnos (desde archivo o Moodle)"),
    ("padron:vaciar", "Vaciar el padrón de una materia"),
]

# Role → new permissions to add
_PADRON_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "PROFESOR": ["padron:leer", "padron:cargar"],
    "COORDINADOR": ["padron:leer", "padron:cargar", "padron:vaciar"],
    "ADMIN": ["padron:leer", "padron:cargar", "padron:vaciar"],
}

# revision identifiers
revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create version_padron and entrada_padron tables."""

    # ── Create version_padron ─────────────────────────────────────────────────
    op.create_table(
        "version_padron",
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
            "materia_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="FK to materias; scopes this version to a specific subject.",
        ),
        sa.Column(
            "cohorte_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="FK to cohortes; scopes this version to a specific cohort.",
        ),
        sa.Column(
            "cargado_por",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="FK to usuarios; who uploaded this version.",
        ),
        sa.Column(
            "cargado_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Timestamp when this version was created.",
        ),
        sa.Column(
            "activa",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="True if this is the currently active version for (tenant, materia, cohorte).",
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
            ["tenant_id"], ["tenants.id"], name="fk_version_padron_tenant"
        ),
        sa.ForeignKeyConstraint(
            ["materia_id"], ["materias.id"], name="fk_version_padron_materia"
        ),
        sa.ForeignKeyConstraint(
            ["cohorte_id"], ["cohortes.id"], name="fk_version_padron_cohorte"
        ),
        sa.ForeignKeyConstraint(
            ["cargado_por"], ["usuarios.id"], name="fk_version_padron_cargado_por"
        ),
    )

    # Partial unique constraint: only one active version per (tenant, materia, cohorte)
    op.create_index(
        "uq_version_padron_activa",
        "version_padron",
        ["tenant_id", "materia_id", "cohorte_id"],
        unique=True,
        postgresql_where=sa.text("activa = true AND deleted_at IS NULL"),
    )

    # Lookup index for non-unique queries
    op.create_index(
        "ix_version_padron_tenant_materia_cohorte",
        "version_padron",
        ["tenant_id", "materia_id", "cohorte_id"],
    )

    op.create_index(
        "ix_version_padron_tenant_id",
        "version_padron",
        ["tenant_id"],
    )

    # ── Create entrada_padron ─────────────────────────────────────────────────
    op.create_table(
        "entrada_padron",
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
            "version_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="FK to version_padron; which version this entry belongs to.",
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="FK to usuarios; NULL when student has no account yet.",
        ),
        sa.Column(
            "nombre",
            sa.String(),
            nullable=False,
            comment="Student first name (plaintext, denormalized for history).",
        ),
        sa.Column(
            "apellidos",
            sa.String(),
            nullable=False,
            comment="Student last name(s) (plaintext, denormalized for history).",
        ),
        sa.Column(
            "email_cifrado",
            sa.Text(),
            nullable=False,
            comment="AES-256-GCM encrypted email address.",
        ),
        sa.Column(
            "comision",
            sa.String(),
            nullable=True,
            comment="Student comision/group code.",
        ),
        sa.Column(
            "regional",
            sa.String(),
            nullable=True,
            comment="Student regional/branch.",
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
            ["tenant_id"], ["tenants.id"], name="fk_entrada_padron_tenant"
        ),
        sa.ForeignKeyConstraint(
            ["version_id"], ["version_padron.id"], name="fk_entrada_padron_version"
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuarios.id"], name="fk_entrada_padron_usuario"
        ),
    )

    # Indexes for entrada_padron
    op.create_index(
        "ix_entrada_padron_version_tenant",
        "entrada_padron",
        ["version_id", "tenant_id"],
    )

    op.create_index(
        "ix_entrada_padron_tenant_id",
        "entrada_padron",
        ["tenant_id"],
    )

    # ── Seed new padron permissions for all existing tenants ──────────────────
    _seed_padron_permissions(op.get_bind())


def _seed_padron_permissions(conn: sa.engine.Connection) -> None:
    """Add padron:leer, padron:cargar, padron:vaciar to all existing tenants.

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
            for codigo, desc in _PADRON_PERMISOS
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
        for rol_codigo, permisos_codigos in _PADRON_ROLE_PERMISSIONS.items():
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
    """Drop entrada_padron and version_padron tables (in dependency order)."""
    op.drop_table("entrada_padron")
    op.drop_table("version_padron")
