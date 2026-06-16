# activia-trace — Frontend

SPA React 18 + TypeScript + Vite para la plataforma activia-trace.

## Setup

```bash
# 1. Instalar dependencias
npm install

# 2. Configurar variables de entorno
cp .env.example .env.local
# Editar .env.local si el backend corre en un puerto diferente a 8000

# 3. Levantar servidor de desarrollo
npm run dev
# Disponible en http://localhost:5173
```

## Stack

| Componente | Tecnología |
|---|---|
| Framework | React 18 + TypeScript |
| Bundler | Vite 5 |
| Estilos | Tailwind CSS v3 |
| Routing | React Router v6 |
| Server state | TanStack Query v5 |
| HTTP client | Axios (centralizado en `src/shared/services/api.ts`) |
| Forms | React Hook Form + Zod |

## Estructura

```
src/
  features/
    auth/            # Login, AuthGuard, sesión JWT
      components/    # AuthGuard, TwoFaChallengePlaceholder
      hooks/         # useAuth (AuthContext + Provider)
      pages/         # LoginPage
      services/      # authService (loginApi, refreshApi)
      types/         # auth.types.ts
    dashboard/       # Placeholder — módulos futuros siguen este patrón
      pages/
  shared/
    components/      # AppShell, Navbar, Spinner
    services/        # api.ts (cliente Axios centralizado)
    utils/           # utilidades transversales
```

## Variables de entorno

| Variable | Descripción | Default |
|---|---|---|
| `VITE_API_BASE_URL` | URL base del backend FastAPI | `http://localhost:8000` |
