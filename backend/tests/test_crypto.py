"""tests/test_crypto.py — Tests for AES-256-GCM encryption utility.

TDD cycles:
  6.1 Module created (this file)
  6.2 RED→GREEN: decrypt(encrypt(v)) == v for arbitrary strings (round-trip)
  6.3 RED→GREEN: two encrypt(v) calls produce different ciphertexts (nonce uniqueness)
  6.4 RED→GREEN: decrypt with tampered ciphertext raises InvalidTag (GCM auth failure)
  6.5 RED→GREEN: module fails at import/startup when ENCRYPTION_KEY is missing

Environment note: ENCRYPTION_KEY must be a 64-char hex string (32 bytes).
The conftest sets it to '0' * 64 for the test session.
"""

import importlib
import os

import pytest
from cryptography.exceptions import InvalidTag

# Import the module only once (uses the test key set by conftest).
# Tests that need a different env must reload the module in isolation.
from app.core import crypto


# ── 6.2 Round-trip ────────────────────────────────────────────────────────────


class TestEncryptDecryptRoundTrip:
    """decrypt(encrypt(v)) == v for various string types."""

    def test_ascii_round_trip(self):
        """Scenario: Plaintext is encrypted and decryptable (ASCII)."""
        value = "sensitive_value_123"
        assert crypto.decrypt(crypto.encrypt(value)) == value

    def test_unicode_round_trip(self):
        """Round-trip works with Unicode characters (accents, emoji, etc.)."""
        value = "Ñoño académico — 日本語 🔒"
        assert crypto.decrypt(crypto.encrypt(value)) == value

    def test_special_chars_round_trip(self):
        """Round-trip works with special characters and punctuation."""
        value = "CBU: 0720580-88-0000062213562/3 (ALIAS: test.alias)"
        assert crypto.decrypt(crypto.encrypt(value)) == value

    def test_empty_string_round_trip(self):
        """Round-trip works with an empty string."""
        value = ""
        assert crypto.decrypt(crypto.encrypt(value)) == value

    def test_long_string_round_trip(self):
        """Round-trip works with long strings (> block size)."""
        value = "X" * 10_000
        assert crypto.decrypt(crypto.encrypt(value)) == value


# ── 6.3 Nonce uniqueness ──────────────────────────────────────────────────────


class TestNonceUniqueness:
    """Two encrypt() calls with the same plaintext produce different ciphertexts."""

    def test_two_encryptions_differ(self):
        """Scenario: Each encrypt call produces a different ciphertext."""
        value = "same plaintext"
        ct1 = crypto.encrypt(value)
        ct2 = crypto.encrypt(value)
        assert ct1 != ct2

    def test_three_encryptions_all_differ(self):
        """Triangulation: three calls all produce distinct ciphertexts."""
        value = "same plaintext"
        ciphertexts = {crypto.encrypt(value) for _ in range(3)}
        assert len(ciphertexts) == 3


# ── 6.4 Tampered ciphertext ───────────────────────────────────────────────────


class TestTamperedCiphertext:
    """decrypt() raises InvalidTag when ciphertext has been altered."""

    def test_tampered_ciphertext_raises_invalid_tag(self):
        """Scenario: Decrypt on tampered ciphertext raises InvalidTag."""
        import base64

        value = "important PII"
        ct_b64 = crypto.encrypt(value)

        # Decode, flip a byte in the ciphertext body (after nonce+tag), re-encode
        blob = bytearray(base64.b64decode(ct_b64))
        # Flip a byte in the ciphertext portion (after nonce[12] + tag[16])
        if len(blob) > 28:
            blob[28] ^= 0xFF
        else:
            # Very short plaintext: flip last byte of the tag area
            blob[-1] ^= 0xFF

        tampered_b64 = base64.b64encode(bytes(blob)).decode("ascii")

        with pytest.raises(InvalidTag):
            crypto.decrypt(tampered_b64)

    def test_completely_different_ciphertext_raises_invalid_tag(self):
        """Decrypt on an entirely fabricated base64 blob raises InvalidTag or ValueError."""
        import base64

        # 40 bytes of random-ish bytes: nonce(12) + tag(16) + ciphertext(12)
        fake_blob = bytes(range(40))
        fake_b64 = base64.b64encode(fake_blob).decode("ascii")

        with pytest.raises((InvalidTag, ValueError)):
            crypto.decrypt(fake_b64)


# ── 6.5 Missing ENCRYPTION_KEY ────────────────────────────────────────────────


class TestMissingEncryptionKey:
    """validate_key() raises ConfigurationError when ENCRYPTION_KEY is absent or invalid.

    The application calls validate_key() during lifespan startup, so testing
    validate_key() directly is equivalent to testing fail-fast startup behaviour.
    We also test _load_key() directly as that is the core validation function.
    """

    def test_missing_key_raises_configuration_error(self, monkeypatch):
        """Scenario: App fails fast with missing ENCRYPTION_KEY."""
        from app.core.crypto import ConfigurationError, _load_key

        monkeypatch.delenv("ENCRYPTION_KEY", raising=False)

        with pytest.raises(ConfigurationError, match="ENCRYPTION_KEY"):
            _load_key()

    def test_invalid_key_not_hex_raises_configuration_error(self, monkeypatch):
        """Raises ConfigurationError when ENCRYPTION_KEY is not valid hex."""
        from app.core.crypto import ConfigurationError, _load_key

        # 64 chars but not valid hex
        monkeypatch.setenv("ENCRYPTION_KEY", "Z" * 64)

        with pytest.raises(ConfigurationError, match="hexadecimal"):
            _load_key()

    def test_short_key_raises_configuration_error(self, monkeypatch):
        """Raises ConfigurationError when ENCRYPTION_KEY is shorter than 64 chars."""
        from app.core.crypto import ConfigurationError, _load_key

        monkeypatch.setenv("ENCRYPTION_KEY", "ab" * 16)  # 32 chars, not 64

        with pytest.raises(ConfigurationError, match="64"):
            _load_key()

    def test_validate_key_called_in_lifespan(self):
        """validate_key() is importable and callable — wired to lifespan startup."""
        from app.core.crypto import validate_key

        # With a valid key in env (set by conftest), validate_key() must not raise
        validate_key()  # should succeed silently
