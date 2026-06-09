## Why

Con las calificaciones e ingestas del padrón ya persistidas (C-10), la plataforma necesita el motor de análisis académico que da sentido a todos los datos importados: detectar alumnos en riesgo, generar rankings, producir reportes de estado y exportar entregas pendientes. Sin este módulo, la ingesta de datos no produce ningún valor operativo para docentes ni coordinación.

## What Changes

- Nuevo endpoint `GET /api/analisis/atrasados` — lista alumnos atrasados según RN-06 (actividades faltantes o nota < umbral configurado en UmbralMateria)
- Nuevo endpoint `GET /api/analisis/ranking` — ranking de actividades aprobadas por alumno, solo los que tienen al menos una aprobada (RN-09)
- Nuevo endpoint `GET /api/analisis/reporte-materia` — métricas consolidadas de una materia (totales, aprobaciones, pendientes)
- Nuevo endpoint `GET /api/analisis/notas-finales` — notas finales agrupadas por alumno, listas para exportar
- Nuevo endpoint `GET /api/analisis/sin-corregir` — lista de TPs con finalización confirmada pero sin calificación numérica (RN-07, RN-08)
- Nuevo endpoint `GET /api/analisis/monitor` — vista transversal del tenant (para COORDINADOR/ADMIN), filtrable por materia, comisión, regional, alumno, estado; con rango de fechas opcional (F2.7, F2.8, F2.9)
- Todos los endpoints protegidos con guard `atrasados:ver`; lógica de cálculo en Services; queries en Repositories
- Tests Strict TDD cubriendo: definición de atrasado vs. umbral, ranking solo ≥1 aprobada, notas finales agrupadas, filtros del monitor, export sin corregir

## Capabilities

### New Capabilities

- `analisis-atrasados`: Cómputo y exposición de alumnos atrasados (RN-06), ranking de aprobadas (RN-09), notas finales agrupadas, monitor de seguimiento con filtros por rol (F2.2, F2.3, F2.5, F2.7, F2.8, F2.9)
- `analisis-reportes`: Reportes rápidos por materia (F2.4) y exportación de TPs sin corregir (F2.6, RN-07, RN-08)

### Modified Capabilities

- `calificaciones`: Se agrega el campo derivado `aprobado` como insumo del motor de análisis; sin cambio de contrato externo, solo consultas nuevas sobre datos existentes

## Impact

- **Nuevos archivos**: `backend/app/routers/analisis.py`, `backend/app/services/analisis_service.py`, `backend/app/repositories/analisis_repository.py`, `backend/app/schemas/analisis.py`, `tests/test_analisis.py`
- **Sin migración**: este change no introduce nuevas tablas ni columnas — lee de `Calificacion`, `EntradaPadron`, `VersionPadron`, `UmbralMateria`, `Materia`
- **Dependencias**: C-10 (calificaciones + padrón ya persistidos); `atrasados:ver` debe estar registrado en la tabla de permisos RBAC (verificar seed de C-04)
- **APIs afectadas**: agrega prefijo `/api/analisis/*` al router de FastAPI
