## Context

El sistema necesita un mecanismo formal para que COORDINADOR/ADMIN publiquen avisos institucionales dentro de un tenant. Los avisos deben tener vigencia temporal (RN-18), opción de acknowledgment (RN-19) y segmentación de audiencia (RN-20). El módulo se apoya en el patrón de tenancy row-level ya establecido en C-02 y sigue el flujo Routers → Services → Repositories → Models.

## Goals / Non-Goals

**Goals:**
- Modelos `Aviso` y `AvisoAck` con tenant_id en ambas tablas.
- Soft delete en `Aviso` (campo `activo`, nunca hard delete).
- Scope de audiencia: `TODOS`, `ROL`, `USUARIO` (enum).
- Acknowledgment idempotente: un segundo `POST /ack` devuelve 200 sin duplicar registro.
- Endpoints protegidos con `require_permission`.
- Migración Alembic numerada correctamente.
- Cobertura TDD ≥80% líneas, ≥90% reglas de negocio.

**Non-Goals:**
- Scope por materia o cohorte (requiere C-06; se deja para extensión futura).
- Envío de notificaciones push/email al publicar (fuera de scope de C-15).
- Paginación avanzada en el listado de avisos (se implementa con skip/limit básico).

## Decisions

### D-1: Enum `AvisoScope` en Python, columna `VARCHAR` en DB

Alternativa considerada: columna `ENUM` nativa de PostgreSQL. Decisión: `VARCHAR` con constraint `CHECK` a través del tipo SQLAlchemy `sa.Enum` para no requerir migración de tipo al agregar valores futuros (ej. `MATERIA`, `COHORTE`).

### D-2: `AvisoAck` usa constraint `UNIQUE(aviso_id, usuario_id)`

Garantiza idempotencia a nivel DB. El endpoint `POST /ack` hace `INSERT ... ON CONFLICT DO NOTHING` o captura `IntegrityError` y retorna 200 de todas formas.

### D-3: Listado de avisos filtra por `activo=True` y ventana de vigencia en el Repository

El filtro `vig_desde <= now() <= vig_hasta` se aplica en `AvisoRepository.list_vigentes()` con scope de tenant. Esto mantiene la lógica en la capa correcta y facilita el test unitario con DB real.

### D-4: Soft delete via `activo = False`

En lugar de un campo `deleted_at`, se usa el campo `activo` que ya forma parte del modelo de dominio (el aviso "desactivado" es un concepto de negocio, no solo un borrado técnico).

### D-5: Permisos nuevos `avisos:publicar` y `avisos:confirmar`

Se agregan al catálogo de permisos existente (tabla de roles/permisos). Los tests verifican explícitamente que sin el permiso adecuado el endpoint retorna 403.

## Risks / Trade-offs

- [Risk] La segmentación por `scope=ROL` requiere que el JWT incluya los roles del usuario para filtrar en memoria o en DB. → Mitigation: el JWT ya contiene roles; el listado aplica el filtro post-query o con un JOIN a la tabla de roles del usuario según el diseño de C-03/C-04. Para C-15 se filtra en Python si es simple, dejando nota de optimización.
- [Risk] Avisos sin `vig_hasta` (abiertos) quedarían siempre visibles. → Mitigation: `vig_hasta` es obligatorio (`NOT NULL`); el schema Pydantic lo valida con `extra='forbid'`.

## Migration Plan

1. Generar migración Alembic: `alembic revision --autogenerate -m "add avisos and aviso_acks tables"`.
2. Verificar que el número de revisión sea el siguiente libre (inspeccionar `backend/alembic/versions/`).
3. Aplicar: `alembic upgrade head` en entorno de test antes de correr la suite.
4. Rollback: `alembic downgrade -1` elimina ambas tablas sin efecto en otras tablas.
