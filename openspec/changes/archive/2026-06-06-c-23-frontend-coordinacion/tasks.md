## 1. Tipos TypeScript (coordinacion/types)

- [ ] 1.1 Crear `frontend/src/features/coordinacion/types/index.ts` con interfaces: `EquipoDocente`, `EquipoDocenteCreate`, `EquipoDocenteUpdate`, `Aviso`, `AvisoCreate`, `Tarea`, `TareaCreate`, `TareaUpdate`, `ComentarioTarea`, `EncuentroAdmin`, `ColoquioConvocatoria`

## 2. Servicios HTTP (coordinacion/services)

- [ ] 2.1 Crear `equiposService.ts`: `getEquipos`, `createEquipo`, `updateEquipo`, `deleteEquipo`, `clonarEquipo`
- [ ] 2.2 Crear `avisosService.ts`: `getAvisos`, `createAviso`, `updateAviso`, `archivarAviso`
- [ ] 2.3 Crear `tareasService.ts`: `getTareas`, `createTarea`, `updateTarea`, `getComentarios`, `createComentario`
- [ ] 2.4 Crear `encuentrosService.ts`: `getEncuentros`, `createEncuentro`
- [ ] 2.5 Crear `coloquiosService.ts`: `getColoquios`, `createColoquio`
- [ ] 2.6 Crear `monitorService.ts`: `getMonitorGlobal` (reutiliza `/v1/analisis/monitor` sin filtro de materia)

## 3. Hooks TanStack Query (coordinacion/hooks)

- [ ] 3.1 Crear `useEquipos.ts`: `useEquipos`, `useCreateEquipo`, `useUpdateEquipo`, `useDeleteEquipo`, `useClonarEquipo`
- [ ] 3.2 Crear `useAvisos.ts`: `useAvisos`, `useCreateAviso`, `useUpdateAviso`, `useArchivarAviso`
- [ ] 3.3 Crear `useTareas.ts`: `useTareas`, `useCreateTarea`, `useUpdateTarea`, `useComentarios`, `useCreateComentario`
- [ ] 3.4 Crear `useEncuentros.ts`: `useEncuentros`, `useCreateEncuentro`
- [ ] 3.5 Crear `useColoquios.ts`: `useColoquios`, `useCreateColoquio`
- [ ] 3.6 Crear `useMonitorGlobal.ts`: `useMonitorGlobal`

## 4. Tests TDD — Equipos

- [ ] 4.1 RED: Escribir `__tests__/TablaEquipos.test.tsx` — render con datos, estado vacío, paginación (≥2 casos)
- [ ] 4.2 GREEN: Crear `components/equipos/TablaEquipos.tsx` — tabla con columnas nombre/vigencia/integrantes/acciones, paginación client-side PAGE_SIZE=20
- [ ] 4.3 RED: Escribir `__tests__/EquipoForm.test.tsx` — render formulario vacío, validación Zod campos requeridos, submit llama al hook (≥2 casos)
- [ ] 4.4 GREEN: Crear `components/equipos/EquipoForm.tsx` — React Hook Form + Zod, campos: nombre, descripción, vigencia_desde, vigencia_hasta

## 5. Tests TDD — Avisos

- [ ] 5.1 RED: Escribir `__tests__/TablaAvisos.test.tsx` — render con avisos activos/archivados, badge de severidad, botón archivar (≥2 casos)
- [ ] 5.2 GREEN: Crear `components/avisos/TablaAvisos.tsx` — tabla con badge de severidad coloreado, columna ack
- [ ] 5.3 RED: Escribir `__tests__/AvisoForm.test.tsx` — validación scope requerido, severidad requerida, submit correcto (≥2 casos)
- [ ] 5.4 GREEN: Crear `components/avisos/AvisoForm.tsx` — RHF + Zod, campos: título, cuerpo, scope (select), severidad (select), vigencia_hasta, requiere_ack (checkbox)

## 6. Tests TDD — Tareas

- [ ] 6.1 RED: Escribir `__tests__/TablaTareas.test.tsx` — render lista, filtro por estado, badge de prioridad (≥2 casos)
- [ ] 6.2 GREEN: Crear `components/tareas/TablaTareas.tsx` — tabla con badge estado, filtros client-side por estado y asignado
- [ ] 6.3 RED: Escribir `__tests__/TareaEstadoSelector.test.tsx` — render con estado actual, click cambia al nuevo estado, llama al hook (≥2 casos)
- [ ] 6.4 GREEN: Crear `components/tareas/TareaEstadoSelector.tsx` — select con estados Pendiente/EnProgreso/Completada
- [ ] 6.5 Crear `components/tareas/HiloComentarios.tsx` — lista de comentarios + textarea para nuevo comentario

