## ADDED Requirements

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
