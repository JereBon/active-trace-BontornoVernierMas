"""schemas/padron.py — Pydantic schemas for padrón endpoints (C-09).

All request schemas use extra='forbid'. tenant_id is never in request payloads.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

_FORBID = ConfigDict(extra="forbid")
_FORBID_FROM_ORM = ConfigDict(extra="forbid", from_attributes=True)


# ── Request schemas ───────────────────────────────────────────────────────────


class ConfirmarImportacionRequest(BaseModel):
    """Request body for POST /v1/padron/confirmar."""

    model_config = _FORBID

    materia_id: uuid.UUID = Field(..., description="ID de la materia")
    cohorte_id: uuid.UUID = Field(..., description="ID de la cohorte")
    entradas: list["EntradaPreviewItem"] = Field(
        ..., min_length=1, description="Listado de entradas del preview a confirmar"
    )


class EntradaPreviewItem(BaseModel):
    """One student entry from the preview to be confirmed."""

    model_config = _FORBID

    nombre: str
    apellidos: str
    email: str
    comision: str | None = None
    regional: str | None = None


class SyncMoodleRequest(BaseModel):
    """Request body for POST /v1/padron/sync-moodle/{materia_id}."""

    model_config = _FORBID

    cohorte_id: uuid.UUID = Field(..., description="ID de la cohorte")
    course_id: int = Field(..., description="ID del curso en Moodle")
    moodle_url: str = Field(..., description="URL base de Moodle (sin slash final)")
    moodle_token: str = Field(..., description="Token de Moodle WS (ya desencriptado)")


# ── Response schemas ──────────────────────────────────────────────────────────


class EntradaPreviewOut(BaseModel):
    """Preview item returned before confirmation."""

    model_config = _FORBID

    nombre: str
    apellidos: str
    email: str
    comision: str | None
    regional: str | None


class VersionPadronOut(BaseModel):
    """Response schema for a VersionPadron."""

    model_config = _FORBID_FROM_ORM

    id: uuid.UUID
    tenant_id: uuid.UUID
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    cargado_por: uuid.UUID
    cargado_at: datetime
    activa: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class VaciarPadronOut(BaseModel):
    """Response after vaciar operation."""

    model_config = _FORBID

    filas_afectadas: int
    message: str
