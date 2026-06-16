"""schemas/materia.py — Pydantic schemas for Materia (C-06: estructura-academica).

All schemas use extra='forbid'. tenant_id is never in request payloads.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.base import EstadoEntidad

_FORBID = ConfigDict(extra="forbid")


class MateriaCreate(BaseModel):
    """Request body for POST /v1/materias."""

    model_config = _FORBID

    codigo: str = Field(..., min_length=1, max_length=50, description="Código único de la materia (ej: PROG_I)")
    nombre: str = Field(..., min_length=1, max_length=200, description="Nombre completo de la materia")
    estado: EstadoEntidad = Field(default=EstadoEntidad.Activa)


class MateriaUpdate(BaseModel):
    """Request body for PATCH /v1/materias/{id}. All fields optional."""

    model_config = _FORBID

    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    nombre: str | None = Field(default=None, min_length=1, max_length=200)
    estado: EstadoEntidad | None = None


class MateriaOut(BaseModel):
    """Response schema for Materia resources."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    codigo: str
    nombre: str
    estado: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
