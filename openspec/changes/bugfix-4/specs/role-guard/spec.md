## ADDED Requirements

### Requirement: AuthGuard verifica roles del usuario
El componente AuthGuard SHALL aceptar una prop opcional `requiredRoles: string[]`. Cuando se especifica, SHALL verificar que el usuario autenticado tenga al menos uno de los roles requeridos. Si no tiene ninguno, SHALL redirigir a `/dashboard`.

#### Scenario: Usuario sin rol requerido es redirigido
- **WHEN** un usuario autenticado sin rol ADMIN visita `/admin`
- **THEN** AuthGuard redirige a `/dashboard`

#### Scenario: Usuario con rol requerido accede sin problema
- **WHEN** un usuario autenticado con rol ADMIN visita `/admin`
- **THEN** AuthGuard renderiza el children sin redirigir

#### Scenario: AuthGuard sin requiredRoles se comporta como antes
- **WHEN** un usuario autenticado visita una ruta sin `requiredRoles`
- **THEN** AuthGuard renderiza el children sin verificar roles

### Requirement: Rutas protegidas por rol en App.tsx
Las rutas en App.tsx SHALL declarar los roles requeridos según el feature:
- `/admin/*` → requiere ADMIN
- `/finanzas/*` → requiere FINANZAS o ADMIN
- `/coordinacion/*` → requiere COORDINADOR o ADMIN
- `/comision/*` → requiere PROFESOR, TUTOR, COORDINADOR o ADMIN
- `/dashboard` → cualquier usuario autenticado

#### Scenario: ADMIN puede acceder a todas las rutas
- **WHEN** un usuario con rol ADMIN navega a cualquier ruta protegida
- **THEN** el acceso es concedido

#### Scenario: FINANZAS no puede acceder a /admin
- **WHEN** un usuario con rol FINANZAS navega a `/admin`
- **THEN** AuthGuard redirige a `/dashboard`
