"""schemas/fecha_academica.py — Pydantic schemas for FechaAcademica (C-17).

All schemas use extra='forbid'. tenant_id is never in request payloads.
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.fecha_academica import TipoEvaluacion

_FORBID = ConfigDict(extra="forbid")


class FechaAcademicaCreate(BaseModel):
    """Request body for POST /v1/fechas-academicas."""

    model_config = _FORBID

    materia_id: uuid.UUID = Field(..., description="UUID de la materia")
    cohorte_id: uuid.UUID = Field(..., description="UUID de la cohorte")
    tipo: TipoEvaluacion = Field(..., description="PARCIAL | TP | COLOQUIO | RECUPERATORIO")
    numero: int = Field(..., ge=1, description="Número de instancia (1 = primero, etc.)")
    periodo: str = Field(..., min_length=1, max_length=20, description="ej: '2026-1'")
    fecha: date = Field(..., description="Fecha exacta de la evaluación")
    titulo: str = Field(..., min_length=1, max_length=300, description="Título descriptivo")


class FechaAcademicaUpdate(BaseModel):
    """Request body for PATCH /v1/fechas-academicas/{id}. All fields optional."""

    model_config = _FORBID

    tipo: TipoEvaluacion | None = None
    numero: int | None = Field(default=None, ge=1)
    periodo: str | None = Field(default=None, min_length=1, max_length=20)
    fecha: date | None = None
    titulo: str | None = Field(default=None, min_length=1, max_length=300)


class FechaAcademicaOut(BaseModel):
    """Response schema for FechaAcademica resources."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    tipo: TipoEvaluacion
    numero: int
    periodo: str
    fecha: date
    titulo: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
