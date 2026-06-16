"""models/aviso_ack.py — AvisoAck model (C-15: avisos-y-acknowledgment).

AvisoAck records the moment a user acknowledged (confirmed reading) an Aviso.

Design decisions:
  - UNIQUE(aviso_id, usuario_id) guarantees one ACK record per user per notice.
    Idempotency is enforced at DB level; the repository layer catches the
    IntegrityError and treats a duplicate as a no-op (returns 200).
  - No updated_at: an ACK is immutable; the first leido_en is the authoritative
    timestamp. If the constraint fires on a retry, the original record is kept.
  - Does NOT inherit TenantScopedMixin because it has no deleted_at / updated_at
    semantics; it owns only tenant_id + PK for isolation and the ACK payload.
"""

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import DateTime, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AvisoAck(Base):
    """Acknowledgment of an Aviso by a specific user.

    Rules:
      - (aviso_id, usuario_id) is unique — one record per user per notice.
      - leido_en is set on creation; never mutated.
      - tenant_id duplicates the parent Aviso's tenant for isolation checks.
    """

    __tablename__ = "aviso_acks"

    __table_args__ = (
        UniqueConstraint("aviso_id", "usuario_id", name="uq_aviso_ack_aviso_usuario"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Tenant owning this ack (denormalized for isolation queries).",
    )
    aviso_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("avisos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="User who acknowledged the notice.",
    )
    leido_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when the user first acknowledged the notice.",
    )
