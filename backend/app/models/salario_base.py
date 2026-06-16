"""models/salario_base.py — SalarioBase model (C-18: liquidaciones-y-honorarios).

SalarioBase defines the base salary amount for a given role within a date range.
Used by LiquidacionService to resolve the monto_base for each docente.

Design decisions (C-18 design.md):
- D4: vigencia by period AAAA-MM — desde/hasta are date columns compared
  against the first/last day of the billing month.
- D3: cálculo logic lives in Service, only I/O in Repository.
- One active record per (tenant, rol) at any instant is the business rule;
  the repository enforces "desde más reciente" when solapes exist (deterministic).
- Inherits TenantScopedMixin: id, tenant_id, created_at, updated_at, deleted_at.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantScopedMixin


class SalarioBase(Base, TenantScopedMixin):
    """Base salary amount per role, with optional date-range validity.

    Rules:
      - rol must match one of the system roles (PROFESOR, TUTOR, NEXO, etc.).
      - monto is stored as Numeric (never float) to avoid rounding errors.
      - hasta = NULL means open-ended (currently active).
      - Vigencia predicate: desde <= fin_mes AND (hasta IS NULL OR hasta >= ini_mes).
    """

    __tablename__ = "salario_base"

    rol: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
        comment="Role code this base salary applies to (e.g. PROFESOR, TUTOR).",
    )

    monto: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=False,
        comment="Base salary amount in currency units (Numeric, not float).",
    )

    desde: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="First date this record is valid (inclusive).",
    )

    hasta: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        default=None,
        comment="Last date this record is valid (inclusive); NULL = open-ended.",
    )

    descripcion: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        default=None,
        comment="Optional human-readable note about this salary entry.",
    )
