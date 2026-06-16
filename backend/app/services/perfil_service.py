"""services/perfil_service.py — PerfilService (C-20: perfil-y-mensajeria-interna).

Handles reading and updating the calling user's own profile.
Identity always comes from the JWT (user_id param = from current_user).

Methods:
  obtener_perfil  — return calling user's decrypted profile
  actualizar_perfil — update editable fields; CUIL is immutable (raises ValueError)
"""

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.usuario import UsuarioRepository, decrypt_usuario
from app.schemas.perfil import PerfilUpdate


class PerfilService:
    """Service for own-profile read/update operations.

    The calling user can only read/update their own profile.
    Identity (user_id) is always sourced from the verified JWT by the router.
    """

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._repo = UsuarioRepository(session, tenant_id)

    async def obtener_perfil(self, user_id: uuid.UUID) -> dict[str, Any]:
        """Return the calling user's profile with decrypted PII.

        Raises:
            NotFoundError: if the user is not found (should never happen with valid JWT).
        """
        usuario = await self._repo.get(user_id)
        if usuario is None:
            raise NotFoundError(f"Usuario {user_id} not found")
        return decrypt_usuario(usuario)

    async def actualizar_perfil(
        self, user_id: uuid.UUID, data: PerfilUpdate
    ) -> dict[str, Any]:
        """Update editable profile fields.

        CUIL is read-only — cannot be changed via the profile endpoint.
        Raises:
            NotFoundError: if the user is not found.
        """
        # Only include fields that were explicitly provided (non-None)
        payload = {k: v for k, v in data.model_dump().items() if v is not None}

        usuario = await self._repo.update_pii(user_id, payload)
        if usuario is None:
            raise NotFoundError(f"Usuario {user_id} not found")
        return decrypt_usuario(usuario)
