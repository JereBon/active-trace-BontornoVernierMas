"""models/tenant.py — Tenant model, the root of multi-tenant data isolation.

Design notes:
- Tenant does NOT inherit TenantScopedMixin because it IS the isolation root.
- Every other domain entity references a Tenant via tenant_id.
- slug is unique across the system (cross-tenant identifier for configuration).
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Tenant(Base):
    """Represents an institution (tenant) in the multi-tenant system.

    Each institution is completely isolated at the data layer via tenant_id
    on every domain entity.
    """

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )
    nombre: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
