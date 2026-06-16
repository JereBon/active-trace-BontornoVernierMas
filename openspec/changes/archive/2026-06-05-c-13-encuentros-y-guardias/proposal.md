## Why

The platform needs to track synchronous encounters (virtual classes) and tutor duty shifts (guardias) so COORDINADOR can supervise availability and coverage, and docentes can publish meeting links and recordings to the LMS with a single click.

## What Changes

- New models: `SlotEncuentro` (recurrence template), `InstanciaEncuentro` (concrete meeting), `Guardia` (duty shift record).
- New endpoints: `POST /v1/encuentros/slots` (create slot + generate instances), `POST /v1/encuentros/unico` (one-off instance), `PATCH /v1/encuentros/{id}` (edit state/urls/comment), `GET /v1/encuentros/html` (HTML block for LMS), `GET /v1/encuentros/admin` (coord/admin overview).
- New endpoints: `POST /v1/guardias/`, `GET /v1/guardias/`, `GET /v1/guardias/exportar` (CSV).
- Alembic migration **0011**: tables `slot_encuentro`, `instancia_encuentro`, `guardia`.
- Permission guards: `encuentros:gestionar` and `guardias:registrar` (already in `permisos.py`).

## Capabilities

### New Capabilities
- `encuentros`: Recurrent and one-off synchronous encounter management with LMS HTML export.
- `guardias`: Tutor duty-shift registration and coordinador-level CSV export.

### Modified Capabilities
<!-- none -->

## Impact

- New migration 0011 (parallel with C-10 which owns 0010).
- New files: `models/encuentro.py`, `models/guardia.py`, `repositories/encuentro.py`, `repositories/guardia.py`, `services/encuentros.py`, `services/guardias.py`, `schemas/encuentro.py`, `schemas/guardia.py`, `api/v1/routers/encuentros.py`, `api/v1/routers/guardias.py`.
- `main.py` must include the two new routers.
- Test file: `tests/test_encuentros.py`.
