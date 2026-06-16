"""models/salario_plus.py — SalarioPlus model (C-18: liquidaciones-y-honorarios).

SalarioPlus defines the additional bonus amount per (grupo/categoria_clave, rol)
combination, applied per commission unit (i.e. multiplied by the number of
commissions of that group the docente covers in the billing period).

Design decisions (C-18 design.md):
- D2: grupo = Materia.categoria_clave (the key resolved from the subject catalog).
- D4: same vigencia semantics as SalarioBase (date-range comparison per period).
- D3: cálculo in Service, I/O only in Repository.
- Inherits TenantScopedMixin: id, tenant_id, created_at, updated_at, deleted_at.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantScopedMixin


class SalarioPlus(Base, TenantScopedMixin):
    """Bonus salary amount per (grupo, rol) pair, applied per commission unit.

    Rules:
      - grupo = Materia.categoria_clave; if a Materia has no categoria_clave,
        no Plus is generated for that subject's commissions (not an error).
      - monto is per-commission (linear accumulation: N comisiones → N × monto).
      - hasta = NULL means open-ended (currently active).
      - Vigencia: desde <= fin_mes AND (hasta IS NULL OR hasta >= ini_mes).
    """

    __tablename__ = "salario_plus"

    grupo: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
        comment="Category key matching Materia.categoria_clave (e.g. 'PROG', 'CALC').",
    )

    rol: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
        comment="Role code this plus applies to (e.g. PROFESOR).",
    )

    descripcion: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        default=None,
        comment="Optional label for the plus entry (e.g. 'Plus Programación').",
    )

    monto: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=False,
        comment="Plus amount per commission unit (Numeric, not float).",
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
