"""api/v1/routers/inbox.py — Internal messaging endpoints (C-20: perfil-y-mensajeria-interna).

Identity and tenant_id ALWAYS come from the verified JWT (CurrentUser).
Messages are private — only sender and recipient can view them.

Endpoints:
  GET    /v1/inbox/           — list received messages (filter: ?solo_no_leidos=true)
  POST   /v1/inbox/           — send a message to another user in the same tenant
  GET    /v1/inbox/enviados   — list sent messages
  GET    /v1/inbox/{id}       — read a single message (auto-marks as leido)
  POST   /v1/inbox/{id}/responder  — reply in thread
"""

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import CurrentUser, DBSession
from app.core.exceptions import NotFoundError
from app.schemas.mensaje_interno import (
    MensajeInternoCreate,
    MensajeInternoOut,
    MensajeInternoResponder,
)
from app.services.mensaje_interno_service import MensajeInternoService

router = APIRouter(
    prefix="/v1/inbox",
    tags=["inbox"],
)


@router.get(
    "/enviados",
    response_model=list[MensajeInternoOut],
    summary="List sent messages (F11.2)",
)
async def get_enviados(
    session: DBSession,
    current_user: CurrentUser,
) -> list[MensajeInternoOut]:
    """Return messages sent by the authenticated user."""
    svc = MensajeInternoService(session, current_user.tenant_id, current_user.user_id)
    return await svc.get_enviados()


@router.get(
    "/{mensaje_id}",
    response_model=MensajeInternoOut,
    summary="Read a single message (F11.2) — auto-marks as leido",
)
async def get_mensaje(
    mensaje_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> MensajeInternoOut:
    """Return a single message. Auto-marks as read if the caller is the recipient."""
    svc = MensajeInternoService(session, current_user.tenant_id, current_user.user_id)
    try:
        out = await svc.get_mensaje(mensaje_id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mensaje not found")
    await session.commit()
    return out


@router.post(
    "/{mensaje_id}/responder",
    response_model=MensajeInternoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Reply to a message in its thread (F11.2, FL-10)",
)
async def responder_mensaje(
    mensaje_id: uuid.UUID,
    body: MensajeInternoResponder,
    session: DBSession,
    current_user: CurrentUser,
) -> MensajeInternoOut:
    """Create a reply within the same thread as the original message."""
    svc = MensajeInternoService(session, current_user.tenant_id, current_user.user_id)
    try:
        out = await svc.responder(mensaje_id, body.cuerpo)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mensaje not found")
    await session.commit()
    return out


@router.get(
    "",
    response_model=list[MensajeInternoOut],
    summary="List received messages / inbox (F11.2)",
)
async def get_inbox(
    session: DBSession,
    current_user: CurrentUser,
    solo_no_leidos: bool = Query(default=False, description="Filter to unread messages only"),
) -> list[MensajeInternoOut]:
    """Return messages received by the authenticated user."""
    svc = MensajeInternoService(session, current_user.tenant_id, current_user.user_id)
    return await svc.get_inbox(solo_no_leidos=solo_no_leidos)


@router.post(
    "",
    response_model=MensajeInternoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message to another user in the same tenant (F11.2, FL-10)",
)
async def enviar_mensaje(
    body: MensajeInternoCreate,
    session: DBSession,
    current_user: CurrentUser,
) -> MensajeInternoOut:
    """Send a new internal message.

    The recipient must be an active user in the same tenant.
    Sender identity always comes from the JWT — never from the request body.
    """
    svc = MensajeInternoService(session, current_user.tenant_id, current_user.user_id)
    try:
        out = await svc.enviar(body)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destinatario not found in this tenant",
        )
    await session.commit()
    return out
