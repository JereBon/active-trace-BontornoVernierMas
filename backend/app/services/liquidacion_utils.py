"""services/liquidacion_utils.py — Pure period utilities (C-18, Task 3.1).

Pure functions for period (AAAA-MM) normalization and vigencia predicates.
No I/O — testable in isolation without DB or async context.

Design decisions (C-18 design.md D4):
- Period is stored/passed as string 'AAAA-MM'.
- ini_mes = date(AAAA, MM, 1)
- fin_mes = last calendar day of the month.
- Vigencia: desde <= fin_mes AND (hasta IS NULL OR hasta >= ini_mes).
"""

import calendar
from datetime import date


def parse_periodo(periodo: str) -> tuple[date, date]:
    """Return (ini_mes, fin_mes) for a period string 'AAAA-MM'.

    ini_mes = first day of the month (date(AAAA, MM, 1))
    fin_mes = last day of the month (date(AAAA, MM, last_day))

    Raises ValueError if the string is not in 'AAAA-MM' format or
    if year/month values are out of range.

    Examples:
        >>> parse_periodo("2025-06")
        (date(2025, 6, 1), date(2025, 6, 30))
        >>> parse_periodo("2025-02")
        (date(2025, 2, 1), date(2025, 2, 28))
    """
    parts = periodo.split("-")
    if len(parts) != 2:
        raise ValueError(f"Invalid period format: {periodo!r}. Expected 'AAAA-MM'.")

    try:
        year = int(parts[0])
        month = int(parts[1])
    except ValueError as exc:
        raise ValueError(f"Non-numeric parts in period: {periodo!r}") from exc

    if month < 1 or month > 12:
        raise ValueError(f"Month out of range in period: {periodo!r}")

    ini_mes = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    fin_mes = date(year, month, last_day)
    return ini_mes, fin_mes


def es_vigente(desde: date, hasta: date | None, ini_mes: date, fin_mes: date) -> bool:
    """Return True if a validity range overlaps with the billing period.

    Vigencia predicate (D4):
      desde <= fin_mes AND (hasta IS NULL OR hasta >= ini_mes)

    Args:
        desde:   First valid date (inclusive).
        hasta:   Last valid date (inclusive); None = open-ended.
        ini_mes: First day of the billing period.
        fin_mes: Last day of the billing period.
    """
    if desde > fin_mes:
        return False
    if hasta is not None and hasta < ini_mes:
        return False
    return True
