"""schemas/calificacion.py — Pydantic schemas for calificaciones endpoints (C-10).

All request schemas use extra='forbid'. tenant_id is never in request payloads
(always from JWT session).
"""

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_FORBID = ConfigDict(extra="forbid")
_FORBID_FROM_ORM = ConfigDict(extra="forbid", from_attributes=True)


# ── Preview response ──────────────────────────────────────────────────────────


class AlumnoPreviewItem(BaseModel):
    """One student's grades from the preview."""

    model_config = _FORBID

    email: str
    notas: dict[str, Any] = Field(default_factory=dict)


class CalificacionPreviewResponse(BaseModel):
    """Response for POST /preview — no data is persisted."""

    model_config = _FORBID

    actividades_numericas: list[str] = Field(
        default_factory=list,
        description="Activity names detected as numeric (columns ending in '(Real)').",
    )
    actividades_textuales: list[str] = Field(
        default_factory=list,
        description="Activity names detected as textual scale.",
    )
    alumnos_preview: list[AlumnoPreviewItem] = Field(
        default_factory=list,
        description="Preview of students and their detected grades.",
    )


# ── Import request ────────────────────────────────────────────────────────────


class ImportarCalificacionesRequest(BaseModel):
    """Form fields for POST /importar (multipart/form-data alongside file upload)."""

    model_config = _FORBID

    asignacion_id: uuid.UUID = Field(..., description="ID of the docente's asignacion.")
    actividades_seleccionadas: list[str] = Field(
        ...,
        min_length=1,
        description="Activity names to include in the import.",
    )


# ── Import response ───────────────────────────────────────────────────────────


class CalificacionImportadaItem(BaseModel):
    """One imported calificacion record."""

    model_config = _FORBID_FROM_ORM

    id: uuid.UUID
    entrada_padron_id: uuid.UUID
    materia_id: uuid.UUID
    actividad: str
    nota_numerica: float | None = None
    nota_textual: str | None = None
    aprobado: bool
    origen: str


class ImportarCalificacionesResponse(BaseModel):
    """Response for POST /importar."""

    model_config = _FORBID

    calificaciones_importadas: int
    mensaje: str


# ── Umbral request ────────────────────────────────────────────────────────────


class UmbralMateriaRequest(BaseModel):
    """Request body for PUT /umbral."""

    model_config = _FORBID

    asignacion_id: uuid.UUID = Field(..., description="ID of the docente's asignacion.")
    umbral_pct: int = Field(
        default=60,
        ge=0,
        le=100,
        description="Minimum passing percentage (0–100). Default: 60.",
    )
    valores_aprobatorios: list[str] = Field(
        default_factory=list,
        description="Textual grade values that count as passing.",
    )


# ── Umbral response ───────────────────────────────────────────────────────────


class UmbralMateriaResponse(BaseModel):
    """Response for PUT /umbral."""

    model_config = _FORBID_FROM_ORM

    id: uuid.UUID
    asignacion_id: uuid.UUID
    materia_id: uuid.UUID
    umbral_pct: int
    valores_aprobatorios: list[str]
