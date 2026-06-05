## Context

El sistema ya tiene padrón de alumnos (C-09): `VersionPadron` y `EntradaPadron` existen. El siguiente paso del camino crítico es persitir las calificaciones que el docente importa desde el LMS y configurar el umbral de aprobación. Sin estos datos, C-11 (análisis de atrasados) no puede funcionar.

El LMS exporta dos tipos de archivos: (1) el reporte de calificaciones con columnas de notas `(Real)` numéricas y columnas de escala textual; (2) el reporte de finalización con estado "Completado / No completado" por actividad y alumno. El sistema debe parsear ambos, generar preview, permitir selección de actividades y persistir.

## Goals / Non-Goals

**Goals:**
- Modelos SQLAlchemy `Calificacion` y `UmbralMateria` con migración 0010.
- Parser de archivo de calificaciones LMS: detecta columnas `(Real)` y textuales, devuelve preview.
- Parser de reporte de finalización: detecta TPs entregados sin nota.
- Repository y Service para calificaciones con scope por `(tenant_id, materia_id, asignacion_id)`.
- Endpoint `POST /calificaciones/{materia_id}/preview` (paso 1: parse sin persistir).
- Endpoint `POST /calificaciones/{materia_id}/importar` (paso 2: confirmar y persistir).
- Endpoint `PUT /calificaciones/{materia_id}/umbral` (configurar umbral para la asignación del usuario autenticado).
- Derivación automática de `aprobado` en la capa de servicio antes de persistir.
- Audit log `CALIFICACIONES_IMPORTAR` al confirmar importación.

**Non-Goals:**
- UI / frontend (queda para el sprint de frontend).
- Endpoint de análisis de atrasados (C-11).
- Importación de finalización de actividades en este change (F1.2 queda como endpoint separado en C-11, pues su output es un análisis, no persistencia de Calificacion).
- Modificación manual de calificaciones (origen `Manual`) — se deja para iteración futura.
- Soporte de formatos distintos a `.xlsx` y `.csv`.

## Decisions

### D1: `aprobado` se calcula en el servicio, no en la BD

**Alternativas**: (a) columna generada en PostgreSQL; (b) trigger; (c) calculada en el servicio.

Se elige (c): la lógica depende de `UmbralMateria` que puede cambiar después de la importación. Al recalcular en el servicio en el momento de la importación (o cuando se actualiza el umbral), se evitan dependencias circulares en SQL y se mantiene la lógica en Python donde es testeable con TDD puro. El campo `aprobado` se almacena desnormalizado para eficiencia de lectura en C-11.

**Consecuencia**: cuando el docente cambia el umbral, el service debe recalcular y actualizar `aprobado` en batch para las calificaciones existentes de esa asignación.

### D2: Preview por in-memory token (mismo patrón que padrón)

El preview se devuelve como JSON sin persistir. El cliente elige las actividades a incluir y llama a `/importar` con la selección. No se usa un "preview token" de sesión: el cliente reenvía el archivo en el paso 2 junto con la lista de actividades seleccionadas. Esto simplifica el servidor (sin estado de sesión intermedio).

### D3: Scope de calificaciones es `(tenant_id, entrada_padron_id, actividad, asignacion_id)`

Cada registro de `Calificacion` está ligado a una `EntradaPadron` (FK) y a una `actividad` (texto, nombre de columna del LMS). La clave de unicidad es `(tenant_id, entrada_padron_id, actividad)` — una nota por alumno por actividad por tenant. No hay `asignacion_id` en `Calificacion` porque la nota es un hecho del alumno en esa actividad, no del docente. El `UmbralMateria` sí lleva `asignacion_id`.

**Alternativa rechazada**: agregar `asignacion_id` a `Calificacion`. Se rechaza porque complicaría el análisis en C-11 cuando múltiples docentes tienen alumnos en la misma materia.

### D4: `UmbralMateria` tiene constraint unique `(tenant_id, asignacion_id, materia_id)`

Un docente (asignación) solo puede tener un umbral por materia. El endpoint `PUT /umbral` hace upsert: crea si no existe, actualiza si ya existe.

### D5: Derivación de `aprobado` para escala textual — lista configurable hardcodeada en esta iteración

RN-02 dice que la lista de valores aprobatorios es configurable. En esta iteración se hardcodea `{"Satisfactorio", "Supera lo esperado"}` como constante en el service/parser. El `UmbralMateria.valores_aprobatorios` ya existe en el modelo para la futura iteración de configuración por tenant.

## Risks / Trade-offs

- **[Riesgo] Recálculo batch de `aprobado` al cambiar umbral puede ser lento para datasets grandes** → Mitigación: en esta iteración el batch es síncrono pero acotado por `(asignacion_id, materia_id)`; si supera N registros, se documenta como mejora pendiente para worker async (C-22).
- **[Riesgo] Columnas LMS pueden variar entre exports de distintas versiones de Moodle** → Mitigación: el parser es tolerante a columnas extra (las ignora) y falla explícito solo en ausencia de columna de alumno requerida.
- **[Trade-off] No persistir F1.2 en `Calificacion`** → El reporte de finalización produce un análisis en memoria (entregas sin nota), no una entidad nueva. Se devuelve como payload del endpoint sin persistencia, simplificando el modelo.

## Migration Plan

1. Aplicar migración 0010 (`alembic upgrade head`) — crea `calificacion` y `umbral_materia`.
2. No hay datos existentes que migrar; las tablas nacen vacías.
3. Rollback: `alembic downgrade -1` — `DROP TABLE calificacion, umbral_materia`.
4. Sin cambios a rutas ni schemas existentes.

## Open Questions

- **OQ-1**: ¿El endpoint de preview debe aceptar solo xlsx o también csv? Se asume ambos (mismo patrón que padrón). Si el LMS de la institución solo exporta xlsx, se puede restringir después.
- **OQ-2**: ¿La columna de identificación del alumno en el LMS export es siempre `Email address`? Se asume que sí, basado en los ejemplos del cliente. Si varía, el parser necesitará configuración de mapping de columnas.
