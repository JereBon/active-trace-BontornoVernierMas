"""core/crypto.py — AES-256-GCM encryption utility for PII at rest.

Spec: C-02 specs/crypto/spec.md

Design decisions (D-04 in design.md):
- Key loaded from ENCRYPTION_KEY env var (64 hex chars = 32 bytes).
- Fail-fast at import time: if key is missing or invalid, raise ConfigurationError.
- Ciphertext format: base64(nonce || tag || ciphertext) — self-contained text blob.
- Nonce: 12 random bytes per call (GCM standard); unique per encryption → same
  plaintext encrypted twice produces different ciphertexts.
- GCM provides authenticated encryption: decrypt raises InvalidTag on tampering.

Usage:
    from app.core.crypto import encrypt, decrypt
    stored = encrypt("CBU sensitive value")
    original = decrypt(stored)
"""

import base64
import os

from cryptography.exceptions import InvalidTag  # noqa: F401 (re-exported for callers)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ── Constants ─────────────────────────────────────────────────────────────────

_NONCE_BYTES = 12  # 96-bit nonce, recommended for AES-GCM
_TAG_BYTES = 16    # 128-bit authentication tag (GCM default)


# ── Key loading (fail-fast on first use and during lifespan) ─────────────────


class ConfigurationError(Exception):
    """Raised when a required configuration value is absent or malformed."""


def _load_key() -> bytes:
    """Load and validate ENCRYPTION_KEY from the environment.

    Raises ConfigurationError if the key is absent or not a valid 64-char hex
    string (= 32 bytes).

    Called by validate_key() (lifespan startup) and lazily on first encrypt/
    decrypt call to ensure fail-fast behaviour without breaking test collection.
    """
    raw = os.environ.get("ENCRYPTION_KEY", "")
    if not raw:
        raise ConfigurationError(
            "ENCRYPTION_KEY environment variable is not set. "
            "The application cannot start without an encryption key."
        )
    if len(raw) != 64:
        raise ConfigurationError(
            f"ENCRYPTION_KEY must be exactly 64 hex characters (32 bytes for AES-256-GCM), "
            f"got {len(raw)} characters."
        )
    try:
        key_bytes = bytes.fromhex(raw)
    except ValueError as exc:
        raise ConfigurationError(
            "ENCRYPTION_KEY is not a valid hexadecimal string."
        ) from exc
    return key_bytes


def validate_key() -> None:
    """Validate and cache the encryption key.

    Call this from the application lifespan startup to ensure the app fails fast
    before handling any requests. Also invoked lazily on first encrypt/decrypt.

    Raises:
        ConfigurationError: if ENCRYPTION_KEY is absent or invalid.
    """
    global _KEY, _AESGCM
    _KEY = _load_key()
    _AESGCM = AESGCM(_KEY)


def _get_aesgcm() -> AESGCM:
    """Return the module-level AESGCM instance, initializing lazily if needed."""
    global _AESGCM
    if _AESGCM is None:
        validate_key()
    return _AESGCM  # type: ignore[return-value]


# Module-level variables — populated by validate_key() (lazily or at startup)
_KEY: bytes | None = None
_AESGCM: AESGCM | None = None


# ── Public API ────────────────────────────────────────────────────────────────


def encrypt(plaintext: str) -> str:
    """Encrypt a plaintext string using AES-256-GCM.

    Returns a base64-encoded string: base64(nonce || tag || ciphertext).
    Each call generates a unique 12-byte random nonce, so the same plaintext
    always produces a different ciphertext (semantic security).

    Args:
        plaintext: The string to encrypt (UTF-8 encoded internally).

    Returns:
        A base64url-safe string suitable for storage in a single DB text column.
    """
    nonce = os.urandom(_NONCE_BYTES)
    plaintext_bytes = plaintext.encode("utf-8")

    # AESGCM.encrypt returns ciphertext + 16-byte tag appended at the end
    ciphertext_with_tag = _get_aesgcm().encrypt(nonce, plaintext_bytes, associated_data=None)

    # Split: last TAG_BYTES are the GCM tag, rest is ciphertext
    ciphertext = ciphertext_with_tag[:-_TAG_BYTES]
    tag = ciphertext_with_tag[-_TAG_BYTES:]

    # Encode as: nonce || tag || ciphertext
    blob = nonce + tag + ciphertext
    return base64.b64encode(blob).decode("ascii")


def decrypt(ciphertext_b64: str) -> str:
    """Decrypt a ciphertext produced by encrypt().

    Args:
        ciphertext_b64: base64-encoded blob from encrypt().

    Returns:
        The original plaintext string.

    Raises:
        cryptography.exceptions.InvalidTag: If the ciphertext has been tampered
            with or the key is wrong (GCM authentication failure).
        ValueError: If the blob is too short to contain nonce + tag.
    """
    blob = base64.b64decode(ciphertext_b64.encode("ascii"))

    min_len = _NONCE_BYTES + _TAG_BYTES
    if len(blob) < min_len:
        raise ValueError(
            f"Ciphertext blob is too short: expected at least {min_len} bytes, "
            f"got {len(blob)}."
        )

    nonce = blob[:_NONCE_BYTES]
    tag = blob[_NONCE_BYTES: _NONCE_BYTES + _TAG_BYTES]
    ciphertext = blob[_NONCE_BYTES + _TAG_BYTES:]

    # Re-combine tag + ciphertext in the format AESGCM.decrypt expects
    # (cryptography library appends tag at end)
    plaintext_bytes = _get_aesgcm().decrypt(nonce, ciphertext + tag, associated_data=None)
    return plaintext_bytes.decode("utf-8")
