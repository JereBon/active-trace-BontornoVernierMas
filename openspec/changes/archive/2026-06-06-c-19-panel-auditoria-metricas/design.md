## Context

La tabla `audit_logs` existe y es append-only desde C-05. Almacena `tenant_id`, `actor_id`, `accion`, `detalle` (JSONB), `fecha_hora`, `filas_afectadas`, `ip`, `user_agent`. El permiso `auditoria:ver` ya está sembrado en `0003_rbac.py` y asignado a los roles COORDINADOR y ADMIN.

El repositorio existente `AuditLogRepository` solo expone `create()` y `list_by_tenant()` con filtro opcional por `actor_id`. Para el panel de métricas se requieren agregaciones SQL (`GROUP BY`, `func.count`, `func.date_trunc`) que no existen.

La tabla `comunicaciones` (C-12) contiene `estado` (Pendiente/Enviada/Fallida/Cancelada), `docente_id` y `tenant_id`, necesaria para el endpoint `/comunicaciones`.

## Goals / Non-Goals

**Goals:**
- Exponer tres endpoints de solo lectura bajo `/api/auditoria/` protegidos con `require_permission("auditoria:ver")`.
- Implementar el scope diferenciado: COORDINADOR ve solo `actor_id == current_user.id`; ADMIN ve todo el tenant.
- Proveer agregaciones SQL eficientes (GROUP BY con índices existentes en `tenant_id` y `actor_id`).
- Cobertura TDD ≥ 80% líneas / 90% reglas de negocio.

**Non-Goals:**
- No modificar ni extender `AuditLogRepository` original (append-only, su interfaz es contrato de C-05).
- No crear nueva tabla de base de datos.
- No agregar migración Alembic (el permiso ya existe).
- No exponer escrituras (todo es GET).
- No implementar frontend para este change.

## Decisions

### D1 — Nuevo `AuditoriaRepository` separado de `AuditLogRepository`

**Decisión**: Crear `repositories/auditoria_repository.py` con métodos de lectura + agregación, sin tocar `AuditLogRepository`.

**Rationale**: `AuditLogRepository` es append-only por contrato (C-05 design.md D1). Mezclar queries analíticas en él viola su responsabilidad única y podría confundir el invariante de inmutabilidad. Un repositorio dedicado expresa claramente que es solo-lectura para análisis.

**Alternativa descartada**: Extender `AuditLogRepository` con métodos `list_*` analíticos. Descartado porque rompe el principio de responsabilidad única del repositorio de escritura.

### D2 — Scope (propio) implementado en Service, no en Repository

**Decisión**: `AuditoriaService` recibe `current_user` completo y decide qué `actor_id` filtrar según el rol. El repositorio siempre recibe un `actor_id` opcional; si se pasa, filtra; si no, retorna todo el tenant.

**Rationale**: La lógica de negocio (quién puede ver qué) pertenece al Service. El Repository no conoce roles.

### D3 — Agregaciones con `func.date_trunc` de PostgreSQL

**Decisión**: Usar `sqlalchemy.func.date_trunc('day', AuditLog.fecha_hora)` para agrupar por día.

**Rationale**: Evita traer filas individuales al Python y agregar en memoria. Los índices en `tenant_id` + `actor_id` reducen el scan. La función `date_trunc` está disponible en PostgreSQL sin extensiones.

**Alternativa descartada**: Traer todos los registros y agregar en Python. Descartado por performance — audit_logs puede tener millones de filas.

### D4 — Sin migración para el permiso

**Decisión**: No crear migración `0016_*`. El permiso `auditoria:ver` ya está en `0003_rbac.py` asignado a COORDINADOR y ADMIN.

**Rationale**: Verificado directamente en el seed existente (líneas 52, 103, 127, 136 de `0003_rbac.py`).

### D5 — Paginación en `/log` con `limit` + `offset`

**Decisión**: El endpoint `/log` acepta `limit` (default 200, máx configurable) y `offset`. El límite default de 200 alinea con el requisito F9.1 (máx configurable, defecto 200).

**Rationale**: Cursor-based pagination sería más eficiente para tablas grandes, pero la tabla de auditoría no se expone como feed en tiempo real — es para revisión puntual. Limit/offset es suficiente y más simple de filtrar.

### D6 — Estado de comunicaciones desde tabla `comunicaciones`

**Decisión**: El endpoint `/comunicaciones` consulta la tabla `comunicaciones` (no `audit_logs`) agrupando por `docente_id` y `estado`.

**Rationale**: F9.1 pide "estado de comunicaciones por docente" — eso es información viva en la tabla de comunicaciones, no en el audit log. Usar audit_logs para esto requeriría parsear JSONB y es frágil.

## Risks / Trade-offs

- **[Riesgo] Queries lentos en audit_logs masivo** → Mitigation: índice en `(tenant_id, fecha_hora)` cubre el filtro de rango de fechas. Si la tabla crece a escala, agregar índice compuesto `(tenant_id, actor_id, fecha_hora)` como migración separada futura.
- **[Trade-off] Dos repositorios para audit_logs** → Acepto la duplicación porque el invariante append-only de C-05 es más importante que la DRY entre repos. La confusión potencial se mitiga con nombres claros: `AuditLogRepository` (escritura), `AuditoriaRepository` (lectura analítica).
- **[Riesgo] COORDINADOR ve sus propias acciones pero no las de su equipo** → Es la regla de negocio correcta según el scope `(propio)` del dominio. Si en el futuro se necesita ampliar el scope, es un cambio en el Service.

## Open Questions

- Ninguna. El permiso está sembrado, el modelo existe, las dependencias (C-05, C-07, C-12) están completas.
