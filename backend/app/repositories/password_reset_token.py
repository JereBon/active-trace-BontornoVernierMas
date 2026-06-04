"""repositories/password_reset_token.py — Single-use password recovery token repo (C-03)."""

import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update

from app.models.password_reset_token import PasswordResetToken


class PasswordResetTokenRepository:
    """Repository for single-use password recovery tokens.

    Methods:
        create(usuario_id, token_hash, expires_at) -> PasswordResetToken
        get_valid_by_hash(token_hash)              -> PasswordResetToken | None
        mark_used(token_id)                        -> None
    """

    def __init__(self, session) -> None:
        self._session = session

    @staticmethod
    def hash_token(raw_token: str) -> str:
        """Return SHA-256 hex of the raw token string."""
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    async def create(
        self,
        usuario_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> PasswordResetToken:
        """Persist a new password reset token hash."""
        token = PasswordResetToken(
            id=uuid.uuid4(),
            usuario_id=usuario_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._session.add(token)
        await self._session.flush()
        await self._session.refresh(token)
        return token

    async def get_valid_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        """Return a valid (non-expired, non-used) token matching the hash.

        Returns None if not found, already used, or expired.
        """
        now = datetime.now(tz=timezone.utc)
        stmt = (
            select(PasswordResetToken)
            .where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > now,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_used(self, token_id: uuid.UUID) -> None:
        """Consume a token — subsequent lookups via get_valid_by_hash will return None."""
        stmt = (
            update(PasswordResetToken)
            .where(PasswordResetToken.id == token_id)
            .values(used_at=datetime.now(tz=timezone.utc))
        )
        await self._session.execute(stmt)
