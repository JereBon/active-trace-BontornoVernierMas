## ADDED Requirements

### Requirement: Sidebar navigation items
El componente AppShell SHALL mostrar ítems de navegación diferenciados por rol del usuario autenticado.

#### Scenario: COORDINADOR/ADMIN ve sección de Coordinación
- **WHEN** el usuario autenticado tiene rol COORDINADOR o ADMIN
- **THEN** el sidebar muestra los ítems: "Equipos", "Avisos", "Tareas", "Monitor", "Encuentros", "Coloquios", "Cuatrimestre" bajo la sección "Coordinación"

#### Scenario: PROFESOR no ve sección de Coordinación
- **WHEN** el usuario autenticado tiene solo rol PROFESOR
- **THEN** el sidebar NO muestra los ítems de coordinación

#### Scenario: Usuario sin rol específico ve solo Dashboard
- **WHEN** el usuario autenticado no tiene rol COORDINADOR ni ADMIN ni PROFESOR
- **THEN** el sidebar muestra solo el ítem "Dashboard"
