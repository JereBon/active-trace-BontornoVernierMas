## Context

activia-trace es una plataforma multi-tenant con RBAC fino. Cualquier acción significativa (importación de calificaciones, gestión de equipos, impersonación, cierre de liquidaciones) debe quedar registrada de forma inmutable para auditoría institucional y cumplimiento de seguridad.

El sistema ya cuenta con: `BaseRepository` con `TenantScopedMixin`, `get_current_user` que retorna `UsuarioAutenticado` (con `permisos_efectivos`), el guard `require_permission`, y migraciones 0001–0003. C-04 (RBAC) está completo.

Restricción clave: el `AuditLog` **no** puede heredar el mixin de soft-delete porque es intrínsecamente append-only — el soft-delete requeriría poder "borrar" o "restaurar" registros, lo cual viola el contrato del log.

## Goals / Non-Goals

**Goals:**
- Modelo `AuditLog` append-only con garantía a nivel aplicación (sin update/delete en el repositorio).
- Helper `audit_action()` reutilizable desde cualquier service con mínimo boilerplate.
- Soporte de impersonación: token distinguible, atribución al actor real, registro de inicio/fin.
- Migración Alembic `0004_audit_log`.
- Tests: append-only forzado, atribución bajo impersonación, registro de acción con código + filas.

**Non-Goals:**
- UI de consulta del log de auditoría (C-xx futuro).
- Rotación / archivado de logs viejos.
- Integración con sistemas SIEM externos.
- Garantías de append-only a nivel DB (triggers, RLS) — queda para hardening futuro.

## Decisions

### D1: AuditLog no hereda TimestampMixin ni SoftDeleteMixin
`fecha_hora` se define explícitamente en el modelo. No tiene `deleted_at`. El repositorio solo expone `create` y consultas de lectura; update y delete no existen en la interfaz pública. Esto hace el contrato explícito y auditable en código.

*Alternativa considerada*: usar `SoftDeleteMixin` igual que el resto de entidades para uniformidad. Rechazada: semanticamente incorrecto — un audit log no se "elimina suavemente", simplemente no se elimina nunca.

### D2: Helper `audit_action()` como función async de utilidad, no como decorator
Un decorator es atractivo pero opaco: oculta que hay I/O (escritura a DB), complica el pasaje de contexto (tenant_id, ip, user_agent) y hace difícil el manejo de errores (¿qué pasa si falla el log?). Una función explícita `await audit_action(session, actor_id, accion, ...)` es más legible y testeable.

*Alternativa considerada*: decorator `@auditar(accion="CALIFICACIONES_IMPORTAR")`. Rechazada por los motivos arriba; puede agregarse encima de la función si se desea en el futuro.

### D3: Política de fallo del helper de auditoría — "best-effort, log y continúa"
Si la escritura del audit log falla (error de DB transitorio), el sistema **no** debe rollbackear la operación principal. El log falla en silencio con un `logger.error()`. La operación de negocio tiene prioridad.

*Alternativa considerada*: falla estricta (el log falla → la operación falla). Rechazada: demasiado frágil para funcionalidades core como importación de calificaciones.

### D4: Token de impersonación como JWT estándar con claim adicional `impersonating_user_id`
El token de sesión bajo impersonación es un JWT normal pero con el claim `impersonating_user_id` (UUID del usuario impersonado) y `sub` = UUID del **actor real**. Esto permite que `get_current_user` retorne siempre la identidad real, y que el claim de impersonación sea visible y verificable.

*Alternativa considerada*: sesión separada con header `X-Impersonate`. Rechazada: más compleja de mantener y propensa a errores en la verificación.

### D5: `actor_impersonado_id` en AuditLog — siempre explícito
Cuando la acción ocurre bajo impersonación, `actor_id` = UUID del actor real, `actor_impersonado_id` = UUID del usuario impersonado. Si no hay impersonación, `actor_impersonado_id` = NULL. Esta distinción es obligatoria para toda acción realizada bajo impersonación.

## Risks / Trade-offs

- [Riesgo] El helper de auditoría se llama manualmente desde cada service → puede olvidarse en nuevos endpoints. → Mitigación: documentar el patrón en CLAUDE.md, code review checklist, y tests de integración que verifican que ciertas acciones generen logs.
- [Riesgo] Volumen alto de registros en producción sin índices adecuados → degradación de consultas. → Mitigación: índices en `(tenant_id, fecha_hora)` y `(actor_id)` desde la migración inicial.
- [Riesgo] Token JWT con claim de impersonación podría ser mal interpretado por middleware futuro. → Mitigación: documentar el claim en el design de auth; `get_current_user` siempre usa `sub` como identidad principal.

## Migration Plan

1. Aplicar migración `0004_audit_log` (crear tabla `audit_logs` con índices).
2. No hay rollback destructivo: la tabla se puede eliminar sin afectar datos de negocio.
3. Los endpoints de impersonación son nuevos; no hay cambios breaking en endpoints existentes.

## Open Questions

- ¿Se necesita endpoint de consulta del log en este change (C-05) o se difiere a un change futuro? → Decisión: diferido. C-05 solo implementa escritura y los endpoints de impersonación.
