"""models/asignacion.py — Asignacion model (C-07: usuarios-y-asignaciones).

Links a Usuario to a role within an academic context (materia, carrera, cohorte)
with temporal validity (desde / hasta).

Design decisions (C-07 design.md):
- All academic FK columns (materia_id, carrera_id, cohorte_id) are nullable:
  ADMIN / FINANZAS roles may have tenant-global scope with no academic context.
- estado_vigencia is NOT stored — it is derived: vigente when
  hasta IS NULL OR hasta >= today. Repositories apply this logic.
- responsable_id models supervisory hierarchy (coordinator of this assignment).
- comisiones stored as TEXT[] (PostgreSQL native array) for simplicity.
- Inherits TenantScopedMixin: id, tenant_id, created_at, updated_at, deleted_at.
"""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantScopedMixin


class Asignacion(Base, TenantScopedMixin):
    """Links a Usuario to a role within an academic context.

    Rules:
      - A vencida assignment (hasta < today) is preserved for history
        but does NOT grant permissions.
      - A user can have multiple active assignments with different roles.
      - responsable_id: the coordinator who supervises this assigned user.
    """

    __tablename__ = "asignaciones"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", name="fk_asignaciones_usuario"),
        nullable=False,
        index=True,
        comment="The user being assigned.",
    )

    rol: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Role code: ALUMNO | TUTOR | PROFESOR | COORDINADOR | NEXO | ADMIN | FINANZAS",
    )

    materia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materias.id", name="fk_asignaciones_materia"),
        nullable=True,
        default=None,
        comment="Scoped to this materia; NULL for tenant-global roles.",
    )

    carrera_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("carreras.id", name="fk_asignaciones_carrera"),
        nullable=True,
        default=None,
        comment="Scoped to this carrera; NULL when not carrera-scoped.",
    )

    cohorte_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cohortes.id", name="fk_asignaciones_cohorte"),
        nullable=True,
        default=None,
        comment="Scoped to this cohorte; NULL when not cohorte-scoped.",
    )

    comisiones: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        default=list,
        server_default="{}",
        comment="List of comision codes covered by this assignment.",
    )

    responsable_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", name="fk_asignaciones_responsable"),
        nullable=True,
        default=None,
        comment="Coordinator who supervises this assignment; nullable.",
    )

    desde: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Start date of validity.",
    )

    hasta: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        default=None,
        comment="End date of validity; NULL means open-ended (still active).",
    )
