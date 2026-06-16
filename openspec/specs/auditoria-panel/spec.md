## Requirements

### Requirement: Panel de métricas de auditoría (F9.1)
El sistema SHALL exponer métricas agregadas de uso del tenant para COORDINADOREs y ADMINs en el endpoint `GET /v1/auditoria/panel`. El COORDINADOR SHALL ver solo sus propias acciones; el ADMIN SHALL ver todo el tenant. El acceso MUST estar protegido por `require_permission("auditoria:ver")`.

#### Scenario: ADMIN obtiene métricas agregadas del tenant
- **WHEN** un usuario con rol ADMIN y permiso `auditoria:ver` llama `GET /v1/auditoria/panel`
- **THEN** el sistema retorna HTTP 200 con `acciones_por_dia` (lista de fecha+conteo), `por_docente` (lista de actor_id+nombre+conteo) y `por_materia` (lista de materia_id+actor_id+conteo), todos filtrados por `tenant_id` del JWT

#### Scenario: COORDINADOR solo ve sus propias métricas
- **WHEN** un usuario con rol COORDINADOR llama `GET /v1/auditoria/panel`
- **THEN** el sistema retorna métricas filtradas exclusivamente por `actor_id == current_user.id`, sin mostrar acciones de otros usuarios del mismo tenant

#### Scenario: Usuario sin permiso no puede acceder al panel
- **WHEN** un usuario sin `auditoria:ver` llama `GET /v1/auditoria/panel`
- **THEN** el sistema retorna HTTP 403

### Requirement: Log completo de auditoría paginado con filtros (F9.2, RN-23/24)
El sistema SHALL exponer el log completo de auditoría en `GET /v1/auditoria/log` con soporte para filtros opcionales: rango de fechas (`fecha_desde`, `fecha_hasta`), `usuario_id` (actor_id), y `accion`. La respuesta MUST incluir paginación via `limit` (default 200) y `offset`.

#### Scenario: Log sin filtros retorna hasta 200 entradas más recientes
- **WHEN** un ADMIN llama `GET /v1/auditoria/log` sin parámetros
- **THEN** el sistema retorna hasta 200 entradas de `audit_logs` del tenant, ordenadas por `fecha_hora` DESC

#### Scenario: Filtro por rango de fechas acota el resultado
- **WHEN** un ADMIN llama `GET /v1/auditoria/log?fecha_desde=2025-01-01&fecha_hasta=2025-01-31`
- **THEN** el sistema retorna solo entradas con `fecha_hora` dentro del rango indicado

#### Scenario: Filtro por usuario_id acota el resultado
- **WHEN** un ADMIN llama `GET /v1/auditoria/log?usuario_id=<uuid>`
- **THEN** el sistema retorna solo entradas donde `actor_id == usuario_id`

#### Scenario: COORDINADOR solo ve su propio log aunque pase usuario_id ajeno
- **WHEN** un COORDINADOR llama `GET /v1/auditoria/log?usuario_id=<otro_uuid>`
- **THEN** el sistema ignora el parámetro y retorna solo entradas donde `actor_id == current_user.id`

#### Scenario: Paginación funciona correctamente
- **WHEN** un ADMIN llama `GET /v1/auditoria/log?limit=10&offset=20`
- **THEN** el sistema retorna hasta 10 entradas saltando las primeras 20, respetando el orden DESC

### Requirement: Estado de comunicaciones por docente (F9.1)
El sistema SHALL exponer en `GET /v1/auditoria/comunicaciones` el conteo de comunicaciones agrupado por docente y por estado (Pendiente, Enviando, Enviado, Error, Cancelado), scoped al tenant del JWT.

#### Scenario: ADMIN obtiene estado de comunicaciones de todos los docentes
- **WHEN** un ADMIN llama `GET /v1/auditoria/comunicaciones`
- **THEN** el sistema retorna una lista donde cada entrada contiene `docente_id` y conteos por estado (`pendiente`, `enviando`, `enviado`, `error`, `cancelado`)

#### Scenario: COORDINADOR solo ve comunicaciones propias
- **WHEN** un COORDINADOR llama `GET /v1/auditoria/comunicaciones`
- **THEN** el sistema retorna solo la entrada correspondiente a `docente_id == current_user.id`

#### Scenario: Sin comunicaciones retorna lista vacía
- **WHEN** un ADMIN llama `GET /v1/auditoria/comunicaciones` y el tenant no tiene comunicaciones
- **THEN** el sistema retorna HTTP 200 con lista vacía `[]`
