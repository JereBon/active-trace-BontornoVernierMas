## Design — C-13: Encuentros y Guardias

### D1 — Domain model mapping

`SlotEncuentro` is a recurrence template linked to `Asignacion` (who created it) and `Materia`.
`InstanciaEncuentro` is a concrete occurrence; `slot_id` is nullable for one-off instances.
`Guardia` is an independent shift record linked to `Asignacion`, `Materia`, `Carrera`, `Cohorte`.

All three tables inherit `TenantScopedMixin` (id, tenant_id, created/updated/deleted_at).

### D2 — Recurrence generation (RN-13)

When a slot with `cant_semanas > 0` is created the service generates exactly `cant_semanas` `InstanciaEncuentro` rows in a single transaction. The first instance date = `fecha_inicio`; subsequent dates add `7 * n` days for n = 1…cant_semanas-1.

When `cant_semanas == 0` the caller must provide `fecha_unica` on the slot; one `InstanciaEncuentro` is created with that date (F6.2 one-off case). The service validates that exactly one of `(cant_semanas > 0, fecha_unica)` is provided.

### D3 — State enum for InstanciaEncuentro

Stored as `String` (not native PG ENUM) to avoid DDL cost on future states.
Valid values: `Programado`, `Realizado`, `Cancelado`.

### D4 — HTML block generation (F6.4)

`GET /v1/encuentros/html?materia_id=&asignacion_id=` returns a plain `text/html` string built in-memory. The service orders instances by `fecha` ASC and generates a table row per instance with columns: fecha, hora, titulo, meet_url (link), video_url (link if set), estado. No file I/O.

### D5 — Guardia CSV export (F6.6)

Same pattern as `exportar_csv` in `EquiposService`: `io.StringIO` + `csv.DictWriter`, headers always present, returns the string. The endpoint wraps it in `StreamingResponse`.

### D6 — Permission scheme

- `encuentros:gestionar` — create slot, create one-off, patch instance, get HTML, get admin list. Required for all encuentro write ops; reads also require it for the admin view.
- `guardias:registrar` — create guardia (tutor self-register); coordinador/admin also have this permission so they can query.

### D7 — Migration 0011

Creates three tables: `slot_encuentro`, `instancia_encuentro`, `guardia`.
down_revision = "0009" (0010 is C-10 parallel branch — this migration does NOT chain from it).

### D8 — No business logic in routers

Routers translate HTTP → service calls and commit transactions. Services contain all logic. Repositories handle all DB access.

### D9 — Audit codes

- `ENCUENTRO_SLOT_CREAR`
- `ENCUENTRO_INSTANCIA_EDITAR`
- `GUARDIA_CREAR`
