"""models/cohorte.py — Cohorte model (C-06: estructura-academica).

Cohorte represents a student intake (cohort / camada) within a Carrera.

Design decisions:
  - carrera_id FK uses RESTRICT on delete: a Carrera with active Cohortes
    cannot be deleted at DB level (soft delete is the only supported path).
  - (tenant_id, carrera_id, nombre) uniqueness enforced via partial DB index.
  - vig_hasta nullable: NULL means the cohort is still open-ended.
"""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, EstadoEntidad, TenantScopedMixin


class Cohorte(Base, TenantScopedMixin):
    """Student intake cohort linked to a specific Carrera.

    Rules:
      - (tenant_id, carrera_id, nombre) is unique among active records.
      - The referenced Carrera must belong to the same tenant (enforced at
        service layer; FK alone cannot check cross-tenant integrity).
    """

    __tablename__ = "cohortes"

    carrera_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("carreras.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    nombre: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Human-readable label, e.g. 'AGO-2025'.",
    )
    anio: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Academic year the cohort started.",
    )
    vig_desde: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Start of validity period.",
    )
    vig_hasta: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        default=None,
        comment="End of validity period; NULL = still open.",
    )
    estado: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default=EstadoEntidad.Activa.value,
        server_default=EstadoEntidad.Activa.value,
        comment="Activa | Inactiva",
    )

    # Relationship (lazy by default — only load when explicitly accessed)
    carrera: Mapped["Carrera"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Carrera",
        lazy="select",
        foreign_keys=[carrera_id],
    )
