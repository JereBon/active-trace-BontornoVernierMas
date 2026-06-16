## Context

activia-trace necesita enviar comunicaciones de email a alumnos atrasados detectados por el módulo de análisis (C-11). Actualmente el sistema tiene toda la infraestructura de identidad, RBAC y auditoría lista, pero no tiene capa de mensajería saliente. Esta capa debe ser asíncrona (no bloquear el request del docente), auditable, con PII cifrada en reposo, y con un gate de aprobación configurable por tenant para envíos masivos.

La entidad `Comunicacion` (E21, KB §04) ya está definida en el modelo de datos con todos sus atributos. La infra de cifrado (`backend/app/core/crypto.py`) y auditoría (`backend/app/core/audit.py`) está lista.

**ADR-003** (KB §08 §8) dejó abierta la elección del worker: asyncio puro vs. Celery/ARQ vs. N8N. Se resuelve aquí.

---

## Goals / Non-Goals

**Goals:**
- Implementar la máquina de estados `Pendiente → Enviando → Enviado | Error | Cancelado` (RN-15) para mensajes salientes.
- Proveer preview obligatorio antes de encolar (F3.1, RN-16).
- Proveer endpoint de encolado masivo con `lote_id` (F3.2).
- Proveer aprobación/cancelación por lote e individual (F3.3, RN-17).
- Cifrar `destinatario` en reposo con AES-256-GCM.
- Worker asíncrono que consume cola y transiciona estados.
- Auditoría de todas las acciones de comunicación.
- Tenant isolation: scope por `tenant_id` en todo query.

**Non-Goals:**
- Integración real con proveedor SMTP/SES (el worker despacha vía stub/config externo en esta iteración; la integración concreta es C-12 extensión o C-22).
- Frontend para visualizar el panel de comunicaciones (es otro change).
- Mensajería interna / bandeja (F3.4) — fuera de alcance.
- Tablón de avisos (F3.5) — fuera de alcance.

---

## Decisions

### D1 — Worker: asyncio puro con polling (resuelve ADR-003)

**Alternativas consideradas**:
- **Celery + Redis**: potente pero agrega dos nuevas dependencias de infraestructura (broker Redis + Celery worker) que complican el docker-compose para este alcance.
- **ARQ**: buen ajuste para asyncio + Redis, pero igual requiere Redis.
- **N8N**: ya existe en el stack para integraciones con Moodle, pero usarlo como worker de cola de mensajes acoplaría la lógica de negocio a un orquestador externo, perdiendo trazabilidad dentro del sistema.
- **asyncio puro con polling** (elegida): el worker es una tarea asyncio que corre en el mismo proceso FastAPI (como background task de arranque) o como proceso separado con el mismo código. Lee mensajes `Pendiente` de la DB con `SELECT FOR UPDATE SKIP LOCKED` para garantizar que dos workers no tomen el mismo mensaje. Sin nueva infraestructura, encaja con SQLAlchemy async ya instalado. El volumen de mensajes en esta etapa no justifica un broker externo. Si el volumen escala, migrar a ARQ es un refactor acotado.

**Consecuencias**: el worker necesita su propio scope de sesión DB (no usa la sesión del request HTTP). Se instancia con `async_sessionmaker` del mismo engine.

### D2 — Lote como UUID generado en el servicio (no en la DB)

El `lote_id` es un UUID generado por `ComunicacionService.encolar_lote()` antes de persistir. Todos los mensajes del mismo lote comparten el mismo `lote_id`. Esto permite agrupar, aprobar o cancelar el lote completo con un único filtro por `lote_id`.

**Alternativa**: tabla `Lote` separada. Rechazada: el lote es un atributo de agrupación, no una entidad con ciclo de vida propio. Si necesita campos adicionales (aprobado_por, aprobado_at) se agregan a `Comunicacion` o se crean en un change futuro.

**Consecuencias**: la "aprobación del lote" es en realidad UPDATE masivo de todos los registros con el mismo `lote_id` que estén en estado `Pendiente`. Es idempotente.

### D3 — Aprobación configurable por tenant vía flag en DB

El flag `requiere_aprobacion_masiva: bool` se añade a la tabla `tenant` (o se resuelve en una config de tenant). Para esta iteración, dado que la tabla `tenant` ya existe (C-01), se agrega la columna `comunicacion_requiere_aprobacion` con default `True`. El servicio consulta este flag al encolar. Si `True` y el lote tiene >1 destinatario, los mensajes quedan en `Pendiente` y esperan aprobación explícita. Si `False`, pasan directo a `Enviando`.

