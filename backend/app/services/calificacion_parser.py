"""services/calificacion_parser.py — LMS file parser for calificaciones (C-10).

Parses .xlsx and .csv files exported from the LMS (Moodle) into structured
grade data without persisting anything.

Design decisions (C-10 design.md D2, OQ-1, OQ-2):
- parse_preview: stateless, returns {actividades_numericas, actividades_textuales,
  alumnos_preview}. Zero DB interaction.
- parse_actividades_seleccionadas: filters to the caller's selected activities
  and returns a flat list of {email, actividad, nota_numerica, nota_textual} dicts.
- RN-01: columns ending in '(Real)' are numeric activities.
- RN-02: other non-system columns are textual activities.
- Student identifier column: 'Email address' (case-insensitive strip, OQ-2).
- System/metadata columns (not activities): 'Email address', 'First name',
  'Surname', 'ID number', 'Institution', 'Department', 'Last downloaded from this course'.
"""

import csv
import io
from typing import Any

# Columns that are metadata, not actividades
_SYSTEM_COLUMNS = frozenset({
    "email address",
    "first name",
    "surname",
    "id number",
    "institution",
    "department",
    "last downloaded from this course",
})

# Suffix that marks a numeric (Real) column
_REAL_SUFFIX = "(real)"

# Column used to identify the student
_EMAIL_COLUMN = "email address"


