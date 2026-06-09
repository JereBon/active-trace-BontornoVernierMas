## 1. Modelos SQLAlchemy

- [x] 1.1 Crear `backend/app/models/aviso.py` con modelo `Aviso`: campos `id` (UUID PK), `tenant_id` (FK), `titulo`, `cuerpo`, `scope` (Enum: TODOS/ROL/USUARIO), `scope_valor` (nullable), `vig_desde`, `vig_hasta`, `activo` (bool, default True), `publicado_por` (UUID FK a usuario), `created_at`, `updated_at`. Heredar de `Base` (soft delete vía `activo`).
- [x] 1.2 Crear `backend/app/models/aviso_ack.py` con modelo `AvisoAck`: campos `id` (UUID PK), `tenant_id`, `aviso_id` (FK a Aviso), `usuario_id` (UUID), `leido_en` (datetime). Constraint UNIQUE(`aviso_id`, `usuario_id`).
- [x] 1.3 Registrar ambos modelos en `backend/app/models/__init__.py`.

## 2. Migración Alembic

- [x] 2.1 Crear migración `backend/alembic/versions/0006_avisos_y_acks.py` (siguiente número libre tras `0005`) con `upgrade()` que crea tablas `avisos` y `aviso_acks`, y `downgrade()` que las elimina.

## 3. Schemas Pydantic

- [x] 3.1 Crear `backend/app/schemas/aviso.py` con:
  - `AvisoCreate`: `titulo`, `cuerpo`, `scope`, `scope_valor` (optional), `vig_desde`, `vig_hasta`. `model_config = ConfigDict(extra='forbid')`. Validador que `vig_hasta > vig_desde`.
  - `AvisoRead`: campos de `AvisoCreate` + `id`, `activo`, `publicado_por`, `tenant_id`, `created_at`.
  - `AvisoPatch`: solo `activo` (bool). `model_config = ConfigDict(extra='forbid')`.
  - `AvisoAckRead`: `usuario_id`, `leido_en`.

## 4. Repository

- [x] 4.1 Crear `backend/app/repositories/aviso_repository.py` con `AvisoRepository`:
  - `create(tenant_id, publicado_por, data: AvisoCreate) -> Aviso`
  - `list_vigentes(tenant_id, usuario_id, roles) -> list[Aviso]` — filtra por `activo=True`, ventana de vigencia y scope de audiencia.
  - `get_by_id(tenant_id, aviso_id) -> Aviso | None`
  - `patch(tenant_id, aviso_id, data: AvisoPatch) -> Aviso`
  - `create_ack(tenant_id, aviso_id, usuario_id) -> AvisoAck` — idempotente (`ON CONFLICT DO NOTHING` o captura IntegrityError).
  - `list_acks(tenant_id, aviso_id) -> list[AvisoAck]`
- [x] 4.2 Registrar `AvisoRepository` en `backend/app/repositories/__init__.py`.

## 5. Router / Endpoints

- [x] 5.1 Crear `backend/app/api/v1/avisos.py` con los endpoints:
  - `POST /api/avisos` — `require_permission("avisos:publicar")`, llama a `AvisoRepository.create`, devuelve 201.
  - `GET /api/avisos` — cualquier usuario autenticado, llama a `list_vigentes` con roles del JWT.
  - `POST /api/avisos/{id}/ack` — `require_permission("avisos:confirmar")`, llama a `create_ack`, devuelve 200.
  - `GET /api/avisos/{id}/acks` — `require_permission("avisos:publicar")`, llama a `list_acks`.
  - `PATCH /api/avisos/{id}` — `require_permission("avisos:publicar")`, soft delete (activo=False), devuelve aviso actualizado.
- [x] 5.2 Registrar el router en `backend/app/main.py` (o en el router principal de la API v1).

## 6. Tests (Strict TDD)

- [x] 6.1 Crear `backend/tests/test_avisos.py`. Safety net: ejecutar suite existente y capturar baseline.
- [x] 6.2 **RED** Test: crear aviso con usuario con permiso → 201, aviso en DB.
- [x] 6.3 **GREEN** Implementar `POST /api/avisos` mínimo para pasar.
- [x] 6.4 **TRIANGULATE** Test: crear aviso sin permiso → 403. Test: `vig_hasta < vig_desde` → 422.
- [x] 6.5 **RED** Test: listar avisos vigentes → solo los activos dentro de ventana de vigencia del tenant.
- [x] 6.6 **GREEN/TRIANGULATE**: aviso desactivado no aparece; aviso fuera de ventana no aparece.
- [x] 6.7 **RED** Test: `POST /ack` primera vez → 200, registro en DB.
- [x] 6.8 **GREEN/TRIANGULATE**: segundo ack idempotente → 200 sin duplicados.
- [x] 6.9 **RED** Test: `GET /acks` con permiso → lista de confirmaciones. Sin permiso → 403.
- [x] 6.10 **REFACTOR**: limpiar tests, extraer fixtures comunes.