**Alternativa**: threshold numérico configurable por tenant (e.g., aprobar solo si >50 destinatarios). Rechazada por complejidad en esta iteración; se puede extender luego.

### D4 — destinatario cifrado AES-256-GCM

`Comunicacion.destinatario` se almacena con `crypto.encrypt(email)` usando el módulo `backend/app/core/crypto.py` ya existente. El descifrado ocurre en el worker al momento del despacho, y en el servicio cuando se necesita para el preview. Nunca se expone el email en texto plano en la respuesta API (se devuelve enmascarado: `***@dominio.com` para las vistas de seguimiento).

### D5 — Máquina de estados: transiciones válidas

```
Pendiente ──►  Enviando ──► Enviado
                    └────► Error
Pendiente ──►  Cancelado
```

Transiciones inválidas (rechazadas por el servicio con 409 Conflict):
- `Enviado → cualquier estado`
- `Cancelado → cualquier estado`
- `Error → cualquier estado` (se puede reencolar como nueva `Comunicacion`)
- `Enviando → Pendiente`
- `Enviando → Cancelado` (sólo se cancela desde `Pendiente`)

El servicio valida la transición antes de escribir en DB. El worker es el único que transiciona de `Pendiente → Enviando` y de `Enviando → Enviado | Error`. Los usuarios sólo pueden transicionar `Pendiente → Cancelado`.

### D6 — Preview no persiste; sólo renderiza

El endpoint `/api/comunicaciones/preview` recibe el template y las variables de sustitución, renderiza y devuelve el resultado. No crea ningún registro en DB. La confirmación del envío es una llamada separada al endpoint de encolado. Esto evita estados intermedios "preview pendiente" y simplifica la máquina de estados.

---

## Risks / Trade-offs

- **[Risk] El polling puede perder mensajes si el worker cae entre `Enviando` y el despacho real** → Mitigation: el worker tiene un timeout; si un mensaje queda en `Enviando` por más de N minutos (configurable), el job de reintento lo vuelve a `Error`. Implementar en la primera iteración como TODO documentado; el volumen inicial es bajo.
- **[Risk] SELECT FOR UPDATE SKIP LOCKED no funciona en SQLite** → Mitigation: no aplica; el stack define PostgreSQL obligatorio. Los tests usan PostgreSQL (no mock DB).
- **[Risk] Cifrar `destinatario` impide buscar por email en DB** → Mitigation: el lookup por email usa la clave de cifrado para comparar; o bien se indexa un hash (SHA-256) del email para búsqueda sin exponer el valor. Para esta iteración se omite el índice de hash (las consultas de estado van por `lote_id` o `id`), documentado como limitación.
- **[Risk] Migración 0013 puede fallar si hay datos en `tenant` sin la nueva columna** → Mitigation: la columna `comunicacion_requiere_aprobacion` tiene `server_default=TRUE`, por lo que no requiere backfill.

---

## Migration Plan

1. Alembic genera la migración `0013_comunicacion` con:
   - Tabla `comunicacion` (todos los campos de E21 + `deleted_at`).
   - Columna `comunicacion_requiere_aprobacion BOOLEAN DEFAULT TRUE NOT NULL` en `tenant`.
   - Índices: `(tenant_id)`, `(lote_id)`, `(estado)`, `(tenant_id, lote_id)`.
2. Deploy: `alembic upgrade head` antes de arrancar el nuevo código.
3. Rollback: `alembic downgrade -1` elimina la tabla y la columna. Sin pérdida de datos existentes.

---

## Open Questions

- OQ-1: ¿El worker debe correr como proceso separado o como background task dentro del proceso FastAPI? Para producción (Easypanel), separado es más robusto; para esta iteración, como background task es más simple. **Decisión provisional**: background task en arranque, con hook de shutdown limpio. Se puede separar sin cambiar la lógica de negocio.
- OQ-2: ¿El provider de email (SMTP / SES / SendGrid) es configurable por tenant o global? **Provisoriamente**: configurable por variable de entorno global. Configuración por tenant es extensión futura.
- OQ-3: ¿Se notifica al docente cuando el lote termina de enviarse? Requiere WebSocket o polling desde frontend. Fuera de alcance de C-12.
