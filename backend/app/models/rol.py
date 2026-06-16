"""models/rol.py — Rol model (C-04: RBAC).

A Rol is the unit of authorisation in activia-trace.  Each tenant owns its
own catalogue of roles.  Domain roles (ALUMNO, TUTOR, …) are seeded by the
0003_rbac migration; additional roles can be created per-tenant via the admin
UI (future change).

Design (design.md D-02):
  - Roles are per-tenant — roles.tenant_id is NOT NULL.
  - (tenant_id, codigo) is unique: two tenants can have a role called 'ADMIN'
    but they are independent records.
"""

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantScopedMixin


class Rol(Base, TenantScopedMixin):
    """Domain role within a tenant (e.g. ALUMNO, PROFESOR, ADMIN)."""

    __tablename__ = "roles"

    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_roles_tenant_codigo"),
    )

    codigo: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Short identifier, e.g. 'ALUMNO', 'ADMIN'.",
    )
    nombre: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Human-readable display name.",
    )
    descripcion: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="Optional description of the role.",
    )
