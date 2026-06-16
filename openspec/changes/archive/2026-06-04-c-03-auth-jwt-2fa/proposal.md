## Why

C-02 estableció los cimientos de persistencia (Tenant, BaseRepository, crypto). Sin autenticación, ningún endpoint puede identificar quién hace la petición ni a qué tenant pertenece. C-03 introduce el sistema de autenticación completo: login con email + Argon2id, JWT access de vida corta con refresh rotation, 2FA TOTP opcional y recuperación de contraseña. Esta capa es prerequisito bloqueante para RBAC (C-04) y todo lo que sigue.

## What Changes

- `POST /api/auth/login` — valida email + password (Argon2id). Si 2FA está activo para el usuario, retorna un token temporal de desafío en vez de la sesión completa. Claims JWT mínimos: `sub` (user_id), `tenant_id`, `roles`, `exp`. Access token 15 min + refresh token con rotación (refresh usado → invalidado).
- `POST /api/auth/2fa/verify` — verifica el código TOTP y completa la emisión de sesión post-login con 2FA activo.
- `POST /api/auth/refresh` — rota el refresh token: invalida el usado, emite nuevo par access + refresh.
- `POST /api/auth/logout` — revoca la sesión (invalida el refresh token activo).
- `POST /api/auth/2fa/enroll` — genera el secret TOTP y el QR URI para enrolar 2FA en el perfil del usuario.
- `POST /api/auth/2fa/confirm` — confirma el enrolamiento TOTP verificando el primer código.
- `POST /api/auth/forgot` — genera token de recuperación de un solo uso, expiración corta, lo envía por email (o lo retorna en dev).
- `POST /api/auth/reset` — consume el token de recuperación y setea la nueva password.
- Dependency `get_current_user` inyectable en cualquier endpoint: verifica el JWT, resuelve `user_id`, `tenant_id` y `roles` — identidad SOLO desde el token, nunca desde parámetros.
- Rate limiting 5 intentos / 60 s por `(IP, email)` en el endpoint de login.
- Modelo `Usuario` básico (email, password_hash, 2fa_secret, 2fa_activo) necesario como tabla de identidad — solo los campos de auth; el resto del perfil va en C-07.
- Migración Alembic `0002_usuario_auth`.

## Capabilities

### New Capabilities

- `auth`: Endpoints de login, refresh, logout, 2FA enroll/verify, recuperación de contraseña, dependency `get_current_user`.

### Modified Capabilities

*(ninguna — primera implementación de auth)*

## Impact

- **Nuevo**: `backend/app/models/usuario.py` (campos de auth), migración `0002_usuario_auth`.
- **Nuevo**: `backend/app/core/security.py` (JWT sign/verify, Argon2id hash/verify).
- **Nuevo**: `backend/app/routers/auth.py`, `backend/app/services/auth.py`, `backend/app/repositories/usuario.py`.
- **Nuevo**: `backend/tests/test_auth.py`.
- **Modificado**: `backend/app/routers/__init__.py` y `backend/app/main.py` para registrar el router de auth.
- Todos los changes siguientes que requieran identidad de usuario dependen de `get_current_user` definido aquí.
