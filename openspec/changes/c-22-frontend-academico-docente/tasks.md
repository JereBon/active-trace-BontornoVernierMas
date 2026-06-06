## 1. Tipos TypeScript y estructura base

- [x] 1.1 Crear `frontend/src/features/comision/types/index.ts` con tipos: `ActividadPreview`, `CalificacionPreviewResponse`, `ImportarResponse`, `UmbralRequest`, `UmbralResponse`, `AtrasadoItem`, `RankingItem`, `NotaFinal`, `ReporteMateria`, `SinCorregirItem`, `MonitorItem`, `LoteStatus`, `PreviewComunicacion`
- [x] 1.2 Crear estructura de directorios: `features/comision/{components,hooks,services,types,pages,__tests__}`

## 2. Servicios de API

- [x] 2.1 Crear `frontend/src/features/comision/services/calificacionesService.ts` — funciones: `previewCalificaciones(materiaId, file)`, `importarCalificaciones(materiaId, asignacionId, file, actividades)`, `configurarUmbral(materiaId, body)`
- [x] 2.2 Crear `frontend/src/features/comision/services/analisisService.ts` — funciones: `getAtrasados(materiaId)`, `getRanking(materiaId)`, `getNotasFinales(materiaId)`, `getReporteMateria(materiaId)`, `getSinCorregir(materiaId)`, `getMonitor(params)`
- [x] 2.3 Crear `frontend/src/features/comision/services/comunicacionesService.ts` — funciones: `previewComunicacion(body)`, `encolarComunicaciones(body)`, `getLoteStatus(loteId)`

## 3. Hooks TanStack Query

- [x] 3.1 Crear `frontend/src/features/comision/hooks/useAtrasados.ts` — `useQuery` sobre `getAtrasados`
- [x] 3.2 Crear `frontend/src/features/comision/hooks/useRanking.ts` — `useQuery` sobre `getRanking`
- [x] 3.3 Crear `frontend/src/features/comision/hooks/useNotasFinales.ts` — `useQuery` sobre `getNotasFinales`
- [x] 3.4 Crear `frontend/src/features/comision/hooks/useReporteMateria.ts` — `useQuery` sobre `getReporteMateria`
- [x] 3.5 Crear `frontend/src/features/comision/hooks/useSinCorregir.ts` — `useQuery` sobre `getSinCorregir`
- [x] 3.6 Crear `frontend/src/features/comision/hooks/useMonitor.ts` — `useQuery` con filtros como parámetros
- [x] 3.7 Crear `frontend/src/features/comision/hooks/useLoteStatus.ts` — `useQuery` con `refetchInterval: 3000` hasta estado terminal
- [x] 3.8 Crear `frontend/src/features/comision/hooks/useImportarCalificaciones.ts` — `useMutation` para preview e importación

## 4. Componentes: Importación de calificaciones

- [x] 4.1 Crear `features/comision/components/ImportarCalificacionesForm.tsx` — dropzone de archivo, botón "Preview", muestra spinner durante la llamada. (<200 LOC)
- [x] 4.2 Crear `features/comision/components/ActividadesSelector.tsx` — checkboxes de actividades numéricas/textuales del preview, botón "Confirmar importación". (<200 LOC)
- [x] 4.3 Crear `features/comision/components/UmbralForm.tsx` — React Hook Form + Zod (umbral_pct 0–100), botón "Guardar umbral". (<200 LOC)

## 5. Componentes: Análisis y reportes

- [x] 5.1 Crear `features/comision/components/TablaAtrasados.tsx` — tabla paginada client-side con columnas: nombre, apellidos, comisión, actividades pendientes. (<200 LOC)
- [x] 5.2 Crear `features/comision/components/TablaRanking.tsx` — tabla de ranking ordenada por aprobados desc. (<200 LOC)
- [x] 5.3 Crear `features/comision/components/TablaNotasFinales.tsx` — tabla con nota promedio por alumno. (<200 LOC)
- [x] 5.4 Crear `features/comision/components/ReporteMateriaCards.tsx` — cards con métricas agregadas (total alumnos, % aprobados, etc). (<200 LOC)
- [x] 5.5 Crear `features/comision/components/TablaSinCorregir.tsx` — tabla con botón "Exportar CSV" (habilitado solo con datos). Lógica CSV con Blob + createObjectURL. (<200 LOC)

