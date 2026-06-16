## ADDED Requirements

### Requirement: Login with email and password issues JWT session
The system SHALL authenticate users via `POST /api/auth/login` accepting `email` and `password`. On success (and no 2FA active), it SHALL return an access token (JWT, 15-minute expiry) and a refresh token (long-lived, configurable). The JWT SHALL contain claims: `sub` (user_id), `tenant_id`, `roles`, `exp`, `iat`, `jti`. Identity and tenant SHALL be derived exclusively from the verified JWT — never from request parameters.

#### Scenario: Successful login without 2FA
- **WHEN** a valid email and password are submitted for an active user with 2FA disabled
- **THEN** the response is HTTP 200 with `access_token`, `refresh_token`, and `token_type: "bearer"`

#### Scenario: Login with wrong password returns 401
- **WHEN** a valid email is submitted with an incorrect password
- **THEN** the response is HTTP 401 with no session tokens issued

#### Scenario: Login with non-existent email returns 401
- **WHEN** an email that does not exist in the tenant is submitted
- **THEN** the response is HTTP 401 (same error as wrong password — no user enumeration)

#### Scenario: Login for inactive user returns 401
- **WHEN** a valid email and password are submitted for a user with `activo=False`
- **THEN** the response is HTTP 401

---

### Requirement: Login with 2FA active returns a challenge token
When a user has TOTP 2FA enabled, login SHALL NOT issue a full session on password validation alone. Instead it SHALL return HTTP 202 with a short-lived `challenge_token` (5-minute JWT with `type: "2fa_challenge"`).

#### Scenario: Login with 2FA active returns challenge
- **WHEN** valid credentials are submitted for a user with `totp_activo=True`
- **THEN** the response is HTTP 202 with a `challenge_token` and no `access_token` or `refresh_token`

#### Scenario: Challenge token cannot access protected endpoints
- **WHEN** the `challenge_token` is used as a Bearer token on a protected endpoint
- **THEN** the response is HTTP 401

---

### Requirement: 2FA verification completes the session
`POST /api/auth/2fa/verify` SHALL accept a `challenge_token` and a TOTP `code`. If both are valid, it SHALL issue the full session (access + refresh tokens).

#### Scenario: Valid TOTP code after challenge completes login
- **WHEN** a valid `challenge_token` and a correct TOTP code are submitted
- **THEN** the response is HTTP 200 with `access_token` and `refresh_token`

#### Scenario: Invalid TOTP code returns 401
- **WHEN** a valid `challenge_token` and an incorrect TOTP code are submitted
- **THEN** the response is HTTP 401 with no session issued

#### Scenario: Expired challenge token returns 401
- **WHEN** a `challenge_token` past its expiry is submitted
- **THEN** the response is HTTP 401

---

### Requirement: Refresh token rotation issues a new session pair
`POST /api/auth/refresh` SHALL accept a valid refresh token and return a new `access_token` + `refresh_token`, invalidating the submitted refresh token immediately (rotation).

#### Scenario: Valid refresh token returns new pair
- **WHEN** a valid, non-revoked refresh token is submitted
- **THEN** the response is HTTP 200 with a new `access_token` and a new `refresh_token`; the old refresh token is revoked

#### Scenario: Reused refresh token forces logout
- **WHEN** a refresh token that has already been used is submitted again
- **THEN** the response is HTTP 401 and ALL active sessions for that user are revoked

#### Scenario: Expired refresh token returns 401
- **WHEN** an expired refresh token is submitted
- **THEN** the response is HTTP 401

---

### Requirement: Logout revokes the active session
`POST /api/auth/logout` SHALL revoke the current refresh token. Subsequent use of that refresh token SHALL return 401.

#### Scenario: Logout invalidates the refresh token
- **WHEN** a user calls logout with a valid session
- **THEN** the refresh token is revoked and cannot be used again

---

