"""repositories/usuario.py — UsuarioRepository for auth operations (C-03).

Extends BaseRepository with email-hash-based lookup and a create_usuario helper
that handles encryption and hashing automatically.
"""

import uuid

from sqlalchemy import select

from app.core.crypto import encrypt
from app.core.security import email_hash as compute_email_hash
from app.core.security import hash_password
from app.models.usuario import Usuario
from app.repositories.base import BaseRepository


class UsuarioRepository(BaseRepository[Usuario]):
    """Tenant-scoped repository for Usuario.

    Constructor inherited from BaseRepository:
        session    — open AsyncSession
        tenant_id  — UUID from verified JWT
        model      — Usuario (passed automatically)

    Additional methods beyond BaseRepository:
        get_by_email_hash(email_hash) -> Usuario | None
        create_usuario(data)          -> Usuario
    """

    def __init__(self, session, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, Usuario)

    # ── Reads ─────────────────────────────────────────────────────────────────

    async def get_by_email_hash(self, email_hash: str) -> Usuario | None:
        """Return the active usuario matching the given email hash in this tenant.

        Args:
            email_hash: SHA-256 hex of email.lower() (64 chars).

        Returns:
            Usuario instance if found and active, None otherwise.
        """
        stmt = (
            select(Usuario)
            .where(
                Usuario.tenant_id == self._tenant_id,
                Usuario.email_hash == email_hash,
                Usuario.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # ── Writes ────────────────────────────────────────────────────────────────

    async def create_usuario(self, data: dict) -> Usuario:
        """Create a new Usuario, encrypting email and hashing password.

        Expected keys in data:
            email    (str) — plaintext email; will be encrypted and hashed
            password (str) — plaintext password; will be hashed with Argon2id

        Optional keys:
            activo (bool, default True)
            totp_activo (bool, default False)

        The method:
          1. Derives email_cifrado  = crypto.encrypt(email)
          2. Derives email_hash     = SHA-256(email.lower())
          3. Derives password_hash  = hash_password(password)
          4. Calls BaseRepository.create() which sets tenant_id automatically

        Args:
            data: Dict with at minimum 'email' and 'password'.

        Returns:
            The persisted Usuario instance.
        """
        plain_email: str = data.pop("email")
        plain_password: str = data.pop("password")

        data["email_cifrado"] = encrypt(plain_email)
        data["email_hash"] = compute_email_hash(plain_email)
        data["password_hash"] = hash_password(plain_password)

        return await self.create(data)
