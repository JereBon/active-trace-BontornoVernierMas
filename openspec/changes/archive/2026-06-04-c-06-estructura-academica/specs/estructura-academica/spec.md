## ADDED Requirements

### Requirement: Gestión de Carreras
El sistema SHALL permitir crear, leer, actualizar y desactivar (soft delete) Carreras dentro del tenant. El par `(tenant_id, codigo)` SHALL ser único. Una Carrera eliminada (soft) no aparecerá en ningún listado ni consulta de detalle.

#### Scenario: Crear carrera con codigo único
- **WHEN** un usuario con permiso `estructura:gestionar` envía POST `/v1/carreras` con `codigo` y `nombre` válidos
- **THEN** el sistema crea la Carrera con `estado=Activa` y retorna 201 con el recurso creado

#### Scenario: Rechazo por codigo duplicado dentro del tenant
- **WHEN** un usuario intenta crear una Carrera con un `codigo` que ya existe para el mismo `tenant_id`
- **THEN** el sistema retorna 409 Conflict

#### Scenario: Listar carreras activas
- **WHEN** un usuario con permiso `estructura:gestionar` envía GET `/v1/carreras`
- **THEN** el sistema retorna solo las Carreras del tenant activo que no tienen `deleted_at`

#### Scenario: Desactivar carrera (soft delete)
- **WHEN** un usuario con permiso `estructura:gestionar` envía DELETE `/v1/carreras/{id}`
- **THEN** el sistema establece `deleted_at` en la Carrera y retorna 204; la Carrera no aparece en listados posteriores

#### Scenario: Acceso denegado sin permiso
- **WHEN** un usuario sin permiso `estructura:gestionar` intenta cualquier operación sobre `/v1/carreras`
- **THEN** el sistema retorna 403 Forbidden

---

### Requirement: Gestión de Cohortes
El sistema SHALL permitir crear, leer, actualizar y desactivar Cohortes dentro del tenant. El par `(tenant_id, carrera_id, nombre)` SHALL ser único.

#### Scenario: Crear cohorte válida
- **WHEN** un usuario con permiso `estructura:gestionar` envía POST `/v1/cohortes` con `carrera_id`, `nombre`, `anio` y `vig_desde` válidos
- **THEN** el sistema crea la Cohorte con `estado=Activa` y retorna 201

#### Scenario: Rechazo por nombre duplicado en la misma carrera y tenant
- **WHEN** un usuario intenta crear una Cohorte con el mismo `nombre` para la misma `carrera_id` dentro del mismo tenant
- **THEN** el sistema retorna 409 Conflict

#### Scenario: Cohorte con FK a carrera de otro tenant rechazada
- **WHEN** un usuario intenta crear una Cohorte referenciando una `carrera_id` que pertenece a otro tenant
- **THEN** el sistema retorna 404 Not Found (la carrera no existe en el tenant del usuario)

#### Scenario: Soft delete de cohorte
- **WHEN** un usuario con permiso `estructura:gestionar` envía DELETE `/v1/cohortes/{id}`
- **THEN** el sistema establece `deleted_at` y retorna 204

---

### Requirement: Gestión de Materias
El sistema SHALL permitir crear, leer, actualizar y desactivar Materias dentro del tenant. El par `(tenant_id, codigo)` SHALL ser único. La Materia es el catálogo plano de unidades académicas; la relación con Carreras y Cohortes se resuelve en la entidad Asignación (change posterior).

#### Scenario: Crear materia con codigo único
- **WHEN** un usuario con permiso `estructura:gestionar` envía POST `/v1/materias` con `codigo` y `nombre` válidos
- **THEN** el sistema crea la Materia con `estado=Activa` y retorna 201

#### Scenario: Rechazo por codigo duplicado dentro del tenant
- **WHEN** un usuario intenta crear una Materia con un `codigo` que ya existe para el mismo `tenant_id`
- **THEN** el sistema retorna 409 Conflict

#### Scenario: Listar materias del tenant
- **WHEN** un usuario con permiso `estructura:gestionar` envía GET `/v1/materias`
- **THEN** el sistema retorna solo las Materias del tenant activo sin `deleted_at`

#### Scenario: Soft delete de materia
- **WHEN** un usuario con permiso `estructura:gestionar` envía DELETE `/v1/materias/{id}`
- **THEN** el sistema establece `deleted_at` y retorna 204
