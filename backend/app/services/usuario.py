"""services/usuario.py — UsuarioService (C-07: usuarios-y-asignaciones).

Orchestrates UsuarioRepository. Never accesses DB directly.
All PII encryption/decryption is delegated to the repository.

Methods:
  crear_usuario        — create user + profile
  obtener_usuario      — get one user by id (with decrypted PII)
  actualizar_usuario   — update profile fields
  desactivar_usuario   — soft-disable (activo=False)
  listar_usuarios      — list all active users in tenant
  obtener_perfil_propio — get the current user's own profile (from JWT)
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.usuario import UsuarioRepository, decrypt_usuario
from app.schemas.usuario import UsuarioCreate, UsuarioOut, UsuarioUpdate


class UsuarioService:
    """Service layer for Usuario operations.

    Instantiated per-request with the active DB session and tenant context
    (always sourced from the verified JWT via the router dependency).
    """

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._repo = UsuarioRepository(session, tenant_id)

    async def crear_usuario(self, data: UsuarioCreate) -> dict[str, Any]:
        """Create a new usuario with optional PII profile.

        Returns a dict with decrypted PII suitable for UsuarioOut.
        """
        payload = data.model_dump()
        usuario = await self._repo.create_usuario_with_pii(payload)
        return decrypt_usuario(usuario)

    async def obtener_usuario(self, usuario_id: uuid.UUID) -> dict[str, Any]:
        """Get a single usuario by ID with decrypted PII.

        Raises:
            NotFoundError: if not found in this tenant.
        """
        usuario = await self._repo.get(usuario_id)
        if usuario is None:
            raise NotFoundError(f"Usuario {usuario_id} not found")
        return decrypt_usuario(usuario)

    async def actualizar_usuario(
        self, usuario_id: uuid.UUID, data: UsuarioUpdate
    ) -> dict[str, Any]:
        """Update a usuario's profile fields.

        Raises:
            NotFoundError: if not found in this tenant.
        """
        payload = {k: v for k, v in data.model_dump().items() if v is not None}
        usuario = await self._repo.update_pii(usuario_id, payload)
        if usuario is None:
            raise NotFoundError(f"Usuario {usuario_id} not found")
        return decrypt_usuario(usuario)

    async def desactivar_usuario(self, usuario_id: uuid.UUID) -> None:
        """Deactivate (soft-disable) a usuario.

        Raises:
            NotFoundError: if not found in this tenant.
        """
        found = await self._repo.deactivate(usuario_id)
        if not found:
            raise NotFoundError(f"Usuario {usuario_id} not found")

    async def listar_usuarios(self) -> list[dict[str, Any]]:
        """List all active usuarios in this tenant with decrypted PII."""
        usuarios = await self._repo.list()
        return [decrypt_usuario(u) for u in usuarios]

    async def obtener_perfil_propio(self, usuario_id: uuid.UUID) -> dict[str, Any]:
        """Get the calling user's own profile (identity always from JWT).

        Raises:
            NotFoundError: if the user is not found (should never happen with valid JWT).
        """
        usuario = await self._repo.get(usuario_id)
        if usuario is None:
            raise NotFoundError(f"Usuario {usuario_id} not found")
        return decrypt_usuario(usuario)
