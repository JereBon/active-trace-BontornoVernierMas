## 1. Migración y modelo de datos

- [x] 1.1 Agregar columna `comunicacion_requiere_aprobacion BOOLEAN NOT NULL DEFAULT TRUE` a la tabla `tenant` en migración 0013
- [x] 1.2 Crear migración Alembic `0013_comunicacion` con tabla `comunicaciones` (todos los campos de E21: id, tenant_id, enviado_por, materia_id, destinatario, asunto, cuerpo, estado, lote_id, enviado_at, created_at, updated_at, deleted_at)
- [x] 1.3 Agregar índices a `comunicaciones`: `(tenant_id)`, `(lote_id)`, `(estado)`, `(tenant_id, lote_id)`
- [x] 1.4 Crear `backend/app/models/comunicacion.py` con clase `Comunicacion(Base, TenantScopedMixin)` y enum `EstadoComunicacion`

## 2. Schemas Pydantic

- [x] 2.1 Crear `backend/app/schemas/comunicacion.py` con schemas: `PreviewRequest`, `PreviewResponse`, `EncoladoRequest`, `EncoladoResponse`, `ComunicacionOut` (destinatario enmascarado), `LoteStatusOut` — todos con `extra='forbid'`

## 3. Repository

- [x] 3.1 Crear `backend/app/repositories/comunicacion_repository.py` con `ComunicacionRepository`: `create_bulk()`, `get_by_id()`, `get_lote()`, `update_estado()`, `get_pendientes_para_worker()` (SELECT FOR UPDATE SKIP LOCKED), `soft_delete()` — todos filtran por `tenant_id`

## 4. Service

- [x] 4.1 Crear `backend/app/services/comunicacion_service.py` con `ComunicacionService`: `preview()` (renderiza sin persistir), `encolar_lote()` (genera lote_id, cifra destinatarios, valida aprobación), `aprobar_lote()`, `cancelar_lote()`, `cancelar_individual()`, `_validar_transicion()` (máquina de estados)
- [x] 4.2 Implementar cifrado de `destinatario` usando `crypto.encrypt()` al encolar y descifrado al despachar
- [x] 4.3 Implementar lógica de aprobación configurable: leer `tenant.comunicacion_requiere_aprobacion` al encolar
- [x] 4.4 Registrar auditoría `COMUNICACION_ENVIAR`, `COMUNICACION_APROBAR`, `COMUNICACION_CANCELAR` usando `audit_action()`

## 5. Router API

- [x] 5.1 Crear `backend/app/routers/comunicaciones.py` con endpoints: `POST /preview`, `POST /encolar`, `PATCH /lotes/{lote_id}/aprobar`, `PATCH /lotes/{lote_id}/cancelar`, `PATCH /{id}/cancelar`, `GET /lotes/{lote_id}` — guards `comunicacion:enviar` y `comunicacion:aprobar` según corresponda
- [x] 5.2 Registrar el router en `backend/app/main.py` con prefijo `/api/comunicaciones`

## 6. Worker asíncrono

- [x] 6.1 Crear `backend/workers/comunicacion_worker.py` con `ComunicacionWorker`: loop asyncio que cada N segundos llama `get_pendientes_para_worker()`, transiciona a `Enviando`, intenta despacho (stub configurable por env), transiciona a `Enviado` o `Error`
- [x] 6.2 Integrar el worker como background task en el startup de FastAPI (`lifespan` handler) con shutdown limpio

## 7. Tests (Strict TDD — escribir ANTES del código de producción)

- [x] 7.1 Tests de máquina de estados: transiciones válidas (Pendiente→Enviando→Enviado, Pendiente→Enviando→Error, Pendiente→Cancelado) e inválidas (desde terminal, Enviando→Cancelado)
- [x] 7.2 Tests de preview: renderizado correcto con variables, 422 con variable faltante, sin persistencia en DB
- [x] 7.3 Tests de encolado masivo: lote_id generado, destinatarios cifrados en DB, respuesta con count, 403 sin permiso, tenant_id from session
- [x] 7.4 Tests de aprobación: aprobar lote (todos los Pendiente del lote), cancelar lote, cancelar individual, 403 sin permiso, 404 de otro tenant
- [x] 7.5 Tests del worker: procesa Pendiente→Enviado, no duplica con SKIP LOCKED (test concurrente)
- [x] 7.6 Tests de auditoría: verificar entrada en AuditLog para COMUNICACION_ENVIAR, COMUNICACION_APROBAR, COMUNICACION_CANCELAR
- [x] 7.7 Tests de tenant isolation: consulta de lote ajeno devuelve 404

## 8. Verificación final

- [x] 8.1 Ejecutar `python -m pytest tests/test_comunicaciones.py -q` y confirmar ≥80% líneas, ≥90% reglas de negocio
- [x] 8.2 Verificar que ningún archivo supere 500 LOC
- [x] 8.3 Verificar que la migración 0013 aplica limpiamente con `alembic upgrade head` y revierte con `alembic downgrade -1`
