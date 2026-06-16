"""0019 — Fix NEXO y PROFESOR permisos (críticos).

CRÍTICO-1: PROFESOR no tenía tareas:gestionar (seed_dev.py incorrecto).
  → GET /v1/tareas devolvía 403 para PROFESOR (viola F8.1, F8.2).

CRÍTICO-2: NEXO tenía estructura:gestionar + usuarios:gestionar en lugar de
  avisos:confirmar (seed_dev.py incorrecto).
  → Privilegio excesivo: NEXO podía gestionar usuarios y estructura académica.
  → Le faltaba la única acción que le corresponde (confirmar avisos).

Revision ID: 0019
Revises: 0018
"""

from __future__ import annotations

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0019"
down_revision: Union[str, tuple[str, ...], None] = "0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ADD: dict[str, list[str]] = {
    "PROFESOR": ["tareas:gestionar"],
    "NEXO":     ["avisos:confirmar"],
}

_REMOVE: dict[str, list[str]] = {
    "NEXO": ["estructura:gestionar", "usuarios:gestionar"],
}


def _patch_tenant(conn: sa.engine.Connection, tenant_id: uuid.UUID) -> None:
    permiso_rows = conn.execute(
        sa.text("SELECT id, codigo FROM permisos WHERE tenant_id = :tid AND deleted_at IS NULL"),
        {"tid": tenant_id},
    ).fetchall()
    permiso_by_codigo: dict[str, uuid.UUID] = {r.codigo: r.id for r in permiso_rows}

    rol_rows = conn.execute(
        sa.text("SELECT id, codigo FROM roles WHERE tenant_id = :tid AND deleted_at IS NULL"),
        {"tid": tenant_id},
    ).fetchall()
    rol_by_codigo: dict[str, uuid.UUID] = {r.codigo: r.id for r in rol_rows}

    # Agregar permisos faltantes (idempotente)
    rows_to_add = []
    for rol_codigo, perm_codigos in _ADD.items():
        rol_id = rol_by_codigo.get(rol_codigo)
        if rol_id is None:
            continue
        for perm_codigo in perm_codigos:
            perm_id = permiso_by_codigo.get(perm_codigo)
            if perm_id is None:
                continue
            rows_to_add.append(
                {
                    "id": uuid.uuid4(),
                    "tenant_id": tenant_id,
                    "rol_id": rol_id,
                    "permiso_id": perm_id,
                }
            )

    if rows_to_add:
        conn.execute(
            sa.text(
                """
                INSERT INTO rol_permisos (id, tenant_id, rol_id, permiso_id, created_at)
                VALUES (:id, :tenant_id, :rol_id, :permiso_id, now())
                ON CONFLICT (rol_id, permiso_id) DO NOTHING
                """
            ),
            rows_to_add,
        )

    # Eliminar permisos indebidos
    for rol_codigo, perm_codigos in _REMOVE.items():
        rol_id = rol_by_codigo.get(rol_codigo)
        if rol_id is None:
            continue
        for perm_codigo in perm_codigos:
            perm_id = permiso_by_codigo.get(perm_codigo)
            if perm_id is None:
                continue
            conn.execute(
                sa.text(
                    "DELETE FROM rol_permisos WHERE rol_id = :rid AND permiso_id = :pid"
                ),
                {"rid": rol_id, "pid": perm_id},
            )


def upgrade() -> None:
    conn = op.get_bind()
    tenant_ids = conn.execute(sa.text("SELECT id FROM tenants")).fetchall()
    for row in tenant_ids:
        _patch_tenant(conn, row.id)


def downgrade() -> None:
    # Revierte a estado roto (solo útil para tests de rollback)
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            DELETE FROM rol_permisos rp
            USING roles r, permisos p
            WHERE rp.rol_id = r.id AND rp.permiso_id = p.id
              AND r.codigo = 'PROFESOR' AND p.codigo = 'tareas:gestionar'
            """
        )
    )
    conn.execute(
        sa.text(
            """
            DELETE FROM rol_permisos rp
            USING roles r, permisos p
            WHERE rp.rol_id = r.id AND rp.permiso_id = p.id
              AND r.codigo = 'NEXO' AND p.codigo = 'avisos:confirmar'
            """
        )
    )
