## ADDED Requirements

### Requirement: AES-256-GCM encryption utility for PII at rest
The system SHALL provide a `crypto` module (`backend/app/core/crypto.py`) that exposes `encrypt(plaintext: str) -> str` and `decrypt(ciphertext: str) -> str` using AES-256-GCM. The encryption key SHALL be loaded from the `ENCRYPTION_KEY` environment variable (64 hex characters = 32 bytes). If `ENCRYPTION_KEY` is absent or invalid, the application SHALL refuse to start.

#### Scenario: Plaintext is encrypted and decryptable
- **WHEN** `encrypt("sensitive_value")` is called
- **THEN** the result is a non-empty string different from the input, and `decrypt(result)` returns `"sensitive_value"`

#### Scenario: Each encrypt call produces a different ciphertext (nonce uniqueness)
- **WHEN** `encrypt` is called twice with the same plaintext
- **THEN** the two ciphertext strings are different (probabilistically guaranteed by random nonce)

---

### Requirement: Ciphertext format is self-contained
The ciphertext SHALL be a base64-encoded blob containing the nonce, authentication tag, and ciphertext in a single field, suitable for storage in a single database text column.

#### Scenario: Ciphertext is a valid base64 string
- **WHEN** `encrypt` is called
- **THEN** the result can be base64-decoded and its length is nonce_len + tag_len + plaintext_len bytes

---

### Requirement: PII fields are never stored in plaintext
Fields marked `[cifrado]` in the data model (DNI, CUIL, CBU, alias_cbu, email PII) SHALL always be passed through `encrypt` before persistence and `decrypt` after retrieval. These values SHALL never appear in logs, error messages, or debug output.

#### Scenario: Decrypt on tampered ciphertext raises an error
- **WHEN** `decrypt` is called with a ciphertext that has been altered
- **THEN** an `InvalidTag` or equivalent integrity error is raised (GCM authentication failure)

---

### Requirement: Missing or malformed ENCRYPTION_KEY prevents startup
If `ENCRYPTION_KEY` is not set or is not a valid 64-character hex string, the crypto module SHALL raise a configuration error at import time (or at `lifespan` startup), preventing the application from serving requests.

#### Scenario: App fails fast with missing ENCRYPTION_KEY
- **WHEN** the application starts without `ENCRYPTION_KEY` in the environment
- **THEN** a `ConfigurationError` (or equivalent) is raised before the first request is handled
