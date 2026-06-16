"""repositories/refresh_token.py — RefreshToken repository (C-03).

RefreshToken does NOT use TenantScopedMixin — it links to a usuario (which
carries tenant_id).  This repository operates at the session level without
tenant scoping in the constructor (tenant filtering is done only where needed).
"""

import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    """Repository for refresh token lifecycle management.

    Constructor:
        session — open AsyncSession

    Methods:
        create(usuario_id, tenant_id, token_hash, expires_at) -> RefreshToken
        get_by_hash(token_hash)              -> RefreshToken | None
        revoke(token_id)                     -> None
        revoke_all_for_user(usuario_id)      -> None
    """

    def __init__(self, session) -> None:
        self._session = session

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def hash_token(raw_token: str) -> str:
        """Return SHA-256 hex of the raw token string."""
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    # ── CRUD ──────────────────────────────────────────────────────────────────

    async def create(
        self,
        usuario_id: uuid.UUID,
        tenant_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        """Persist a new refresh token hash.

        Args:
            usuario_id:  Owner of this token.
            tenant_id:   Denormalized for audit / future cross-tenant queries.
            token_hash:  SHA-256 hash of the raw token value sent to the client.
            expires_at:  When the token expires (absolute UTC datetime).

        Returns:
            Persisted RefreshToken instance.
        """
        token = RefreshToken(
            id=uuid.uuid4(),
            usuario_id=usuario_id,
            tenant_id=tenant_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._session.add(token)
        await self._session.flush()
        await self._session.refresh(token)
        return token

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        """Return the RefreshToken matching the given hash, or None.

        No expiry / revocation check — callers must check token.revoked_at
        and token.expires_at to determine validity.
        """
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke(self, token_id: uuid.UUID) -> None:
        """Mark a single refresh token as revoked."""
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.id == token_id)
            .values(revoked_at=datetime.now(tz=timezone.utc))
        )
        await self._session.execute(stmt)

    async def revoke_all_for_user(self, usuario_id: uuid.UUID) -> None:
        """Revoke ALL active refresh tokens for a user (reuse-detection response).

        Called when a revoked token is presented again, indicating potential theft.
        """
        now = datetime.now(tz=timezone.utc)
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.usuario_id == usuario_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        await self._session.execute(stmt)
