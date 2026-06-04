## ADDED Requirements

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
