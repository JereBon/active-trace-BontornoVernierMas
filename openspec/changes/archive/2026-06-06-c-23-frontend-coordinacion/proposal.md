## Why

El COORDINADOR/ADMIN carece de interfaces de gestión en el frontend: no puede administrar equipos docentes, publicar avisos, gestionar tareas internas ni monitorear el estado general de las comisiones. La capa backend de C-08, C-13, C-14, C-15, C-16 y C-17 está completamente disponible; falta la capa de presentación que habilite el rol de coordinación operativa de la plataforma.

## What Changes

- **Feature `coordinacion/equipos`**: ABM de equipos docentes (crear, editar, dar de baja, clonar cuatrimestre anterior, asignación masiva, export CSV). Consume endpoints `C-08`.
- **Feature `coordinacion/avisos`**: ABM de avisos con scope (global/materia/cohorte/rol), severidad, vigencia y requiere_ack. Visualización segmentada. Consume `C-15`.
- **Feature `coordinacion/tareas`**: Lista de tareas, crear+asignar, cambio de estado (state machine), delegar, hilo de comentarios, filtros admin. Consume `C-16`.
- **Feature `coordinacion/monitor`**: Vista global de comisiones (F2.7) y resumen ejecutivo (F2.9). Consume análisis existente.
- **Feature `coordinacion/encuentros`**: Gestión de slots e instancias de encuentros. Consume `C-13`.
- **Feature `coordinacion/coloquios`**: Gestión de convocatorias y turnos de coloquios. Consume `C-14`.
- **Feature `coordinacion/cuatrimestre`**: Asistente FL-03 para configurar un nuevo cuatrimestre (materias, cohortes, equipos). Consume `C-06`, `C-17`.
- **Routing**: Nuevas rutas `/coordinacion/*` en `App.tsx`.
- **AppShell**: Nuevos ítems de navegación de coordinación con visibilidad por rol.

## Capabilities

### New Capabilities

- `frontend-coordinacion`: UI completa del rol COORDINADOR/ADMIN — equipos docentes, avisos, tareas internas, monitor global, encuentros admin, coloquios, asistente de cuatrimestre.

### Modified Capabilities

- `frontend-shell`: Se agrega sección de navegación para rutas `/coordinacion/*` con control de visibilidad por rol COORDINADOR/ADMIN.

## Impact

- **Archivos nuevos**: `frontend/src/features/coordinacion/{types,services,hooks,components,pages}/`
- **Archivos modificados**: `frontend/src/App.tsx` (nuevas rutas), `frontend/src/shared/components/AppShell.tsx` (nav items)
- **APIs consumidas**: `/v1/equipos-docentes/*`, `/v1/avisos/*`, `/v1/tareas/*`, `/v1/encuentros/*`, `/v1/coloquios/*`, `/v1/analisis/monitor`
- **Sin cambios de backend**: C-23 es puramente frontend. El backend ya expone todos los endpoints necesarios.
- **Dependencias**: `C-08`, `C-13`, `C-14`, `C-15`, `C-16`, `C-17` (backend), `C-21` (frontend shell base)