## 6. Componentes: Monitor

- [x] 6.1 Crear `features/comision/components/FiltrosMonitor.tsx` — inputs de texto + toggle "solo atrasados", botón "Buscar". (<200 LOC)
- [x] 6.2 Crear `features/comision/components/TablaMonitor.tsx` — tabla paginada con límite/offset, columnas: nombre, comisión, materia, estado. (<200 LOC)

## 7. Componentes: Comunicaciones

- [x] 7.1 Crear `features/comision/components/FormularioComunicacion.tsx` — React Hook Form + Zod (asunto y cuerpo requeridos), botón "Preview" + "Enviar". (<200 LOC)
- [x] 7.2 Crear `features/comision/components/PreviewComunicacionPanel.tsx` — muestra el asunto y cuerpo renderizados del preview server-side. (<200 LOC)
- [x] 7.3 Crear `features/comision/components/TrackingLotePanel.tsx` — muestra contadores de Pendiente/Enviado/Fallido/Cancelado con polling via `useLoteStatus`. (<200 LOC)

## 8. Páginas

- [x] 8.1 Crear `features/comision/pages/ImportacionPage.tsx` — composición de `ImportarCalificacionesForm`, `ActividadesSelector`, `UmbralForm`. (<200 LOC)
- [x] 8.2 Crear `features/comision/pages/AtrasadosPage.tsx` — tabs: Atrasados, Ranking, Notas Finales, Reporte. (<200 LOC)
- [x] 8.3 Crear `features/comision/pages/SinCorregirPage.tsx` — listado y export CSV. (<200 LOC)
- [x] 8.4 Crear `features/comision/pages/ComunicacionPage.tsx` — formulario, preview y tracking. (<200 LOC)
- [x] 8.5 Crear `features/comision/pages/MonitorPage.tsx` — filtros y tabla del monitor. (<200 LOC)
- [x] 8.6 Crear `features/comision/pages/ComisionLayout.tsx` — layout con tabs/nav secundaria de las sub-páginas de la feature. (<200 LOC)

## 9. Routing y navegación

- [x] 9.1 Actualizar `frontend/src/App.tsx` — agregar rutas `/comision/:materiaId/*` con sub-rutas a cada página, bajo AuthGuard
- [x] 9.2 Actualizar `frontend/src/shared/components/AppShell.tsx` — agregar ítem "Comisión" en el menú lateral con icono

## 10. Tests

- [x] 10.1 Crear `features/comision/__tests__/ImportarCalificacionesForm.test.tsx` — test RED: render inicial sin datos; test GREEN + triangulación: preview exitoso con actividades, error 422 muestra mensaje
- [x] 10.2 Crear `features/comision/__tests__/ActividadesSelector.test.tsx` — test: checkboxes habilitados, validación sin selección, selección y confirmación
- [x] 10.3 Crear `features/comision/__tests__/UmbralForm.test.tsx` — test: validación Zod (vacío, fuera de rango, válido), submit exitoso
- [x] 10.4 Crear `features/comision/__tests__/TablaAtrasados.test.tsx` — test: render con datos, estado vacío, paginación client-side
- [x] 10.5 Crear `features/comision/__tests__/TablaSinCorregir.test.tsx` — test: render con datos, botón CSV habilitado/deshabilitado, export genera Blob
- [x] 10.6 Crear `features/comision/__tests__/FormularioComunicacion.test.tsx` — test: validación campos vacíos, preview server-side, error de variable inválida
- [x] 10.7 Crear `features/comision/__tests__/TrackingLotePanel.test.tsx` — test: contadores iniciales, polling activo, detención al estado terminal
