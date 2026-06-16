"""models/carrera.py — Carrera model (C-06: estructura-academica).

Carrera represents an academic program offered by a tenant institution.

Design decisions:
  - (tenant_id, codigo) uniqueness is enforced at DB level via a partial index
    (see migration 0004_estructura_academica.py). The model does NOT declare
    UniqueConstraint to avoid conflict with the partial index approach.
  - estado is stored as a plain String (mapped via EstadoEntidad enum) so the
    column value is human-readable without PG enum catalog management.
  - Soft delete via TenantScopedMixin.deleted_at; active = deleted_at IS NULL.
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, EstadoEntidad, TenantScopedMixin


class Carrera(Base, TenantScopedMixin):
    """Academic program owned by a tenant.

    Rules:
      - (tenant_id, codigo) is unique among active records.
      - An inactive Carrera cannot have new open Cohortes (enforced at service
        layer, not DB level, to keep migration simple).
    """

    __tablename__ = "carreras"

    codigo: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Short code, unique within tenant (e.g. 'TUPAD').",
    )
    nombre: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Full display name of the academic program.",
    )
    estado: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default=EstadoEntidad.Activa.value,
        server_default=EstadoEntidad.Activa.value,
        comment="Activa | Inactiva",
    )
