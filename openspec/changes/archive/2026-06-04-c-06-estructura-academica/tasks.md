## 1. Migración Alembic

- [x] 1.1 Verificar número de migración disponible en `backend/alembic/versions/` (usar `0004` si libre, `0005` si C-05 ya lo tomó)
- [x] 1.2 Crear `backend/alembic/versions/000X_estructura_academica.py` con tablas `carreras`, `cohortes`, `materias`
- [x] 1.3 Tabla `carreras`: columnas `id` (UUID PK), `tenant_id` (UUID FK), `codigo` (text), `nombre` (text), `estado` (enum), `deleted_at`, `created_at`, `updated_at`; índice único `(tenant_id, codigo)` donde `deleted_at IS NULL`
- [x] 1.4 Tabla `cohortes`: columnas `id`, `tenant_id`, `carrera_id` (UUID FK → carreras.id), `nombre`, `anio` (int), `vig_desde` (date), `vig_hasta` (date nullable), `estado`, `deleted_at`, `created_at`, `updated_at`; índice único `(tenant_id, carrera_id, nombre)` donde `deleted_at IS NULL`
- [x] 1.5 Tabla `materias`: columnas `id`, `tenant_id`, `codigo`, `nombre`, `estado`, `deleted_at`, `created_at`, `updated_at`; índice único `(tenant_id, codigo)` donde `deleted_at IS NULL`
- [x] 1.6 Insertar permiso `estructura:gestionar` en tabla `permisos` y asignarlo al rol ADMIN en `rol_permisos` dentro de la migración

## 2. Modelos SQLAlchemy

- [x] 2.1 Definir enum `EstadoEntidad` (`Activa`, `Inactiva`) en `backend/app/models/base.py` o módulo de enums compartidos
- [x] 2.2 Crear `backend/app/models/carrera.py` con modelo `Carrera` que extiende `BaseModel` (con `TenantScopedMixin` si existe)
- [x] 2.3 Crear `backend/app/models/cohorte.py` con modelo `Cohorte` y FK a `Carrera`
- [x] 2.4 Crear `backend/app/models/materia.py` con modelo `Materia`
- [x] 2.5 Registrar los tres modelos en `backend/app/models/__init__.py`

## 3. Repositories

- [x] 3.1 Crear `backend/app/repositories/carrera.py` con `CarreraRepository` que extiende `BaseRepository`; filtro de tenant y `deleted_at IS NULL` por defecto; método `get_by_codigo(tenant_id, codigo)`
- [x] 3.2 Crear `backend/app/repositories/cohorte.py` con `CohorteRepository`; filtro de tenant; método `get_by_nombre(tenant_id, carrera_id, nombre)`
- [x] 3.3 Crear `backend/app/repositories/materia.py` con `MateriaRepository`; filtro de tenant; método `get_by_codigo(tenant_id, codigo)`
- [x] 3.4 Registrar los tres repositories en `backend/app/repositories/__init__.py`

## 4. Schemas Pydantic

- [x] 4.1 Crear `backend/app/schemas/carrera.py` con `CarreraCreate`, `CarreraUpdate`, `CarreraOut` (todos con `model_config = ConfigDict(extra='forbid')`)
- [x] 4.2 Crear `backend/app/schemas/cohorte.py` con `CohorteCreate`, `CohorteUpdate`, `CohorteOut`
- [x] 4.3 Crear `backend/app/schemas/materia.py` con `MateriaCreate`, `MateriaUpdate`, `MateriaOut`

## 5. Services

- [x] 5.1 Crear `backend/app/services/carrera.py` con `CarreraService`: `create` (valida unicidad → 409), `list`, `get`, `update`, `soft_delete`
- [x] 5.2 Crear `backend/app/services/cohorte.py` con `CohorteService`: `create` (valida unicidad + carrera existe en tenant → 404/409), `list`, `get`, `update`, `soft_delete`
- [x] 5.3 Crear `backend/app/services/materia.py` con `MateriaService`: `create` (valida unicidad → 409), `list`, `get`, `update`, `soft_delete`

## 6. Routers FastAPI

- [x] 6.1 Crear `backend/app/routers/carreras.py` con endpoints: `POST /v1/carreras`, `GET /v1/carreras`, `GET /v1/carreras/{id}`, `PATCH /v1/carreras/{id}`, `DELETE /v1/carreras/{id}`; todos con `require_permission("estructura:gestionar")`
- [x] 6.2 Crear `backend/app/routers/cohortes.py` con endpoints análogos bajo `/v1/cohortes`
- [x] 6.3 Crear `backend/app/routers/materias.py` con endpoints análogos bajo `/v1/materias`
- [x] 6.4 Registrar los tres routers en `backend/app/main.py`

## 7. Tests (Strict TDD — RED → GREEN → TRIANGULATE → REFACTOR)

- [x] 7.1 Crear `backend/tests/test_estructura_academica.py` con fixture de DB y tenant de prueba
- [x] 7.2 Test: crear Carrera → 201; verificar en DB
- [x] 7.3 Test: crear Carrera con `codigo` duplicado → 409
- [x] 7.4 Test: soft delete de Carrera → 204; no aparece en listado
- [x] 7.5 Test: acceso sin permiso `estructura:gestionar` → 403
- [x] 7.6 Test: crear Cohorte → 201; unicidad `(tenant_id, carrera_id, nombre)` → 409
- [x] 7.7 Test: crear Cohorte con `carrera_id` de otro tenant → 404
- [x] 7.8 Test: crear Materia → 201; código duplicado → 409; soft delete → 204
- [x] 7.9 Ejecutar `pytest backend/tests/test_estructura_academica.py -v` y verificar que todos los tests pasan
- [x] 7.10 Verificar cobertura ≥ 80% líneas, ≥ 90% reglas de negocio en el módulo
