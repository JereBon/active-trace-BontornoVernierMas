## Context

El shell SPA (C-21) provee: cliente HTTP Axios con JWT automático, AuthContext con roles, AppShell con navegación, AuthGuard para rutas protegidas, y la estructura feature-based `features/{name}/{components,hooks,services,types,pages}`. El backend (C-10/C-11/C-12) expone 12 endpoints REST completamente probados para calificaciones, análisis y comunicaciones.

## Goals / Non-Goals

**Goals:**
- Entregar la feature `comision` completa para el rol PROFESOR operando sobre una materia específica.
- Mantener la coherencia con los patrones ya establecidos en `features/auth` y `features/dashboard`.
- Toda la comunicación HTTP pasa por `@/shared/services/api` (Axios centralizado).
- Cobertura de tests de componentes e integración con mocks de API.

**Non-Goals:**
- No modificar el backend ni los schemas de BD.
- No implementar roles COORDINADOR o ADMIN (esos van en C-23/C-24).
- No implementar funcionalidades de liquidaciones, equipos ni coloquios.
- No construir gráficos interactivos avanzados (D3, recharts) — solo tablas y badges de estado.

## Decisions

### D1 — Estructura feature única `comision/`

Se agrupa todo bajo `features/comision/` en lugar de crear una feature por sub-módulo (`importacion/`, `analisis/`, `comunicacion/`). Razón: todas las vistas comparten el parámetro de ruta `materiaId` y el contexto de una asignación docente. Una feature única evita duplicación de contexto y simplifica las rutas.

Alternativa descartada: features separadas. Generaría 4 carpetas con contexto duplicado y rutas más complejas sin beneficio real.

### D2 — Polling para tracking del lote de comunicaciones

La API de lotes no tiene WebSocket ni SSE. Se implementa polling con `refetchInterval` de TanStack Query (cada 3s, máximo 2min o hasta estado terminal: `Enviado`/`Fallido`/`Cancelado`).

Alternativa descartada: SSE. Requeriría cambios en el backend (fuera de scope).

### D3 — Formulario de comunicaciones con variables usando React Hook Form + Zod

El asunto y cuerpo pueden incluir variables `{nombre}`, `{materia}`, etc. La validación Zod solo verifica que los campos no estén vacíos. El botón "Preview" llama a `POST /v1/comunicaciones/preview` para validación server-side de variables. Los errores del backend se muestran inline.

### D4 — Export CSV sin librería externa

El export de "sin corregir" se construye en el cliente usando `Blob` + `URL.createObjectURL`. Los datos ya están en memoria (resultado de la query). No se agrega dependencia npm.

### D5 — Contexto de materia via parámetro de ruta

La ruta raíz de la feature es `/comision/:materiaId`. Todos los sub-hooks leen `materiaId` desde `useParams()`. No se usa Context API para el `materiaId` — el prop drilling es mínimo dado que cada página lo lee directamente de la URL.

### D6 — Mocks de API en tests con msw (si disponible) o vi.mock

Si `msw` está instalado, se usa para los tests de integración (handlers declarados en `src/__mocks__/handlers.ts`). Si no, se usa `vi.mock('@/shared/services/api')` directamente. El plan de implementación usa `vi.mock` para no agregar dependencias.

## Risks / Trade-offs

- [Polling agresivo en lotes] → Mitigación: stop automático al alcanzar estado terminal; el intervalo de 3s es razonable para el volumen esperado.
- [Tamaño de archivo LMS] → Mitigación: el backend valida el formato; el frontend solo muestra errores 422.
- [Sin paginación server-side en atrasados] → El endpoint devuelve todos los atrasados de la materia. Para materias grandes puede ser lento. Mitigación: paginación client-side con slice sobre el array.
- [Cambio de API de atrasados sin versionado] → Si el backend cambia la forma de `AtrasadoOut`, los tipos TypeScript del frontend fallarán en compilación. Mitigación: tipos definidos explícitamente en `features/comision/types/`.

## Migration Plan

1. Crear la feature `comision/` desde cero (no hay archivos previos).
2. Registrar las rutas en `App.tsx` y el enlace en `AppShell`.
3. No hay migraciones de BD ni cambios de schema.
4. Rollback: revertir `App.tsx` y eliminar `features/comision/` — sin efecto en el backend.