class CalificacionParseError(Exception):
    """Raised when a calificaciones file is missing required columns or is malformed."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


def _normalize(header: str) -> str:
    """Normalize a column header: strip whitespace and lowercase."""
    return header.strip().lower()


def _strip_real_suffix(header: str) -> str:
    """Remove ' (Real)' suffix from a numeric column header.

    'Parcial 1 (Real)' → 'Parcial 1'
    """
    normalized = header.strip()
    if normalized.lower().endswith("(real)"):
        return normalized[: -len("(real)")].strip()
    return normalized


def _classify_headers(headers: list[str]) -> tuple[list[str], list[str], str]:
    """Classify raw column headers into numeric activities, textual activities, email column.

    Returns:
        (actividades_numericas, actividades_textuales, email_col)
        where email_col is the exact original header matching 'Email address'.

    Raises:
        CalificacionParseError: if 'Email address' column is missing.
    """
    email_col: str | None = None
    numericas: list[str] = []
    textuales: list[str] = []

    for h in headers:
        norm = _normalize(h)
        if norm == _EMAIL_COLUMN:
            email_col = h
            continue
        if norm in _SYSTEM_COLUMNS:
            continue  # skip metadata columns
        if norm.endswith(_REAL_SUFFIX):
            numericas.append(_strip_real_suffix(h))
        else:
            textuales.append(h.strip())

    if email_col is None:
        raise CalificacionParseError(
            "Missing required column: 'Email address'. "
            "Make sure the LMS export includes the student email column."
        )

    return numericas, textuales, email_col


def _parse_rows_xlsx(file_bytes: bytes) -> tuple[list[str], list[dict[str, Any]]]:
    """Parse an xlsx file into (headers, rows).

    Each row is a dict mapping raw header → cell value.
    """
    try:
        import openpyxl  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError(
            "openpyxl is required for .xlsx parsing. "
            "Install it with: pip install openpyxl"
        ) from exc

    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
    ws = wb.active
    raw_rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if not raw_rows:
        raise CalificacionParseError("File is empty — no rows found.")

    headers = [str(h) if h is not None else "" for h in raw_rows[0]]

    rows: list[dict[str, Any]] = []
    for row_values in raw_rows[1:]:
        if all(v is None or str(v).strip() == "" for v in row_values):
            continue
        rows.append({headers[i]: (row_values[i] if row_values[i] is not None else "") for i in range(len(headers))})

    return headers, rows


def _parse_rows_csv(file_bytes: bytes) -> tuple[list[str], list[dict[str, Any]]]:
    """Parse a csv file into (headers, rows)."""
    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = file_bytes.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise CalificacionParseError("File is empty — no headers found.")

    headers = list(reader.fieldnames)
    rows: list[dict[str, Any]] = [dict(row) for row in reader if any((v or "").strip() for v in row.values())]
    return headers, rows


def _parse_bytes(file_bytes: bytes, filename: str) -> tuple[list[str], list[dict[str, Any]]]:
    """Dispatch to xlsx or csv parser based on filename extension."""
    name = filename.lower()
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return _parse_rows_xlsx(file_bytes)
    elif name.endswith(".csv"):
        return _parse_rows_csv(file_bytes)
    else:
        # Try xlsx first, fall back to csv
        try:
            return _parse_rows_xlsx(file_bytes)
        except Exception:  # noqa: BLE001
            return _parse_rows_csv(file_bytes)


class CalificacionParser:
    """Stateless parser for LMS calificaciones file exports.

    Methods:
        parse_preview(file_bytes, filename)
            → dict with actividades_numericas, actividades_textuales, alumnos_preview

        parse_actividades_seleccionadas(file_bytes, filename, actividades)
            → list of dicts {email, actividad, nota_numerica, nota_textual}
    """

    def parse_preview(
        self,
        file_bytes: bytes,
        filename: str,
    ) -> dict[str, Any]:
        """Parse a LMS export and return a preview without persisting.

        Args:
            file_bytes: Raw bytes of the uploaded file.
            filename:   Original filename (used for format detection).

        Returns:
            Dict with keys:
              actividades_numericas: list of activity names (numeric columns)
              actividades_textuales: list of activity names (textual columns)
              alumnos_preview: list of {email, notas: {actividad: valor}} dicts

        Raises:
            CalificacionParseError: If 'Email address' column is missing.
        """
        headers, rows = _parse_bytes(file_bytes, filename)
        actividades_numericas, actividades_textuales, email_col = _classify_headers(headers)

        # Build per-activity lookup maps: original header → clean activity name
        # numeric: "Parcial 1 (Real)" → "Parcial 1"
        numeric_header_to_name: dict[str, str] = {}
        for h in headers:
            norm = _normalize(h)
            if norm.endswith(_REAL_SUFFIX) and norm not in _SYSTEM_COLUMNS:
                numeric_header_to_name[h] = _strip_real_suffix(h)

        # textual: identity
        textual_header_to_name: dict[str, str] = {}
        for h in headers:
            norm = _normalize(h)
            if norm not in _SYSTEM_COLUMNS and not norm.endswith(_REAL_SUFFIX):
                textual_header_to_name[h] = h.strip()

        alumnos_preview: list[dict[str, Any]] = []
        for row in rows:
            email = str(row.get(email_col, "")).strip()
            if not email:
                continue

            notas: dict[str, Any] = {}
            for h, name in numeric_header_to_name.items():
                val = row.get(h)
                if val is not None and str(val).strip():
                    try:
                        notas[name] = float(str(val).replace(",", "."))
                    except ValueError:
                        notas[name] = str(val).strip()
            for h, name in textual_header_to_name.items():
                val = row.get(h)
                if val is not None and str(val).strip():
                    notas[name] = str(val).strip()

            alumnos_preview.append({"email": email, "notas": notas})

        return {
            "actividades_numericas": actividades_numericas,
            "actividades_textuales": actividades_textuales,
            "alumnos_preview": alumnos_preview,
        }

    def parse_actividades_seleccionadas(
        self,
        file_bytes: bytes,
        filename: str,
        actividades: list[str],
    ) -> list[dict[str, Any]]:
        """Parse and filter to the selected activities only.

        Args:
            file_bytes:  Raw bytes of the uploaded file.
            filename:    Original filename.
            actividades: List of activity names to include (clean names, no '(Real)').

        Returns:
            List of dicts:
              {email, actividad, nota_numerica (float|None), nota_textual (str|None)}
            One entry per (alumno × actividad) combination.

        Raises:
            CalificacionParseError: If 'Email address' column is missing.
        """
        actividades_set = set(actividades)
        headers, rows = _parse_bytes(file_bytes, filename)
        actividades_numericas, actividades_textuales, email_col = _classify_headers(headers)

        # Build lookup: clean_name → original_header for numeric columns
        numeric_name_to_header: dict[str, str] = {}
        for h in headers:
            norm = _normalize(h)
            if norm.endswith(_REAL_SUFFIX) and norm not in _SYSTEM_COLUMNS:
                clean = _strip_real_suffix(h)
                numeric_name_to_header[clean] = h

        # textual: clean_name == original header (stripped)
        textual_name_to_header: dict[str, str] = {}
        for h in headers:
            norm = _normalize(h)
            if norm not in _SYSTEM_COLUMNS and not norm.endswith(_REAL_SUFFIX):
                textual_name_to_header[h.strip()] = h

        result: list[dict[str, Any]] = []
        for row in rows:
            email = str(row.get(email_col, "")).strip()
            if not email:
                continue

            for actividad in actividades:
                nota_numerica: float | None = None
                nota_textual: str | None = None

                if actividad in numeric_name_to_header:
                    raw = row.get(numeric_name_to_header[actividad])
                    if raw is not None and str(raw).strip():
                        try:
                            nota_numerica = float(str(raw).replace(",", "."))
                        except ValueError:
                            pass

                elif actividad in textual_name_to_header:
                    raw = row.get(textual_name_to_header[actividad])
                    if raw is not None and str(raw).strip():
                        nota_textual = str(raw).strip()

                else:
                    # activity not found in this file; skip
                    continue

                result.append(
                    {
                        "email": email,
                        "actividad": actividad,
                        "nota_numerica": nota_numerica,
                        "nota_textual": nota_textual,
                    }
                )

        return result
