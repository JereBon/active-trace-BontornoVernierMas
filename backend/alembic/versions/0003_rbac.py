"""Create RBAC tables and seed base roles/permissions (C-04: rbac-permisos-finos).

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-04

Creates four tables:
  - roles          : domain roles per tenant (ALUMNO, TUTOR, …)
  - permisos       : fine-grained permissions per tenant (modulo:accion)
  - rol_permisos   : many-to-many association role ↔ permission
  - usuario_roles  : user ↔ role assignment with temporal validity

Seeding:
  seed_roles_base(conn, tenant_id) inserts the 7 domain roles and their
  permission matrix.  Called for every existing tenant during upgrade().
  Uses INSERT … ON CONFLICT DO NOTHING for idempotency.
"""

import uuid
from datetime import date
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ── Permission catalogue (matches core/permisos.py) ───────────────────────────

_ALL_PERMISOS: list[tuple[str, str]] = [
    ("academico:ver_propio", "Ver el propio historial académico"),
    ("evaluaciones:reservar", "Reservar turnos de evaluación"),
    ("avisos:confirmar", "Confirmar recepción de avisos"),
    ("calificaciones:importar", "Importar calificaciones desde Moodle"),
    ("atrasados:ver", "Ver listado de alumnos atrasados"),
    ("entregas:ver_sin_corregir", "Ver entregas pendientes de corrección"),
    ("comunicacion:enviar", "Enviar comunicaciones a alumnos"),
    ("comunicacion:aprobar", "Aprobar comunicaciones antes de envío"),
    ("encuentros:gestionar", "Crear y gestionar encuentros"),
    ("guardias:registrar", "Registrar asistencia de guardias"),
    ("tareas:gestionar", "Gestionar tareas y actividades"),
    ("avisos:publicar", "Publicar avisos institucionales"),
    ("equipos:asignar", "Asignar docentes a equipos"),
    ("estructura:gestionar", "Gestionar estructura académica"),
    ("usuarios:gestionar", "Gestionar usuarios del sistema"),
    ("auditoria:ver", "Ver registros de auditoría"),
    ("liquidaciones:operar", "Operar liquidaciones de honorarios"),
    ("liquidaciones:cerrar", "Cerrar liquidaciones de honorarios"),
    ("facturas:gestionar", "Gestionar facturas de docentes"),
    ("tenant:configurar", "Configurar parámetros del tenant"),
    ("impersonacion:usar", "Usar impersonación de usuarios"),
]

# ── Role → Permission matrix ───────────────────────────────────────────────────

_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "ALUMNO": [
        "academico:ver_propio",
        "evaluaciones:reservar",
        "avisos:confirmar",
    ],
    "TUTOR": [
        "avisos:confirmar",
        "atrasados:ver",
        "entregas:ver_sin_corregir",
        "encuentros:gestionar",
        "guardias:registrar",
    ],
    "PROFESOR": [
        "avisos:confirmar",
        "calificaciones:importar",
        "atrasados:ver",
        "entregas:ver_sin_corregir",
        "comunicacion:enviar",
        "encuentros:gestionar",
        "guardias:registrar",
        "tareas:gestionar",
    ],
    "COORDINADOR": [
        "avisos:confirmar",
        "calificaciones:importar",
        "atrasados:ver",
        "entregas:ver_sin_corregir",
        "comunicacion:enviar",
        "comunicacion:aprobar",
        "encuentros:gestionar",
        "guardias:registrar",
        "tareas:gestionar",
        "avisos:publicar",
        "equipos:asignar",
        "auditoria:ver",
    ],
    "NEXO": [
        "avisos:confirmar",
    ],
    "ADMIN": [
        "academico:ver_propio",
        "evaluaciones:reservar",
        "avisos:confirmar",
        "calificaciones:importar",
        "atrasados:ver",
        "entregas:ver_sin_corregir",
        "comunicacion:enviar",
        "comunicacion:aprobar",
        "encuentros:gestionar",
        "guardias:registrar",
        "tareas:gestionar",
        "avisos:publicar",
        "equipos:asignar",
        "estructura:gestionar",
        "usuarios:gestionar",
        "auditoria:ver",
        "tenant:configurar",
        "impersonacion:usar",
    ],
    "FINANZAS": [
        "avisos:confirmar",
        "auditoria:ver",
        "liquidaciones:operar",
        "liquidaciones:cerrar",
        "facturas:gestionar",
    ],
}

_ROLE_NOMBRES: dict[str, str] = {
    "ALUMNO": "Alumno",
    "TUTOR": "Tutor",
    "PROFESOR": "Profesor",
    "COORDINADOR": "Coordinador",
    "NEXO": "Nexo institucional",
    "ADMIN": "Administrador",
    "FINANZAS": "Finanzas",
}


