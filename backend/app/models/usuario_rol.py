"""models/usuario_rol.py — UsuarioRol model (C-04: RBAC).

Assigns a Rol to a Usuario with temporal validity.  A role assignment is
*active* when vig_desde <= today AND (vig_hasta IS NULL OR vig_hasta >= today).

Design (design.md D-03):
  - vig_hasta IS NULL means the assignment never expires.
  - Expired assignments are NEVER deleted (append-only audit trail).
  - The effective-permissions query filters by vigencia at query time.
"""

import uuid
import datetime

from sqlalchemy import Date, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantScopedMixin


class UsuarioRol(Base, TenantScopedMixin):
    """Role assignment for a user within a tenant, with temporal validity."""

    __tablename__ = "usuario_roles"

    __table_args__ = (
        # Prevents identical duplicate rows for the same (user, role, start).
        # Overlapping period validation lives in the service layer (C-06+).
        UniqueConstraint(
            "usuario_id", "rol_id", "vig_desde",
            name="uq_usuario_roles_usuario_rol_desde",
        ),
    )

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="FK → usuarios.id",
    )
    rol_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="FK → roles.id",
    )
    vig_desde: Mapped[datetime.date] = mapped_column(
        Date,
        nullable=False,
        comment="First day the role assignment is active.",
    )
    vig_hasta: Mapped[datetime.date | None] = mapped_column(
        Date,
        nullable=True,
        default=None,
        comment="Last day the role assignment is active (NULL = no expiry).",
    )
