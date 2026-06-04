"""repositories/usuario_rol.py — UsuarioRolRepository (C-04: RBAC).

Key method: get_permisos_efectivos(usuario_id) — joins usuario_roles →
rol_permisos → permisos filtering by vigencia (vig_hasta IS NULL OR
vig_hasta >= today).  Returns a set[str] of permission codes.
"""

import uuid
from datetime import date

from sqlalchemy import select, and_, or_

from app.models.usuario_rol import UsuarioRol
from app.models.rol_permiso import RolPermiso
from app.models.permiso import Permiso
from app.repositories.base import BaseRepository


class UsuarioRolRepository(BaseRepository[UsuarioRol]):
    """Tenant-scoped repository for UsuarioRol with permission resolution."""

    def __init__(self, session, tenant_id):
        super().__init__(session, tenant_id, UsuarioRol)

    async def get_permisos_efectivos(self, usuario_id: uuid.UUID) -> set[str]:
        """Return the set of effective permission codes for *usuario_id*.

        Effective = all permissions from all roles that are currently active
        (vig_desde <= today AND (vig_hasta IS NULL OR vig_hasta >= today)).

        Fail-closed: if the user has no active role assignments, returns an
        empty set — the caller/guard will deny access.
        """
        today = date.today()

        stmt = (
            select(Permiso.codigo)
            .join(RolPermiso, RolPermiso.permiso_id == Permiso.id)
            .join(UsuarioRol, UsuarioRol.rol_id == RolPermiso.rol_id)
            .where(
                UsuarioRol.usuario_id == usuario_id,
                UsuarioRol.tenant_id == self._tenant_id,
                UsuarioRol.deleted_at.is_(None),
                UsuarioRol.vig_desde <= today,
                or_(
                    UsuarioRol.vig_hasta.is_(None),
                    UsuarioRol.vig_hasta >= today,
                ),
                Permiso.tenant_id == self._tenant_id,
                Permiso.deleted_at.is_(None),
            )
            .distinct()
        )

        result = await self._session.execute(stmt)
        return set(result.scalars().all())
