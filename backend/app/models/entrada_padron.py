"""models/entrada_padron.py — EntradaPadron model (C-09: padron-ingesta-moodle).

One row per student in a VersionPadron. The student may not yet have a user
account in the system (usuario_id is nullable). PII (email) is stored
AES-256-GCM encrypted.

Design decisions (C-09 design.md):
- usuario_id nullable: allows loading students before they create an account.
  Matching to an existing Usuario is done later by email lookup.
- email_cifrado: AES-256-GCM via app.core.crypto (same pattern as Usuario).
- nombre / apellidos: plaintext, denormalized for historical record. They
  are institutional information, not considered sensitive PII in this context.
- comision / regional: optional institutional grouping attributes.
- Inherits TenantScopedMixin: id, tenant_id, created_at, updated_at, deleted_at.
"""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantScopedMixin


class EntradaPadron(Base, TenantScopedMixin):
    """One student entry within a VersionPadron.

    Rules:
      - usuario_id may be NULL (student without an account yet).
      - email is stored encrypted (AES-256-GCM).
      - Soft delete: deleted_at IS NULL means active.
    """

    __tablename__ = "entrada_padron"

    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("version_padron.id", name="fk_entrada_padron_version"),
        nullable=False,
        index=True,
        comment="FK to version_padron; which version this entry belongs to.",
    )

    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", name="fk_entrada_padron_usuario"),
        nullable=True,
        default=None,
        comment="FK to usuarios; NULL when the student has no account yet.",
    )

    nombre: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Student first name (plaintext, denormalized for history).",
    )

    apellidos: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Student last name(s) (plaintext, denormalized for history).",
    )

    email_cifrado: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="AES-256-GCM encrypted email address.",
    )

    comision: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        default=None,
        comment="Student comision/group code.",
    )

    regional: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        default=None,
        comment="Student regional/branch.",
    )
