## 1. Modelo AuditLog

- [x] 1.1 Crear `backend/app/models/audit_log.py` con el modelo SQLAlchemy `AuditLog` (campos: id UUID PK, tenant_id, fecha_hora UTC, actor_id, actor_impersonado_id nullable, accion str, detalle JSONB, filas_afectadas int, ip str, user_agent str). Sin TimestampMixin, sin SoftDeleteMixin.
- [x] 1.2 Agregar `AuditLog` a `backend/app/models/__init__.py`

## 2. Repositorio de auditoría

- [x] 2.1 Crear `backend/app/repositories/audit_log.py` con clase `AuditLogRepository` que hereda de `BaseRepository` con `TenantScopedMixin`. Solo exponer `create()` y `list_by_tenant()`. Los métodos `update` y `delete` MUST lanzar `NotImplementedError`.
- [x] 2.2 Agregar `AuditLogRepository` a `backend/app/repositories/__init__.py`

## 3. Helper de auditoría

- [x] 3.1 Crear `backend/app/core/audit.py` con función async `audit_action(session, actor_id, tenant_id, accion, detalle, filas_afectadas, ip, user_agent, actor_impersonado_id=None)`. Usa `AuditLogRepository` internamente. Implementar política best-effort: capturar excepciones, loguear con `logger.error` y continuar sin propagar.

## 4. Migración Alembic

- [x] 4.1 Crear migración `backend/alembic/versions/0004_audit_log.py` con `op.create_table("audit_logs", ...)`. Incluir índices en `(tenant_id, fecha_hora)` y `(actor_id)`. Sin `downgrade` destructivo (solo `op.drop_table`).

## 5. Endpoints de impersonación

- [x] 5.1 Crear `backend/app/routers/auth.py` (o extender el existente) con `POST /api/auth/impersonate`: requiere permiso `impersonacion:usar`, recibe `user_id` en body, retorna JWT con claims `sub` = actor real y `impersonating_user_id` = usuario impersonado. Registrar `IMPERSONACION_INICIAR` vía `audit_action()`.
- [x] 5.2 Agregar `POST /api/auth/impersonate/end`: extrae actor real e impersonado del token actual, registra `IMPERSONACION_FINALIZAR`, retorna nuevo JWT sin claim de impersonación.
- [x] 5.3 Actualizar `get_current_user` en `backend/app/core/dependencies.py` (o equivalente) para extraer `impersonating_user_id` del JWT y exponer el contexto de impersonación en `UsuarioAutenticado`.

## 6. Tests

- [x] 6.1 Crear `backend/tests/test_audit_log.py`: test append-only (update lanza NotImplementedError, delete lanza NotImplementedError), test creación de registro con todos los campos.
- [x] 6.2 Agregar tests de atribución bajo impersonación: verificar que `actor_id` = actor real y `actor_impersonado_id` = usuario impersonado al registrar acción bajo sesión de impersonación.
- [x] 6.3 Agregar tests de endpoints de impersonación: inicio sin permiso → 403, inicio con permiso → JWT con claim, fin → registro IMPERSONACION_FINALIZAR.
- [x] 6.4 Agregar test del helper `audit_action()`: fallo de DB no propaga excepción, acción con código + filas_afectadas persiste correctamente.
