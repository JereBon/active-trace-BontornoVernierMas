"""models/programa_materia.py — ProgramaMateria model (C-17).

Programa oficial de una materia para una carrera/cohorte dentro de un tenant.
Permite registrar el documento de contenidos de cada materia, con referencia
opcional al archivo almacenado externamente.

Design decisions:
  - carrera_id y cohorte_id son opcionales: un programa puede ser genérico
    o estar acotado a una combinación específica.
  - referencia_archivo almacena la URL/path al archivo; el upload es externo.
  - vigente controla si el programa es el activo; publicado_en registra cuándo
    fue publicado al alumno.
  - Soft delete via deleted_at (TenantScopedMixin).
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantScopedMixin


class ProgramaMateria(Base, TenantScopedMixin):
    """Programa oficial de una materia en un período académico del tenant.

    Rules:
      - materia_id is required; carrera_id and cohorte_id are optional.
      - vigente=True marks the current program for that materia/cohorte combo.
      - referencia_archivo is a URL/path to the externally stored file.
    """

    __tablename__ = "programa_materia"

    materia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materias.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    carrera_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("carreras.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    cohorte_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cohortes.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    titulo: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Título descriptivo del programa (ej: 'Prog. I - Cohorte MAR-2026')",
    )
    referencia_archivo: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        comment="URL/path al archivo en el servicio de almacenamiento externo.",
    )
    vigente: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="True si este es el programa activo para la combinación materia/cohorte.",
    )
    publicado_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp en que el programa fue publicado al alumno.",
    )
