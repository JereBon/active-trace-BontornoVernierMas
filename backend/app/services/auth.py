"""services/auth.py — Authentication service (C-03).

Orchestrates login, 2FA, session refresh, logout, TOTP enrollment, and
password recovery. All business logic lives here; routers delegate to this.

Design decisions:
  D-01: Refresh tokens stored as SHA-256 hashes in DB; plaintext sent to client.
  D-03: JWT claims: sub, tenant_id, roles, exp, iat, jti.
  D-04: Rate limiting via in-memory RateLimiter (sliding window 5/60s per ip:email).
  D-05: 2FA challenge token — short-lived JWT with type:"2fa_challenge".
  D-06: Password reset token — 32 random bytes, SHA-256 hash in DB, 15 min expiry.
"""

import os
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import timedelta, timezone, datetime

import pyotp
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import encrypt, decrypt
from app.core.exceptions import AuthError, AppError
from app.core.rate_limit import rate_limiter
from app.core.security import (
    create_access_token,
    decode_access_token,
    email_hash as compute_email_hash,
    hash_password,
    verify_password,
)
from app.repositories.password_reset_token import PasswordResetTokenRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.usuario import UsuarioRepository

# ── Constants ─────────────────────────────────────────────────────────────────

_ACCESS_TOKEN_EXPIRE = timedelta(minutes=15)
_REFRESH_TOKEN_EXPIRE = timedelta(days=7)
_CHALLENGE_TOKEN_EXPIRE = timedelta(minutes=5)
_RESET_TOKEN_EXPIRE = timedelta(minutes=15)
_LOGIN_RATE_LIMIT = 5
_LOGIN_RATE_WINDOW = 60  # seconds


# ── Result types ──────────────────────────────────────────────────────────────


@dataclass
class SessionTokens:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@dataclass
class LoginResult:
    """Result of a login attempt.

    If totp_required is True, challenge_token is set and session_tokens is None.
    """
    totp_required: bool = False
    challenge_token: str | None = None
    session_tokens: SessionTokens | None = None


@dataclass
class TotpEnrollResult:
    secret: str
    uri: str


# ── AuthService ───────────────────────────────────────────────────────────────


