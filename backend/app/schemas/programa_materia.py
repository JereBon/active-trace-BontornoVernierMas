"""schemas/programa_materia.py — Pydantic schemas for ProgramaMateria (C-17).

All schemas use extra='forbid'. tenant_id is never in request payloads.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

_FORBID = ConfigDict(extra="forbid")


class ProgramaMateriaCreate(BaseModel):
    """Request body for POST /v1/programas."""

    model_config = _FORBID

    materia_id: uuid.UUID = Field(..., description="UUID de la materia")
    carrera_id: uuid.UUID | None = Field(default=None, description="UUID de la carrera (opcional)")
    cohorte_id: uuid.UUID | None = Field(default=None, description="UUID de la cohorte (opcional)")
    titulo: str = Field(..., min_length=1, max_length=300, description="Título descriptivo del programa")
    referencia_archivo: str | None = Field(
        default=None,
        max_length=1000,
        description="URL/path al archivo en el servicio de almacenamiento externo",
    )
    vigente: bool = Field(default=True, description="Si este programa es el vigente para la combinación")
    publicado_en: datetime | None = Field(default=None, description="Fecha de publicación al alumno")


class ProgramaMateriaUpdate(BaseModel):
    """Request body for PATCH /v1/programas/{id}. All fields optional."""

    model_config = _FORBID

    titulo: str | None = Field(default=None, min_length=1, max_length=300)
    referencia_archivo: str | None = Field(default=None, max_length=1000)
    vigente: bool | None = None
    publicado_en: datetime | None = None


class ProgramaMateriaOut(BaseModel):
    """Response schema for ProgramaMateria resources."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    materia_id: uuid.UUID
    carrera_id: uuid.UUID | None
    cohorte_id: uuid.UUID | None
    titulo: str
    referencia_archivo: str | None
    vigente: bool
    publicado_en: datetime | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
