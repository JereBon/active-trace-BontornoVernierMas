"""models/usuario.py — Usuario model (auth + full PII profile).

C-03: auth fields (email_cifrado, email_hash, password_hash, totp_*, activo).
C-07: PII profile fields (nombre, apellidos, dni_cifrado, cuil_cifrado,
      cbu_cifrado, alias_cbu_cifrado, banco, regional, legajo,
      legajo_profesional, facturador). All nullable for backward compatibility.

Design decisions:
- email stored encrypted (AES-256-GCM via crypto.py); random nonce means same
  email encrypts to different blobs — not directly comparable in SQL.
- email_hash: SHA-256(email.lower()) stored as hex string for indexed lookup.
- All PII fields ending in '_cifrado' are AES-256-GCM encrypted blobs.
  Repositories (not models) handle encrypt/decrypt.
- totp_secret_cifrado: encrypted TOTP secret; NULL when 2FA not enrolled.
- totp_activo: True only after enrollment is confirmed.
"""

from sqlalchemy import Boolean, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantScopedMixin


class Usuario(Base, TenantScopedMixin):
    """User account — auth fields + full PII profile (C-03 + C-07)."""

    __tablename__ = "usuarios"

    __table_args__ = (
        # email_hash is unique per tenant (same email cannot be registered twice
        # in the same tenant, but different tenants can have the same email).
        UniqueConstraint("tenant_id", "email_hash", name="uq_usuarios_tenant_email_hash"),
    )

    # ── Auth fields (C-03) ────────────────────────────────────────────────────

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

    # ── PII profile fields (C-07) ─────────────────────────────────────────────
    # All nullable: pre-existing auth-only users have NULL profile fields.

    nombre: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        default=None,
        comment="First name (plaintext).",
    )

    apellidos: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        default=None,
        comment="Last name(s) (plaintext).",
    )

    dni_cifrado: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="AES-256-GCM encrypted national ID (DNI).",
    )

    cuil_cifrado: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="AES-256-GCM encrypted tax ID (CUIL).",
    )

    cbu_cifrado: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="AES-256-GCM encrypted bank account key (CBU).",
    )

    alias_cbu_cifrado: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="AES-256-GCM encrypted CBU alias.",
    )

    banco: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        default=None,
        comment="Bank name (plaintext).",
    )

    regional: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        default=None,
        comment="Institutional delegation / branch (plaintext).",
    )

    legajo: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        default=None,
        comment="Institutional record number (business attribute, not PK).",
    )

    legajo_profesional: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        default=None,
        comment="Professional college / registry record number.",
    )

    facturador: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
        default=None,
        comment="True if the user issues invoices (monotributo / etc.).",
    )
