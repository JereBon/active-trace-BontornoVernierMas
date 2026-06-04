"""repositories/usuario.py — UsuarioRepository (C-03 auth + C-07 PII profile).

Extends BaseRepository with:
  - email-hash-based lookup
  - create_usuario helper (encrypt email, hash password, encrypt PII)
  - create_usuario_with_pii: full profile creation with PII encryption
  - update_pii: update profile fields with PII encryption
  - deactivate: soft-disable (activo=False)
  - decrypt_usuario: helper to add plaintext PII fields to a dict from a model

All queries are scoped to tenant_id. PII fields ending in '_cifrado' are
encrypted with AES-256-GCM before persist and decrypted on read.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from app.core.crypto import decrypt, encrypt
from app.core.security import email_hash as compute_email_hash
from app.core.security import hash_password
from app.models.usuario import Usuario
from app.repositories.base import BaseRepository

# PII fields that require encryption at rest
_ENCRYPTED_FIELDS = {
    "dni": "dni_cifrado",
    "cuil": "cuil_cifrado",
    "cbu": "cbu_cifrado",
    "alias_cbu": "alias_cbu_cifrado",
}


def _encrypt_pii_fields(data: dict) -> dict:
    """Convert plaintext PII keys to encrypted column keys.

    Input keys: 'dni', 'cuil', 'cbu', 'alias_cbu'
    Output keys: 'dni_cifrado', 'cuil_cifrado', 'cbu_cifrado', 'alias_cbu_cifrado'

    None values are stored as None (no encryption needed).
    """
    result = {}
    for plain_key, cipher_key in _ENCRYPTED_FIELDS.items():
        if plain_key in data:
            val = data.pop(plain_key)
            result[cipher_key] = encrypt(val) if val is not None else None
    return result


def decrypt_usuario(usuario: Usuario) -> dict[str, Any]:
    """Return a dict of the usuario's fields with PII fields decrypted.

    The returned dict is suitable for building UsuarioOut in the service layer.
    """
    d: dict[str, Any] = {
        "id": usuario.id,
        "tenant_id": usuario.tenant_id,
        "nombre": usuario.nombre,
        "apellidos": usuario.apellidos,
        "banco": usuario.banco,
        "regional": usuario.regional,
        "legajo": usuario.legajo,
        "legajo_profesional": usuario.legajo_profesional,
        "facturador": usuario.facturador,
        "activo": usuario.activo,
        "created_at": usuario.created_at,
        "updated_at": usuario.updated_at,
    }
    def _safe_decrypt(ciphertext: str | None) -> str | None:
        """Decrypt or return None if the ciphertext is invalid/placeholder."""
        if not ciphertext:
            return None
        try:
            return decrypt(ciphertext)
        except (ValueError, Exception):
            return None  # Treat invalid/placeholder ciphertext as missing

    # Decrypt email
    d["email"] = _safe_decrypt(usuario.email_cifrado)
    # Decrypt PII fields
    d["dni"] = _safe_decrypt(usuario.dni_cifrado)
    d["cuil"] = _safe_decrypt(usuario.cuil_cifrado)
    d["cbu"] = _safe_decrypt(usuario.cbu_cifrado)
    d["alias_cbu"] = _safe_decrypt(usuario.alias_cbu_cifrado)
    return d


class UsuarioRepository(BaseRepository[Usuario]):
    """Tenant-scoped repository for Usuario (auth + PII profile).

    Constructor inherited from BaseRepository:
        session    — open AsyncSession
        tenant_id  — UUID from verified JWT
        model      — Usuario (passed automatically)
    """

    def __init__(self, session, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, Usuario)

    # ── Reads ─────────────────────────────────────────────────────────────────

    async def get_by_email_hash(self, email_hash: str) -> Usuario | None:
        """Return the active usuario matching the given email hash in this tenant."""
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

        Expected keys: 'email' (str), 'password' (str).
        Optional: 'activo' (bool), 'totp_activo' (bool).
        """
        plain_email: str = data.pop("email")
        plain_password: str = data.pop("password")

        data["email_cifrado"] = encrypt(plain_email)
        data["email_hash"] = compute_email_hash(plain_email)
        data["password_hash"] = hash_password(plain_password)

        return await self.create(data)

    async def create_usuario_with_pii(self, data: dict) -> Usuario:
        """Create a Usuario with full PII profile.

        Expected keys:
            email (str), password (str)
        Optional PII keys (all encrypted at rest):
            dni, cuil, cbu, alias_cbu
        Optional plaintext profile keys:
            nombre, apellidos, banco, regional, legajo, legajo_profesional, facturador
        """
        plain_email: str = data.pop("email")
        plain_password: str = data.pop("password")

        data["email_cifrado"] = encrypt(plain_email)
        data["email_hash"] = compute_email_hash(plain_email)
        data["password_hash"] = hash_password(plain_password)

        # Encrypt PII fields
        data.update(_encrypt_pii_fields(data))

        return await self.create(data)

    async def update_pii(self, usuario_id: uuid.UUID, data: dict) -> Usuario | None:
        """Update a Usuario's profile fields.

        Encrypts PII fields before calling BaseRepository.update().
        Returns None if the usuario is not found in this tenant.
        """
        data.update(_encrypt_pii_fields(data))
        return await self.update(usuario_id, data)

    async def deactivate(self, usuario_id: uuid.UUID) -> bool:
        """Deactivate (soft-disable) a Usuario by setting activo=False.

        Returns True if found and deactivated, False if not found.
        """
        instance = await self.get(usuario_id)
        if instance is None:
            return False
        instance.activo = False
        instance.updated_at = datetime.now(tz=timezone.utc)
        self._session.add(instance)
        await self._session.flush()
        return True
