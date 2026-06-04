"""models/password_reset_token.py — Single-use password recovery token (C-03).

Design decisions (C-03 design.md D-06):
- Token: 32 random bytes; hash (SHA-256) stored in DB; plaintext sent once in dev.
- Expiry: 15 minutes after creation.
- Single-use: used_at is set on consumption; subsequent use returns 400.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PasswordResetToken(Base):
    """Single-use password recovery token."""

    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        comment="SHA-256 hex of the raw 32-byte token. Plaintext never stored.",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Token is invalid after this timestamp (15 min from creation).",
    )

    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="Set when the token is consumed. NULL = still valid (if not expired).",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
