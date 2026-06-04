"""repositories/rol.py — RolRepository (C-04: RBAC)."""

from app.models.rol import Rol
from app.repositories.base import BaseRepository


class RolRepository(BaseRepository[Rol]):
    """Tenant-scoped repository for Rol."""

    def __init__(self, session, tenant_id):
        super().__init__(session, tenant_id, Rol)

    async def get_by_codigo(self, codigo: str) -> Rol | None:
        """Return the active Rol with the given codigo in this tenant."""
        results = await self.list(codigo=codigo)
        return results[0] if results else None
