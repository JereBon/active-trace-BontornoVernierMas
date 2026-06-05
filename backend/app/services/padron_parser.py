"""services/padron_parser.py — File parser for padrón uploads (C-09).

Parses .xlsx and .csv files into EntradaPadronRaw DTOs without persisting
anything. The PadronService decides whether to confirm after preview.

Design decisions (C-09 design.md D4):
- Parser encapsulated here; PadronService calls it. Zero DB interaction.
- Required columns: nombre, apellidos, email, comision, regional.
  Missing columns raise PadronParseError with a list of missing names.
- Column matching is case-insensitive and strips whitespace from headers.
- comision and regional are allowed to be empty strings (treated as None).
"""

import csv
import io
from typing import Any

from pydantic import BaseModel, ConfigDict


class EntradaPadronRaw(BaseModel):
    """Parsed (pre-validation) student entry from a padrón file.

    All fields are strings before persistence. The service handles
    encryption and linking to Usuario.
    """

    model_config = ConfigDict(extra="forbid")

    nombre: str
    apellidos: str
    email: str
    comision: str | None = None
    regional: str | None = None


class PadronParseError(Exception):
    """Raised when a padrón file is missing required columns or is malformed.

    Attributes:
        missing_columns: List of column names that were expected but not found.
        detail: Human-readable error message.
    """

    def __init__(self, detail: str, missing_columns: list[str] | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.missing_columns = missing_columns or []


# Required column names (case-insensitive match)
_REQUIRED_COLUMNS = {"nombre", "apellidos", "email", "comision", "regional"}


def _normalize_header(header: str) -> str:
    """Normalize a column header: lowercase and strip whitespace."""
    return header.strip().lower()


def _validate_headers(headers: list[str]) -> None:
    """Raise PadronParseError if any required columns are missing."""
    normalized = {_normalize_header(h) for h in headers}
    missing = sorted(_REQUIRED_COLUMNS - normalized)
    if missing:
        raise PadronParseError(
            f"Missing required columns: {', '.join(missing)}",
            missing_columns=missing,
        )


def _row_to_entrada(row: dict[str, Any]) -> EntradaPadronRaw:
    """Convert a normalized row dict to EntradaPadronRaw."""
    # Normalize all keys
    normalized = {_normalize_header(k): (v or "").strip() for k, v in row.items()}
    return EntradaPadronRaw(
        nombre=normalized["nombre"],
        apellidos=normalized["apellidos"],
        email=normalized["email"],
        comision=normalized.get("comision") or None,
        regional=normalized.get("regional") or None,
    )


class PadronParser:
    """Stateless parser for padrón file uploads.

    Methods:
        parse_xlsx(file_bytes) -> list[EntradaPadronRaw]
        parse_csv(file_bytes)  -> list[EntradaPadronRaw]
    """

    def parse_xlsx(self, file_bytes: bytes) -> list[EntradaPadronRaw]:
        """Parse an .xlsx file into a list of EntradaPadronRaw.

        Args:
            file_bytes: Raw bytes of the .xlsx file.

        Returns:
            List of parsed entries.

        Raises:
            PadronParseError: If required columns are missing.
            ImportError: If openpyxl is not installed.
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

        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            raise PadronParseError("File is empty — no rows found.")

        # First row is the header
        headers = [str(h) if h is not None else "" for h in rows[0]]
        _validate_headers(headers)

        entries: list[EntradaPadronRaw] = []
        for row_values in rows[1:]:
            # Skip empty rows
            if all(v is None or str(v).strip() == "" for v in row_values):
                continue
            row_dict = {headers[i]: (str(v) if v is not None else "") for i, v in enumerate(row_values)}
            entries.append(_row_to_entrada(row_dict))

        wb.close()
        return entries

    def parse_csv(self, file_bytes: bytes) -> list[EntradaPadronRaw]:
        """Parse a .csv file into a list of EntradaPadronRaw.

        Handles UTF-8 and Latin-1 encodings. Uses csv.DictReader.

        Args:
            file_bytes: Raw bytes of the .csv file.

        Returns:
            List of parsed entries.

        Raises:
            PadronParseError: If required columns are missing.
        """
        # Try UTF-8 first, fall back to Latin-1
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = file_bytes.decode("latin-1")

        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None:
            raise PadronParseError("File is empty — no headers found.")

        _validate_headers(list(reader.fieldnames))

        entries: list[EntradaPadronRaw] = []
        for row in reader:
            # Skip empty rows
            if all(not (v or "").strip() for v in row.values()):
                continue
            entries.append(_row_to_entrada(row))

        return entries
