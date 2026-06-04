"""models/rol_permiso.py — RolPermiso association table (C-04: RBAC).

Associates a Rol with a Permiso within the same tenant.  Uses an explicit
model (not SQLAlchemy relationship secondary) so we can add auditing columns
in the future.

Design notes:
  - (rol_id, permiso_id) is unique — a role cannot have the same permission
    twice.
  - tenant_id is denormalised here for defence-in-depth: the application code
    should always ensure rol and permiso belong to the same tenant, and the
    column lets a DBA audit/repair without joins.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RolPermiso(Base):
    """Many-to-many link between Rol and Permiso."""

    __tablename__ = "rol_permisos"

    __table_args__ = (
        UniqueConstraint("rol_id", "permiso_id", name="uq_rol_permisos_rol_permiso"),
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
        comment="Denormalised for defence-in-depth tenant checks.",
    )
    rol_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="FK → roles.id",
    )
    permiso_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="FK → permisos.id",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
