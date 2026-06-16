## 1. Migración de base de datos

- [x] 1.1 Crear migración Alembic `0009_version_padron_entrada_padron` con tablas `version_padron` y `entrada_padron`
- [x] 1.2 Agregar constraint único parcial `(tenant_id, materia_id, cohorte_id) WHERE activa = true` en `version_padron`
- [x] 1.3 Agregar índices: `(tenant_id, materia_id, cohorte_id)` en `version_padron`; `(version_id, tenant_id)` en `entrada_padron`
- [x] 1.4 Verificar que `downgrade()` dropea ambas tablas en orden correcto

## 2. Modelos ORM

- [x] 2.1 Crear `backend/app/models/version_padron.py` con `VersionPadron(Base, TenantScopedMixin)` — campos: materia_id, cohorte_id, cargado_por, cargado_at, activa
- [x] 2.2 Crear `backend/app/models/entrada_padron.py` con `EntradaPadron(Base, TenantScopedMixin)` — campos: version_id, usuario_id (nullable), nombre, apellidos, email (cifrado), comision, regional
- [x] 2.3 Agregar `VersionPadron` y `EntradaPadron` al `__init__.py` de modelos para que Alembic los detecte

## 3. Repository

- [x] 3.1 Crear `backend/app/repositories/padron_repository.py` con `PadronRepository(TenantScopedRepository)`
- [x] 3.2 Implementar `get_version_activa(materia_id, cohorte_id)` → VersionPadron | None
- [x] 3.3 Implementar `crear_version(materia_id, cohorte_id, cargado_por)` → VersionPadron (desactiva la anterior en la misma transacción)
- [x] 3.4 Implementar `bulk_insert_entradas(version_id, entradas)` → list[EntradaPadron]
- [x] 3.5 Implementar `soft_delete_by_materia(materia_id)` — soft delete de todas las versiones y entradas del tenant para esa materia

## 4. Parser de archivos

- [x] 4.1 Crear `backend/app/services/padron_parser.py` con `PadronParser`
- [x] 4.2 Implementar `parse_xlsx(file_bytes)` → list[EntradaPadronRaw] | raise `PadronParseError` si faltan columnas
- [x] 4.3 Implementar `parse_csv(file_bytes)` → list[EntradaPadronRaw] | raise `PadronParseError` si faltan columnas
- [x] 4.4 Definir DTO `EntradaPadronRaw` (Pydantic, `extra='forbid'`) con campos: nombre, apellidos, email, comision, regional

## 5. Cliente Moodle WS

- [x] 5.1 Crear `backend/app/integrations/moodle_ws.py` con `MoodleWSClient` y `MoodleWSError`
- [x] 5.2 Implementar `get_enrolled_users(course_id)` usando `httpx.AsyncClient`
- [x] 5.3 Implementar `health_check()` → bool
- [x] 5.4 Implementar retry con backoff exponencial (3 intentos, 1s/2s/4s) solo para errores de red; no reintentar 4xx

## 6. Servicio de padrón

- [x] 6.1 Crear `backend/app/services/padron_service.py` con `PadronService`
- [x] 6.2 Implementar `preview_desde_archivo(file, content_type)` → list[EntradaPadronRaw] (parsea sin persistir)
- [x] 6.3 Implementar `confirmar_importacion(materia_id, cohorte_id, entradas, usuario_id)` → VersionPadron (persiste + audit log `PADRON_CARGAR`)
- [x] 6.4 Implementar `sync_desde_moodle(materia_id, cohorte_id, usuario_id)` → VersionPadron (llama MoodleWSClient + confirmar_importacion)
- [x] 6.5 Implementar `vaciar_padron(materia_id, usuario_id)` → None (soft delete + audit log `PADRON_CARGAR` acción=VACIAR)
- [x] 6.6 Cifrar `EntradaPadron.email` usando `app.core.crypto` (AES-256) al persistir

## 7. Router

- [x] 7.1 Crear `backend/app/routers/padron_router.py` con prefix `/padron` (implemented at `app/api/v1/routers/padron.py` per project convention)
- [x] 7.2 Endpoint `POST /padron/preview` — sube archivo, devuelve preview; requiere `padron:cargar`
- [x] 7.3 Endpoint `POST /padron/confirmar` — confirma importación desde preview; requiere `padron:cargar`
- [x] 7.4 Endpoint `POST /padron/sync-moodle/{materia_id}` — sync on-demand desde Moodle; requiere `padron:cargar`; devuelve 502 si Moodle no disponible
- [x] 7.5 Endpoint `DELETE /padron/materia/{materia_id}` — vacía padrón; requiere `padron:vaciar`
- [x] 7.6 Endpoint `GET /padron/materia/{materia_id}` — lista versiones activas/históricas; requiere `padron:leer`
- [x] 7.7 Registrar permisos `padron:leer`, `padron:cargar`, `padron:vaciar` en el catálogo de permisos
- [x] 7.8 Incluir `padron_router` en el router principal de la app

## 8. Tests (Strict TDD — escribir test ANTES del código de cada tarea)

- [x] 8.1 Test: versioning — activar nueva versión desactiva la anterior (safety net, RED, GREEN, triangulación con 2+ casos)
- [x] 8.2 Test: primera carga de padrón crea versión activa
- [x] 8.3 Test: parser xlsx — columnas válidas devuelven DTOs; columnas faltantes devuelven PadronParseError con detalle
- [x] 8.4 Test: parser csv — igual que xlsx
- [x] 8.5 Test: `EntradaPadron` sin `usuario_id` (alumno sin cuenta) — persiste con usuario_id=None
- [x] 8.6 Test: tenant isolation — entradas de tenant_id distinto no se mezclan
- [x] 8.7 Test: MoodleWSClient mock — respuesta exitosa mapea a entradas; error 5xx lanza MoodleWSError; retry ocurre ante error de red; no retry ante 4xx
- [x] 8.8 Test: fallback 502 en sync on-demand cuando Moodle caído
- [x] 8.9 Test: vaciado scope-isolated — solo afecta materia×tenant del llamador
- [x] 8.10 Test: RBAC — 403 sin permiso `padron:cargar`; 403 sin permiso `padron:vaciar`
- [x] 8.11 Verificar cobertura ≥80% líneas y ≥90% reglas de negocio

## 9. Registro de permisos en datos iniciales

- [x] 9.1 Agregar `padron:leer`, `padron:cargar`, `padron:vaciar` al seed/fixture de permisos
- [x] 9.2 Asignar permisos a roles: PROFESOR (leer + cargar para sus materias), COORDINADOR (leer + cargar + vaciar global), ADMIN (todos)
