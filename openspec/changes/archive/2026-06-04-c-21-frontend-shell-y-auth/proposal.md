## Why

El backend de autenticación (C-04) está completo y operativo, pero no existe ninguna interfaz de usuario para que los usuarios accedan al sistema. Se necesita la SPA shell con React 18 + TypeScript que sirva como punto de entrada visual de activia-trace: login, guard de rutas y cliente HTTP centralizado listo para integrar todos los módulos de frontend que vienen en fases posteriores.

## What Changes

- **Nuevo**: proyecto frontend en `frontend/` con Vite + React 18 + TypeScript
- **Nuevo**: estructura de carpetas feature-based (`features/{name}/{components,hooks,services,types,pages}`)
- **Nuevo**: cliente HTTP centralizado (`src/shared/services/api.ts`) con Axios, interceptor de JWT y refresh automático silencioso
- **Nuevo**: página de Login (`features/auth/pages/LoginPage.tsx`) con formulario email + password (React Hook Form + Zod)
- **Nuevo**: Auth Guard (`features/auth/components/AuthGuard.tsx`) que redirige a `/login` si no hay sesión activa
- **Nuevo**: Shell layout principal con React Router v6 y rutas protegidas
- **Nuevo**: store de sesión (`features/auth/hooks/useAuth.ts`) que gestiona tokens y estado de usuario en memoria/localStorage
- **Nuevo**: configuración base de Tailwind CSS, TanStack Query v5 y React Router v6

## Capabilities

### New Capabilities
- `frontend-auth`: Login page, auth guard, gestión de sesión JWT (access token + refresh rotation), interceptor HTTP, manejo de challenge 2FA (reservado para futuro, scaffolded).
- `frontend-shell`: SPA shell, layout principal, React Router, TanStack Query provider, Tailwind, estructura feature-based.

### Modified Capabilities

## Impact

- Crea el directorio `frontend/` con todos los archivos fuente (sin ejecutar build)
- Depende de `POST /api/auth/login` y `POST /api/auth/refresh` del backend (C-04)
- No afecta el backend ni la base de datos
- Habilita el desarrollo paralelo de todos los módulos de frontend (C-22 en adelante)
