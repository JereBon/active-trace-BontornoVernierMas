"""services/liquidacion_calc.py — Pure salary calculation function (C-18, Task 3.2).

_calcular_montos is a pure function (no I/O, no side effects) that computes
monto_base, monto_plus and total given pre-fetched salary data.

Formula (C-18 RN-21/PA-23):
  monto_base = base_rol (the vigente SalarioBase.monto for the docente's rol)
  monto_plus = Σ( plus_por_clave[clave] × N_comisiones_de_esa_clave )
  total = monto_base + monto_plus

Where:
  - asignaciones_por_clave: dict mapping categoria_clave (str | None) →
    number of commissions of that group (int). None key = no-clave commissions.
  - base_rol: Decimal (0 if no vigente base found).
  - plus_por_clave: dict mapping categoria_clave (str) → Decimal (SalarioPlus.monto).
    Claves not present = no plus defined for that group.

Edge cases:
  - categoria_clave is None → those commissions add to no Plus (counted in base).
  - A clave present in asignaciones_por_clave but absent from plus_por_clave
    → 0 plus for that group (no Plus record defined).
  - All amounts are Decimal; never float.

This function is designed for unit testing without any DB fixture.
"""

from decimal import Decimal


def _calcular_montos(
    asignaciones_por_clave: dict[str | None, int],
    base_rol: Decimal,
    plus_por_clave: dict[str, Decimal],
) -> tuple[Decimal, Decimal, Decimal]:
    """Compute (monto_base, monto_plus, total) for one docente in one period.

    Args:
        asignaciones_por_clave:
            Mapping from categoria_clave (or None) to the count of commissions
            in that group. Example: {"PROG": 2, None: 1} means 2 PROG commissions
            and 1 commission from a subject with no clave.

        base_rol:
            The base salary amount for the docente's role (Decimal). Zero if no
            vigente SalarioBase exists.

        plus_por_clave:
            Mapping from categoria_clave (str) to SalarioPlus.monto (Decimal).
            Only claves that have a vigente SalarioPlus record appear here.

    Returns:
        Tuple (monto_base, monto_plus, total) — all Decimal.

    Examples:
        >>> _calcular_montos({"PROG": 2}, Decimal("1000"), {"PROG": Decimal("200")})
        (Decimal('1000'), Decimal('400'), Decimal('1400'))
        >>> _calcular_montos({None: 3}, Decimal("1000"), {})
        (Decimal('1000'), Decimal('0'), Decimal('1000'))
    """
    monto_base = base_rol
    monto_plus = Decimal("0")

    for clave, n_comisiones in asignaciones_por_clave.items():
        if clave is None:
            # No clave → no Plus for these commissions
            continue
        plus_unitario = plus_por_clave.get(clave, Decimal("0"))
        monto_plus += plus_unitario * Decimal(n_comisiones)

    total = monto_base + monto_plus
    return monto_base, monto_plus, total
