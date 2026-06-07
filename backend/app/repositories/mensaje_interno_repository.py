"""repositories/mensaje_interno_repository.py — MensajeInternoRepository (C-20).

Tenant-scoped repository for internal messages.
All queries filter by tenant_id and exclude soft-deleted records.
Additionally, inbox/sent queries scope by the calling user's id — a user
can never read another user's messages.

Methods:
  get_inbox           — messages where destinatario_id == user_id
  get_enviados        — messages where remitente_id == user_id
  get_mensaje         — single message visible to this user (sender OR recipient)
  marcar_leido        — set leido=True on a message (recipient only)
  enviar              — create a new MensajeInterno
  responder           — create a reply with hilo_id set

Design decisions (C-20):
- Inbox isolation: a user can only see messages where they are sender or recipient.
  No query returns cross-user messages within a tenant.
- hilo_id propagation: replies inherit the root message id as hilo_id.
  If the message being replied to is itself a reply, hilo_id is preserved.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, or_, select

from app.models.mensaje_interno import MensajeInterno
from app.repositories.base import BaseRepository


class MensajeInternoRepository(BaseRepository[MensajeInterno]):
    """Tenant-scoped repository for MensajeInterno with per-user isolation."""

    def __init__(self, session, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, MensajeInterno)

    # ── Inbox (received messages) ─────────────────────────────────────────────

    async def get_inbox(
        self,
        user_id: uuid.UUID,
        *,
        solo_no_leidos: bool = False,
    ) -> list[MensajeInterno]:
        """Return messages received by user_id in this tenant.

        Args:
            user_id:         The recipient's UUID (from JWT — never from request).
            solo_no_leidos:  When True, filter to unread messages only.
        """
        conditions = [
            MensajeInterno.tenant_id == self._tenant_id,
            MensajeInterno.destinatario_id == user_id,
            MensajeInterno.deleted_at.is_(None),
        ]
        if solo_no_leidos:
            conditions.append(MensajeInterno.leido.is_(False))

        stmt = select(MensajeInterno).where(and_(*conditions)).order_by(
            MensajeInterno.created_at.desc()
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ── Sent messages ─────────────────────────────────────────────────────────

    async def get_enviados(self, user_id: uuid.UUID) -> list[MensajeInterno]:
        """Return messages sent by user_id in this tenant."""
        stmt = (
            select(MensajeInterno)
            .where(
                MensajeInterno.tenant_id == self._tenant_id,
                MensajeInterno.remitente_id == user_id,
                MensajeInterno.deleted_at.is_(None),
            )
            .order_by(MensajeInterno.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ── Single message access ─────────────────────────────────────────────────

    async def get_para_usuario(
        self, mensaje_id: uuid.UUID, user_id: uuid.UUID
    ) -> MensajeInterno | None:
        """Return a message if the user is either sender or recipient.

        Returns None if the message doesn't exist, belongs to another tenant,
        has been soft-deleted, or the user is neither sender nor recipient.
        """
        stmt = select(MensajeInterno).where(
            MensajeInterno.id == mensaje_id,
            MensajeInterno.tenant_id == self._tenant_id,
            MensajeInterno.deleted_at.is_(None),
            or_(
                MensajeInterno.remitente_id == user_id,
                MensajeInterno.destinatario_id == user_id,
            ),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # ── Mutations ─────────────────────────────────────────────────────────────

    async def marcar_leido(
        self, mensaje_id: uuid.UUID, user_id: uuid.UUID
    ) -> MensajeInterno | None:
        """Mark a received message as read.

        Only the recipient can mark as read. Returns None if not found or
        the user is not the recipient.
        """
        stmt = select(MensajeInterno).where(
            MensajeInterno.id == mensaje_id,
            MensajeInterno.tenant_id == self._tenant_id,
            MensajeInterno.destinatario_id == user_id,
            MensajeInterno.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        instance = result.scalar_one_or_none()
        if instance is None:
            return None

        instance.leido = True
        instance.updated_at = datetime.now(tz=timezone.utc)
        self._session.add(instance)
        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    async def enviar(
        self,
        remitente_id: uuid.UUID,
        destinatario_id: uuid.UUID,
        asunto: str,
        cuerpo: str,
        hilo_id: uuid.UUID | None = None,
    ) -> MensajeInterno:
        """Create and persist a new MensajeInterno.

        tenant_id is always sourced from the repository instance (JWT),
        remitente_id from the JWT — never from caller-supplied data.
        """
        data = {
            "remitente_id": remitente_id,
            "destinatario_id": destinatario_id,
            "asunto": asunto,
            "cuerpo": cuerpo,
            "leido": False,
            "hilo_id": hilo_id,
        }
        return await self.create(data)
