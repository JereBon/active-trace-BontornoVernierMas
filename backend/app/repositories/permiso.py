"""repositories/permiso.py — PermisoRepository (C-04: RBAC)."""

from app.models.permiso import Permiso
from app.repositories.base import BaseRepository


class PermisoRepository(BaseRepository[Permiso]):
    """Tenant-scoped repository for Permiso."""

    def __init__(self, session, tenant_id):
        super().__init__(session, tenant_id, Permiso)

    async def get_by_codigo(self, codigo: str) -> Permiso | None:
        """Return the active Permiso with the given codigo in this tenant."""
        results = await self.list(codigo=codigo)
        return results[0] if results else None
