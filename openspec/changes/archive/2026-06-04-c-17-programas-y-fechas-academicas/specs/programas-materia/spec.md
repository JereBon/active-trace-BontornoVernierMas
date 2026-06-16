## ADDED Requirements

### Requirement: Crear programa de materia

El sistema SHALL permitir a usuarios con permiso `estructura:gestionar` crear un programa de materia asociando un documento oficial a una materia, con referencia opcional a cohorte y carrera.

#### Scenario: Creación exitosa de programa

- **WHEN** un usuario autenticado con permiso `estructura:gestionar` envía POST `/api/programas` con `materia_id`, `titulo`, y campos opcionales válidos
- **THEN** el sistema crea el registro `ProgramaMateria` con `tenant_id` extraído del JWT, retorna HTTP 201 y el objeto creado

#### Scenario: Acceso denegado sin permiso

- **WHEN** un usuario autenticado SIN permiso `estructura:gestionar` envía POST `/api/programas`
- **THEN** el sistema retorna HTTP 403 y no crea ningún registro

#### Scenario: Campos no declarados rechazados

- **WHEN** se envía POST `/api/programas` con campos extra no definidos en el schema
- **THEN** el sistema retorna HTTP 422 (extra='forbid')

---

### Requirement: Listar programas de materia

El sistema SHALL permitir listar todos los programas activos del tenant del usuario autenticado.

#### Scenario: Listado filtrado por tenant

- **WHEN** un usuario autenticado envía GET `/api/programas`
- **THEN** el sistema retorna solo los programas cuyo `tenant_id` coincide con el del JWT, excluyendo soft-deleted

#### Scenario: Aislamiento multi-tenant

- **WHEN** existen programas de dos tenants distintos en la DB
- **THEN** cada usuario solo ve los programas de su propio tenant

---

### Requirement: Obtener programa por materia

El sistema SHALL permitir obtener los programas de una materia específica del tenant.

#### Scenario: Consulta exitosa

- **WHEN** un usuario autenticado envía GET `/api/programas/{materia_id}`
- **THEN** el sistema retorna la lista de programas de esa materia dentro del tenant del usuario

#### Scenario: Materia sin programas

- **WHEN** la materia existe pero no tiene programas asociados en el tenant
- **THEN** el sistema retorna HTTP 200 con lista vacía

---

### Requirement: Soft delete de programa

El sistema SHALL permitir marcar un programa como eliminado sin borrarlo físicamente.

#### Scenario: Soft delete exitoso

- **WHEN** un usuario con permiso `estructura:gestionar` envía DELETE `/api/programas/{id}`
- **THEN** el sistema establece `deleted_at` con el timestamp actual y retorna HTTP 204

#### Scenario: Programa soft-deleted no aparece en listados

- **WHEN** un programa tiene `deleted_at` no nulo
- **THEN** no aparece en GET `/api/programas` ni en GET `/api/programas/{materia_id}`
