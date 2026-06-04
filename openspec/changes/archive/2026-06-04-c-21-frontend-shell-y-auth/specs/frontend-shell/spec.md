## ADDED Requirements

### Requirement: Estructura de proyecto frontend
El sistema SHALL tener un proyecto frontend en `frontend/` con Vite + React 18 + TypeScript siguiendo la estructura feature-based: `src/features/{name}/{components,hooks,services,types,pages}` y `src/shared/{services,components,utils}`.

#### Scenario: Estructura de directorios presente
- **WHEN** se inspecciona el directorio `frontend/src/`
- **THEN** existen las carpetas `features/auth/`, `shared/services/`, y `shared/components/`

### Requirement: Cliente HTTP centralizado
El sistema SHALL tener un único cliente Axios en `src/shared/services/api.ts` que agregue automáticamente el header `Authorization: Bearer <token>` a todas las requests cuando hay una sesión activa, apuntando a `VITE_API_BASE_URL`.

#### Scenario: Request autenticada
- **WHEN** se hace cualquier llamada usando el cliente centralizado y hay un access token en memoria
- **THEN** la request incluye el header `Authorization: Bearer <token>`

#### Scenario: Request sin sesión
- **WHEN** se hace una llamada usando el cliente y no hay access token
- **THEN** la request se envía sin header Authorization

### Requirement: Auth Guard para rutas protegidas
El sistema SHALL proteger todas las rutas excepto `/login` con un `AuthGuard`. Cualquier acceso a ruta protegida sin sesión activa MUST redirigir a `/login` con la ruta original como `next` parameter para restaurar la navegación post-login.

#### Scenario: Acceso a ruta protegida sin sesión
- **WHEN** el usuario navega a cualquier ruta protegida sin estar autenticado
- **THEN** es redirigido a `/login?next=<ruta-original>`

#### Scenario: Acceso a ruta protegida con sesión válida
- **WHEN** el usuario navega a una ruta protegida con sesión activa
- **THEN** la ruta se renderiza normalmente

### Requirement: Shell layout principal
El sistema SHALL tener un layout shell (`AppShell`) con navbar, sidebar placeholder y un `<Outlet />` para los módulos futuros. El layout MUST estar disponible para todas las rutas protegidas.

#### Scenario: Shell renderiza contenido de módulo
- **WHEN** el usuario autenticado navega a una ruta protegida
- **THEN** el contenido de la ruta se renderiza dentro del `<Outlet />` del AppShell

### Requirement: Providers globales
El sistema SHALL configurar `QueryClientProvider` (TanStack Query v5) y `AuthProvider` como providers globales en `App.tsx`, disponibles para todos los componentes del árbol.

#### Scenario: QueryClient disponible globalmente
- **WHEN** cualquier componente dentro del árbol llama a `useQuery` o `useMutation`
- **THEN** tiene acceso al `QueryClient` global sin configuración adicional
