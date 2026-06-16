"""services/mensaje_interno_service.py — MensajeInternoService (C-20).

Orchestrates MensajeInternoRepository and enforces business rules:
  - Recipient must belong to the same tenant.
  - Sender identity always comes from JWT (user_id param).
  - hilo_id propagation: replies set hilo_id to the root message id.

Methods:
  get_inbox     — received messages for the calling user
  get_enviados  — sent messages for the calling user
  get_mensaje   — single message (marks as leido if recipient is reading)
  enviar        — send a new message
  responder     — reply in a thread
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.mensaje_interno import MensajeInterno
from app.repositories.mensaje_interno_repository import MensajeInternoRepository
from app.repositories.usuario import UsuarioRepository
from app.schemas.mensaje_interno import MensajeInternoCreate, MensajeInternoOut


def _to_out(m: MensajeInterno) -> MensajeInternoOut:
    """Convert ORM instance to response schema."""
    return MensajeInternoOut(
        id=m.id,
        tenant_id=m.tenant_id,
        remitente_id=m.remitente_id,
        destinatario_id=m.destinatario_id,
        asunto=m.asunto,
        cuerpo=m.cuerpo,
        leido=m.leido,
        hilo_id=m.hilo_id,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class MensajeInternoService:
    """Service for internal messaging operations.

    tenant_id and the calling user_id always come from the verified JWT
    (injected by the router dependency — never from request body/params).
    """

    def __init__(
        self,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        self._repo = MensajeInternoRepository(session, tenant_id)
        self._usuario_repo = UsuarioRepository(session, tenant_id)
        self._tenant_id = tenant_id
        self._user_id = user_id

    async def get_inbox(self, *, solo_no_leidos: bool = False) -> list[MensajeInternoOut]:
        """Return messages received by the calling user."""
        mensajes = await self._repo.get_inbox(
            self._user_id, solo_no_leidos=solo_no_leidos
        )
        return [_to_out(m) for m in mensajes]

    async def get_enviados(self) -> list[MensajeInternoOut]:
        """Return messages sent by the calling user."""
        mensajes = await self._repo.get_enviados(self._user_id)
        return [_to_out(m) for m in mensajes]

    async def get_mensaje(self, mensaje_id: uuid.UUID) -> MensajeInternoOut:
        """Return a single message and mark it as read if the caller is the recipient.

        Raises:
            NotFoundError: if not found or caller is not sender/recipient.
        """
        mensaje = await self._repo.get_para_usuario(mensaje_id, self._user_id)
        if mensaje is None:
            raise NotFoundError(f"Mensaje {mensaje_id} not found")

        # Auto-mark as read when recipient views the message
        if mensaje.destinatario_id == self._user_id and not mensaje.leido:
            await self._repo.marcar_leido(mensaje_id, self._user_id)
            mensaje.leido = True  # reflect locally without extra DB roundtrip

        return _to_out(mensaje)

    async def enviar(self, data: MensajeInternoCreate) -> MensajeInternoOut:
        """Send a new message to another user in the same tenant.

        Raises:
            NotFoundError: if the recipient does not exist in this tenant.
        """
        # Guard: recipient must exist in the same tenant
        destinatario = await self._usuario_repo.get(data.destinatario_id)
        if destinatario is None:
            raise NotFoundError(
                f"Destinatario {data.destinatario_id} not found in this tenant"
            )

        mensaje = await self._repo.enviar(
            remitente_id=self._user_id,
            destinatario_id=data.destinatario_id,
            asunto=data.asunto,
            cuerpo=data.cuerpo,
            hilo_id=None,
        )
        return _to_out(mensaje)

    async def responder(
        self, mensaje_id: uuid.UUID, cuerpo: str
    ) -> MensajeInternoOut:
        """Reply to a message, creating a new MensajeInterno in the same thread.

        hilo_id is set to the root message id (the original message's hilo_id
        if it's already a reply, otherwise the original message's id).

        Raises:
            NotFoundError: if the original message is not found or caller has no access.
        """
        original = await self._repo.get_para_usuario(mensaje_id, self._user_id)
        if original is None:
            raise NotFoundError(f"Mensaje {mensaje_id} not found")

        # Determine thread root
        hilo_id = original.hilo_id if original.hilo_id is not None else original.id

        # Reply goes to the other party
        if original.remitente_id == self._user_id:
            destinatario_id = original.destinatario_id
        else:
            destinatario_id = original.remitente_id

        reply = await self._repo.enviar(
            remitente_id=self._user_id,
            destinatario_id=destinatario_id,
            asunto=f"Re: {original.asunto}",
            cuerpo=cuerpo,
            hilo_id=hilo_id,
        )
        return _to_out(reply)
