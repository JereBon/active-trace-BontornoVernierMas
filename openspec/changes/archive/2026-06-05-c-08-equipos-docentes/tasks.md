## 1. Schemas Pydantic

- [x] 1.1 Extender `backend/app/schemas/asignacion.py`: agregar `AsignacionUpdate`, `AsignacionFilter`, `AsignacionMasivaCreate`, `ClonarEquipoRequest`, `VigenciaMasivaRequest`, `AsignacionMasivaOut` (con campo `omitidos`)
- [x] 1.2 Escribir tests unitarios para validación de schemas (rol inválido → 422, lista vacía → 422, extra fields → 422)

## 2. Repositorio

- [x] 2.1 Extender `backend/app/repositories/asignacion.py`: método `list_with_filters(filters: AsignacionFilter)` con filtros opcionales y scope de tenant
- [x] 2.2 Agregar `bulk_create(items: list[dict]) -> tuple[list[Asignacion], list[uuid.UUID]]` — retorna (creadas, omitidas)
- [x] 2.3 Agregar `clone_team(origen_cohorte_id, destino_cohorte_id, materia_id, carrera_id, desde, hasta) -> tuple[list[Asignacion], list[uuid.UUID]]`
- [x] 2.4 Agregar `bulk_update_vigencia(materia_id, carrera_id, cohorte_id, desde, hasta) -> int` — retorna filas afectadas
- [x] 2.5 Agregar `get(id) -> Asignacion | None` — get by id scoped to tenant (para edición y delete)
- [x] 2.6 Agregar `update(id, data: dict) -> Asignacion | None` — update scoped to tenant
- [x] 2.7 Tests RED→GREEN para cada método nuevo del repositorio usando DB real de test

## 3. Servicio

- [x] 3.1 Crear `backend/app/services/equipos.py`: clase `EquiposService` con `__init__(session, tenant_id)`
- [x] 3.2 Implementar `mis_asignaciones(usuario_id) -> list[Asignacion]` — delega a `get_vigentes_by_usuario`
- [x] 3.3 Implementar `list_asignaciones(filters: AsignacionFilter) -> list[Asignacion]` — delega a `list_with_filters`
- [x] 3.4 Implementar `create_asignacion(data: AsignacionCreate) -> Asignacion` con auditoría `ASIGNACION_CREAR`
- [x] 3.5 Implementar `update_asignacion(id, data: AsignacionUpdate, actor_id) -> Asignacion` con auditoría `ASIGNACION_MODIFICAR`
- [x] 3.6 Implementar `delete_asignacion(id, actor_id) -> None` — soft delete con auditoría `ASIGNACION_ELIMINAR`
- [x] 3.7 Implementar `asignacion_masiva(data: AsignacionMasivaCreate, actor_id) -> AsignacionMasivaOut` con auditoría por bloque
- [x] 3.8 Implementar `clonar_equipo(data: ClonarEquipoRequest, actor_id) -> AsignacionMasivaOut` con auditoría
- [x] 3.9 Implementar `vigencia_masiva(data: VigenciaMasivaRequest, actor_id) -> dict` con auditoría `ASIGNACION_MODIFICAR` y `filas_afectadas`
- [x] 3.10 Implementar `exportar_csv(filters: AsignacionFilter) -> str` — retorna contenido CSV como string
- [x] 3.11 Tests RED→GREEN para cada método del servicio con DB real de test

## 4. Router

- [x] 4.1 Crear `backend/app/api/v1/routers/equipos.py` con prefijo `/v1/equipos`
- [x] 4.2 Implementar `GET /mis-asignaciones` — sin guard elevado, solo sesión autenticada
- [x] 4.3 Implementar `GET /` — con guard `equipos:asignar`, query params de filtro opcionales
- [x] 4.4 Implementar `POST /` — con guard `equipos:asignar`, body `AsignacionCreate`
- [x] 4.5 Implementar `PUT /{id}` — con guard `equipos:asignar`, body `AsignacionUpdate`
- [x] 4.6 Implementar `DELETE /{id}` — con guard `equipos:asignar`, retorna 204
- [x] 4.7 Implementar `POST /asignacion-masiva` — con guard `equipos:asignar`
- [x] 4.8 Implementar `POST /clonar` — con guard `equipos:asignar`
- [x] 4.9 Implementar `PUT /vigencia-masiva` — con guard `equipos:asignar`
- [x] 4.10 Implementar `GET /exportar` — con guard `equipos:asignar`, responde `StreamingResponse` CSV

## 5. Registro del router en la aplicación

- [x] 5.1 Importar y montar `equipos.router` en `backend/app/main.py` o en el `__init__.py` del API v1

## 6. Tests de integración

- [x] 6.1 Test: `GET /mis-asignaciones` retorna solo asignaciones vigentes del usuario autenticado
- [x] 6.2 Test: `GET /` sin permiso `equipos:asignar` → 403
- [x] 6.3 Test: `POST /` crea asignación y genera entrada en audit_log
- [x] 6.4 Test: `PUT /{id}` actualiza vigencia y genera audit_log
- [x] 6.5 Test: `DELETE /{id}` soft-delete y genera audit_log (deleted_at seteado, no aparece en listados)
- [x] 6.6 Test: `POST /asignacion-masiva` con N usuarios crea N asignaciones; duplicado es omitido sin abortar
- [x] 6.7 Test: `POST /clonar` duplica asignaciones vigentes del origen con nuevo cohorte y nuevas fechas; origen intacto
- [x] 6.8 Test: `PUT /vigencia-masiva` actualiza fechas en todas las asignaciones del equipo y retorna `filas_afectadas`
- [x] 6.9 Test: `GET /exportar` retorna CSV con cabeceras correctas; equipo vacío retorna solo cabeceras
- [x] 6.10 Test: aislamiento multi-tenant — usuario de tenant A no puede ver ni modificar asignaciones de tenant B
