## 1. Modelo Tenant y mixin base

- [x] 1.1 Crear `backend/app/models/base.py`: `DeclarativeBase` única (`Base`) y `TenantScopedMixin` con columnas `id` (UUID PK, default `uuid4`), `tenant_id` (UUID, NOT NULL), `created_at` (datetime, `server_default=func.now()`), `updated_at` (datetime, `onupdate=func.now()`), `deleted_at` (datetime, nullable)
- [x] 1.2 Crear `backend/app/models/tenant.py`: modelo `Tenant` (hereda solo `Base`, NO el mixin — es la raíz) con `id` UUID PK, `slug` texto único, `nombre` texto, `activo` bool default True, `created_at`, `updated_at`
- [x] 1.3 Registrar `Tenant` en `backend/app/models/__init__.py` (importar para que Alembic lo detecte)

## 2. BaseRepository genérico

- [x] 2.1 Crear `backend/app/repositories/base.py`: clase `BaseRepository[T]` con constructor `(session: AsyncSession, tenant_id: UUID, model: type[T])`. Métodos: `get(id: UUID) -> T | None`, `list(**filters) -> list[T]`, `create(data: dict) -> T`, `update(id: UUID, data: dict) -> T | None`, `soft_delete(id: UUID) -> bool`
- [x] 2.2 Asegurar que `get` y `list` filtren siempre por `tenant_id = self.tenant_id AND deleted_at IS NULL`
- [x] 2.3 Asegurar que `soft_delete` setea `deleted_at = datetime.utcnow()` y NO emite DELETE SQL
- [x] 2.4 Crear `backend/app/repositories/__init__.py` exportando `BaseRepository`

## 3. Utilidad de cifrado AES-256-GCM

- [x] 3.1 Crear `backend/app/core/crypto.py`: cargar `ENCRYPTION_KEY` desde env en módulo load; levantar `ConfigurationError` si falta o no es hex de 64 chars
- [x] 3.2 Implementar `encrypt(plaintext: str) -> str`: nonce random 12 bytes, AES-256-GCM, salida `base64(nonce + tag + ciphertext)`
- [x] 3.3 Implementar `decrypt(ciphertext: str) -> str`: parsear base64, extraer nonce + tag + ciphertext, verificar GCM tag, retornar plaintext; levantar error si tag inválido
- [x] 3.4 Verificar que `ENCRYPTION_KEY` se valida en `lifespan` startup (o al importar el módulo) para fail-fast antes del primer request

## 4. Migración Alembic 0001

- [x] 4.1 Crear `backend/alembic/versions/0001_tenant.py`: `upgrade()` crea tabla `tenants` con columnas `id` UUID PK, `slug` VARCHAR UNIQUE NOT NULL, `nombre` VARCHAR NOT NULL, `activo` BOOLEAN NOT NULL DEFAULT TRUE, `created_at` TIMESTAMP NOT NULL, `updated_at` TIMESTAMP NOT NULL
- [x] 4.2 Implementar `downgrade()`: `DROP TABLE tenants`
- [x] 4.3 Verificar que `alembic upgrade head` pasa en DB efímera de tests (sin error)
- [x] 4.4 Verificar que `alembic downgrade -1` revierte sin error

## 5. Tests — aislamiento multi-tenant

- [x] 5.1 Crear `backend/tests/test_tenancy.py` con fixture de dos tenants en DB de test
- [x] 5.2 Test RED→GREEN: `BaseRepository` con `tenant_id=A` no retorna registros de `tenant_id=B` (`get` → None, `list` → [])
- [x] 5.3 Test RED→GREEN: `soft_delete` setea `deleted_at`, el registro no aparece en `list/get` pero persiste en DB con query directo
- [x] 5.4 Test RED→GREEN: `created_at` y `updated_at` son auto-seteados en `create`; `updated_at` cambia en `update`
- [x] 5.5 Triangulación: múltiples registros de distintos tenants mezclados — `list` retorna solo los del tenant correcto

## 6. Tests — cifrado round-trip

- [x] 6.1 Crear `backend/tests/test_crypto.py`
- [x] 6.2 Test RED→GREEN: `decrypt(encrypt(value)) == value` para strings arbitrarios (incluyendo Unicode y caracteres especiales)
- [x] 6.3 Test RED→GREEN: dos llamadas `encrypt(value)` producen ciphertexts distintos (nonce único)
- [x] 6.4 Test RED→GREEN: `decrypt` con ciphertext adulterado levanta error de integridad GCM
- [x] 6.5 Test RED→GREEN: módulo falla en import/startup si `ENCRYPTION_KEY` no está configurada

## 7. Verificación final

- [x] 7.1 Correr suite completa `pytest backend/tests/` — todos pasan (≥80% cobertura de líneas)
- [x] 7.2 Verificar que `alembic check` no reporta migraciones pendientes sin aplicar
- [x] 7.3 Revisar que ningún archivo supera 500 LOC
