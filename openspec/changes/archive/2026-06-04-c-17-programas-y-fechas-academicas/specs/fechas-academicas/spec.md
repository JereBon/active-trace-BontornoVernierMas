## ADDED Requirements

### Requirement: Crear fecha académica

El sistema SHALL permitir a usuarios con permiso `estructura:gestionar` registrar instancias evaluativas (parcial, TP, coloquio, recuperatorio) del calendario académico del tenant.

#### Scenario: Creación exitosa de fecha académica

- **WHEN** un usuario con permiso `estructura:gestionar` envía POST `/api/fechas-academicas` con `materia_id`, `cohorte_id`, `tipo` (PARCIAL|TP|COLOQUIO|RECUPERATORIO), `numero`, `periodo`, `fecha` y `titulo`
- **THEN** el sistema crea el registro con `tenant_id` del JWT, retorna HTTP 201 y el objeto creado

#### Scenario: Acceso denegado sin permiso

- **WHEN** un usuario SIN permiso `estructura:gestionar` envía POST `/api/fechas-academicas`
- **THEN** el sistema retorna HTTP 403

#### Scenario: Tipo inválido rechazado

- **WHEN** se envía POST `/api/fechas-academicas` con `tipo` fuera del enum definido
- **THEN** el sistema retorna HTTP 422

---

### Requirement: Listar fechas académicas

El sistema SHALL permitir listar las fechas académicas activas del tenant, con filtros opcionales por materia y cohorte.

#### Scenario: Listado por tenant

- **WHEN** un usuario autenticado envía GET `/api/fechas-academicas`
- **THEN** el sistema retorna solo las fechas del tenant del usuario, excluyendo soft-deleted

#### Scenario: Filtro por materia_id

- **WHEN** se envía GET `/api/fechas-academicas?materia_id={uuid}`
- **THEN** el sistema retorna solo las fechas de esa materia dentro del tenant

#### Scenario: Aislamiento multi-tenant

- **WHEN** existen fechas académicas de dos tenants distintos en la DB
- **THEN** cada usuario solo ve las fechas de su propio tenant

---

### Requirement: Soft delete de fecha académica

El sistema SHALL permitir marcar una fecha académica como eliminada sin borrarla físicamente.

#### Scenario: Soft delete exitoso

- **WHEN** un usuario con permiso `estructura:gestionar` envía DELETE `/api/fechas-academicas/{id}`
- **THEN** el sistema establece `deleted_at` con el timestamp actual y retorna HTTP 204

#### Scenario: Fecha soft-deleted no aparece en listados

- **WHEN** una fecha tiene `deleted_at` no nulo
- **THEN** no aparece en GET `/api/fechas-academicas`
