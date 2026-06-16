# Spec: encuentros

## Overview
Manages synchronous encounter slots and their concrete instances for a materia/asignacion pair.

## Scenarios

### SC-01: Create recurrent slot (F6.1, RN-13)
- Given a valid `asignacion_id`, `materia_id`, `titulo`, `hora`, `dia_semana`, `fecha_inicio`, `cant_semanas >= 1`
- When POST /v1/encuentros/slots
- Then a `SlotEncuentro` is persisted and exactly `cant_semanas` `InstanciaEncuentro` rows are generated, with dates = fecha_inicio + 7*n days for n = 0…cant_semanas-1, each with estado=Programado
- And audit log entry ENCUENTRO_SLOT_CREAR is written

### SC-02: Create one-off encounter (F6.2)
- Given a valid `asignacion_id`, `materia_id`, `titulo`, `hora`, `fecha_unica`, `cant_semanas=0`
- When POST /v1/encuentros/slots
- Then one `SlotEncuentro` with `fecha_unica` set and one `InstanciaEncuentro` with that date are persisted

### SC-03: Edit instance state (F6.3)
- Given an existing `InstanciaEncuentro` in the caller's tenant
- When PATCH /v1/encuentros/{id} with estado=Realizado, video_url="https://..."
- Then the instance is updated and returned

### SC-04: Generate HTML block (F6.4)
- Given instances for a materia/asignacion
- When GET /v1/encuentros/html?materia_id=&asignacion_id=
- Then response Content-Type is text/html and contains a table with encuentros ordered by fecha ASC

### SC-05: Admin view (F6.5)
- Given COORDINADOR or ADMIN credentials
- When GET /v1/encuentros/admin?materia_id= (optional filter)
- Then all instancias for the tenant are returned (beyond the requester's own asignacion)

## Acceptance criteria
- Permission `encuentros:gestionar` required for all endpoints
- `tenant_id` always sourced from JWT; never from request body
- Instances generated in single transaction with slot
- `cant_semanas=0` requires `fecha_unica` present; `cant_semanas>0` ignores `fecha_unica`
