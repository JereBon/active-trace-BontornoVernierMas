## Why

El sistema necesita persistir y analizar las calificaciones importadas desde el LMS para detectar alumnos en riesgo académico. Sin los modelos `Calificacion` y `UmbralMateria` y su pipeline de ingesta, los flujos de análisis (atrasados, ranking, reportes) no tienen datos sobre los cuales operar. Este change cierra la brecha entre la ingesta de padrón (C-09) y el análisis académico (C-11).

## What Changes

- **Nuevo modelo `Calificacion`**: almacena nota numérica, textual, campo derivado `aprobado`, origen (Importado | Manual) y referencia a `EntradaPadron` y `Materia`.
- **Nuevo modelo `UmbralMateria`**: almacena el umbral de aprobación (porcentaje y valores textuales aprobatorios) por asignación docente y materia, con default 60 %.
- **Migración Alembic 0010**: crea las tablas `calificacion` y `umbral_materia`.
- **Parser de calificaciones LMS (F1.1)**: detecta columnas numéricas `(Real)` (RN-01) y textuales (RN-02), genera vista previa de actividades, permite selección antes de importar.
- **Parser de reporte de finalización (F1.2)**: detecta TPs entregados sin nota para la tabla de pendientes sin corregir (RN-07, RN-08).
- **Endpoint de configuración de umbral (F2.1)**: crea o actualiza `UmbralMateria` para la asignación del docente autenticado (RN-03). No afecta umbrales de otros docentes.
- **Audit log**: acción `CALIFICACIONES_IMPORTAR` al finalizar cada importación.
- **Tests TDD**: derivación de `aprobado` (numérica vs umbral, textual vs conjunto aprobatorio), import + preview, selección de actividades, aislamiento de umbral por asignación.

## Capabilities

### New Capabilities
- `calificaciones`: Persistencia, ingesta desde LMS y configuración de umbral de aprobación por materia y docente.

### Modified Capabilities
- `padron-ingesta`: La entidad `EntradaPadron` ya existe; `Calificacion` la referencia como FK. No cambia el comportamiento de la ingesta de padrón, pero establece la dependencia estructural.

## Impact

- **Nuevos archivos**: `app/models/calificacion.py`, `app/models/umbral_materia.py`, `app/repositories/calificacion_repository.py`, `app/services/calificacion_service.py`, `app/services/calificacion_parser.py`, `app/routers/calificaciones.py`, `alembic/versions/0010_calificacion_umbral_materia.py`, `tests/test_calificaciones.py`.
- **Dependencia ascendente**: C-11 (análisis de atrasados) depende de que existan registros en `Calificacion` y `UmbralMateria`.
- **Sin cambios a APIs existentes**: ningún router ni schema existente se modifica.
- **Permisos RBAC**: requiere permiso `calificaciones:importar` para importar y `calificaciones:umbral` para configurar umbral (ambos nuevos; se declaran en el decorador `require_permission`).
