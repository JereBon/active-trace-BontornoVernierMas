"""api/v1/routers/guardias.py — Guardia endpoints (C-13).

All endpoints require 'guardias:registrar' permission.
Identity and tenant_id always come from the verified JWT (CurrentUser).
No business logic here — only HTTP translation → service calls.

Endpoints:
  POST   /v1/guardias/          Register a new guardia (F6.6)
  GET    /v1/guardias/          List guardias with optional filters (F6.6)
  GET    /v1/guardias/exportar  Export guardias as CSV (F6.6)
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse

from app.core.dependencies import CurrentUser, DBSession
from app.core.permisos import GUARDIAS_REGISTRAR
from app.core.rbac import require_permission
from app.schemas.guardia import GuardiaCreate, GuardiaFilter, GuardiaOut
from app.services.guardias import GuardiasService

router = APIRouter(prefix="/v1/guardias", tags=["guardias"])

_GUARD = [Depends(require_permission(GUARDIAS_REGISTRAR))]


# ── POST / — register guardia ─────────────────────────────────────────────────


@router.post(
    "/",
    response_model=GuardiaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una guardia (F6.6)",
    dependencies=_GUARD,
)
async def crear_guardia(
    body: GuardiaCreate,
    session: DBSession,
    current_user: CurrentUser,
) -> GuardiaOut:
    """Register a tutor duty-shift (guardia)."""
    svc = GuardiasService(session, current_user.tenant_id)
    guardia = await svc.crear_guardia(body, actor_id=current_user.user_id)
    await session.commit()
    return GuardiaOut.model_validate(guardia)


# ── GET / — list guardias ─────────────────────────────────────────────────────


@router.get(
    "/",
    response_model=list[GuardiaOut],
    summary="Listar guardias con filtros opcionales (F6.6)",
    dependencies=_GUARD,
)
async def list_guardias(
    session: DBSession,
    current_user: CurrentUser,
    materia_id: Optional[uuid.UUID] = Query(default=None),
    asignacion_id: Optional[uuid.UUID] = Query(default=None),
    carrera_id: Optional[uuid.UUID] = Query(default=None),
    cohorte_id: Optional[uuid.UUID] = Query(default=None),
    estado: Optional[str] = Query(default=None),
) -> list[GuardiaOut]:
    """Return guardias for the current tenant with optional filters."""
    filters = GuardiaFilter(
        materia_id=materia_id,
        asignacion_id=asignacion_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        estado=estado,
    )
    svc = GuardiasService(session, current_user.tenant_id)
    guardias = await svc.list_guardias(filters)
    return [GuardiaOut.model_validate(g) for g in guardias]


# ── GET /exportar — CSV download ──────────────────────────────────────────────


@router.get(
    "/exportar",
    summary="Exportar guardias a CSV (F6.6)",
    dependencies=_GUARD,
    response_class=StreamingResponse,
)
async def exportar_guardias(
    session: DBSession,
    current_user: CurrentUser,
    materia_id: Optional[uuid.UUID] = Query(default=None),
    asignacion_id: Optional[uuid.UUID] = Query(default=None),
    carrera_id: Optional[uuid.UUID] = Query(default=None),
    cohorte_id: Optional[uuid.UUID] = Query(default=None),
    estado: Optional[str] = Query(default=None),
) -> StreamingResponse:
    """Download guardias as a CSV file."""
    filters = GuardiaFilter(
        materia_id=materia_id,
        asignacion_id=asignacion_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        estado=estado,
    )
    svc = GuardiasService(session, current_user.tenant_id)
    csv_content = await svc.exportar_csv(filters)

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="guardias.csv"'},
    )
