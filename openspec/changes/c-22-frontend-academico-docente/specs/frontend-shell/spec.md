## MODIFIED Requirements

### Requirement: AppShell expone navegación a las features habilitadas para el rol
El sistema SHALL mostrar en la navegación lateral los enlaces disponibles para el rol autenticado. Con C-22, los usuarios con roles PROFESOR o COORDINADOR MUST ver un enlace a "Comisión" que lleva a `/comision/:materiaId` (o al selector de materia si no hay materiaId activo).

#### Scenario: PROFESOR ve enlace a Comisión
- **WHEN** un usuario con rol PROFESOR está autenticado y ve el AppShell
- **THEN** el menú lateral incluye el ítem "Comisión" con icono y enlace a la sección de comisión

#### Scenario: App.tsx registra rutas de comisión
- **WHEN** el router de la aplicación está inicializado
- **THEN** las rutas `/comision/:materiaId` y sus sub-rutas están registradas y protegidas por AuthGuard
