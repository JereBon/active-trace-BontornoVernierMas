## Why

El sistema genera logs de auditoría (C-05) y comunicaciones (C-12) de forma continua, pero no existe ninguna interfaz que permita a COORDINADOREs y ADMINs consultar, filtrar ni agregar esos datos. Sin este panel, la auditoría es ciega: los datos existen pero no son accionables.

## What Changes

- Nuevo módulo de solo lectura sobre `audit_logs` (append-only, sin escrituras).
- Tres endpoints REST bajo `/api/auditoria/`:
  - `GET /panel` — métricas agregadas: acciones por día, interacciones por docente, interacciones por docente×materia.
  - `GET /log` — log completo paginado con filtros (rango de fechas, materia, usuario, acción).
  - `GET /comunicaciones` — estado de comunicaciones por docente (conteo por estado: Pendiente, Enviada, Fallida, Cancelada).
- Scope de visibilidad diferenciado: COORDINADOR ve solo sus propias acciones (`actor_id == current_user.id`); ADMIN ve todo el tenant.
- Guard universal: `require_permission("auditoria:ver")` en todos los endpoints.
- Sin nueva tabla de base de datos; sin migración Alembic (el permiso `auditoria:ver` ya está sembrado en `0003_rbac.py`).

## Capabilities

### New Capabilities
- `auditoria-panel`: Panel de métricas de auditoría — agregaciones por día/docente/materia y log paginado con filtros sobre `audit_logs`.

### Modified Capabilities
<!-- Ninguna: no cambia ninguna especificación existente de otros módulos. -->

## Impact

- **Backend**: nuevos archivos `repositories/auditoria_repository.py`, `services/auditoria_service.py`, `schemas/auditoria.py`, `api/v1/routers/auditoria.py`. Registro del router en `main.py`.
- **Base de datos**: solo lectura sobre `audit_logs` y `comunicaciones`. Sin DDL.
- **Seguridad**: scope de tenant obligatorio; scope `(propio)` para COORDINADOR.
- **Tests**: `tests/test_auditoria.py` — TDD sobre agregaciones, filtros, scope y paginación.
