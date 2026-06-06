## Why

El backend de activia-trace está completo hasta C-12 (camino crítico cerrado: calificaciones, análisis de atrasados, comunicaciones con worker). El rol PROFESOR carece de interfaz para operar sobre esos datos: no puede importar calificaciones, ver atrasados, ni enviar comunicaciones desde el SPA. C-22 cierra ese gap entregando la feature frontend del flujo académico-docente completa sobre el shell ya existente (C-21).

## What Changes

- Nueva feature `comision` en `frontend/src/features/comision/` con páginas, hooks, servicios y tipos propios.
- Flujo de **importación de calificaciones**: upload de archivo LMS, preview de actividades detectadas, selección de actividades a importar, confirmación.
- **Configuración de umbral** por materia/asignación (formulario Zod + React Hook Form).
- **Vista de atrasados**: tabla de alumnos con actividades pendientes/reprobadas, paginación, filtros.
- **Ranking** de aprobados por actividad y **notas finales** por alumno.
- **Reporte rápido** de métricas agregadas de la materia.
- **Entregas sin corregir**: listado + export CSV.
- **Comunicación a atrasados**: formulario de asunto/cuerpo con variables, preview renderizado, envío al worker, tracking de estado del lote en tiempo real (polling).
- **Monitor de seguimiento**: tabla con filtros por materia, comisión, regional, nombre; scroll y paginación.
- Rutas nuevas registradas en `App.tsx`: `/comision/:materiaId/*`.
- Tests de componentes e integración con mocks de API (Vitest + Testing Library).

## Capabilities

### New Capabilities

- `calificaciones-import-ui`: Flujo de importación de calificaciones desde el frontend (upload → preview → selección → confirm).
- `atrasados-ui`: Vista de tabla de atrasados con filtros, ranking, notas finales y reporte.
- `sin-corregir-ui`: Listado de entregas sin corregir con export CSV.
- `comunicacion-docente-ui`: Formulario de comunicación a atrasados, preview, envío y tracking de estado del lote.
- `monitor-ui`: Monitor de seguimiento de alumnos con filtros combinados.

### Modified Capabilities

- `frontend-shell`: Se agregan rutas `/comision/:materiaId/*` en `App.tsx` y un enlace en la navegación lateral del `AppShell`.

## Impact

- **Archivos nuevos**: todo bajo `frontend/src/features/comision/` (componentes, hooks, servicios, tipos, páginas) y sus tests en `frontend/src/features/comision/__tests__/`.
- **Archivos modificados**: `frontend/src/App.tsx` (nuevas rutas), `frontend/src/shared/components/AppShell.tsx` (enlace nav).
- **APIs consumidas** (backend ya disponible):
  - `POST /v1/calificaciones/{materia_id}/preview`
  - `POST /v1/calificaciones/{materia_id}/importar`
  - `PUT  /v1/calificaciones/{materia_id}/umbral`
  - `GET  /v1/analisis/atrasados?materia_id=`
  - `GET  /v1/analisis/ranking?materia_id=`
  - `GET  /v1/analisis/notas-finales?materia_id=`
  - `GET  /v1/analisis/reporte-materia?materia_id=`
  - `GET  /v1/analisis/sin-corregir?materia_id=`
  - `GET  /v1/analisis/monitor`
  - `POST /v1/comunicaciones/preview`
  - `POST /v1/comunicaciones/encolar`
  - `GET  /v1/comunicaciones/lotes/{lote_id}`
- **Sin cambios de schema ni migraciones de BD** — feature puramente frontend.
- **Dependencias de paquetes**: ninguna nueva (Vitest + Testing Library ya declarados en el shell).