## 7. Tests TDD — Monitor Global

- [ ] 7.1 RED: Escribir `__tests__/MonitorGlobal.test.tsx` — render tabla sin filtro materia, apply filtros actualiza query (≥2 casos)
- [ ] 7.2 GREEN: Crear `components/monitor/MonitorGlobalPanel.tsx` — reutiliza tipos `MonitorItem` de `features/comision/types`, tabla con FiltrosMonitor

## 8. Componentes — Encuentros y Coloquios

- [ ] 8.1 Crear `components/encuentros/TablaEncuentros.tsx` — lista con fecha, tipo, cupo, estado
- [ ] 8.2 Crear `components/encuentros/EncuentroForm.tsx` — RHF + Zod: fecha, tipo, cupo_maximo
- [ ] 8.3 Crear `components/coloquios/TablaColoquios.tsx` — lista de convocatorias con materia y estado
- [ ] 8.4 Crear `components/coloquios/ColoquioForm.tsx` — RHF + Zod: materia_id, fecha, descripción

## 9. Asistente de Cuatrimestre

- [ ] 9.1 Crear `components/cuatrimestre/StepperCuatrimestre.tsx` — indicador de 3 pasos (< 200 LOC)
- [ ] 9.2 Crear `components/cuatrimestre/PasoMateriasCohortesForm.tsx` — selección de materias y cohortes (paso 1)
- [ ] 9.3 Crear `components/cuatrimestre/PasoEquiposForm.tsx` — asignación de equipo por materia (paso 2)
- [ ] 9.4 Crear `components/cuatrimestre/ResumenCuatrimestre.tsx` — resumen + botón confirmar (paso 3)

## 10. Páginas

- [ ] 10.1 Crear `pages/CoordinacionLayout.tsx` — layout con sub-nav horizontal de tabs (Equipos/Avisos/Tareas/Monitor/Encuentros/Coloquios/Cuatrimestre)
- [ ] 10.2 Crear `pages/EquiposPage.tsx` — title + botón "Nuevo Equipo" + `TablaEquipos` + modal/drawer `EquipoForm` + botón "Exportar CSV"
- [ ] 10.3 Crear `pages/AvisosPage.tsx` — title + botón "Nuevo Aviso" + `TablaAvisos` + modal `AvisoForm`
- [ ] 10.4 Crear `pages/TareasPage.tsx` — title + botón "Nueva Tarea" + `TablaTareas` + drawer detalle con `HiloComentarios` + `TareaEstadoSelector`
- [ ] 10.5 Crear `pages/MonitorGlobalPage.tsx` — title + `MonitorGlobalPanel`
- [ ] 10.6 Crear `pages/EncuentrosPage.tsx` — title + botón "Nuevo Encuentro" + `TablaEncuentros` + modal `EncuentroForm`
- [ ] 10.7 Crear `pages/ColoquiosPage.tsx` — title + botón "Nueva Convocatoria" + `TablaColoquios` + modal `ColoquioForm`
- [ ] 10.8 Crear `pages/CuatrimestrePage.tsx` — stepper de 3 pasos con `StepperCuatrimestre`

## 11. Routing y Navegación

- [ ] 11.1 Actualizar `frontend/src/App.tsx` — agregar rutas `/coordinacion/*` con `CoordinacionLayout` e hijos (equipos, avisos, tareas, monitor, encuentros, coloquios, cuatrimestre)
- [ ] 11.2 Actualizar `frontend/src/shared/components/AppShell.tsx` — leer roles del usuario desde `useAuth()`; mostrar sección "Coordinación" solo para COORDINADOR/ADMIN; verificar que `useAuth` expone `roles[]` y extenderlo si hace falta

## 12. Utilidad Export CSV

- [ ] 12.1 Crear `frontend/src/shared/utils/exportCsv.ts` — función `exportToCsv(rows: Record<string, unknown>[], filename: string): void` usando `Blob` + `URL.createObjectURL`
- [ ] 12.2 RED: Escribir `__tests__/exportCsv.test.ts` — genera CSV correcto con headers, maneja array vacío (≥2 casos)
- [ ] 12.3 GREEN: completar implementación `exportToCsv` para pasar los tests
