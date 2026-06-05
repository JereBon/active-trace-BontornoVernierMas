"""schemas/encuentro.py — Pydantic v2 schemas for Encuentros (C-13).

Request/response DTOs for SlotEncuentro and InstanciaEncuentro.
All schemas use extra='forbid' to reject undeclared fields.
"""

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SlotCreate(BaseModel):
    """Request body for creating a SlotEncuentro (F6.1 recurrente, F6.2 único)."""

    model_config = ConfigDict(extra="forbid")

    asignacion_id: uuid.UUID
    materia_id: uuid.UUID
    titulo: str = Field(..., min_length=1, max_length=200)
    hora: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="HH:MM format")
    dia_semana: str = Field(
        ...,
        description="Lunes | Martes | Miercoles | Jueves | Viernes | Sabado | Domingo",
    )
    fecha_inicio: date
    cant_semanas: int = Field(default=0, ge=0, description="0 = fecha_unica mode")
    fecha_unica: Optional[date] = Field(default=None, description="Used when cant_semanas=0")
    meet_url: Optional[str] = None
    vig_desde: Optional[date] = None
    vig_hasta: Optional[date] = None


class SlotOut(BaseModel):
    """Response schema for SlotEncuentro."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    asignacion_id: uuid.UUID
    materia_id: uuid.UUID
    titulo: str
    hora: str
    dia_semana: str
    fecha_inicio: date
    cant_semanas: int
    fecha_unica: Optional[date] = None
    meet_url: Optional[str] = None
    vig_desde: Optional[date] = None
    vig_hasta: Optional[date] = None
    created_at: datetime
    updated_at: datetime


class InstanciaOut(BaseModel):
    """Response schema for InstanciaEncuentro."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    slot_id: Optional[uuid.UUID] = None
    materia_id: uuid.UUID
    fecha: date
    hora: str
    titulo: str
    estado: str
    meet_url: Optional[str] = None
    video_url: Optional[str] = None
    comentario: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class InstanciaUpdate(BaseModel):
    """Request body for editing an InstanciaEncuentro (F6.3)."""

    model_config = ConfigDict(extra="forbid")

    estado: Optional[str] = Field(
        default=None,
        description="Programado | Realizado | Cancelado",
    )
    meet_url: Optional[str] = None
    video_url: Optional[str] = None
    comentario: Optional[str] = None


class SlotWithInstancesOut(BaseModel):
    """Response with slot + generated instances."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    slot: SlotOut
    instancias: list[InstanciaOut]
