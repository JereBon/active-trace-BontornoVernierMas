"""Add missing facturas permissions to ADMIN/PROFESOR/TUTOR roles (C-24 fix).

Revision ID: 0018
Revises: 0017
Create Date: 2026-06-19

The permission facturas:subir_propias was never seeded because it was added
to the catalogue after 0003_rbac.py had already run. Additionally, the ADMIN
role was missing facturas:gestionar and facturas:subir_propias.

This migration:
  1. Creates facturas:subir_propias permission for all tenants (if missing).
  2. Assigns facturas:gestionar + facturas:subir_propias to ADMIN.
  3. Assigns facturas:subir_propias to PROFESOR and TUTOR (per original matrix).
"""

from typing import Sequence, Union

import uuid

import sqlalchemy as sa
from alembic import op

revision: str = "0018"
down_revision: Union[str, tuple[str, ...], None] = "0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_PERMISOS_A_CREAR: list[tuple[str, str]] = [
    ("facturas:subir_propias", "Subir y ver mis propias facturas"),
]

_ROLES_PERMISOS: dict[str, list[str]] = {
    "ADMIN": ["facturas:gestionar", "facturas:subir_propias"],
    "PROFESOR": ["facturas:subir_propias"],
    "TUTOR": ["facturas:subir_propias"],
}


def _all_perm_codigos() -> set[str]:
    s: set[str] = set()
    for codes in _ROLES_PERMISOS.values():
        s.update(codes)
    return s


def upgrade() -> None:
    conn = op.get_bind()
    tenants = conn.execute(sa.text("SELECT id FROM tenants")).fetchall()
    all_codigos = _all_perm_codigos()

    for (tenant_id,) in tenants:
        # 1. Create missing permissions
        for codigo, desc in _PERMISOS_A_CREAR:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO permisos (id, tenant_id, codigo, descripcion,
                                          created_at, updated_at, deleted_at)
                    VALUES (:id, :tid, :codigo, :desc, now(), now(), NULL)
                    ON CONFLICT (tenant_id, codigo) DO NOTHING
                    """
                ),
                {"id": uuid.uuid4(), "tid": tenant_id, "codigo": codigo, "desc": desc},
            )

        # 2. Map codigo -> permiso_id
        permiso_rows = conn.execute(
            sa.text(
                """
                SELECT id, codigo FROM permisos
                WHERE tenant_id = :tid AND deleted_at IS NULL
                  AND codigo = ANY(:codigos)
                """
            ),
            {"tid": tenant_id, "codigos": list(all_codigos)},
        ).fetchall()
        permiso_by_codigo = {r.codigo: r.id for r in permiso_rows}

        # 3. Assign permissions to roles
        for rol_codigo, perm_codigos in _ROLES_PERMISOS.items():
            role = conn.execute(
                sa.text(
                    "SELECT id FROM roles WHERE tenant_id = :tid AND codigo = :rc AND deleted_at IS NULL"
                ),
                {"tid": tenant_id, "rc": rol_codigo},
            ).fetchone()
            if role is None:
                continue
            rol_id = role[0]

            for perm_codigo in perm_codigos:
                perm_id = permiso_by_codigo.get(perm_codigo)
                if perm_id is None:
                    continue
                conn.execute(
                    sa.text(
                        """
                        INSERT INTO rol_permisos (id, tenant_id, rol_id, permiso_id, created_at)
                        VALUES (:id, :tid, :rid, :pid, now())
                        ON CONFLICT (rol_id, permiso_id) DO NOTHING
                        """
                    ),
                    {
                        "id": uuid.uuid4(),
                        "tid": tenant_id,
                        "rid": rol_id,
                        "pid": perm_id,
                    },
                )


def downgrade() -> None:
    conn = op.get_bind()
    tenants = conn.execute(sa.text("SELECT id FROM tenants")).fetchall()
    all_codigos = _all_perm_codigos()

    for (tenant_id,) in tenants:
        # Get permiso ids
        permiso_rows = conn.execute(
            sa.text(
                """
                SELECT id, codigo FROM permisos
                WHERE tenant_id = :tid AND deleted_at IS NULL
                  AND codigo = ANY(:codigos)
                """
            ),
            {"tid": tenant_id, "codigos": list(all_codigos)},
        ).fetchall()

        for row in permiso_rows:
            # Remove from rol_permisos
            conn.execute(
                sa.text("DELETE FROM rol_permisos WHERE permiso_id = :pid"),
                {"pid": row.id},
            )

        # Delete permissions that were created by this migration
        for codigo, _ in _PERMISOS_A_CREAR:
            conn.execute(
                sa.text(
                    "DELETE FROM permisos WHERE tenant_id = :tid AND codigo = :codigo"
                ),
                {"tid": tenant_id, "codigo": codigo},
            )
