"""api/v1/routers/encuentros.py — Encuentros endpoints (C-13).

All endpoints require 'encuentros:gestionar' permission.
Identity and tenant_id always come from the verified JWT (CurrentUser).
No business logic here — only HTTP translation → service calls.

Endpoints:
  POST   /v1/encuentros/slots      Create slot + generate instances (F6.1, F6.2)
  PATCH  /v1/encuentros/{id}       Edit a single instance (F6.3)
  GET    /v1/encuentros/html       HTML block for LMS (F6.4)
  GET    /v1/encuentros/admin      Admin/coord overview of all instances (F6.5)
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import HTMLResponse

from app.core.dependencies import CurrentUser, DBSession
from app.core.permisos import ENCUENTROS_GESTIONAR
from app.core.rbac import require_permission
from app.schemas.encuentro import (
    InstanciaOut,
    InstanciaUpdate,
    SlotCreate,
    SlotWithInstancesOut,
)
from app.services.encuentros import EncuentrosService

router = APIRouter(prefix="/v1/encuentros", tags=["encuentros"])

_GUARD = [Depends(require_permission(ENCUENTROS_GESTIONAR))]


# ── POST /slots — create slot + instances ────────────────────────────────────


@router.post(
    "/slots",
    response_model=SlotWithInstancesOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear slot de encuentro (recurrente o único)",
    dependencies=_GUARD,
)
async def crear_slot(
    body: SlotCreate,
    session: DBSession,
    current_user: CurrentUser,
) -> SlotWithInstancesOut:
    """Create a SlotEncuentro and generate all InstanciaEncuentro rows.

    For F6.1 (recurrent): body.cant_semanas > 0.
    For F6.2 (one-off): body.cant_semanas == 0 and body.fecha_unica is set.
    """
    from fastapi import HTTPException

    svc = EncuentrosService(session, current_user.tenant_id)
    try:
        result = await svc.crear_slot_recurrente(body, actor_id=current_user.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    await session.commit()
    return result


# ── PATCH /{id} — edit instance ───────────────────────────────────────────────


@router.patch(
    "/{instancia_id}",
    response_model=InstanciaOut,
    summary="Editar instancia de encuentro (F6.3)",
    dependencies=_GUARD,
)
async def editar_instancia(
    instancia_id: uuid.UUID,
    body: InstanciaUpdate,
    session: DBSession,
    current_user: CurrentUser,
) -> InstanciaOut:
    """Update estado, meet_url, video_url, or comentario of an instance."""
    from app.core.exceptions import NotFoundError
    from fastapi import HTTPException

    svc = EncuentrosService(session, current_user.tenant_id)
    try:
        updated = await svc.editar_instancia(instancia_id, body, actor_id=current_user.user_id)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="InstanciaEncuentro no encontrada",
        )
    await session.commit()
    return InstanciaOut.model_validate(updated)


# ── GET /html — LMS HTML block ────────────────────────────────────────────────


@router.get(
    "/html",
    response_class=HTMLResponse,
    summary="Generar bloque HTML de encuentros para el aula virtual (F6.4)",
    dependencies=_GUARD,
)
async def generar_html(
    session: DBSession,
    current_user: CurrentUser,
    materia_id: uuid.UUID = Query(...),
    asignacion_id: Optional[uuid.UUID] = Query(default=None),
) -> str:
    """Return an HTML table with scheduled encounters, ready to embed in the LMS."""
    svc = EncuentrosService(session, current_user.tenant_id)
    return await svc.generar_html(materia_id=materia_id, asignacion_id=asignacion_id)


# ── GET /admin — admin overview ───────────────────────────────────────────────


@router.get(
    "/admin",
    response_model=list[InstanciaOut],
    summary="Vista de administración de encuentros (F6.5)",
    dependencies=_GUARD,
)
async def list_admin(
    session: DBSession,
    current_user: CurrentUser,
    materia_id: Optional[uuid.UUID] = Query(default=None),
) -> list[InstanciaOut]:
    """Return all encounter instances for the tenant (coordinator/admin view)."""
    svc = EncuentrosService(session, current_user.tenant_id)
    instancias = await svc.list_admin(materia_id=materia_id)
    return [InstanciaOut.model_validate(i) for i in instancias]
