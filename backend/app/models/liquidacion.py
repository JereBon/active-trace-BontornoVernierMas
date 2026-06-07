"""models/liquidacion.py — Liquidacion model (C-18: liquidaciones-y-honorarios).

A Liquidacion record represents one docente's calculated salary for a single
billing period (AAAA-MM) within a cohorte. Once closed (estado=Cerrada) the
record is immutable — no further mutations are allowed (RN-22, D5).

Design decisions (C-18 design.md):
- D1: excluido_por_factura is derived from Usuario.facturador at calculation
  time and stored here (denormalized for immutability after close).
- D3: cálculo in LiquidacionService, this model is only the persistence shape.
- D5: estado ∈ {Abierta, Cerrada} — immutability enforced by Service (409).
- D6: KPI aggregates NOT stored; derived from rows at query time.
- comisiones: stored as TEXT[] matching Asignacion.comisiones format.
- Montos: Numeric (never float).
- Inherits TenantScopedMixin: id, tenant_id, created_at, updated_at, deleted_at.
"""

import enum
import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text, Boolean
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantScopedMixin


class EstadoLiquidacion(str, enum.Enum):
    """Possible states for a Liquidacion record."""

    Abierta = "Abierta"
    Cerrada = "Cerrada"


class Liquidacion(Base, TenantScopedMixin):
    """Single docente salary record for a billing period within a cohorte.

    Rules (C-18 RN-21/22/31-40):
      - (cohorte_id, periodo, usuario_id) should be unique among Abierta records.
      - Once estado=Cerrada, no mutations are allowed (Service enforces 409).
      - excluido_por_factura=True → excluded from total_sin_factura KPI.
      - es_nexo=True → included in total_sin_factura but in a separate segment.
      - comisiones: snapshot of the commissions that generated this record.
    """

    __tablename__ = "liquidaciones"

    cohorte_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cohortes.id", name="fk_liquidaciones_cohorte"),
        nullable=False,
        index=True,
        comment="Cohorte this liquidation belongs to.",
    )

    periodo: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        index=True,
        comment="Billing period in AAAA-MM format (e.g. '2025-06').",
    )

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", name="fk_liquidaciones_usuario"),
        nullable=False,
        index=True,
        comment="Docente this liquidation is for.",
    )

    rol: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Role active at the time of calculation (from Asignacion.rol).",
    )

    comisiones: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        default=list,
        server_default="{}",
        comment="Snapshot of commission codes covered by this docente in the period.",
    )

    monto_base: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=False,
        comment="Base salary component (from SalarioBase vigente al periodo).",
    )

    monto_plus: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=False,
        comment="Accumulated plus salary (Σ Plus(clave, rol) × N comisiones de esa clave).",
    )

    total: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=False,
        comment="monto_base + monto_plus.",
    )

    es_nexo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="True when the docente holds the NEXO role (separate segment, but included in total).",
    )

    excluido_por_factura: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="True when Usuario.facturador=True (excluded from total_sin_factura KPI).",
    )

    estado: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default=EstadoLiquidacion.Abierta.value,
        server_default=EstadoLiquidacion.Abierta.value,
        comment="Abierta | Cerrada. Once Cerrada, no mutations are allowed.",
    )
