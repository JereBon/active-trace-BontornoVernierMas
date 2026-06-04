"""models/usuario.py — Usuario model for authentication (C-03).

Contains only auth-related fields. Full profile (PII, legajo) added in C-07.

Design decisions (C-03 design.md D-02):
- email stored encrypted (AES-256-GCM via crypto.py); random nonce means same
  email encrypts to different blobs — not directly comparable in SQL.
- email_hash: SHA-256(email.lower()) stored as hex string for indexed lookup.
- totp_secret_cifrado: encrypted TOTP secret; NULL when 2FA not enrolled.
- totp_activo: True only after enrollment is confirmed.
"""

from sqlalchemy import Boolean, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantScopedMixin


class Usuario(Base, TenantScopedMixin):
    """User account — auth fields only.

    Full profile columns (nombre, apellido, legajo, etc.) come in C-07.
    """

    __tablename__ = "usuarios"

    __table_args__ = (
        # email_hash is unique per tenant (same email cannot be registered twice
        # in the same tenant, but different tenants can have the same email).
        UniqueConstraint("tenant_id", "email_hash", name="uq_usuarios_tenant_email_hash"),
    )

    # ── Auth fields ───────────────────────────────────────────────────────────

    email_cifrado: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="AES-256-GCM encrypted email (base64 blob); not directly searchable.",
    )

    email_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="SHA-256(email.lower()) hex string — used for O(log n) lookup.",
    )

    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Argon2id hash of the plaintext password.",
    )

    totp_secret_cifrado: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="AES-256-GCM encrypted TOTP secret; NULL until 2FA is enrolled.",
    )

    totp_activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="True only after 2FA enrollment is confirmed via /2fa/confirm.",
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="Soft-disable flag; inactive users cannot authenticate.",
    )
