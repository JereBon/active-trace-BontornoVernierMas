"""schemas/cohorte.py — Pydantic schemas for Cohorte (C-06: estructura-academica).

All schemas use extra='forbid'. tenant_id is never in request payloads.
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.base import EstadoEntidad

_FORBID = ConfigDict(extra="forbid")


class CohorteCreate(BaseModel):
    """Request body for POST /v1/cohortes."""

    model_config = _FORBID

    carrera_id: uuid.UUID = Field(..., description="UUID de la Carrera a la que pertenece esta cohorte")
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre de la cohorte (ej: AGO-2025)")
    anio: int = Field(..., ge=2000, le=2100, description="Año de inicio de la cohorte")
    vig_desde: date = Field(..., description="Inicio de vigencia")
    vig_hasta: date | None = Field(default=None, description="Fin de vigencia; null = abierta")
    estado: EstadoEntidad = Field(default=EstadoEntidad.Activa)

    @model_validator(mode="after")
    def vig_hasta_after_vig_desde(self) -> "CohorteCreate":
        if self.vig_hasta is not None and self.vig_hasta < self.vig_desde:
            raise ValueError("vig_hasta must be after vig_desde")
        return self


class CohorteUpdate(BaseModel):
    """Request body for PATCH /v1/cohortes/{id}. All fields optional."""

    model_config = _FORBID

    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    anio: int | None = Field(default=None, ge=2000, le=2100)
    vig_desde: date | None = None
    vig_hasta: date | None = None
    estado: EstadoEntidad | None = None


class CohorteOut(BaseModel):
    """Response schema for Cohorte resources."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    carrera_id: uuid.UUID
    nombre: str
    anio: int
    vig_desde: date
    vig_hasta: date | None
    estado: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
