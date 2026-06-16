## 1. Migración Alembic

- [x] 1.1 Crear migración `0006_programas_y_fechas_academicas.py` con tablas `programa_materia` y `fecha_academica`, incluyendo FKs a `materia`, `cohorte`, `carrera` y `tenant`, columnas `deleted_at` para soft delete, e índices por `tenant_id`.

## 2. Modelos SQLAlchemy

- [x] 2.1 Crear `backend/app/models/programa_materia.py` con el modelo `ProgramaMateria` (campos: id UUID PK, tenant_id, materia_id, carrera_id nullable, cohorte_id nullable, titulo, referencia_archivo nullable, vigente bool default True, publicado_en datetime nullable, deleted_at nullable, created_at, updated_at).
- [x] 2.2 Crear `backend/app/models/fecha_academica.py` con el modelo `FechaAcademica` y el enum `TipoEvaluacion` (PARCIAL, TP, COLOQUIO, RECUPERATORIO). Campos: id UUID PK, tenant_id, materia_id, cohorte_id, tipo enum, numero int, periodo str, fecha date, titulo, deleted_at nullable, created_at, updated_at.
- [x] 2.3 Exportar ambos modelos desde `backend/app/models/__init__.py`.

## 3. Schemas Pydantic

- [x] 3.1 Crear `backend/app/schemas/programa_materia.py` con `ProgramaMateriaCreate`, `ProgramaMateriaRead` y `ProgramaMateriaUpdate`. Todos con `model_config = ConfigDict(extra='forbid')`.
- [x] 3.2 Crear `backend/app/schemas/fecha_academica.py` con `FechaAcademicaCreate`, `FechaAcademicaRead` y `FechaAcademicaUpdate`. Todos con `model_config = ConfigDict(extra='forbid')`.

## 4. Repositories

- [x] 4.1 Crear `backend/app/repositories/programa_materia.py` con `ProgramaMateriaRepository` (métodos: `create`, `list_by_tenant`, `list_by_materia`, `get_by_id`, `soft_delete`). Todos los queries filtran por `tenant_id` y excluyen `deleted_at is not null`.
- [x] 4.2 Crear `backend/app/repositories/fecha_academica.py` con `FechaAcademicaRepository` (métodos: `create`, `list_by_tenant`, `list_by_materia`, `get_by_id`, `soft_delete`). Filtro por `tenant_id` y exclusión de soft-deleted obligatorios.
- [x] 4.3 Exportar ambos repositories desde `backend/app/repositories/__init__.py`.

## 5. Routers FastAPI

- [x] 5.1 Crear `backend/app/api/routes/programas.py` con endpoints:
  - `POST /api/programas` → crear programa (requiere `estructura:gestionar`)
  - `GET /api/programas` → listar programas del tenant
  - `GET /api/programas/{materia_id}` → listar programas de una materia
  - `DELETE /api/programas/{id}` → soft delete (requiere `estructura:gestionar`)
- [x] 5.2 Crear `backend/app/api/routes/fechas_academicas.py` con endpoints:
  - `POST /api/fechas-academicas` → crear fecha (requiere `estructura:gestionar`)
  - `GET /api/fechas-academicas` → listar fechas del tenant (acepta query param `materia_id`)
  - `DELETE /api/fechas-academicas/{id}` → soft delete (requiere `estructura:gestionar`)
- [x] 5.3 Registrar ambos routers en `backend/app/main.py`.

## 6. Tests (Strict TDD)

- [x] 6.1 Crear `backend/tests/test_programas.py`:
  - Safety net: migración aplicada, baseline 0 tests fallando.
  - RED: test creación exitosa → GREEN: implementar → TRIANGULATE: test sin permiso (403) + test campos extra (422).
  - Test listado filtra por tenant (aislamiento multi-tenant).
  - Test GET `/api/programas/{materia_id}` retorna lista vacía si no hay programas.
  - Test soft delete: registro con `deleted_at` no aparece en listados.
- [x] 6.2 Crear `backend/tests/test_fechas_academicas.py`:
  - Safety net baseline.
  - RED: test creación exitosa → GREEN → TRIANGULATE: test sin permiso (403) + tipo inválido (422).
  - Test listado con filtro por `materia_id`.
  - Test aislamiento multi-tenant.
  - Test soft delete.

## 7. Verificación final

- [x] 7.1 Ejecutar `pytest backend/tests/test_programas.py backend/tests/test_fechas_academicas.py -v` y confirmar que todos los tests pasan.
- [x] 7.2 Verificar cobertura ≥80% líneas en los módulos nuevos.
