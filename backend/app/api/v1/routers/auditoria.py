"""api/v1/routers/auditoria.py — Auditoria endpoints (C-19: panel-auditoria-metricas).

Identity and tenant_id ALWAYS come from the verified JWT (CurrentUser).
Never from URL params, body, or headers.

Endpoints:
  GET /v1/auditoria/panel           — aggregate metrics panel (auditoria:ver)
  GET /v1/auditoria/log             — filtered, paginated audit log (auditoria:ver)
  GET /v1/auditoria/comunicaciones  — communication status by docente (auditoria:ver)

All endpoints require permission: auditoria:ver.
Scope (propio) for COORDINADOR is applied in AuditoriaService, not here.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import CurrentUser, DBSession
from app.core.permisos import AUDITORIA_VER
from app.core.rbac import require_permission
from app.schemas.auditoria import (
    ComunicacionDocenteOut,
    LogPaginadoOut,
    PanelMetricasOut,
)
from app.services.auditoria_service import AuditoriaService

router = APIRouter(
    prefix="/v1/auditoria",
    tags=["auditoria"],
)

_PERM = Depends(require_permission(AUDITORIA_VER))


# ── GET /panel ────────────────────────────────────────────────────────────────


@router.get(
    "/panel",
    response_model=PanelMetricasOut,
    dependencies=[_PERM],
    summary="Aggregate audit metrics panel (F9.1, RN-19)",
)
async def get_panel(
    session: DBSession,
    current_user: CurrentUser,
) -> Any:
    """Return aggregate audit metrics.

    COORDINADOR: scoped to own actions.
    ADMIN: all actions in the tenant.
    """
    svc = AuditoriaService(session, current_user.tenant_id)
    return await svc.get_panel(current_user)


# ── GET /log ──────────────────────────────────────────────────────────────────


@router.get(
    "/log",
    response_model=LogPaginadoOut,
    dependencies=[_PERM],
    summary="Paginated, filtered audit log (F9.2)",
)
async def get_log(
    session: DBSession,
    current_user: CurrentUser,
    fecha_desde: date | None = Query(default=None, description="Include entries on or after this date"),
    fecha_hasta: date | None = Query(default=None, description="Include entries on or before this date"),
    usuario_id: uuid.UUID | None = Query(default=None, description="Filter by actor (ADMIN only)"),
    accion: str | None = Query(default=None, description="Filter by exact action code"),
    limit: int = Query(default=200, ge=1, le=1000, description="Max entries (default 200)"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
) -> Any:
    """Return paginated audit log entries with optional filters.

    COORDINADOR: actor_id is forced to own user_id; usuario_id param ignored.
    ADMIN: actor_id uses usuario_id param (if provided).
    """
    svc = AuditoriaService(session, current_user.tenant_id)
    return await svc.get_log(
        current_user,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        usuario_id=usuario_id,
        accion=accion,
        limit=limit,
        offset=offset,
    )


# ── GET /comunicaciones ───────────────────────────────────────────────────────


@router.get(
    "/comunicaciones",
    response_model=list[ComunicacionDocenteOut],
    dependencies=[_PERM],
    summary="Communication status by docente (F9.3)",
)
async def get_comunicaciones(
    session: DBSession,
    current_user: CurrentUser,
) -> Any:
    """Return communication counts grouped by estado for each docente.

    COORDINADOR: scoped to own sent communications.
    ADMIN: all docentes in the tenant.

    Data source: 'comunicaciones' table (not audit_logs).
    """
    svc = AuditoriaService(session, current_user.tenant_id)
    return await svc.get_comunicaciones(current_user)