class AuthService:
    """Stateless service — all state lives in the DB and JWT payloads.

    Constructor:
        session    — open AsyncSession (injected from dependency)
        tenant_id  — UUID from the tenant context (for multi-tenant isolation)

    Note: for login (before we know the user's tenant), tenant_id can be any UUID
    if the lookup is done via email_hash across all active tenants.  In a
    single-tenant-per-request design, the tenant is resolved from the HTTP host
    header or a URL prefix BEFORE the service is instantiated.
    """

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._usuario_repo = UsuarioRepository(session, tenant_id)
        self._rt_repo = RefreshTokenRepository(session)
        self._prt_repo = PasswordResetTokenRepository(session)

    # ── Login ─────────────────────────────────────────────────────────────────

    async def login(self, email: str, password: str, ip: str) -> LoginResult:
        """Authenticate user by email + password.

        Applies rate limiting on failed attempts.  On success, resets the counter.

        Returns a LoginResult with:
          - session_tokens if no 2FA active
          - challenge_token (HTTP 202) if 2FA active

        Raises:
            AuthError: for invalid credentials, inactive user, or rate limit
                       (TooManyRequestsError is a subclass of AppError).
        """
        rate_key = f"{ip}:{email.lower()}"

        # Check rate limit BEFORE verifying credentials (fail fast)
        rate_limiter.check(rate_key, limit=_LOGIN_RATE_LIMIT, window_seconds=_LOGIN_RATE_WINDOW)

        eh = compute_email_hash(email)
        usuario = await self._usuario_repo.get_by_email_hash(eh)

        if usuario is None or not verify_password(password, usuario.password_hash):
            raise AuthError("Invalid credentials", code="invalid_credentials")

        if not usuario.activo:
            raise AuthError("User account is inactive", code="inactive_user")

        # Credentials OK — reset the failure counter
        rate_limiter.reset(rate_key)

        if usuario.totp_activo:
            # Issue a short-lived 2FA challenge token
            challenge = create_access_token(
                {
                    "sub": str(usuario.id),
                    "tenant_id": str(usuario.tenant_id),
                    "type": "2fa_challenge",
                },
                expires_delta=_CHALLENGE_TOKEN_EXPIRE,
            )
            return LoginResult(totp_required=True, challenge_token=challenge)

        tokens = await self._issue_session(usuario.id, usuario.tenant_id)
        return LoginResult(totp_required=False, session_tokens=tokens)

    # ── 2FA verify ────────────────────────────────────────────────────────────

    async def verify_2fa(self, challenge_token: str, totp_code: str) -> SessionTokens:
        """Complete login for a user with 2FA active.

        Args:
            challenge_token: Short-lived JWT with type:"2fa_challenge".
            totp_code:       6-digit TOTP from the authenticator app.

        Returns:
            SessionTokens (access + refresh).

        Raises:
            AuthError: invalid/expired challenge token, invalid TOTP code.
        """
        try:
            payload = decode_access_token(challenge_token)
        except AuthError:
            raise AuthError("Invalid or expired challenge token", code="invalid_token")

        if payload.get("type") != "2fa_challenge":
            raise AuthError("Token is not a 2FA challenge", code="invalid_token")

        usuario_id = uuid.UUID(payload["sub"])
        tenant_id = uuid.UUID(payload["tenant_id"])

        # Look up using the tenant_id from the JWT claim, not self._tenant_id
        from sqlalchemy import select
        from app.models.usuario import Usuario as _Usuario
        stmt = select(_Usuario).where(
            _Usuario.id == usuario_id,
            _Usuario.tenant_id == tenant_id,
            _Usuario.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        usuario = result.scalar_one_or_none()
        if usuario is None or not usuario.activo:
            raise AuthError("User not found or inactive", code="invalid_credentials")

        if not usuario.totp_secret_cifrado:
            raise AuthError("2FA not enrolled", code="totp_not_enrolled")

        secret = decrypt(usuario.totp_secret_cifrado)
        totp = pyotp.TOTP(secret)
        if not totp.verify(totp_code, valid_window=1):
            raise AuthError("Invalid TOTP code", code="invalid_totp")

        return await self._issue_session(usuario_id, tenant_id)

    # ── Refresh ───────────────────────────────────────────────────────────────

    async def refresh_session(self, refresh_token: str) -> SessionTokens:
        """Rotate a refresh token, issuing a new access + refresh pair.

        Detects reuse: if the token is already revoked → revoke ALL sessions.

        Raises:
            AuthError: expired, revoked, or not found token.
        """
        token_hash = RefreshTokenRepository.hash_token(refresh_token)
        db_token = await self._rt_repo.get_by_hash(token_hash)

        if db_token is None:
            raise AuthError("Invalid refresh token", code="invalid_token")

        # Reuse detection
        if db_token.revoked_at is not None:
            await self._rt_repo.revoke_all_for_user(db_token.usuario_id)
            await self._session.commit()
            raise AuthError("Refresh token reuse detected", code="token_reuse")

        if db_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(tz=timezone.utc):
            raise AuthError("Refresh token expired", code="token_expired")

        # Revoke the old token immediately (rotation)
        await self._rt_repo.revoke(db_token.id)

        return await self._issue_session(db_token.usuario_id, db_token.tenant_id)

    # ── Logout ────────────────────────────────────────────────────────────────

    async def logout(self, refresh_token: str) -> None:
        """Revoke the given refresh token.

        Silently succeeds even if the token is already revoked or not found
        (idempotent from the client's perspective).
        """
        token_hash = RefreshTokenRepository.hash_token(refresh_token)
        db_token = await self._rt_repo.get_by_hash(token_hash)
        if db_token and db_token.revoked_at is None:
            await self._rt_repo.revoke(db_token.id)

    # ── TOTP enrollment ───────────────────────────────────────────────────────

    async def enroll_totp(self, usuario_id: uuid.UUID) -> TotpEnrollResult:
        """Generate a TOTP secret for a user and return the otpauth:// URI.

        Does NOT activate 2FA yet — call confirm_totp() after verifying the
        first code.

        Args:
            usuario_id: ID of the authenticated user requesting enrollment.

        Returns:
            TotpEnrollResult with base32 secret and otpauth URI.

        Raises:
            AuthError: if the user is not found.
        """
        usuario = await self._usuario_repo.get(usuario_id)
        if usuario is None:
            raise AuthError("User not found", code="not_found")

        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)

        # Store encrypted secret (not yet active)
        await self._usuario_repo.update(
            usuario_id,
            {"totp_secret_cifrado": encrypt(secret), "totp_activo": False},
        )

        # Decrypt the stored email to build the URI label
        plain_email = decrypt(usuario.email_cifrado)
        uri = totp.provisioning_uri(name=plain_email, issuer_name="activia-trace")

        return TotpEnrollResult(secret=secret, uri=uri)

    async def confirm_totp(self, usuario_id: uuid.UUID, code: str) -> bool:
        """Verify the first TOTP code and activate 2FA on success.

        Args:
            usuario_id: Authenticated user's ID.
            code:       6-digit TOTP from the authenticator app.

        Returns:
            True if code is valid and 2FA is now active.

        Raises:
            AuthError: user not found or secret not generated yet.
        """
        usuario = await self._usuario_repo.get(usuario_id)
        if usuario is None:
            raise AuthError("User not found", code="not_found")

        if not usuario.totp_secret_cifrado:
            raise AuthError("TOTP not enrolled — call /2fa/enroll first", code="totp_not_enrolled")

        secret = decrypt(usuario.totp_secret_cifrado)
        totp = pyotp.TOTP(secret)

        if not totp.verify(code, valid_window=1):
            return False

        await self._usuario_repo.update(usuario_id, {"totp_activo": True})
        return True

    # ── Password recovery ─────────────────────────────────────────────────────

    async def forgot_password(self, email: str, dev_mode: bool = False) -> str | None:
        """Generate a single-use password reset token.

        To prevent user enumeration, always returns HTTP 200 regardless of
        whether the email exists.

        Args:
            email:    Email address submitted by the user.
            dev_mode: If True, returns the raw token in the response (for tests).
                      In production, the token would be sent by email.

        Returns:
            Raw token string in dev_mode, None otherwise.
        """
        eh = compute_email_hash(email)
        usuario = await self._usuario_repo.get_by_email_hash(eh)

        if usuario is None:
            return None

        raw_token = secrets.token_hex(32)  # 32 bytes = 64 hex chars
        token_hash = PasswordResetTokenRepository.hash_token(raw_token)
        expires_at = datetime.now(tz=timezone.utc) + _RESET_TOKEN_EXPIRE

        await self._prt_repo.create(
            usuario_id=usuario.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        if dev_mode:
            return raw_token

        # Production: log the token (SMTP email infrastructure is out of scope for C-03)
        import logging
        logging.getLogger(__name__).info(
            "Password reset token generated (no SMTP configured)",
            extra={"usuario_id": str(usuario.id)},
        )
        return None

    async def reset_password(self, token: str, new_password: str) -> None:
        """Consume a reset token and update the user's password.

        Args:
            token:        Raw token from the reset email / dev response.
            new_password: New plaintext password (will be hashed with Argon2id).

        Raises:
            AuthError (HTTP 400): token not found, expired, or already used.
        """
        token_hash = PasswordResetTokenRepository.hash_token(token)
        db_token = await self._prt_repo.get_valid_by_hash(token_hash)

        if db_token is None:
            raise AuthError("Invalid or expired reset token", code="invalid_reset_token")

        # Mark consumed BEFORE updating password — prevents race condition
        await self._prt_repo.mark_used(db_token.id)

        new_hash = hash_password(new_password)
        await self._usuario_repo.update(db_token.usuario_id, {"password_hash": new_hash})

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _issue_session(
        self,
        usuario_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> SessionTokens:
        """Create and persist a new access + refresh token pair."""
        from app.core.config import get_settings
        settings = get_settings()

        access_expire = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            {
                "sub": str(usuario_id),
                "tenant_id": str(tenant_id),
                "roles": [],  # populated in C-04
                "type": "access",
            },
            expires_delta=access_expire,
        )

        # Generate raw refresh token (not stored in DB)
        raw_refresh = secrets.token_hex(32)
        token_hash = RefreshTokenRepository.hash_token(raw_refresh)
        expires_at = datetime.now(tz=timezone.utc) + _REFRESH_TOKEN_EXPIRE

        await self._rt_repo.create(
            usuario_id=usuario_id,
            tenant_id=tenant_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        return SessionTokens(access_token=access_token, refresh_token=raw_refresh)