### Requirement: get_current_user dependency resolves identity from JWT
A FastAPI dependency `get_current_user` SHALL verify the Bearer JWT on every protected request and return the authenticated user with `user_id`, `tenant_id`, and `roles`. It SHALL reject expired, malformed, or invalidated tokens with HTTP 401.

#### Scenario: Valid token resolves user identity
- **WHEN** a request with a valid Bearer access token is made
- **THEN** `get_current_user` returns the user object with correct `user_id` and `tenant_id`

#### Scenario: Expired or invalid token returns 401
- **WHEN** a request with an expired or tampered access token is made
- **THEN** `get_current_user` raises HTTP 401

---

### Requirement: Rate limiting on login endpoint
The login endpoint SHALL enforce a limit of 5 failed attempts per `(IP, email)` pair within a 60-second sliding window. On exceeding the limit it SHALL return HTTP 429.

#### Scenario: Sixth failed attempt within 60 seconds returns 429
- **WHEN** 5 consecutive failed login attempts are made from the same IP for the same email within 60 seconds, and a 6th attempt is made
- **THEN** the response is HTTP 429

#### Scenario: Successful login resets the rate limit counter
- **WHEN** a successful login occurs after prior failed attempts
- **THEN** the counter for that `(IP, email)` pair is reset

---

### Requirement: 2FA TOTP enrollment
`POST /api/auth/2fa/enroll` (authenticated) SHALL generate a TOTP secret and return the `otpauth://` URI and a base32 secret for QR display. `POST /api/auth/2fa/confirm` SHALL verify the first TOTP code and activate 2FA on the user account.

#### Scenario: Enrollment returns a valid TOTP URI
- **WHEN** an authenticated user calls enroll
- **THEN** the response contains a valid `otpauth://totp/...` URI and a base32 `secret`

#### Scenario: Confirm with valid code activates 2FA
- **WHEN** a valid TOTP code is submitted to confirm enrollment
- **THEN** `totp_activo` is set to True on the user and subsequent logins require 2FA

#### Scenario: Confirm with invalid code returns 400
- **WHEN** an incorrect TOTP code is submitted to confirm enrollment
- **THEN** the response is HTTP 400 and `totp_activo` remains False

---

### Requirement: Password recovery with single-use token
`POST /api/auth/forgot` SHALL accept an email and generate a single-use recovery token (32 random bytes, 15-minute expiry). In dev/test the token SHALL be returned in the response; in production it SHALL be sent by email (or logged if SMTP is not configured). `POST /api/auth/reset` SHALL accept the token and a new password, consume the token, and update the password hash.

#### Scenario: Forgot with valid email generates token
- **WHEN** a registered email is submitted to /forgot
- **THEN** the response is HTTP 200 and a single-use reset token is generated (returned in dev mode)

#### Scenario: Forgot with unknown email returns 200 (no enumeration)
- **WHEN** an unregistered email is submitted to /forgot
- **THEN** the response is HTTP 200 with no indication of whether the email exists

#### Scenario: Reset with valid token updates password
- **WHEN** a valid, non-expired reset token and a new password are submitted
- **THEN** the password is updated and the token is consumed (cannot be reused)

#### Scenario: Reset with expired or used token returns 400
- **WHEN** an expired or already-used reset token is submitted
- **THEN** the response is HTTP 400

---

### Requirement: Password stored with Argon2id
All passwords SHALL be hashed with Argon2id before persistence. Plaintext passwords SHALL never be stored or logged.

#### Scenario: Password hash is Argon2id format
- **WHEN** a user is created or their password is updated
- **THEN** `password_hash` in the database starts with `$argon2id$`

#### Scenario: Correct password verifies successfully
- **WHEN** `verify_password(plaintext, hash)` is called with matching values
- **THEN** the result is True

#### Scenario: Wrong password fails verification
- **WHEN** `verify_password(plaintext, hash)` is called with a non-matching password
- **THEN** the result is False
