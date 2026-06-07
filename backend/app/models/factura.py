"""models/factura.py — Factura model (C-18: liquidaciones-y-honorarios).

A Factura represents the invoice a facturante docente submits for a given
billing period. Managed by FacturaService (CRUD + state transitions).

Design decisions (C-18 design.md):
- D8: referencia_archivo is just a reference string (path/name), not content.
- Estado ∈ {Pendiente, Abonada} — abonada_at is set when transitioning to Abonada.
- tamano_kb stored as Numeric for precision.
- Inherits TenantScopedMixin: id, tenant_id, created_at, updated_at, deleted_at.
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantScopedMixin


class EstadoFactura(str, enum.Enum):
    """Possible states for a Factura record."""

    Pendiente = "Pendiente"
    Abonada = "Abonada"


class Factura(Base, TenantScopedMixin):
    """Invoice submitted by a facturante docente for a billing period.

    Rules:
      - usuario_id references the docente (who must have Usuario.facturador=True).
      - periodo is in AAAA-MM format, matching Liquidacion.periodo.
      - estado transitions: Pendiente → Abonada (abonada_at set on transition).
      - referencia_archivo: human-readable reference (filename/path), not binary.
    """

    __tablename__ = "facturas"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", name="fk_facturas_usuario"),
        nullable=False,
        index=True,
        comment="Docente who submitted this invoice.",
    )

    periodo: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        index=True,
        comment="Billing period in AAAA-MM format (e.g. '2025-06').",
    )

    detalle: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="Free-form description of the invoice contents.",
    )

    referencia_archivo: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        default=None,
        comment="Reference to the uploaded file (filename or path), not binary content.",
    )

    tamano_kb: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=True,
        default=None,
        comment="File size in kilobytes (Numeric for precision).",
    )

    estado: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default=EstadoFactura.Pendiente.value,
        server_default=EstadoFactura.Pendiente.value,
        comment="Pendiente | Abonada.",
    )

    cargada_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="Timestamp when the invoice was uploaded.",
    )

    abonada_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="Timestamp when the invoice was marked as paid; NULL until paid.",
    )
