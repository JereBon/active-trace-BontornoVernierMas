## ADDED Requirements

### Requirement: AuditLog es append-only
El sistema SHALL garantizar que ningún registro de `AuditLog` pueda ser modificado ni eliminado a nivel de aplicación. El repositorio de auditoría MUST exponer únicamente operaciones de creación y lectura.

#### Scenario: Intento de update rechazado
- **WHEN** cualquier capa de aplicación intenta llamar un método de update sobre un registro AuditLog
- **THEN** el sistema SHALL lanzar un error (NotImplementedError o equivalente) y NO modificar ningún registro

#### Scenario: Intento de delete rechazado
- **WHEN** cualquier capa de aplicación intenta llamar un método de delete (hard o soft) sobre un registro AuditLog
- **THEN** el sistema SHALL lanzar un error y NO eliminar ningún registro

#### Scenario: Creación exitosa de registro
- **WHEN** se invoca el helper `audit_action()` con actor_id, tenant_id, accion y detalle válidos
- **THEN** el sistema SHALL persistir un nuevo registro con fecha_hora en UTC, filas_afectadas y todos los campos requeridos

### Requirement: Atribución correcta de acciones bajo impersonación
Toda acción realizada bajo una sesión de impersonación MUST atribuirse al actor real (quién impersona), no al usuario impersonado. El campo `actor_impersonado_id` SHALL registrar al usuario impersonado cuando aplica.

#### Scenario: Acción bajo impersonación registra actor real
- **WHEN** un usuario con permiso `impersonacion:usar` opera bajo una sesión de impersonación y se registra una acción en el audit log
- **THEN** `actor_id` SHALL ser el UUID del usuario que impersona (actor real)
- **AND** `actor_impersonado_id` SHALL ser el UUID del usuario impersonado

#### Scenario: Acción sin impersonación no registra impersonado
- **WHEN** un usuario opera en una sesión normal (sin impersonación) y se registra una acción
- **THEN** `actor_id` SHALL ser el UUID del usuario autenticado
- **AND** `actor_impersonado_id` SHALL ser NULL

### Requirement: Registro de inicio y fin de impersonación
El sistema SHALL registrar automáticamente los códigos de acción `IMPERSONACION_INICIAR` e `IMPERSONACION_FINALIZAR` en el audit log al iniciar y finalizar una sesión de impersonación.

#### Scenario: Inicio de impersonación registrado
- **WHEN** un usuario con permiso `impersonacion:usar` llama a `POST /api/auth/impersonate` con un `user_id` válido
- **THEN** el sistema SHALL crear un registro AuditLog con `accion = "IMPERSONACION_INICIAR"`, `actor_id` = UUID del solicitante, `actor_impersonado_id` = UUID del usuario a impersonar
- **AND** SHALL retornar un JWT con el claim `impersonating_user_id`

#### Scenario: Inicio de impersonación sin permiso rechazado
- **WHEN** un usuario sin permiso `impersonacion:usar` llama a `POST /api/auth/impersonate`
- **THEN** el sistema SHALL retornar HTTP 403 y NO crear ningún registro AuditLog

#### Scenario: Fin de impersonación registrado
- **WHEN** un usuario bajo sesión de impersonación llama a `POST /api/auth/impersonate/end`
- **THEN** el sistema SHALL crear un registro AuditLog con `accion = "IMPERSONACION_FINALIZAR"`, `actor_id` = UUID del actor real, `actor_impersonado_id` = UUID del usuario impersonado

### Requirement: Helper de auditoría reutilizable
El sistema SHALL proveer una función `audit_action()` que cualquier service pueda llamar para registrar una acción con mínimo boilerplate. SHALL aceptar: session, actor_id, tenant_id, accion (código string), detalle (dict/JSONB), filas_afectadas (int), ip (str), user_agent (str), actor_impersonado_id (UUID, nullable).

#### Scenario: Helper registra acción con código y filas afectadas
- **WHEN** se llama `audit_action()` con accion="CALIFICACIONES_IMPORTAR" y filas_afectadas=42
- **THEN** el registro persiste con `accion = "CALIFICACIONES_IMPORTAR"` y `filas_afectadas = 42`

#### Scenario: Fallo del helper no interrumpe la operación principal
- **WHEN** la escritura del audit log falla por error transitorio de base de datos
- **THEN** el sistema SHALL registrar el error en el log de aplicación (logger.error) y NO propagar la excepción al caller
- **AND** la operación de negocio original SHALL continuar normalmente
