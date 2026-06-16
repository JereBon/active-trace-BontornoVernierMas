## Why

C-01 dejó el esqueleto FastAPI corriendo pero sin ninguna entidad en base de datos. Todos los changes siguientes (auth, RBAC, dominio académico) necesitan la capa de persistencia fundamental: el modelo `Tenant`, los mixins compartidos, la convención de migración Alembic, el repositorio genérico con scope de tenant siempre activo y la utilidad de cifrado AES-256 para PII. Sin esto nada puede construirse.

## What Changes

- Nuevo modelo `Tenant` (id UUID, slug, nombre, activo, timestamps).
- Mixin `TenantScopedMixin`: `id` (UUID PK), `tenant_id` (FK → Tenant), `created_at`, `updated_at`, `deleted_at` (soft delete). Toda entidad del dominio hereda este mixin.
- `BaseRepository[T]` genérico (SQLAlchemy 2.0 async): scope de tenant SIEMPRE activo por defecto; soft delete transparente; métodos `get`, `list`, `create`, `update`, `soft_delete`.
- Utilidad `crypto.py`: cifrado/descifrado AES-256-GCM para atributos `[cifrado]` (DNI, CUIL, CBU, email PII). Clave derivada de env var `ENCRYPTION_KEY`. Nunca loguear valores cifrados.
- Migración Alembic `0001_tenant.py` + convención documentada: una migración por cambio de schema, nombres numerados secuencialmente.
- Tests: aislamiento multi-tenant, soft delete transparente, cifrado round-trip, timestamps automáticos.

## Capabilities

### New Capabilities

- `tenancy`: Modelo Tenant, mixin TenantScopedMixin, BaseRepository con tenant scope, soft delete transversal.
- `crypto`: Utilidad AES-256-GCM para cifrado/descifrado de atributos PII en reposo.

### Modified Capabilities

*(ninguna — primera vez que se crean specs de persistencia)*

## Impact

- **Nuevo**: `backend/app/models/tenant.py`, `backend/app/models/base.py` (mixin).
- **Nuevo**: `backend/app/repositories/base.py` (BaseRepository genérico).
- **Nuevo**: `backend/app/core/crypto.py`.
- **Nuevo**: `backend/alembic/versions/0001_tenant.py`.
- **Tests**: `backend/tests/test_tenancy.py`, `backend/tests/test_crypto.py`.
- Todos los changes futuros dependen de este foundation de datos.
