## Context

C-02 provee `BaseRepository`, `TenantScopedMixin`, `crypto.py` y la tabla `tenants`. Este change construye sobre eso la capa de autenticación completa. La tabla `usuarios` se crea con solo los campos necesarios para auth (email cifrado, password_hash, 2fa_secret cifrado, 2fa_activo); el perfil completo con PII va en C-07.

Constraints:
- Governance CRÍTICO: identidad SOLO del JWT verificado, nunca de parámetros de request.
- `SECRET_KEY` en env var (mínimo 32 chars) para firma JWT.
- Argon2id para password hashing (nunca bcrypt/MD5/SHA simple).
- Access token: 15 min. Refresh token: vida larga configurable (default 7 días), rotación en cada uso.
- 2FA TOTP opcional por usuario (no por tenant); RFC 6238 / Google Authenticator compatible.
- Rate limit en login: 5 intentos / 60 s por `(IP + email)`.
- Email de recuperación: en dev, retornar el token en la respuesta; en prod, enviar email (infraestructura de email fuera de scope de este change — el servicio loguea el token si no hay SMTP configurado).

## Goals / Non-Goals

**Goals:**
- Login completo con y sin 2FA, emitiendo par JWT access + refresh.
- Refresh rotation: un token usado se invalida de inmediato (reuso detectado → logout forzado).
- Logout que revoca la sesión.
- Enrolamiento y verificación TOTP.
- Recuperación de contraseña con token de un solo uso.
- `get_current_user` dependency reutilizable por todos los endpoints.
- Rate limiting en login.
- Modelo `Usuario` mínimo + migración Alembic `0002`.

**Non-Goals:**
- Perfil completo del usuario (nombre, PII, legajo) — C-07.
- RBAC y permisos finos — C-04.
- Impersonation — posterior.
- Moodle SSO — Fase 2 (ADR-001).
- Envío real de emails (SMTP) — infraestructura fuera de scope.

## Decisions

### D-01: Refresh tokens en tabla DB (no cookies, no Redis)
**Elegido**: Tabla `refresh_tokens` (`id`, `user_id`, `tenant_id`, `token_hash`, `expires_at`, `revoked_at`). El refresh token se almacena como hash SHA-256 en DB; el valor en claro se envía al cliente.
**Por qué**: Permite revocación individual y detección de reuso (si el token usado ya está en DB como usado → posible robo → logout forzado de todas las sesiones del usuario).
**Alternativa descartada**: Redis — dependencia extra no justificada para MVP.

### D-02: Tabla `usuarios` mínima en este change (solo campos auth)
**Elegido**: `usuarios(id UUID, tenant_id UUID, email_cifrado TEXT, password_hash TEXT, totp_secret_cifrado TEXT, totp_activo BOOL, activo BOOL, created_at, updated_at, deleted_at)`.
**Por qué**: Evita crear un modelo gigante ahora que C-07 completará el perfil. Email se almacena cifrado (AES-256-GCM de C-02) para proteger PII incluso en auth.
**Nota**: el email se busca comparando el valor cifrado; como el cifrado tiene nonce aleatorio, la búsqueda por email requiere descifrar en memoria o un índice hash determinístico. Se elige un índice de hash SHA-256(email_lower) en una columna `email_hash` para búsquedas eficientes sin exponer el email en texto plano.

### D-03: JWT firmado con HS256, claims mínimos
**Elegido**: `{"sub": str(user_id), "tenant_id": str(tenant_id), "roles": [...], "exp": unix_ts, "iat": unix_ts, "jti": uuid}`. Librería `python-jose` o `PyJWT`.
**Por qué**: Claims mínimos = surface de ataque mínima. `jti` permite invalidar tokens individuales si fuera necesario en el futuro.
**Permisos NO van en el token**: se resuelven server-side en cada request (C-04).

### D-04: Rate limiting en memoria con sliding window
**Elegido**: Dict en memoria (o `slowapi` + `limits`) con clave `f"{ip}:{email_lower}"`. 5 intentos / 60 s sliding window. En producción con múltiples workers, usar Redis — documentado como TODO pero no bloqueante para MVP single-worker.
**Alternativa descartada**: Rate limit solo por IP — fácil de evadir con muchos emails; solo por email — permite DDoS de una IP contra muchos emails.

### D-05: 2FA como gate entre credenciales y sesión
**Elegido**: Login con 2FA activo retorna HTTP 202 con un `challenge_token` de vida muy corta (5 min, firmado JWT con claim `type: "2fa_challenge"`). El cliente llama a `POST /2fa/verify` con el challenge_token + código TOTP para obtener la sesión real.
**Por qué**: Separa claramente el flujo 1FA del 2FA sin complicar el modelo de sesiones. El challenge_token no otorga acceso a ningún endpoint protegido.

### D-06: Recuperación de contraseña — token SHA-256 en tabla DB
**Elegido**: Tabla `password_reset_tokens` (`id`, `user_id`, `token_hash`, `expires_at`, `used_at`). Token de 32 bytes aleatorios, expiración 15 min. En dev/test: retornar el token en la respuesta JSON. En prod: loguear el token (SMTP se configura en futuro change).
**Por qué**: Token de un solo uso con hash en DB; el valor en claro nunca persiste.

## Risks / Trade-offs

- **[Riesgo] Rate limit en memoria no escala a múltiples workers** → Mitigación: documentar el TODO de Redis; para MVP con un worker es suficiente.
- **[Riesgo] Email cifrado con nonce aleatorio no es buscable por índice B-tree** → Mitigación: columna `email_hash` (SHA-256 del email en minúsculas) solo para lookup; el valor cifrado es el dato real almacenado.
- **[Trade-off] Refresh token en DB agrega una query por refresh** → Aceptable: el refresh ocurre raramente (cada 15 min o menos).
- **[Riesgo] Challenge token de 2FA puede ser phishing** → Mitigación: vida muy corta (5 min), no reutilizable, scope explícito en el claim.

## Migration Plan

1. Migración `0002_usuario_auth`: crea tablas `usuarios`, `refresh_tokens`, `password_reset_tokens`.
2. Reversible: `downgrade()` hace DROP de las tres tablas en orden inverso (FK constraints).
3. En producción: aplicar antes de levantar la nueva versión de la app.

## Open Questions

*(ninguna — el scope está completamente definido por ADR-001 y las reglas duras del proyecto)*
