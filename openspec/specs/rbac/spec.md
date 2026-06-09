## ADDED Requirements

### Requirement: Permiso estructura:gestionar en catálogo
El sistema SHALL incluir el permiso `estructura:gestionar` en el catálogo de permisos (`permisos`). Este permiso SHALL ser asignado por defecto al rol ADMIN dentro de cada tenant al aplicar la migración o seed correspondiente.

#### Scenario: Permiso existe tras migración
- **WHEN** la migración `0004_estructura_academica` se aplica
- **THEN** el permiso `estructura:gestionar` existe en la tabla `permisos`

#### Scenario: ADMIN puede gestionar estructura académica
- **WHEN** un usuario con rol ADMIN activo envía cualquier operación a los endpoints de estructura académica
- **THEN** el sistema permite la operación (permiso concedido)

#### Scenario: Rol sin permiso no puede gestionar estructura académica
- **WHEN** un usuario con rol ALUMNO o TUTOR (sin `estructura:gestionar`) envía una petición a los endpoints de estructura académica
- **THEN** el sistema retorna 403 Forbidden
