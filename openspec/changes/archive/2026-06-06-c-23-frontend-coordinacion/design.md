## Context

El frontend de active-trace tiene implementado el shell base (C-21) y la feature `comision/` para el rol PROFESOR (C-22). El backend expone endpoints para equipos docentes (C-08), encuentros (C-13), coloquios (C-14), avisos (C-15), tareas (C-16) y fechas académicas (C-17). C-23 construye la feature `coordinacion/` para el rol COORDINADOR/ADMIN sobre ese backend ya disponible.

Stack: React 18 + TypeScript + TanStack Query + React Hook Form + Zod + Tailwind CSS + Axios centralizado en `@/shared/services/api`.

Patrón establecido (C-22): `features/{nombre}/{types,services,hooks,components,pages}` — cada sub-feature con su propio service (funciones puras), hooks TanStack Query, componentes < 200 LOC y tests Vitest + Testing Library.

## Goals / Non-Goals

**Goals:**
- Crear `frontend/src/features/coordinacion/` con sub-features: equipos, avisos, tareas, encuentros, coloquios, monitor, cuatrimestre.
- Cada sub-feature: types → service → hook → componentes → página.
- Tests TDD para componentes críticos (ABM equipos, publicación de aviso, workflow de tarea, filtros de monitor).
- Rutas `/coordinacion/*` en `App.tsx` + nav items en `AppShell.tsx` visibles para COORDINADOR/ADMIN.
- Export CSV de equipos (client-side, sin nuevo endpoint).
- Clonar equipo de cuatrimestre anterior (1 llamada `POST /v1/equipos-docentes/clonar`).

**Non-Goals:**
- No se crean endpoints nuevos de backend.
- No se implementa impersonación ni cambio de tenant.
- No se incluye C-24 (finanzas/admin).
- No se construye lógica de cálculo de liquidaciones.

## Decisions

### D-01: Estructura como feature única con sub-carpetas por dominio
**Decisión**: `features/coordinacion/` con sub-carpetas `equipos/`, `avisos/`, `tareas/`, `encuentros/`, `coloquios/`, `monitor/`, `cuatrimestre/`.
**Rationale**: Agrupa por rol (COORDINADOR), no por entidad backend. Evita dispersar rutas. Sigue el mismo patrón que `features/comision/` (C-22).
**Alternativa descartada**: Una feature por entidad (`features/equipos/`, `features/avisos/`...) — generaría 7 carpetas top-level sin relación de rol explícita.

### D-02: Servicios separados por sub-feature
**Decisión**: `coordinacion/services/equiposService.ts`, `avisosService.ts`, `tareasService.ts`, etc. — funciones puras que importan `api` de `@/shared/services/api`.
**Rationale**: Aísla la superficie de API por dominio. Facilita mocking en tests (patrón de C-22).
**Alternativa descartada**: Un único `coordinacionService.ts` — demasiado grande, dificulta tree-shaking y tests unitarios.

### D-03: Export CSV client-side
**Decisión**: La exportación de equipos se genera en el navegador con `Array.join()` + `Blob` + `URL.createObjectURL`. Sin endpoint `/export` en backend.
**Rationale**: El volumen de datos (equipos docentes por tenant) es bajo. No justifica un endpoint dedicado. Menor superficie de ataque.
**Alternativa descartada**: Endpoint `GET /v1/equipos-docentes/export.csv` — overhead innecesario para volúmenes pequeños.

### D-04: Visibilidad de nav por rol desde JWT claims
**Decisión**: `AppShell` lee `useAuth()` para obtener los roles del usuario y muestra/oculta el ítem de Coordinación.
**Rationale**: El control de acceso visual debe reflejar el RBAC del backend. El token JWT ya contiene `roles[]`.
**Alternativa descartada**: Mostrar siempre el menú y dejar que el backend retorne 403 — mala UX y expone rutas a roles no autorizados.

### D-05: Asistente de cuatrimestre como stepper en página única
**Decisión**: `CuatrimestrePage` implementa un stepper de 3 pasos: (1) materias/cohortes, (2) equipos base, (3) confirmación. Sin modal wizard externo.
**Rationale**: Flujo FL-03 es lineal; un stepper inline es más accesible que un modal multilayer. Sin dependencias adicionales (ya existe Tailwind).

### D-06: Paginación client-side para tablas de coordinación
**Decisión**: Las tablas (equipos, avisos, tareas) paginan localmente (PAGE_SIZE=20). Los endpoints ya filtran por tenant; el volumen por tenant es acotado.
**Rationale**: Consistente con patrón de C-22 (`TablaAtrasados`). Evita complejidad de cursor/offset pagination en frontend sin cambiar el backend.

## Risks / Trade-offs

- **[Risk] Endpoints C-14 (coloquios) no verificados en staging** → Mitigation: los tipos TypeScript se derivan del schema Pydantic; si hay discrepancia, el componente muestra error de red y el test unitario mockea el servicio para no bloquear.
- **[Risk] El hook `useAuth()` puede no exponer `roles[]` directamente** → Mitigation: leer `frontend/src/features/auth/hooks/useAuth.ts` antes de implementar `AppShell`; si no expone roles, extenderlo para parsear el JWT claim `roles`.
- **[Risk] Clonar equipo falla si el endpoint no existe aún** → Mitigation: el botón "Clonar" quedará deshabilitado con tooltip "Próximamente" si `POST /v1/equipos-docentes/clonar` devuelve 404 al primer intento.
- **[Trade-off] Export CSV client-side limita a datos ya cargados en memoria** → Aceptado: para el volumen actual (< 500 docentes por tenant) es suficiente.
