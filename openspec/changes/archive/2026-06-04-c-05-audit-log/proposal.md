## Why

El sistema requiere trazabilidad completa de toda acción significativa para cumplir con los requisitos de auditoría institucional y seguridad multi-tenant. Sin un log de auditoría inmutable, no es posible detectar accesos indebidos, reconstruir eventos ante incidentes, ni auditar el uso de la funcionalidad de impersonación.

## What Changes

- Nuevo modelo `AuditLog` (E-AUD): registro append-only de acciones significativas con campos actor_id, actor_impersonado_id (nullable), tenant_id, accion (código string), detalle (JSONB), filas_afectadas, ip, user_agent, fecha_hora.
- Helper/función de auditoría reutilizable desde cualquier service para registrar acciones con mínimo boilerplate.
- Endpoint `POST /api/auth/impersonate` con permiso `impersonacion:usar`: inicia sesión de impersonación, genera token distinguible y registra `IMPERSONACION_INICIAR` en el audit log.
- Endpoint `POST /api/auth/impersonate/end`: finaliza impersonación, registra `IMPERSONACION_FINALIZAR`.
- Migración Alembic `0004_audit_log`.
- El modelo es estrictamente append-only: sin UPDATE ni DELETE a nivel aplicación ni base de datos.
- Las acciones bajo impersonación se atribuyen siempre al actor real (quién impersona), no al usuario impersonado.

## Capabilities

### New Capabilities
- `audit-log`: Registro inmutable de acciones significativas del sistema. Cubre modelo AuditLog, helper de auditoría, migración 0004, y endpoints de impersonación con registro de inicio/fin.

### Modified Capabilities

## Impact

- `backend/app/models/`: nuevo archivo `audit_log.py`
- `backend/app/repositories/`: nuevo `audit_log.py` (solo `create` y `list`, sin update/delete)
- `backend/app/core/audit.py`: helper de auditoría reutilizable
- `backend/alembic/versions/`: nueva migración `0004_audit_log`
- `backend/app/routers/auth.py`: nuevos endpoints de impersonación
- `backend/app/models/__init__.py`, `backend/app/repositories/__init__.py`: exports actualizados
- `backend/tests/`: tests append-only, atribución bajo impersonación, registro de acción
