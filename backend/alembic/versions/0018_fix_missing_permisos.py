"""0018 — Agregar permisos faltantes y asignar TUTOR tareas:gestionar.

Corrige tres bugs críticos detectados en auditoría:
  1. evaluaciones:gestionar y evaluaciones:resultado no estaban en la DB
     → Épica 7 (Coloquios) devolvía 403 para todos los roles.
  2. calificaciones:umbral no estaba en la DB
     → F2.1 (umbral de aprobación) devolvía 403 para todos los roles.
  3. TUTOR no tenía tareas:gestionar
     → F8.1 (ver mis tareas) devolvía 403 para TUTOR, contradiciendo la KB.

Revision ID: 0018
Revises: 0017
"""

from __future__ import annotations

import uuid
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0018"
down_revision: Union[str, tuple[str, ...], None] = "0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Permisos nuevos a insertar
_NEW_PERMISOS: list[tuple[str, str]] = [
    ("evaluaciones:gestionar", "Crear y gestionar convocatorias de coloquio"),
    ("evaluaciones:resultado", "Registrar resultados de evaluaciones orales"),
    ("calificaciones:umbral", "Configurar umbral de aprobación por materia"),
]

# A qué roles asignar cada permiso nuevo
_NEW_ROLE_PERMISOS: dict[str, list[str]] = {
    "TUTOR": [
        "tareas:gestionar",          # F8.1: TUTOR puede ver sus tareas asignadas
    ],
    "PROFESOR": [
        "calificaciones:umbral",     # F2.1: PROFESOR configura umbral de su materia
    ],
    "COORDINADOR": [
        "calificaciones:umbral",
        "evaluaciones:gestionar",    # F7.1-F7.5: COORDINADOR gestiona coloquios
        "evaluaciones:resultado",
    ],
    "ADMIN": [
        "calificaciones:umbral",
        "evaluaciones:gestionar",
        "evaluaciones:resultado",
    ],
}


def _patch_tenant(conn: sa.engine.Connection, tenant_id: uuid.UUID) -> None:
    # 1. Insertar los 3 permisos nuevos (idempotente)
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
        [
            {
                "id": uuid.uuid4(),
                "tenant_id": tenant_id,
                "codigo": codigo,
                "descripcion": desc,
            }
            for codigo, desc in _NEW_PERMISOS
        ],
    )

    # 2. Obtener id→codigo de todos los permisos del tenant
    permiso_rows = conn.execute(
        sa.text(
            "SELECT id, codigo FROM permisos WHERE tenant_id = :tid AND deleted_at IS NULL"
        ),
        {"tid": tenant_id},
    ).fetchall()
    permiso_by_codigo: dict[str, uuid.UUID] = {r.codigo: r.id for r in permiso_rows}

    # 3. Obtener id→codigo de roles del tenant
    rol_rows = conn.execute(
        sa.text(
            "SELECT id, codigo FROM roles WHERE tenant_id = :tid AND deleted_at IS NULL"
        ),
        {"tid": tenant_id},
    ).fetchall()
    rol_by_codigo: dict[str, uuid.UUID] = {r.codigo: r.id for r in rol_rows}

    # 4. Insertar las nuevas asignaciones rol↔permiso (idempotente)
    rp_rows = []
    for rol_codigo, permisos_codigos in _NEW_ROLE_PERMISOS.items():
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
                ON CONFLICT (rol_id, permiso_id) DO NOTHING
                """
            ),
            rp_rows,
        )


def upgrade() -> None:
    conn = op.get_bind()
    tenant_ids = conn.execute(sa.text("SELECT id FROM tenants")).fetchall()
    for row in tenant_ids:
        _patch_tenant(conn, row.id)


def downgrade() -> None:
    conn = op.get_bind()
    codigos = [c for c, _ in _NEW_PERMISOS] + ["tareas:gestionar"]
    conn.execute(
        sa.text(
            """
            DELETE FROM rol_permisos
            WHERE permiso_id IN (
                SELECT id FROM permisos WHERE codigo = ANY(:codigos)
                AND codigo IN ('evaluaciones:gestionar','evaluaciones:resultado',
                               'calificaciones:umbral')
            )
            """
        ),
        {"codigos": codigos},
    )
    conn.execute(
        sa.text(
            """
            DELETE FROM permisos
            WHERE codigo IN ('evaluaciones:gestionar','evaluaciones:resultado',
                             'calificaciones:umbral')
            """
        )
    )
