"""models/permiso.py — Permiso model (C-04: RBAC).

A Permiso represents a fine-grained capability expressed as 'modulo:accion'
(e.g. 'calificaciones:importar').  Permissions are stored as data — never
hardcoded — so the catalogue is administrable per tenant without a deploy.

Design (design.md D-01):
  - codigo is the canonical string compared at runtime by require_permission.
  - (tenant_id, codigo) is unique within a tenant's catalogue.
"""

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantScopedMixin


class Permiso(Base, TenantScopedMixin):
    """Fine-grained permission expressed as 'modulo:accion'."""

    __tablename__ = "permisos"

    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_permisos_tenant_codigo"),
    )

    codigo: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Permission code in 'modulo:accion' format (e.g. 'calificaciones:importar').",
    )
    descripcion: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="Human-readable description of what this permission allows.",
    )
