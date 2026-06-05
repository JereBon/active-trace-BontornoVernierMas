## Context

C-10 dejó persistidas las entidades `Calificacion` (con campo `aprobado` derivado), `UmbralMateria`, `EntradaPadron` y `VersionPadron`. Este change construye sobre esas bases el motor de análisis académico: consultas derivadas que cruzan esas tablas para producir listas de alumnos atrasados, rankings, reportes de estado y exportación de TPs sin corregir. No hay nuevas tablas — todo se calcula en tiempo de consulta con datos ya persistidos.

El módulo se agrega como nuevo prefijo `/api/analisis/*` al router principal de FastAPI. La identidad del usuario, su tenant y sus permisos provienen exclusivamente del JWT; ningún parámetro de la request determina el scope del tenant.

## Goals / Non-Goals

**Goals:**
- Implementar el motor de análisis académico completo (F2.2–F2.9) sobre los datos de C-10
- Exponer endpoints REST bajo `/api/analisis/*` con guard `atrasados:ver`
- Mantener la separación estricta Routers → Services → Repositories: sin SQL en Services, sin lógica en Routers
- Cubrir ≥90% de las reglas de negocio con tests Strict TDD usando DB real

**Non-Goals:**
- Frontend — este change es solo la API backend
- Nuevas tablas o migraciones Alembic (no se necesitan)
- Integración con Moodle (el archivo de finalización ya está persistido en C-10 como calificaciones textuales)
- Paginación avanzada en el monitor (se implementa con `limit`/`offset` simples)

## Decisions

**D1 — Un solo AnalisisRepository, no repositorios por endpoint**

Alternativa considerada: un `AtrasadosRepository`, `RankingRepository`, etc. Rechazado por inflación innecesaria de archivos. Las consultas del módulo de análisis son todas lecturas sobre el mismo conjunto de entidades (`Calificacion`, `EntradaPadron`, `VersionPadron`, `UmbralMateria`). Un único `AnalisisRepository` con métodos bien nombrados es más fácil de mantener y testear.

**D2 — Lógica de clasificación de "atrasado" en AnalisisService, no en el repositorio**

El repositorio devuelve listas crudas de `Calificacion` agrupadas por alumno. El service aplica RN-06 (atrasado si tiene actividades faltantes O nota < umbral). Esto permite testear la lógica de negocio sin depender de la BD — las funciones puras del service reciben listas de calificaciones y devuelven un resultado determinista.

*Excepción*: el campo `aprobado` ya está precalculado en `Calificacion` (C-10), entonces el service confía en ese campo para el ranking y el cálculo de notas finales, sin recalcular desde el umbral.

**D3 — Detección de "sin corregir" basada en nota_textual nula + finalizado_lms**

RN-07 y RN-08 requieren cruzar el reporte de finalización del LMS con las calificaciones. Decisión: el reporte de finalización del LMS se importa como calificaciones textuales con `nota_textual = NULL` y un campo `finalizado_lms = True` (campo booleano adicional en `Calificacion`, ya previsto en C-10 o que se agrega en este change como columna con default `False`). Si ese campo no existe, se usa una convención alternativa: actividades con `nota_textual IS NULL AND origen = 'Importado'` y la actividad figura en el reporte de finalización. **Verificar si el modelo `Calificacion` de C-10 ya tiene `finalizado_lms`; si no, agregar como migration 0012.**

**D4 — Monitor general usa VersionPadron activa como fuente de alumnos**

El monitor (F2.7) muestra todos los alumnos del tenant con su estado de actividades. La fuente de alumnos es `EntradaPadron` de la `VersionPadron` activa de cada materia. Esto garantiza que el monitor refleja el padrón vigente. Alumnos en versiones inactivas no aparecen.

**D5 — Schemas Pydantic con `extra='forbid'`**

Todos los schemas de respuesta (`AtrasadoOut`, `RankingItemOut`, `MonitorItemOut`, etc.) usan `model_config = ConfigDict(extra='forbid')`. Los schemas de query params se validan como `BaseModel` o como parámetros de `Query()` en el router.

## Risks / Trade-offs

- **Performance en monitor con muchos alumnos**: el monitor transversal puede implicar grandes JOINs si el tenant tiene miles de alumnos. Mitigación: paginación `limit`/`offset` en el endpoint; índices en `(tenant_id, materia_id)` ya existentes de C-10.
- **Campo `finalizado_lms` puede no existir en C-10**: si el modelo `Calificacion` de C-10 no tiene ese campo, se necesita migration 0012. Verificar antes de implementar la task de "sin corregir".
- **Cálculo de "atrasado" depende de actividades esperadas**: RN-06 dice "actividades faltantes", pero el sistema solo conoce las actividades que se importaron. "Faltante" significa que el alumno no tiene `Calificacion` para una actividad que sí tienen otros alumnos de la misma versión. Esto es una definición implícita que el service implementa: conjunto de actividades = unión de todas las actividades de la materia; alumno atrasado si le falta alguna del conjunto.

## Migration Plan

- Si `Calificacion` ya tiene `finalizado_lms`: sin migración.
- Si no existe: migration `0012_add_finalizado_lms_calificacion.py` con `ALTER TABLE calificaciones ADD COLUMN finalizado_lms BOOLEAN NOT NULL DEFAULT FALSE`.
- Sin rollback complejo — la columna tiene default `False`, es backward-compatible.
- Verificar modelo en `backend/app/models/calificacion.py` como primer paso de implementación.

## Open Questions

- Q1: ¿`Calificacion` ya tiene campo `finalizado_lms`? (→ determina si se necesita migration 0012)
- Q2: ¿El endpoint de "notas finales" debe devolver un promedio ponderado o simplemente agrupar y listar las notas por actividad? (decisión: listar y calcular promedio simple por alumno, sin ponderación)
