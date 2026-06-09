## Purpose
Gestionar asignaciones de usuarios a roles dentro de contextos académicos con vigencia temporal, garantizando aislamiento multi-tenant y control de permisos efectivos basado en fechas.
## Requirements
### Requirement: Modelo de asignación usuario-rol-contexto
El sistema SHALL persistir asignaciones que vinculan un usuario con un rol dentro de un contexto académico (materia, carrera y/o cohorte), con vigencia temporal (desde/hasta).

#### Scenario: Asignación con contexto académico
- **WHEN** se crea una asignación con `usuario_id`, `rol`, `materia_id` y `desde`
- **THEN** el sistema persiste la asignación con `tenant_id` del contexto actual y la asignación es visible en el historial

#### Scenario: Asignación sin contexto académico (alcance tenant)
- **WHEN** se crea una asignación con `usuario_id`, `rol = ADMIN` y sin `materia_id`/`carrera_id`/`cohorte_id`
- **THEN** el sistema persiste la asignación con alcance de tenant global

### Requirement: Vigencia de asignaciones
Una asignación vencida (`hasta < fecha actual`) SHALL ser conservada en el histórico pero NO SHALL otorgar permisos efectivos al usuario.

#### Scenario: Asignación vigente otorga permisos
- **WHEN** un usuario tiene una asignación con `hasta IS NULL` o `hasta >= hoy`
- **THEN** los permisos del rol de esa asignación son efectivos para el usuario

#### Scenario: Asignación vencida no otorga permisos
- **WHEN** un usuario tiene una asignación con `hasta < hoy`
- **THEN** los permisos de ese rol NO son efectivos, y el usuario recibe 403 si intenta usar esos permisos

#### Scenario: Historial preservado
- **WHEN** una asignación vence
- **THEN** el registro permanece en la base de datos con sus datos originales intactos

### Requirement: Aislamiento multi-tenant de asignaciones
El sistema SHALL garantizar que las asignaciones de un tenant nunca sean visibles ni accesibles desde otro tenant.

#### Scenario: Query con scope de tenant
- **WHEN** se consultan asignaciones de un usuario
- **THEN** el sistema filtra por `tenant_id` derivado de la sesión autenticada, nunca por parámetro de la petición

### Requirement: Listado de asignaciones con filtros opcionales
El sistema SHALL soportar consultas de asignaciones con filtros opcionales por materia, carrera, cohorte, usuario, rol y estado de vigencia. Todos los queries SHALL filtrar por `tenant_id` del contexto de sesión.

#### Scenario: Listado sin filtros retorna todas las asignaciones del tenant
- **WHEN** se consulta la lista de asignaciones sin parámetros adicionales
- **THEN** el sistema retorna todas las asignaciones no eliminadas del tenant de la sesión

#### Scenario: Filtro por cohorte acota el resultado
- **WHEN** se consulta con `cohorte_id=<uuid>`
- **THEN** el sistema retorna solo asignaciones donde `cohorte_id` coincide y `tenant_id` es el del tenant de la sesión

#### Scenario: Filtro `solo_vigentes=true` excluye asignaciones vencidas
- **WHEN** se consulta con `solo_vigentes=true`
- **THEN** el sistema retorna solo asignaciones donde `hasta IS NULL OR hasta >= fecha_actual`

### Requirement: Operación masiva de creación de asignaciones
El sistema SHALL soportar la creación en bloque de múltiples asignaciones en una sola transacción. Si alguna asignación ya existe (mismo usuario, rol, contexto), SHALL omitirla sin abortar la transacción.

#### Scenario: Bulk create con lista válida
- **WHEN** se solicita crear N asignaciones con contexto académico y vigencia válidos
- **THEN** el sistema persiste todas las asignaciones nuevas en una sola transacción y retorna los registros creados

#### Scenario: Idempotencia en bulk create
- **WHEN** una de las asignaciones de la lista ya existe con los mismos `usuario_id`, `rol`, `materia_id`, `carrera_id`, `cohorte_id`
- **THEN** el sistema omite esa asignación sin abortar y continúa con las restantes

### Requirement: Operación de clonado de equipo
El sistema SHALL soportar la duplicación de un conjunto de asignaciones desde un cohorte origen a un cohorte destino, reemplazando `cohorte_id` y las fechas de vigencia en cada registro duplicado.

#### Scenario: Clonado produce nuevas instancias independientes
- **WHEN** se clona un equipo de cohorte A a cohorte B
- **THEN** cada asignación clonada es un registro nuevo con un `id` distinto, `cohorte_id = cohorte_B`, `desde` y `hasta` del período destino, manteniendo `usuario_id`, `rol`, `materia_id`, `carrera_id`, `comisiones` y `responsable_id` del original

#### Scenario: Las asignaciones origen no son modificadas por el clonado
- **WHEN** se clona un equipo
- **THEN** las asignaciones del equipo origen permanecen sin cambios

### Requirement: Modificación masiva de fechas de vigencia
El sistema SHALL soportar la actualización atómica de `desde` y `hasta` en un conjunto de asignaciones identificadas por su equipo (materia × carrera × cohorte).

#### Scenario: Actualización atómica de vigencia de equipo
- **WHEN** se solicita la modificación masiva con `materia_id`, `carrera_id`, `cohorte_id`, `desde`, `hasta`
- **THEN** el sistema actualiza en una sola transacción todas las asignaciones no eliminadas del equipo y retorna la cantidad de filas afectadas

#### Scenario: Equipo inexistente retorna cero filas afectadas
- **WHEN** se solicita modificación masiva para un equipo que no tiene asignaciones activas
- **THEN** el sistema retorna `{"filas_afectadas": 0}` sin error

