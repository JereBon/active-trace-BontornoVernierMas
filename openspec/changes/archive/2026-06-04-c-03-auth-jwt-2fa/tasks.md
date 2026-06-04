## 1. Modelo Usuario (campos auth) y migración

- [x] 1.1 Crear `backend/app/models/usuario.py`: modelo `Usuario` heredando `Base` + `TenantScopedMixin`. Columnas: `email_cifrado` TEXT NOT NULL, `email_hash` VARCHAR(64) NOT NULL (SHA-256 lowercase, único por tenant), `password_hash` TEXT NOT NULL, `totp_secret_cifrado` TEXT nullable, `totp_activo` BOOL default False, `activo` BOOL default True
- [x] 1.2 Crear `backend/app/models/refresh_token.py`: modelo `RefreshToken` (no hereda mixin — no tiene tenant_id directo, usa FK a usuario). Columnas: `id` UUID PK, `usuario_id` UUID FK → usuarios, `tenant_id` UUID NOT NULL, `token_hash` VARCHAR(64) UNIQUE NOT NULL, `expires_at` DATETIME NOT NULL, `revoked_at` DATETIME nullable, `created_at` DATETIME
- [x] 1.3 Crear `backend/app/models/password_reset_token.py`: modelo `PasswordResetToken`. Columnas: `id` UUID PK, `usuario_id` UUID FK → usuarios, `token_hash` VARCHAR(64) UNIQUE NOT NULL, `expires_at` DATETIME NOT NULL, `used_at` DATETIME nullable, `created_at` DATETIME
- [x] 1.4 Registrar los tres modelos en `backend/app/models/__init__.py`
- [x] 1.5 Crear `backend/alembic/versions/0002_usuario_auth.py`: `upgrade()` crea tablas `usuarios`, `refresh_tokens`, `password_reset_tokens` con índices y FK. `downgrade()` hace DROP en orden inverso

## 2. Utilidades de seguridad (core/security.py)

- [x] 2.1 Crear `backend/app/core/security.py`: función `hash_password(plain: str) -> str` (Argon2id via `argon2-cffi`)
- [x] 2.2 Implementar `verify_password(plain: str, hashed: str) -> bool` (Argon2id verify)
- [x] 2.3 Implementar `create_access_token(data: dict, expires_delta: timedelta) -> str` (JWT HS256, `SECRET_KEY` desde config)
- [x] 2.4 Implementar `decode_access_token(token: str) -> dict` — verifica firma y expiración; lanza `AuthError` si inválido
- [x] 2.5 Implementar `email_hash(email: str) -> str` — SHA-256 del email en minúsculas para índice de búsqueda
- [x] 2.6 Agregar `SECRET_KEY` (str, min 32 chars) a `backend/app/core/config.py`; fail-fast si falta

## 3. Repository de Usuario

- [x] 3.1 Crear `backend/app/repositories/usuario.py`: `UsuarioRepository(BaseRepository[Usuario])` con método `get_by_email_hash(email_hash: str) -> Usuario | None`
- [x] 3.2 Implementar `create_usuario(data: dict) -> Usuario`: cifra email con `crypto.encrypt`, calcula `email_hash`, hashea password con `hash_password`, persiste

## 4. Repositories de tokens

- [x] 4.1 Crear `backend/app/repositories/refresh_token.py`: métodos `create`, `get_by_hash(token_hash: str) -> RefreshToken | None`, `revoke(token_id: UUID)`, `revoke_all_for_user(usuario_id: UUID)`
- [x] 4.2 Crear `backend/app/repositories/password_reset_token.py`: métodos `create`, `get_valid_by_hash(token_hash: str) -> PasswordResetToken | None`, `mark_used(token_id: UUID)`

## 5. Servicio de autenticación