def seed_roles_base(conn: sa.engine.Connection, tenant_id: uuid.UUID) -> None:
    """Insert domain roles + permissions for *tenant_id*.

    Idempotent: all inserts use ON CONFLICT DO NOTHING.
    Safe to call multiple times on the same tenant.
    """
    today = date.today()

    # 1. Insert permissions ────────────────────────────────────────────────────
    permiso_rows = [
        {
            "id": uuid.uuid4(),
            "tenant_id": tenant_id,
            "codigo": codigo,
            "descripcion": desc,
            "created_at": sa.func.now(),
            "updated_at": sa.func.now(),
            "deleted_at": None,
        }
        for codigo, desc in _ALL_PERMISOS
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

    # 2. Fetch permission id→codigo mapping for this tenant ───────────────────
    rows = conn.execute(
        sa.text(
            "SELECT id, codigo FROM permisos WHERE tenant_id = :tid AND deleted_at IS NULL"
        ),
        {"tid": tenant_id},
    ).fetchall()
    permiso_by_codigo: dict[str, uuid.UUID] = {r.codigo: r.id for r in rows}

    # 3. Insert roles ──────────────────────────────────────────────────────────
    rol_rows = [
        {
            "id": uuid.uuid4(),
            "tenant_id": tenant_id,
            "codigo": codigo,
            "nombre": _ROLE_NOMBRES[codigo],
            "descripcion": None,
            "created_at": sa.func.now(),
            "updated_at": sa.func.now(),
            "deleted_at": None,
        }
        for codigo in _ROLE_PERMISSIONS
    ]
    conn.execute(
        sa.text(
            """
            INSERT INTO roles (id, tenant_id, codigo, nombre, descripcion,
                               created_at, updated_at, deleted_at)
            VALUES (:id, :tenant_id, :codigo, :nombre, :descripcion,
                    now(), now(), NULL)
            ON CONFLICT (tenant_id, codigo) DO NOTHING
            """
        ),
        rol_rows,
    )

    # 4. Fetch role id→codigo mapping for this tenant ─────────────────────────
    rol_rows_db = conn.execute(
        sa.text(
            "SELECT id, codigo FROM roles WHERE tenant_id = :tid AND deleted_at IS NULL"
        ),
        {"tid": tenant_id},
    ).fetchall()
    rol_by_codigo: dict[str, uuid.UUID] = {r.codigo: r.id for r in rol_rows_db}

    # 5. Insert rol_permisos associations ─────────────────────────────────────
    rp_rows = []
    for rol_codigo, permisos_codigos in _ROLE_PERMISSIONS.items():
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
                    "created_at": sa.func.now(),
                }
            )

    if rp_rows:
        conn.execute(
            sa.text(
                """
                INSERT INTO rol_permisos (id, tenant_id, rol_id, permiso_id, created_at)
                VALUES (:id, :tenant_id, :rol_id, :permiso_id, now())
                ON CONFLICT (rol_id, permiso_id) DO NOTHING
                """
            ),
            rp_rows,
        )


def upgrade() -> None:
    """Create RBAC tables and seed roles for all existing tenants."""

    # ── roles ─────────────────────────────────────────────────────────────────
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("codigo", sa.String(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
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
        sa.UniqueConstraint("tenant_id", "codigo", name="uq_roles_tenant_codigo"),
    )

    # ── permisos ──────────────────────────────────────────────────────────────
    op.create_table(
        "permisos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("codigo", sa.String(), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
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
        sa.UniqueConstraint("tenant_id", "codigo", name="uq_permisos_tenant_codigo"),
    )

    # ── rol_permisos ──────────────────────────────────────────────────────────
    op.create_table(
        "rol_permisos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column(
            "rol_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "permiso_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("permisos.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("rol_id", "permiso_id", name="uq_rol_permisos_rol_permiso"),
    )

    # ── usuario_roles ─────────────────────────────────────────────────────────
    op.create_table(
        "usuario_roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
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
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "rol_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("vig_desde", sa.Date(), nullable=False),
        sa.Column("vig_hasta", sa.Date(), nullable=True),
        sa.UniqueConstraint(
            "usuario_id", "rol_id", "vig_desde",
            name="uq_usuario_roles_usuario_rol_desde",
        ),
    )

    # ── Seed existing tenants ─────────────────────────────────────────────────
    conn = op.get_bind()
    tenant_ids = conn.execute(sa.text("SELECT id FROM tenants")).fetchall()
    for row in tenant_ids:
        seed_roles_base(conn, row.id)


def downgrade() -> None:
    """Drop RBAC tables in reverse FK order."""
    op.drop_table("usuario_roles")
    op.drop_table("rol_permisos")
    op.drop_table("permisos")
    op.drop_table("roles")
