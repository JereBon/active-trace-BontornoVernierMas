"""schemas/evaluacion.py — Pydantic schemas for Evaluacion, Reserva, Resultado (C-14).

All schemas use extra='forbid' to reject undeclared fields.
tenant_id is NEVER in request schemas — always sourced from JWT.

Schemas:
  EvaluacionCreate     — POST /v1/coloquios (COORDINADOR/ADMIN)
  EvaluacionPatch      — PATCH /v1/coloquios/{id} (COORDINADOR/ADMIN)
  EvaluacionOut        — Response for Evaluacion resources
  EvaluacionMetricas   — Panel metrics response (F7.1)
  ReservaCreate        — POST /v1/coloquios/{id}/reservas (ALUMNO)
  ReservaOut           — Response for ReservaEvaluacion resources
  ResultadoCreate      — POST /v1/coloquios/{id}/resultados (COORDINADOR/ADMIN)
  ResultadoOut         — Response for ResultadoEvaluacion resources
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.evaluacion import EstadoEvaluacion, EstadoReserva, TipoEvaluacionColoquio

_FORBID = ConfigDict(extra="forbid")
_FORBID_FROM_ATTRS = ConfigDict(extra="forbid", from_attributes=True)


# ── Evaluacion schemas ────────────────────────────────────────────────────────


class EvaluacionCreate(BaseModel):
    """Request body for POST /v1/coloquios — create a coloquio call."""

    model_config = _FORBID

    materia_id: uuid.UUID = Field(..., description="FK → materias.id")
    cohorte_id: uuid.UUID = Field(..., description="FK → cohortes.id")
    tipo: TipoEvaluacionColoquio = Field(
        default=TipoEvaluacionColoquio.Coloquio,
        description="Parcial | TP | Coloquio | Recuperatorio",
    )
    instancia: str = Field(..., min_length=1, max_length=255, description="Label, e.g. 'Coloquio Final'")
    dias_disponibles: int = Field(..., ge=1, description="Days the enrollment window is open")
    cupos_disponibles: int = Field(..., ge=1, description="Maximum active reservations allowed")


class EvaluacionPatch(BaseModel):
    """Request body for PATCH /v1/coloquios/{id} — update mutable fields."""

    model_config = _FORBID

    instancia: str | None = Field(default=None, min_length=1, max_length=255)
    dias_disponibles: int | None = Field(default=None, ge=1)
    cupos_disponibles: int | None = Field(default=None, ge=1)
    estado: EstadoEvaluacion | None = Field(default=None, description="Abierta | Cerrada | Cancelada")


class EvaluacionOut(BaseModel):
    """Response schema for a single Evaluacion."""

    model_config = _FORBID_FROM_ATTRS

    id: uuid.UUID
    tenant_id: uuid.UUID
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    tipo: str
    instancia: str
    dias_disponibles: int
    cupos_disponibles: int
    estado: str
    created_at: datetime
    updated_at: datetime


class EvaluacionMetricas(BaseModel):
    """Panel metrics for F7.1 — summary across all evaluaciones in tenant."""

    model_config = _FORBID_FROM_ATTRS

    total_convocatorias: int = Field(..., description="Total Evaluacion records (Abierta)")
    total_reservas_activas: int = Field(..., description="Total ReservaEvaluacion with estado=Activa")
    total_resultados: int = Field(..., description="Total ResultadoEvaluacion records")
    total_cupos_libres: int = Field(..., description="Sum of cupos_disponibles across open evaluaciones")


# ── Reserva schemas ───────────────────────────────────────────────────────────


class ReservaCreate(BaseModel):
    """Request body for POST /v1/coloquios/{evaluacion_id}/reservas — alumno books a slot."""

    model_config = _FORBID

    fecha_hora: datetime = Field(..., description="Chosen datetime slot for the coloquio")


class ReservaOut(BaseModel):
    """Response schema for a ReservaEvaluacion."""

    model_config = _FORBID_FROM_ATTRS

    id: uuid.UUID
    tenant_id: uuid.UUID
    evaluacion_id: uuid.UUID
    alumno_id: uuid.UUID
    fecha_hora: datetime
    estado: str
    created_at: datetime
    updated_at: datetime


# ── Resultado schemas ─────────────────────────────────────────────────────────


class ResultadoCreate(BaseModel):
    """Request body for POST /v1/coloquios/{evaluacion_id}/resultados — register outcome."""

    model_config = _FORBID

    alumno_id: uuid.UUID = Field(..., description="FK → usuarios.id (ALUMNO being evaluated)")
    aprobado: bool = Field(..., description="True if the student passed")
    nota_final: str | None = Field(default=None, max_length=100, description="Numeric or qualitative grade")
    observaciones: str | None = Field(default=None, description="Optional examiner notes")


class ResultadoOut(BaseModel):
    """Response schema for a ResultadoEvaluacion."""

    model_config = _FORBID_FROM_ATTRS

    id: uuid.UUID
    tenant_id: uuid.UUID
    evaluacion_id: uuid.UUID
    alumno_id: uuid.UUID
    aprobado: bool
    nota_final: str | None
    observaciones: str | None
    created_at: datetime
    updated_at: datetime
