"""models/materia.py — Materia model (C-06: estructura-academica).

Materia is the flat subject catalog for a tenant.  Every module that tracks
academic activity (calificaciones, encuentros, guardias, etc.) references
Materia as the canonical unit of the curriculum.

Design decisions:
  - Relationship to Carrera/Cohorte deferred to entity Asignacion (C-07).
  - (tenant_id, codigo) uniqueness enforced via partial DB index.
  - One catalog per tenant; no cross-tenant sharing of Materia records.
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, EstadoEntidad, TenantScopedMixin


class Materia(Base, TenantScopedMixin):
    """Subject in the tenant's academic catalog.

    Rules:
      - (tenant_id, codigo) is unique among active records.
      - A Materia can belong to multiple Carreras/Cohortes via Asignacion (C-07).
    """

    __tablename__ = "materias"

    codigo: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Short code, unique within tenant (e.g. 'PROG_I').",
    )
    nombre: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Full display name (e.g. 'Programación I').",
    )
    estado: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default=EstadoEntidad.Activa.value,
        server_default=EstadoEntidad.Activa.value,
        comment="Activa | Inactiva",
    )
