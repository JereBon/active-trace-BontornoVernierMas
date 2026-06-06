## ADDED Requirements

### Requirement: Modelo Comunicacion con máquina de estados (RN-15)
El sistema SHALL persistir cada comunicación saliente como un registro `Comunicacion` con los campos: `id`, `tenant_id`, `enviado_por`, `materia_id`, `destinatario` (cifrado AES-256-GCM), `asunto`, `cuerpo`, `estado`, `lote_id`, `enviado_at`, `created_at`, `updated_at`, `deleted_at`.
El campo `estado` SHALL seguir el ciclo: `Pendiente → Enviando → Enviado | Error`, y `Pendiente → Cancelado`. Las transiciones fuera de este ciclo MUST ser rechazadas con error 409 Conflict.

#### Scenario: Transición válida Pendiente a Enviando
- **WHEN** el worker toma un mensaje en estado `Pendiente`
- **THEN** el sistema transiciona el estado a `Enviando` y persiste el cambio

#### Scenario: Transición válida Enviando a Enviado
- **WHEN** el worker despacha el mensaje exitosamente
- **THEN** el sistema transiciona el estado a `Enviado` y registra `enviado_at` con la hora actual

#### Scenario: Transición válida Enviando a Error
- **WHEN** el despacho del mensaje falla
- **THEN** el sistema transiciona el estado a `Error` y preserva el registro para reintento manual

#### Scenario: Transición válida Pendiente a Cancelado
- **WHEN** un usuario con permiso `comunicacion:enviar` cancela un mensaje en estado `Pendiente`
- **THEN** el sistema transiciona el estado a `Cancelado`

#### Scenario: Transición inválida desde estado terminal
- **WHEN** se intenta cambiar el estado de un mensaje que ya está en `Enviado`, `Cancelado` o `Error`
- **THEN** el sistema rechaza la operación con 409 Conflict y no modifica el registro

#### Scenario: Cancelación de mensaje en estado Enviando
- **WHEN** se intenta cancelar un mensaje en estado `Enviando`
- **THEN** el sistema rechaza la operación con 409 Conflict

### Requirement: destinatario cifrado en reposo (AES-256-GCM)
El campo `destinatario` de `Comunicacion` SHALL almacenarse siempre cifrado con AES-256-GCM usando el módulo `crypto`. La dirección de email en texto plano MUST NOT aparecer en la base de datos ni en las respuestas API. Las respuestas de seguimiento SHALL devolver el email enmascarado (`***@dominio.com`).

#### Scenario: Almacenamiento cifrado
- **WHEN** se encola un nuevo mensaje con destinatario `alumno@ejemplo.com`
- **THEN** la fila en base de datos contiene el `destinatario` cifrado, no el email en texto plano

#### Scenario: Enmascaramiento en respuesta API
- **WHEN** un usuario consulta el estado de un lote de comunicaciones vía API
- **THEN** la respuesta muestra `***@ejemplo.com` y no el email completo

### Requirement: Preview obligatorio antes de encolar (F3.1, RN-16)
El sistema SHALL proveer un endpoint `POST /api/comunicaciones/preview` que reciba un template de asunto y cuerpo junto con las variables de sustitución, y devuelva el mensaje renderizado sin persistir ningún registro. El encolado MUST ser una llamada separada posterior.

#### Scenario: Preview exitoso con variables
- **WHEN** se envía un preview con template `"Hola {{nombre}}"` y variable `nombre="Ana"`
- **THEN** el sistema devuelve el asunto y cuerpo renderizado con `"Hola Ana"` y no crea ningún registro en base de datos

#### Scenario: Preview con variable faltante
- **WHEN** se envía un preview con template `"Hola {{nombre}}"` pero no se provee la variable `nombre`
- **THEN** el sistema devuelve 422 Unprocessable Entity indicando la variable faltante

### Requirement: Envío masivo con cola y lote_id (F3.2)
El sistema SHALL proveer un endpoint `POST /api/comunicaciones/encolar` protegido con guard `comunicacion:enviar`, que acepte una lista de destinatarios con sus variables y un template. Todos los mensajes del mismo request SHALL compartir un `lote_id` generado por el servicio. Si `tenant.comunicacion_requiere_aprobacion` es `True` y el lote tiene más de un destinatario, los mensajes entran en estado `Pendiente` y esperan aprobación. De lo contrario, el worker los toma directamente.

#### Scenario: Encolado masivo con aprobación requerida
- **WHEN** un usuario con permiso `comunicacion:enviar` encola un lote de 10 mensajes y el tenant tiene `comunicacion_requiere_aprobacion=True`
- **THEN** los 10 registros quedan en estado `Pendiente` y se devuelve el `lote_id` y el count de mensajes encolados

#### Scenario: Encolado con aprobación no requerida
- **WHEN** un usuario con permiso `comunicacion:enviar` encola un lote y el tenant tiene `comunicacion_requiere_aprobacion=False`
- **THEN** los mensajes quedan disponibles para que el worker los procese directamente (sin esperar aprobación)

#### Scenario: Encolado sin permiso
- **WHEN** un usuario sin permiso `comunicacion:enviar` intenta encolar mensajes
- **THEN** el sistema responde 403 Forbidden y no crea ningún registro

