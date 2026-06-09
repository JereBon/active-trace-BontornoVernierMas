# Tasks — C-13: Encuentros y Guardias

## Task 1.1 — Alembic migration 0011
- [x] Create `backend/alembic/versions/0011_encuentros_y_guardias.py`
  - down_revision = "0009"
  - Tables: `slot_encuentro`, `instancia_encuentro`, `guardia`
  - All columns per E9, E10, E11 in knowledge-base/04_modelo_de_datos.md

## Task 1.2 — Models: SlotEncuentro + InstanciaEncuentro
- [x] Create `backend/app/models/encuentro.py`
  - `SlotEncuentro(Base, TenantScopedMixin)`: asignacion_id, materia_id, titulo, hora, dia_semana, fecha_inicio, cant_semanas, fecha_unica, meet_url, vig_desde, vig_hasta
  - `InstanciaEncuentro(Base, TenantScopedMixin)`: slot_id (nullable), materia_id, fecha, hora, titulo, estado, meet_url, video_url, comentario

## Task 1.3 — Model: Guardia
- [x] Create `backend/app/models/guardia.py`
  - `Guardia(Base, TenantScopedMixin)`: asignacion_id, materia_id, carrera_id, cohorte_id, dia, horario, estado, comentarios, creada_at

## Task 1.4 — Schemas: encuentros
- [x] Create `backend/app/schemas/encuentro.py`
  - `SlotCreate`, `SlotOut`, `InstanciaOut`, `InstanciaUpdate`, `SlotWithInstancesOut`

## Task 1.5 — Schemas: guardias
- [x] Create `backend/app/schemas/guardia.py`
  - `GuardiaCreate`, `GuardiaOut`, `GuardiaFilter`

## Task 1.6 — Repository: EncuentroRepository
- [x] Create `backend/app/repositories/encuentro.py`
  - `SlotEncuentroRepository(BaseRepository[SlotEncuentro])`: create via base
  - `InstanciaEncuentroRepository(BaseRepository[InstanciaEncuentro])`: list_by_materia_slot, list_for_admin

## Task 1.7 — Repository: GuardiaRepository
- [x] Create `backend/app/repositories/guardia.py`
  - `GuardiaRepository(BaseRepository[Guardia])`: list_with_filters

## Task 1.8 — Service: EncuentrosService
- [x] Create `backend/app/services/encuentros.py`
  - `crear_slot_recurrente(data, actor_id)` — generates instances in transaction
  - `editar_instancia(id, data, actor_id)` — patch state/urls/comment
  - `generar_html(materia_id, asignacion_id)` — returns HTML string
  - `list_admin(materia_id?)` — returns all instances for tenant

## Task 1.9 — Service: GuardiasService
- [x] Create `backend/app/services/guardias.py`
  - `crear_guardia(data, actor_id)`
  - `list_guardias(filters)`
  - `exportar_csv(filters)`

## Task 1.10 — Router: /v1/encuentros
- [x] Create `backend/app/api/v1/routers/encuentros.py`
  - POST /v1/encuentros/slots
  - PATCH /v1/encuentros/{id}
  - GET /v1/encuentros/html
  - GET /v1/encuentros/admin

## Task 1.11 — Router: /v1/guardias
- [x] Create `backend/app/api/v1/routers/guardias.py`
  - POST /v1/guardias/
  - GET /v1/guardias/
  - GET /v1/guardias/exportar

## Task 1.12 — Register routers in main.py
- [x] Added encuentros_router and guardias_router to `create_application()`

## Task 1.13 — Tests (Strict TDD)
- [x] Create `backend/tests/test_encuentros.py`
  - Test: crear_slot_recurrente — 3 semanas genera 3 instancias ✅
  - Test: crear_slot_recurrente — 1 semana genera 1 instancia (triangulation) ✅
  - Test: encontrar_unico (cant_semanas=0) genera 1 instancia ✅
  - Test: editar_instancia estado + video_url ✅
  - Test: generar_html contiene tabla ✅
  - Test: list_admin retorna instancias del tenant ✅
  - Test: crear_guardia y listar ✅
  - Test: exportar_csv guardias tiene headers ✅
  - Test: tenant isolation — instancias de otro tenant no visibles ✅
  - Test: list_guardias por tenant ✅
