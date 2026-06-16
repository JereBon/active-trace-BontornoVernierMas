"""api/v1/routers/comunicaciones.py — Comunicaciones endpoints (C-12).

Identity and tenant_id ALWAYS come from the verified JWT (CurrentUser).
Never from URL params, body, or headers.

Endpoints:
  POST   /v1/comunicaciones/preview                — render preview (comunicacion:enviar)
  POST   /v1/comunicaciones/encolar                — enqueue batch (comunicacion:enviar)
  GET    /v1/comunicaciones/lotes/{lote_id}        — get lote status (comunicacion:enviar)
  PATCH  /v1/comunicaciones/lotes/{lote_id}/aprobar  — approve lote (comunicacion:aprobar)
  PATCH  /v1/comunicaciones/lotes/{lote_id}/cancelar — cancel lote (comunicacion:aprobar)
  PATCH  /v1/comunicaciones/{id}/cancelar          — cancel individual (comunicacion:enviar)
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.dependencies import CurrentUser, DBSession
from app.core.permisos import COMUNICACION_APROBAR, COMUNICACION_ENVIAR
from app.core.rbac import require_permission
from app.schemas.comunicacion import (
    EncoladoRequest,
    EncoladoResponse,
    LoteStatusOut,
    PreviewRequest,
    PreviewResponse,
)
from app.services.comunicacion_service import ComunicacionService

router = APIRouter(
    prefix="/v1/comunicaciones",
    tags=["comunicaciones"],
)

_PERM_ENVIAR = Depends(require_permission(COMUNICACION_ENVIAR))
_PERM_APROBAR = Depends(require_permission(COMUNICACION_APROBAR))


# ── POST /preview ─────────────────────────────────────────────────────────────


@router.post(
    "/preview",
    response_model=PreviewResponse,
    dependencies=[_PERM_ENVIAR],
    summary="Render a message preview without persisting (F3.1, RN-16)",
)
async def preview_comunicacion(
    body: PreviewRequest,
    session: DBSession,
    current_user: CurrentUser,
) -> PreviewResponse:
    """Render asunto + cuerpo with variable substitution. No DB writes.

    Returns 422 if any template variable is missing.
    """
    svc = ComunicacionService(session, current_user.tenant_id, current_user.user_id)
    try:
        return await svc.preview(body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


# ── POST /encolar ─────────────────────────────────────────────────────────────


@router.post(
    "/encolar",
    response_model=EncoladoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_PERM_ENVIAR],
    summary="Enqueue a batch of outbound communications (F3.2)",
)
async def encolar_comunicaciones(
    body: EncoladoRequest,
    request: Request,
    session: DBSession,
    current_user: CurrentUser,
) -> EncoladoResponse:
    """Encrypt destinatarios and enqueue the batch.

    If tenant requires approval and batch has >1 recipient, messages stay
    Pendiente until a user with comunicacion:aprobar approves the lote.
    """
    svc = ComunicacionService(session, current_user.tenant_id, current_user.user_id)
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")
    return await svc.encolar_lote(
        materia_id=body.materia_id,
        asunto=body.asunto,
        cuerpo=body.cuerpo,
        destinatarios=body.destinatarios,
        ip=ip,
        user_agent=ua,
    )


# ── GET /lotes/{lote_id} ──────────────────────────────────────────────────────


@router.get(
    "/lotes/{lote_id}",
    response_model=LoteStatusOut,
    dependencies=[_PERM_ENVIAR],
    summary="Get status of a lote (destinatarios masked)",
)
async def get_lote_status(
    lote_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> LoteStatusOut:
    """Return lote status with masked destinatarios. Returns 404 if not found or wrong tenant."""
    svc = ComunicacionService(session, current_user.tenant_id, current_user.user_id)
    try:
        return await svc.get_lote_status(lote_id)
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote not found.")


# ── PATCH /lotes/{lote_id}/aprobar ───────────────────────────────────────────


@router.patch(
    "/lotes/{lote_id}/aprobar",
    dependencies=[_PERM_APROBAR],
    summary="Approve a lote for dispatch (F3.3, RN-17)",
)
async def aprobar_lote(
    lote_id: uuid.UUID,
    request: Request,
    session: DBSession,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Mark all Pendiente messages in the lote as approved for the worker."""
    svc = ComunicacionService(session, current_user.tenant_id, current_user.user_id)
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")
    try:
        count = await svc.aprobar_lote(lote_id, ip=ip, user_agent=ua)
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote not found.")
    return {"lote_id": str(lote_id), "approved": count}


# ── PATCH /lotes/{lote_id}/cancelar ──────────────────────────────────────────


@router.patch(
    "/lotes/{lote_id}/cancelar",
    dependencies=[_PERM_APROBAR],
    summary="Cancel all Pendiente messages in a lote",
)
async def cancelar_lote(
    lote_id: uuid.UUID,
    request: Request,
    session: DBSession,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Cancel all Pendiente messages in the lote."""
    svc = ComunicacionService(session, current_user.tenant_id, current_user.user_id)
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")
    try:
        count = await svc.cancelar_lote(lote_id, ip=ip, user_agent=ua)
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote not found.")
    return {"lote_id": str(lote_id), "cancelled": count}


# ── PATCH /{id}/cancelar ─────────────────────────────────────────────────────


@router.patch(
    "/{comunicacion_id}/cancelar",
    dependencies=[_PERM_ENVIAR],
    summary="Cancel a single Pendiente message",
)
async def cancelar_individual(
    comunicacion_id: uuid.UUID,
    request: Request,
    session: DBSession,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Cancel a single message. Returns 409 if already in a terminal state."""
    svc = ComunicacionService(session, current_user.tenant_id, current_user.user_id)
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")
    try:
        await svc.cancelar_individual(comunicacion_id, ip=ip, user_agent=ua)
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comunicacion not found.")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return {"id": str(comunicacion_id), "estado": "Cancelado"}
