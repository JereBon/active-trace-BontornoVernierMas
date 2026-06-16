"""models/refresh_token.py — Refresh token storage for JWT rotation (C-03).

Design decisions (C-03 design.md D-01):
- Token value stored as SHA-256 hash; plaintext sent to client, never persisted.
- revoked_at: NULL = active; set on first use (rotation) or on logout.
- Reuse detection: if a revoked token is presented, revoke ALL sessions for the user.
- Not a TenantScopedMixin subclass — the token links to a usuario (which carries
  tenant_id). tenant_id is denormalized here for efficient cross-tenant queries and
  future auditing without JOINs.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RefreshToken(Base):
    """Persisted refresh token hash, used for rotation and reuse detection."""

    __tablename__ = "refresh_tokens"

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

    # Denormalized for efficient queries / auditing without JOINs
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        comment="SHA-256 hex of the raw refresh token bytes. Unique across all tenants.",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="Set on rotation or logout. NULL = still valid (if not expired).",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