#### Scenario: Encolado con tenant_id from session
- **WHEN** un usuario autenticado encola mensajes
- **THEN** todos los registros creados llevan el `tenant_id` de la sesión JWT, ignorando cualquier `tenant_id` del body

### Requirement: Aprobación y cancelación de lote (F3.3, RN-17)
El sistema SHALL proveer endpoints para que usuarios con permiso `comunicacion:aprobar` aprueben o cancelen un lote completo (`PATCH /api/comunicaciones/lotes/{lote_id}/aprobar`, `PATCH /api/comunicaciones/lotes/{lote_id}/cancelar`) o mensajes individuales (`PATCH /api/comunicaciones/{id}/cancelar`). La aprobación SHALL transicionar todos los mensajes `Pendiente` del lote al estado procesable por el worker. La cancelación SHALL transicionar todos los mensajes `Pendiente` a `Cancelado`.

#### Scenario: Aprobación de lote completo
- **WHEN** un usuario con permiso `comunicacion:aprobar` aprueba el lote con `lote_id=X`
- **THEN** todos los mensajes de ese lote en estado `Pendiente` quedan disponibles para el worker y se registra una entrada de auditoría `COMUNICACION_APROBAR`

#### Scenario: Cancelación de lote completo
- **WHEN** un usuario con permiso `comunicacion:aprobar` cancela el lote con `lote_id=X`
- **THEN** todos los mensajes de ese lote en estado `Pendiente` pasan a `Cancelado` y se registra `COMUNICACION_CANCELAR`

#### Scenario: Cancelación individual
- **WHEN** un usuario con permiso `comunicacion:enviar` cancela un mensaje individual en estado `Pendiente`
- **THEN** sólo ese mensaje pasa a `Cancelado`; los demás del lote no se ven afectados

#### Scenario: Aprobación sin permiso
- **WHEN** un usuario sin permiso `comunicacion:aprobar` intenta aprobar un lote
- **THEN** el sistema responde 403 Forbidden

#### Scenario: Aprobación de lote de otro tenant
- **WHEN** un usuario intenta aprobar un lote que pertenece a otro tenant
- **THEN** el sistema responde 404 Not Found (no revela la existencia del lote)

### Requirement: Worker asíncrono procesa cola (KB §08 §5.2)
El sistema SHALL incluir un worker asíncrono que consulte periódicamente los mensajes en estado `Pendiente` aprobados (o todos si no se requiere aprobación) usando `SELECT FOR UPDATE SKIP LOCKED`, transicione cada uno a `Enviando`, intente el despacho, y finalmente transicione a `Enviado` o `Error`. El worker MUST garantizar que dos instancias concurrentes no procesen el mismo mensaje.

#### Scenario: Worker procesa mensaje Pendiente
- **WHEN** existe un mensaje en estado `Pendiente` aprobado y el worker corre un ciclo
- **THEN** el mensaje transiciona a `Enviando` y luego a `Enviado`, con `enviado_at` registrado

#### Scenario: Worker no duplica procesamiento concurrente
- **WHEN** dos workers corren simultáneamente y hay un solo mensaje `Pendiente`
- **THEN** sólo uno de los workers procesa el mensaje; el otro lo omite (SKIP LOCKED)

### Requirement: Auditoría de envíos y aprobaciones
El sistema SHALL registrar una entrada en `AuditLog` con acción `COMUNICACION_ENVIAR` al encolar un lote, `COMUNICACION_APROBAR` al aprobar, y `COMUNICACION_CANCELAR` al cancelar (lote o individual). El `detalle` del log SHALL incluir `lote_id`, `count` de mensajes afectados y `materia_id`.

#### Scenario: Auditoría al encolar
- **WHEN** se encola un lote de mensajes exitosamente
- **THEN** existe un registro en `AuditLog` con acción `COMUNICACION_ENVIAR`, el `tenant_id` correcto y el `lote_id` generado

#### Scenario: Auditoría al cancelar lote
- **WHEN** se cancela un lote
- **THEN** existe un registro en `AuditLog` con acción `COMUNICACION_CANCELAR` y `lote_id`

### Requirement: Tenant isolation en todas las operaciones
Todos los repositories y endpoints de comunicaciones SHALL filtrar por `tenant_id` obtenido de la sesión JWT. Ninguna operación SHALL poder acceder a comunicaciones de otro tenant.

#### Scenario: Consulta de lote propio
- **WHEN** un usuario consulta el estado de un lote que pertenece a su tenant
- **THEN** recibe la información del lote correctamente

#### Scenario: Consulta de lote ajeno
- **WHEN** un usuario consulta el `lote_id` de otro tenant
- **THEN** el sistema devuelve 404 Not Found, sin revelar que el lote existe

### Requirement: Soft delete en registros Comunicacion
El sistema SHALL usar soft delete (`deleted_at`) en todos los registros de `Comunicacion`. Los registros con `deleted_at IS NOT NULL` SHALL ser excluidos de todas las consultas por defecto.

#### Scenario: Soft delete preserva el registro
- **WHEN** se elimina (soft delete) un registro de comunicación
- **THEN** el registro permanece en base de datos con `deleted_at` populated y no aparece en consultas de estado normales
