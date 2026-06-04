"""core/security.py — Password hashing, JWT creation/verification, and email hashing (C-03).

Functions:
  hash_password(plain)          -> Argon2id hash string
  verify_password(plain, hash)  -> bool
  create_access_token(data, expires_delta) -> JWT string
  decode_access_token(token)    -> dict  (raises AuthError on invalid)
  email_hash(email)             -> SHA-256 hex string (lowercase)

Design decisions (C-03 design.md):
  D-02: email_hash uses SHA-256(email.lower()) for deterministic indexed lookup.
  D-03: JWT signed with HS256; claims: sub, tenant_id, roles, exp, iat, jti.
"""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from jose import JWTError, jwt

from app.core.exceptions import AuthError

# ── Argon2id configuration ────────────────────────────────────────────────────
# OWASP recommended minimum: time_cost=2, memory_cost=19456 (19 MiB), parallelism=1
_ph = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)

# ── JWT algorithm ─────────────────────────────────────────────────────────────
_ALGORITHM = "HS256"


# ── Password hashing ──────────────────────────────────────────────────────────


def hash_password(plain: str) -> str:
    """Return an Argon2id hash of the plaintext password.

    The returned string begins with `$argon2id$` and is self-contained
    (includes algorithm params and salt).

    Args:
        plain: The plaintext password. MUST NOT be logged or stored as-is.

    Returns:
        Argon2id hash string suitable for DB storage in password_hash column.
    """
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against an Argon2id hash.

    Args:
        plain:  Plaintext password from the login request.
        hashed: Stored Argon2id hash from the DB.

    Returns:
        True if password matches, False otherwise.
        NEVER raises — invalid hashes or mismatches return False.
    """
    try:
        return _ph.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


# ── JWT ───────────────────────────────────────────────────────────────────────


def create_access_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    """Create a signed JWT access token.

    Args:
        data:          Payload claims to include (will be shallow-copied).
        expires_delta: Lifetime of the token from now.

    Returns:
        Encoded JWT string (HS256).
    """
    from app.core.config import get_settings

    payload = dict(data)
    now = datetime.now(tz=timezone.utc)
    payload["iat"] = now
    payload["exp"] = now + expires_delta
    payload.setdefault("jti", str(uuid.uuid4()))

    settings = get_settings()
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT access token.

    Args:
        token: Raw JWT string from the Authorization header.

    Returns:
        Decoded payload dict.

    Raises:
        AuthError: If the token is expired, malformed, or has an invalid signature.
    """
    from app.core.config import get_settings

    settings = get_settings()
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[_ALGORITHM],
        )
        return payload
    except JWTError as exc:
        raise AuthError("Invalid or expired token", code="invalid_token") from exc


# ── Email hash ────────────────────────────────────────────────────────────────


def email_hash(email: str) -> str:
    """Compute the deterministic search index for an email address.

    The email is lowercased and then hashed with SHA-256.  The result is a
    64-character lowercase hex string, suitable for storage in the
    `email_hash` column.

    Args:
        email: Raw email string (any case).

    Returns:
        SHA-256 hex digest of email.lower().
    """
    return hashlib.sha256(email.lower().encode("utf-8")).hexdigest()
