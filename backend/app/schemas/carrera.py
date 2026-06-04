"""schemas/carrera.py — Pydantic schemas for Carrera (C-06: estructura-academica).

All schemas use extra='forbid' to reject undeclared fields per project rules.
tenant_id is NEVER in request schemas — it is always sourced from the JWT.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.base import EstadoEntidad

_FORBID = ConfigDict(extra="forbid")


class CarreraCreate(BaseModel):
    """Request body for POST /v1/carreras."""

    model_config = _FORBID

    codigo: str = Field(..., min_length=1, max_length=50, description="Código único del programa (ej: TUPAD)")
    nombre: str = Field(..., min_length=1, max_length=200, description="Nombre completo del programa académico")
    estado: EstadoEntidad = Field(default=EstadoEntidad.Activa)


class CarreraUpdate(BaseModel):
    """Request body for PATCH /v1/carreras/{id}. All fields are optional."""

    model_config = _FORBID

    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    nombre: str | None = Field(default=None, min_length=1, max_length=200)
    estado: EstadoEntidad | None = None


class CarreraOut(BaseModel):
    """Response schema for Carrera resources."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    codigo: str
    nombre: str
    estado: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
