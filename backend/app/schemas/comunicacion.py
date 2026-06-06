"""schemas/comunicacion.py — Pydantic DTOs for comunicaciones (C-12).

All schemas use extra='forbid' to reject undeclared fields.

Schemas:
  PreviewRequest    — input for POST /v1/comunicaciones/preview
  PreviewResponse   — rendered preview output (asunto + cuerpo)
  DestinatarioItem  — one recipient with their template variables
  EncoladoRequest   — input for POST /v1/comunicaciones/encolar
  EncoladoResponse  — lote_id and count after successful enqueue
  ComunicacionOut   — single message status (destinatario masked)
  LoteStatusOut     — lote status with list of messages
"""

import re
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


# ── Shared helper ──────────────────────────────────────────────────────────────

def _mask_email(email: str) -> str:
    """Mask an email for safe display in API responses.

    Example: 'alumno@universidad.edu' → '***@universidad.edu'
    """
    if "@" not in email:
        return "***"
    _, domain = email.split("@", 1)
    return f"***@{domain}"


def _render_template(template: str, variables: dict[str, str]) -> str:
    """Render a template string by replacing {{key}} placeholders.

    Raises ValueError listing all missing keys if any placeholder has no value.
    """
    # Find all placeholders
    placeholders = re.findall(r"\{\{(\w+)\}\}", template)
    missing = [p for p in placeholders if p not in variables]
    if missing:
        raise ValueError(f"Missing template variables: {', '.join(missing)}")
    result = template
    for key, value in variables.items():
        result = result.replace(f"{{{{{key}}}}}", value)
    return result


# ── Preview ───────────────────────────────────────────────────────────────────


class PreviewRequest(BaseModel):
    """Input for the preview endpoint. No DB writes occur."""

    model_config = ConfigDict(extra="forbid")

    asunto: str
    cuerpo: str
    variables: dict[str, str] = {}


class PreviewResponse(BaseModel):
    """Rendered preview — asunto and cuerpo with variables substituted."""

    model_config = ConfigDict(extra="forbid")

    asunto: str
    cuerpo: str


# ── Encolado ──────────────────────────────────────────────────────────────────


class DestinatarioItem(BaseModel):
    """One recipient in a bulk send request."""

    model_config = ConfigDict(extra="forbid")

    email: str
    variables: dict[str, str] = {}


class EncoladoRequest(BaseModel):
    """Input for the enqueue endpoint."""

    model_config = ConfigDict(extra="forbid")

    materia_id: uuid.UUID | None = None
    asunto: str
    cuerpo: str
    destinatarios: list[DestinatarioItem]

    @field_validator("destinatarios")
    @classmethod
    def at_least_one_recipient(cls, v: list[DestinatarioItem]) -> list[DestinatarioItem]:
        if not v:
            raise ValueError("At least one recipient is required.")
        return v


class EncoladoResponse(BaseModel):
    """Response after successfully enqueuing a batch."""

    model_config = ConfigDict(extra="forbid")

    lote_id: uuid.UUID
    count: int
    requiere_aprobacion: bool


# ── Single message output ─────────────────────────────────────────────────────


class ComunicacionOut(BaseModel):
    """Single communication record for API responses.

    destinatario is always masked (***@domain) to protect PII.
    """

    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    lote_id: uuid.UUID
    destinatario: str          # always masked value, never plaintext
    asunto: str
    estado: str
    aprobado: bool
    enviado_at: Any | None = None
    created_at: Any


# ── Lote status ───────────────────────────────────────────────────────────────


class LoteStatusOut(BaseModel):
    """Status of a batch with its individual messages."""

    model_config = ConfigDict(extra="forbid")

    lote_id: uuid.UUID
    total: int
    pendientes: int
    enviados: int
    errores: int
    cancelados: int
    mensajes: list[ComunicacionOut]