- [x] 5.1 Crear `backend/app/services/auth.py`: `AuthService` con `login(email, password, ip) -> LoginResult`; aplica rate limiting, verifica credenciales, bifurca según `totp_activo`
- [x] 5.2 Implementar `verify_2fa(challenge_token: str, totp_code: str) -> SessionTokens`; valida claim `type: "2fa_challenge"`, verifica TOTP con `pyotp`
- [x] 5.3 Implementar `refresh_session(refresh_token: str) -> SessionTokens`; detecta reuso (→ revoca todas las sesiones), rota el token
- [x] 5.4 Implementar `logout(refresh_token: str)`: revoca el token activo
- [x] 5.5 Implementar `enroll_totp(usuario_id: UUID) -> TotpEnrollResult`: genera secret con `pyotp`, retorna `otpauth://` URI
- [x] 5.6 Implementar `confirm_totp(usuario_id: UUID, code: str) -> bool`: verifica el código y activa 2FA
- [x] 5.7 Implementar `forgot_password(email: str, dev_mode: bool) -> str | None`: genera token 32 bytes, persiste hash, retorna token en dev
- [x] 5.8 Implementar `reset_password(token: str, new_password: str)`: consume el token, actualiza `password_hash`

## 6. Rate limiting

- [x] 6.1 Implementar `backend/app/core/rate_limit.py`: `RateLimiter` con sliding window en memoria, método `check(key: str, limit: int, window_seconds: int) -> bool`; lanza `TooManyRequestsError` al exceder

## 7. Dependency get_current_user

- [x] 7.1 Crear `backend/app/core/deps.py`: dependency `get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = ...) -> Usuario`; decodifica JWT, verifica que el usuario existe y está activo; lanza HTTP 401 si falla

## 8. Router de autenticación

- [x] 8.1 Crear `backend/app/routers/auth.py` con endpoints:
  - `POST /api/auth/login` → `LoginRequest` → `LoginResponse | ChallengeResponse`
  - `POST /api/auth/2fa/verify` → `TwoFAVerifyRequest` → `SessionResponse`
  - `POST /api/auth/refresh` → `RefreshRequest` → `SessionResponse`
  - `POST /api/auth/logout` → `LogoutRequest` → 204
  - `POST /api/auth/2fa/enroll` → (auth required) → `TotpEnrollResponse`
  - `POST /api/auth/2fa/confirm` → (auth required) → `TotpConfirmResponse`
  - `POST /api/auth/forgot` → `ForgotRequest` → 200
  - `POST /api/auth/reset` → `ResetRequest` → 200
- [x] 8.2 Todos los schemas Pydantic con `extra='forbid'`; ningún endpoint recibe `tenant_id` como parámetro (se resuelve del JWT o de la lógica interna)
- [x] 8.3 Registrar el router en `backend/app/main.py`

## 9. Tests — autenticación (TDD estricto)

- [x] 9.1 Crear `backend/tests/test_auth.py` con fixtures: tenant de test, usuario activo, usuario inactivo, usuario con 2FA
- [x] 9.2 Test RED→GREEN: login OK sin 2FA → HTTP 200 + tokens
- [x] 9.3 Test RED→GREEN: login con password incorrecto → HTTP 401
- [x] 9.4 Test RED→GREEN: login usuario inactivo → HTTP 401
- [x] 9.5 Test RED→GREEN: login con 2FA activo → HTTP 202 + challenge_token (sin access_token)
- [x] 9.6 Test RED→GREEN: `2fa/verify` con código correcto → HTTP 200 + sesión completa
- [x] 9.7 Test RED→GREEN: `2fa/verify` con código incorrecto → HTTP 401
- [x] 9.8 Test RED→GREEN: refresh rotation — primer refresh OK, segundo refresh con el mismo token → HTTP 401 + todas las sesiones revocadas
- [x] 9.9 Test RED→GREEN: logout revoca el refresh token
- [x] 9.10 Test RED→GREEN: `get_current_user` con token válido → usuario correcto; con token expirado → HTTP 401
- [x] 9.11 Test RED→GREEN: rate limiting — 5 fallos seguidos del mismo (IP, email) → 6to intento HTTP 429
- [x] 9.12 Triangulación: `forgot` + `reset` — token válido actualiza password; token reusado → HTTP 400
- [x] 9.13 Test RED→GREEN: `hash_password` produce hash Argon2id; `verify_password` OK/KO

## 10. Verificación final

- [x] 10.1 Correr `pytest backend/tests/` — todos los tests pasan
- [x] 10.2 Verificar `alembic upgrade head` y `alembic downgrade -1` en DB efímera
- [x] 10.3 Revisar que ningún archivo supera 500 LOC; `routers/auth.py` y `services/auth.py` bajo control
