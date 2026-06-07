"""models/mensaje_interno.py — MensajeInterno model (C-20: perfil-y-mensajeria-interna).

Design decisions:
- tenant_id in every row; queries always scoped by tenant + owner.
- hilo_id is optional: NULL for root messages, set to the root message id for replies.
- Soft delete via deleted_at from TenantScopedMixin.
- leido starts as False; set to True when the recipient reads the message.
- remitente_id and destinatario_id reference usuarios.id (UUID, no FK constraint
  at DB level to avoid cross-schema complications with tenant isolation).
"""

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantScopedMixin
import uuid as _uuid


class MensajeInterno(Base, TenantScopedMixin):
    """Internal message between two users of the same tenant (C-20)."""

    __tablename__ = "mensajes_internos"

    remitente_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="FK → usuarios.id — sender (always sourced from JWT).",
    )

    destinatario_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="FK → usuarios.id — recipient.",
    )

    asunto: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Message subject line.",
    )

    cuerpo: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Message body (plaintext).",
    )

    leido: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="True once the recipient has viewed the message.",
    )

    hilo_id: Mapped[_uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        default=None,
        index=True,
        comment="Thread root message id. NULL for root messages; set for replies.",
    )
