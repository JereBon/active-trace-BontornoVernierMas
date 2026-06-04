## Context

C-01 estableció el esqueleto FastAPI con conectividad a PostgreSQL y health check. No hay ninguna tabla de dominio ni entidad ORM definida. Este change introduce la capa de persistencia fundamental sobre la que se construye todo el sistema: el modelo `Tenant`, el mixin de columnas comunes, el `BaseRepository` con tenant scope, el cifrado AES-256-GCM para PII, y la primera migración Alembic.

Constraints:
- Python 3.13, SQLAlchemy 2.0 async, Alembic, PostgreSQL.
- Toda entidad lleva `tenant_id` — no hay entidades globales excepto `Tenant` mismo.
- Governance CRÍTICO: ningún código escrito sin revisión.
- Soft delete siempre; nunca borrado físico.
- `ENCRYPTION_KEY` en env var (ya declarada en `.env.example` desde C-01).

## Goals / Non-Goals

**Goals:**
- Definir `Tenant` como raíz de aislamiento.
- Mixin `TenantScopedMixin` reutilizable por todos los models del dominio.
- `BaseRepository[T]` genérico que aplique tenant scope en todo query por defecto.
- Soft delete transparente: `deleted_at IS NULL` filtrado en `BaseRepository.list/get`.
- Cifrado/descifrado AES-256-GCM en `backend/app/core/crypto.py`.
- Migración `0001_tenant` que cree la tabla `tenants`.
- Test suite: aislamiento multi-tenant, soft delete, cifrado round-trip, timestamps.

**Non-Goals:**
- Modelos de dominio (Usuario, Carrera, etc.) — esos van en C-06/C-07.
- Autenticación y sesiones — C-03.
- RBAC — C-04.
- Cifrado de columnas a nivel ORM automático (tipo híbrido) — no se implementa en este change; el cifrado se aplica manualmente en el service layer.

## Decisions

### D-01: SQLAlchemy `DeclarativeBase` + `AsyncSession`
**Elegido**: Una única `Base = DeclarativeBase()` en `backend/app/models/base.py`. Toda model hereda de `Base` y de `TenantScopedMixin`.  
**Alternativa descartada**: `declarative_base()` (API antigua) — incompatible con typing estricto de SA 2.0.

### D-02: `TenantScopedMixin` como clase Python separada (no herencia de `Base`)
**Elegido**: Mixin puro con `__abstract__ = True` que aporta columnas `id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at`. Los models concretos declaran `__tablename__` y sus columnas propias.  
**Razón**: Permite reusar el mixin sin acoplar el árbol de herencia; SQLAlchemy 2.0 admite mixins con columnas mapeadas.

### D-03: `BaseRepository[T]` genérico con `tenant_id` como parámetro de construcción
**Elegido**: El repositorio recibe `tenant_id: UUID` en el constructor (extraído del JWT verificado en el router). Todos los métodos (`get`, `list`, `create`, `update`, `soft_delete`) aplican `WHERE tenant_id = :tenant_id AND deleted_at IS NULL` por defecto.  
**Alternativa descartada**: Pasar `tenant_id` en cada método — más propenso a olvidarlo.  
**Por qué importa**: Un query sin scope de tenant es un bug de seguridad que debe ser imposible por defecto.

### D-04: Cifrado AES-256-GCM con clave de 32 bytes desde env var
**Elegido**: `crypto.py` expone `encrypt(plaintext: str) -> str` y `decrypt(ciphertext: str) -> str`. Formato de salida: `base64(nonce || tag || ciphertext)` en un único campo texto.  
**Clave**: `ENCRYPTION_KEY` (hex de 64 chars = 32 bytes). Si no está configurada, la app no arranca.  
**Alternativa descartada**: Fernet (AES-128-CBC) — GCM provee autenticación integrada y es el estándar actual.

### D-05: Una migración Alembic por change de schema; nombres `NNNN_descripcion`
**Convención establecida**: `backend/alembic/versions/0001_tenant.py`. No usar autogenerate sin revisión; cada migración es escrita a mano para garantizar reversibilidad.

## Risks / Trade-offs

- **[Riesgo] Rotación de `ENCRYPTION_KEY`** → todos los valores cifrados en reposo se vuelven ilegibles sin la clave original. Mitigación: documentar explícitamente que la key es inmutable post-deploy; la rotación requiere re-cifrado batch (fuera de scope de este change).
- **[Trade-off] Cifrado manual en service layer** → el desarrollador puede olvidar cifrar. Mitigación: las specs y el code review exigen verificación; en C-07 se puede añadir un tipo híbrido SA si el patrón manual resulta frágil.
- **[Riesgo] Tenant scope olvidado en queries ad-hoc** → data leak entre tenants. Mitigación: `BaseRepository` hace imposible el query sin scope; cualquier query directo en un service falla en code review (regla dura #9).

## Migration Plan

1. Aplicar `alembic upgrade head` en ambiente de test (DB efímera de pytest).
2. En producción (cuando aplique): `alembic upgrade head` sin downtime (tabla nueva, sin ALTER).
3. Rollback: `alembic downgrade -1` (DROP TABLE tenants — seguro porque no hay datos de producción en este change).

## Open Questions

*(ninguna — el scope de este change está completamente definido por las reglas duras del proyecto)*
