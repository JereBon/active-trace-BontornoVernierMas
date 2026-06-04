## 1. Scaffold del proyecto frontend

- [x] 1.1 Crear `frontend/package.json` con todas las dependencias (react 18, typescript, vite, tailwindcss, react-router-dom v6, @tanstack/react-query v5, axios, react-hook-form, zod, @hookform/resolvers)
- [x] 1.2 Crear `frontend/tsconfig.json` y `frontend/tsconfig.node.json` con path alias `@/` → `src/`
- [x] 1.3 Crear `frontend/vite.config.ts` con alias `@/`, plugin react, y puerto 5173
- [x] 1.4 Crear `frontend/tailwind.config.ts` y `frontend/postcss.config.js`
- [x] 1.5 Crear `frontend/index.html` con el punto de entrada Vite
- [ ] 1.6 Crear `frontend/.env.example` con `VITE_API_BASE_URL=http://localhost:8000` ⚠️ dotfile — crear manualmente: `echo "VITE_API_BASE_URL=http://localhost:8000" > frontend/.env.example`
- [ ] 1.7 Crear `frontend/.gitignore` (node_modules, dist, .env.local) ⚠️ dotfile — crear manualmente (ver contenido abajo)

## 2. Estructura de directorios y archivos base

- [x] 2.1 Crear `frontend/src/main.tsx` (punto de entrada React, monta `<App />`)
- [x] 2.2 Crear `frontend/src/App.tsx` (providers: QueryClientProvider + AuthProvider + BrowserRouter + Routes)
- [x] 2.3 Crear `frontend/src/index.css` con directivas Tailwind (`@tailwind base/components/utilities`)
- [x] 2.4 Crear la estructura vacía de carpetas: `src/features/auth/{components,hooks,services,types,pages}` y `src/shared/{services,components,utils}`

## 3. Cliente HTTP centralizado

- [x] 3.1 Crear `frontend/src/shared/services/api.ts` — instancia Axios con `baseURL: import.meta.env.VITE_API_BASE_URL`, interceptor de request que agrega `Authorization: Bearer <token>` desde módulo en memoria
- [x] 3.2 Agregar interceptor de respuesta en `api.ts` — captura 401, ejecuta refresh, encola requests concurrentes, reintenta con nuevo token; si refresh falla, limpia sesión y redirige a `/login`
- [x] 3.3 Exponer funciones `setAccessToken(token: string | null)` y `getAccessToken(): string | null` en `api.ts` para gestión del token en memoria

## 4. Auth context y hook de sesión

- [x] 4.1 Crear `frontend/src/features/auth/types/auth.types.ts` — interfaces `User`, `LoginRequest`, `LoginResponse`, `RefreshResponse`, `AuthChallenge`
- [x] 4.2 Crear `frontend/src/features/auth/hooks/useAuth.ts` — React Context + hook `useAuth()` que expone `user`, `isAuthenticated`, `login()`, `logout()`, `isLoading`
- [x] 4.3 Crear `frontend/src/features/auth/services/authService.ts` — funciones `loginApi(req)` y `refreshApi()` usando el cliente centralizado

## 5. Login page

- [x] 5.1 Crear `frontend/src/features/auth/pages/LoginPage.tsx` — formulario con React Hook Form + Zod (validación email required, password required ≥1 char)
- [x] 5.2 Conectar submit del formulario a `useAuth().login()`, mostrar error del servidor en campo `root`
- [x] 5.3 Manejar respuesta de challenge 2FA: si el backend responde `{challenge: "2fa_required"}`, mostrar `TwoFaChallengePlaceholder`
- [x] 5.4 Crear `frontend/src/features/auth/components/TwoFaChallengePlaceholder.tsx` — pantalla scaffold con campo TOTP y mensaje "2FA — próximamente"
- [x] 5.5 Redirigir a `/dashboard` (o al `next` param) tras login exitoso

## 6. Auth Guard y Shell

- [x] 6.1 Crear `frontend/src/features/auth/components/AuthGuard.tsx` — si `!isAuthenticated && !isLoading`, redirige a `/login?next=<pathname>`; si `isLoading`, muestra spinner
- [x] 6.2 Crear `frontend/src/shared/components/AppShell.tsx` — layout con navbar top, sidebar placeholder y `<Outlet />`
- [x] 6.3 Crear `frontend/src/shared/components/Navbar.tsx` — logo "activia-trace", nombre del usuario autenticado y botón logout
- [x] 6.4 Crear `frontend/src/shared/components/Spinner.tsx` — componente de loading genérico

## 7. Routing

- [x] 7.1 Definir las rutas en `App.tsx`: `/login` → `LoginPage`, resto → `AuthGuard` + `AppShell` + `<Outlet />` con ruta `/dashboard` placeholder
- [x] 7.2 Crear `frontend/src/features/dashboard/pages/DashboardPage.tsx` — página placeholder "Dashboard — próximamente"

## 8. Integración final y revisión

- [x] 8.1 Verificar que todos los imports usan path alias `@/` (no rutas relativas profundas)
- [x] 8.2 Verificar que no hay uso de `any` en TypeScript
- [x] 8.3 Verificar que todos los componentes usan PascalCase y son function components
- [x] 8.4 Verificar que el Zod schema del login tiene `extra: forbid` equivalente (no campos extra aceptados)
- [x] 8.5 Agregar instrucciones de setup en `frontend/README.md` (`npm install`, `cp .env.example .env.local`, `npm run dev`)

---

### Dotfiles pendientes (crear manualmente)

**`frontend/.env.example`**:
```
VITE_API_BASE_URL=http://localhost:8000
```

**`frontend/.gitignore`**:
```
node_modules/
dist/
.env.local
.env.*.local
*.log
.DS_Store
```
