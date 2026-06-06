## ADDED Requirements

### Requirement: Docente puede previsualizar el mensaje antes de enviar
El sistema SHALL permitir al usuario completar asunto y cuerpo del mensaje con variables (`{nombre}`, `{materia}`, etc.) y obtener un preview renderizado llamando al backend.

#### Scenario: Preview exitoso muestra mensaje renderizado
- **WHEN** el usuario completa asunto y cuerpo y hace clic en "Preview"
- **THEN** el sistema llama a `POST /v1/comunicaciones/preview` con una entrada de prueba y muestra el asunto y cuerpo renderizados

#### Scenario: Variable inválida muestra error
- **WHEN** el backend devuelve 422 por variable no reconocida
- **THEN** el sistema muestra el mensaje de error inline junto al campo correspondiente

### Requirement: Docente puede enviar comunicaciones a atrasados
El sistema SHALL permitir enviar un mensaje masivo a los alumnos atrasados de la materia. El formulario MUST pre-cargar los destinatarios desde la lista de atrasados actual.

#### Scenario: Envío encola el lote
- **WHEN** el usuario confirma el envío con destinatarios y mensaje válidos
- **THEN** el sistema llama a `POST /v1/comunicaciones/encolar` y muestra el `lote_id` retornado

#### Scenario: Envío sin destinatarios muestra validación
- **WHEN** el usuario intenta enviar sin ningún destinatario seleccionado
- **THEN** el sistema muestra un error de validación y no llama al endpoint

### Requirement: Docente puede seguir el estado del lote en tiempo real
El sistema SHALL hacer polling al estado del lote cada 3 segundos hasta que todos los mensajes alcancen un estado terminal (Enviado, Fallido o Cancelado), o hasta 2 minutos.

#### Scenario: Polling muestra estados actualizados
- **WHEN** el lote está en estado Pendiente o parcialmente enviado
- **THEN** el sistema llama a `GET /v1/comunicaciones/lotes/{lote_id}` cada 3s y actualiza los contadores visibles

#### Scenario: Polling se detiene al completar
- **WHEN** todos los mensajes del lote alcanzan un estado terminal
- **THEN** el sistema detiene el polling y muestra un resumen final con conteos de enviados/fallidos/cancelados
