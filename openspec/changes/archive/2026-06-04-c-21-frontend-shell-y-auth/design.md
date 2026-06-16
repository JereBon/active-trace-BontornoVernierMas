## Context

El sistema ya tiene un backend FastAPI multi-tenant con autenticación JWT (access token de vida corta + refresh rotation). El frontend parte de cero: no existe ningún archivo en `frontend/`. Este change establece la fundación de la SPA que usarán todos los módulos de negocio futuros (C-22 en adelante). El stack elegido (React 18 + TypeScript + Vite + Tailwind + TanStack Query + React Router v6 + Axios) ya está definido en la KB y en CLAUDE.md.

## Goals / Non-Goals

**Goals:**
- Proyecto frontend completamente scaffolded y listo para desarrollo
- Cliente HTTP centralizado con interceptor JWT y refresh silencioso
- Login page funcional conectada al backend
- Auth Guard que protege todas las rutas excepto `/login`
- Estructura feature-based lista para recibir nuevos módulos
- Sin tests de frontend en este change (los E2E van en changes posteriores)

**Non-Goals:**
- Build/bundle productivo (no ejecutar npm build)
- Tests automatizados (Playwright va en change posterior)
- Módulos de negocio (alumnos, materias, etc.)
- Flujo de 2FA completo (solo scaffold del challenge para el futuro)

## Decisions

### D-01: Vite como bundler (no CRA)
CRA está deprecated. Vite tiene HMR más rápido, primera clase TypeScript, y es el estándar actual del stack indicado en CLAUDE.md.

### D-02: TanStack Query v5 para server state
Todo fetch que va al backend pasa por hooks de `services/`. TanStack Query v5 gestiona cache, loading states y background refetch. El `QueryClient` vive en `App.tsx` wrapeando el árbol completo.

### D-03: Estado de autenticación en memoria + localStorage
- `accessToken`: en memoria (variable de módulo en `api.ts`) — más seguro que localStorage contra XSS
- `refreshToken`: en `localStorage` con key `rt` — necesario para persistir sesión entre tabs/recargas
- `user` / `tenant`: en un React Context (`AuthContext`) para acceso reactivo desde componentes

### D-04: Interceptor de refresh silencioso en Axios
El interceptor de respuesta captura 401, llama a `POST /api/auth/refresh`, actualiza el `accessToken` en memoria y reinicia la request original. Se usa una queue para evitar race conditions de refresh múltiple concurrente. Si el refresh falla, se limpia el estado y se redirige a `/login`.

### D-05: Estructura feature-based desde el inicio
Cada feature sigue: `features/{name}/{components,hooks,services,types,pages}`. El módulo `auth` es el primero. `shared/` contiene lo transversal (cliente HTTP, componentes UI genéricos, utils). Esta estructura escala horizontalmente sin reorganización.

### D-06: React Router v6 con layout anidado
Rutas protegidas anidadas bajo un `<AuthGuard>` que actúa como layout. Si no hay sesión, `<Navigate to="/login" replace />`. Si hay sesión en `/login`, redirige a `/dashboard`. El shell tiene un `<Outlet />` para los módulos futuros.

### D-07: Formulario de login con React Hook Form + Zod
Validación en cliente con Zod schema. Los errores del servidor se mapean al campo `root` del form. Sin estados de formulario ad-hoc.

## Risks / Trade-offs

- [Refresh concurrente] Si múltiples requests fallan con 401 simultáneamente, solo el primero ejecuta el refresh; los demás esperan en cola → Mitigación: flag `isRefreshing` + array de callbacks resueltos tras el refresh exitoso.
- [accessToken en memoria se pierde al recargar] → Mitigación: al recargar, el interceptor intenta el refresh automáticamente antes de fallar; si el refreshToken en localStorage es válido, la sesión se recupera transparentemente.
- [Sin tests en este change] → Aceptado. Los tests E2E (Playwright) y unitarios de componentes van en el change de testing dedicado.

## Migration Plan

1. Crear `frontend/` con todos los archivos fuente manualmente (sin ejecutar npm)
2. El desarrollador ejecuta `npm install` + `npm run dev` para levantar el servidor de desarrollo
3. El frontend apunta a `http://localhost:8000` (variable `VITE_API_BASE_URL` en `.env.local`)
4. No hay migración de datos ni cambios al backend

## Open Questions

- Ninguna. El scope está completamente definido por las dependencias del backend (C-04 cerrado).
