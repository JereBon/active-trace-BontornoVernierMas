"""schemas/guardia.py — Pydantic v2 schemas for Guardia (C-13).

Request/response DTOs for Guardia (duty shift).
All schemas use extra='forbid' to reject undeclared fields.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class GuardiaCreate(BaseModel):
    """Request body for registering a new Guardia (F6.6)."""

    model_config = ConfigDict(extra="forbid")

    asignacion_id: uuid.UUID
    materia_id: uuid.UUID
    carrera_id: uuid.UUID
    cohorte_id: uuid.UUID
    dia: str = Field(
        ...,
        description="Lunes | Martes | Miercoles | Jueves | Viernes | Sabado | Domingo",
    )
    horario: str = Field(..., max_length=20, description="Range e.g. '14:00-14:45'")
    estado: str = Field(
        default="Pendiente",
        description="Pendiente | Realizada | Cancelada",
    )
    comentarios: Optional[str] = None


class GuardiaOut(BaseModel):
    """Response schema for Guardia."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    asignacion_id: uuid.UUID
    materia_id: uuid.UUID
    carrera_id: uuid.UUID
    cohorte_id: uuid.UUID
    dia: str
    horario: str
    estado: str
    comentarios: Optional[str] = None
    creada_at: datetime
    created_at: datetime
    updated_at: datetime


class GuardiaFilter(BaseModel):
    """Optional filters for listing guardias."""

    model_config = ConfigDict(extra="forbid")

    materia_id: Optional[uuid.UUID] = None
    asignacion_id: Optional[uuid.UUID] = None
    carrera_id: Optional[uuid.UUID] = None
    cohorte_id: Optional[uuid.UUID] = None
    estado: Optional[str] = None
