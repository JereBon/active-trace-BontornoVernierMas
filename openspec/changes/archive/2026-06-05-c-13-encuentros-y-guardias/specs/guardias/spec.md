# Spec: guardias

## Overview
Tutor duty-shift registration and coordinator-level visibility with CSV export.

## Scenarios

### SC-01: Register a guardia (F6.6)
- Given a TUTOR (or COORDINADOR/ADMIN) authenticated user
- When POST /v1/guardias/ with asignacion_id, materia_id, carrera_id, cohorte_id, dia, horario, estado, comentarios
- Then a `Guardia` is persisted with estado=Pendiente (or as provided)
- And audit log entry GUARDIA_CREAR is written

### SC-02: List guardias
- Given any authenticated user with guardias:registrar
- When GET /v1/guardias/?materia_id=&asignacion_id= (optional filters)
- Then guardias for the current tenant matching filters are returned

### SC-03: Export CSV
- Given COORDINADOR or ADMIN credentials
- When GET /v1/guardias/exportar (with optional filters)
- Then response is text/csv with all matching guardias, headers always present

## Acceptance criteria
- Permission `guardias:registrar` required for all endpoints
- `tenant_id` always from JWT
- CSV uses io.StringIO; no temp files
