## Context

C-07 creó el modelo `Asignacion` y un repositorio básico (`list_by_usuario`, `get_vigentes_by_usuario`). C-08 construye sobre esa base para exponer la gestión completa de equipos docentes: endpoints REST para CRUD individual, asignación masiva, clonado entre cohortes, modificación masiva de vigencia y exportación.

El permiso `equipos:asignar` ya está registrado en `permisos.py` y en la migración 0003. La infraestructura de auditoría (C-05), RBAC (C-04) y multi-tenancy (C-01) están operativas. No se necesita nueva migración porque no se agregan columnas ni tablas al schema.

## Goals / Non-Goals

**Goals:**
- Exponer endpoints `/v1/equipos/*` con guard `equipos:asignar`
- Vista propia del docente autenticado (`mis-asignaciones`) sin requerir permiso elevado
- Asignación masiva: N docentes × materia × carrera × cohorte × rol en una sola operación (RN-30)
- Clonado entre cohortes (RN-12): duplica asignaciones activas con nuevas fechas
- Modificación masiva de vigencia: actualiza `desde`/`hasta` de todo el equipo de una sola vez
- Exportación a CSV del equipo completo
- Auditoría (`ASIGNACION_CREAR`, `ASIGNACION_MODIFICAR`, `ASIGNACION_ELIMINAR`) en todas las mutaciones
- Tests: clonado, masivo, vigencia masiva, exportación — TDD estricto

**Non-Goals:**
- No se crea ninguna migración Alembic (el modelo ya existe)
- No se modela la grilla salarial ni liquidaciones (C-18)
- No se implementa la vista frontend (C-21 en adelante)
- No se elimina hard delete — solo soft delete

## Decisions

### D1 — Router separado `/v1/equipos`
El dominio de equipos docentes es suficientemente amplio (8 endpoints) para merecer su propio router. Patrón idéntico a `carreras.py`, `usuarios.py`, etc.

Alternativa rechazada: montar bajo `/v1/asignaciones` — confunde con el concepto de asignación de alumnos que se implementará en C-09.

### D2 — `mis-asignaciones` sin guard elevado; resto con `equipos:asignar`
`GET /v1/equipos/mis-asignaciones` es una vista propia del docente. No requiere `equipos:asignar`; basta con tener sesión autenticada. La identidad del usuario viene exclusivamente del JWT (`current_user.user_id`).

### D3 — Extensión del repositorio existente en lugar de repositorio nuevo
Se extiende `AsignacionRepository` con métodos nuevos: `list_with_filters`, `get_by_team`, `bulk_create`, `clone_team`, `bulk_update_vigencia`. Mantener un único repositorio por entidad es el patrón del proyecto.

### D4 — Clonado como operación de servicio (no SQL bulk copy)
El clonado itera las asignaciones vigentes del origen, crea nuevos objetos `Asignacion` con nuevas fechas y el nuevo `cohorte_id`, y los persiste en bloque. Esto permite que cada registro pase por las validaciones del repositorio base y genere un audit log individual.

Alternativa rechazada: `INSERT INTO ... SELECT ...` — bypassa el repositorio y el audit log.

### D5 — Exportación en memoria como CSV (sin archivos temporales)
El endpoint de exportación genera el CSV en memoria usando `io.StringIO` y responde con `StreamingResponse`. No se escriben archivos en disco.

### D6 — Filtros del listado como query params opcionales
`GET /v1/equipos/` acepta `materia_id`, `carrera_id`, `cohorte_id`, `usuario_id`, `rol`, `solo_vigentes` como query params opcionales. El repositorio recibe un objeto de filtro tipado (Pydantic) para evitar pasar kwargs sueltos.

### D7 — Asignación masiva retorna lista de IDs creados
`POST /v1/equipos/asignacion-masiva` recibe `usuario_ids: list[UUID]` + contexto académico + vigencia. Retorna `list[AsignacionOut]` con las asignaciones creadas. Si algún usuario_id produce un duplicado, se omite (idempotente) sin abortar la operación completa.

## Risks / Trade-offs

- [Risk] La clonación puede generar asignaciones duplicadas si el equipo destino ya tiene asignaciones para los mismos usuarios → Mitigación: el servicio verifica por `(usuario_id, rol, materia_id, carrera_id, cohorte_id)` antes de insertar; omite duplicados y los lista en la respuesta como `omitidos`.
- [Risk] Una modificación masiva de vigencia puede afectar muchas filas en una sola transacción → Mitigación: se hace en una sola transacción; si falla, el rollback es completo. El audit log registra `filas_afectadas`.
- [Risk] `equipos:asignar` ya existe en permisos.py pero puede no estar asignado a los roles en la migración 0003 → Mitigación: verificar en tests de integración que COORDINADOR y ADMIN tienen este permiso; si no, documentar que requiere seed manual.

## Migration Plan

Sin migración Alembic. La migración 0008 (C-07) ya tiene la tabla `asignaciones` completa.

Pasos de deploy:
1. Merge del PR → imagen se re-buildea
2. Los endpoints quedan disponibles automáticamente al arrancar el servidor
3. Rollback: revertir commit — los endpoints desaparecen; la tabla no cambia

## Open Questions

- ¿El permiso `equipos:ver` existe o debe crearse? Actualmente solo existe `equipos:asignar`. En la implementación se usará `equipos:asignar` también para lectura del listado global (coordinadores), dado que quien puede asignar puede ver. Si se necesita separar read/write, se crea `EQUIPOS_VER` en permisos.py. Decisión tomada: usar solo `equipos:asignar` para simplificar; `mis-asignaciones` no requiere permiso.
