"""schemas/tarea.py — Pydantic v2 schemas for Tarea and ComentarioTarea (C-16).

Request/response DTOs for internal task management.
All schemas use extra='forbid' to reject undeclared fields.

Valid estados: Pendiente | En_progreso | Resuelta | Cancelada
Valid transitions: Pendiente → En_progreso → Resuelta | Cancelada
                   Pendiente → Cancelada
"""

import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# Valid estado values
ESTADOS_VALIDOS = frozenset({"Pendiente", "En_progreso", "Resuelta", "Cancelada"})

# Valid state transitions (from → to)
TRANSICIONES_VALIDAS: dict[str, frozenset[str]] = {
    "Pendiente": frozenset({"En_progreso", "Cancelada"}),
    "En_progreso": frozenset({"Resuelta", "Cancelada"}),
    "Resuelta": frozenset(),
    "Cancelada": frozenset(),
}


class TareaCreate(BaseModel):
    """Request body for creating a new Tarea (F8.1)."""

    model_config = ConfigDict(extra="forbid")

    titulo: str = Field(..., max_length=255, description="Short title of the task.")
    descripcion: Optional[str] = Field(None, description="Full description of the task.")
    asignado_a: uuid.UUID = Field(..., description="UUID of the user who must resolve the task.")
    materia_id: Optional[uuid.UUID] = Field(
        None,
        description="Materia context; nullable for institutional-level tasks.",
    )
    contexto_id: Optional[uuid.UUID] = Field(
        None,
        description="Optional reference to another domain entity.",
    )


class TareaOut(BaseModel):
    """Response schema for Tarea."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    titulo: str
    descripcion: Optional[str] = None
    asignado_a: uuid.UUID
    asignado_por: uuid.UUID
    estado: str
    materia_id: Optional[uuid.UUID] = None
    contexto_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class TareaEstadoUpdate(BaseModel):
    """Request body for changing Tarea estado (F8.2)."""

    model_config = ConfigDict(extra="forbid")

    estado: Literal["Pendiente", "En_progreso", "Resuelta", "Cancelada"] = Field(
        ...,
        description="New estado for the task. Must be a valid transition from the current estado.",
    )


class TareaDelegarUpdate(BaseModel):
    """Request body for delegating (reassigning) a Tarea (F8.3)."""

    model_config = ConfigDict(extra="forbid")

    asignado_a: uuid.UUID = Field(
        ...,
        description="UUID of the new assignee. Original asignado_por is preserved.",
    )


class TareaFilter(BaseModel):
    """Optional filters for listing tareas."""

    model_config = ConfigDict(extra="forbid")

    estado: Optional[str] = None
    asignado_a: Optional[uuid.UUID] = None
    materia_id: Optional[uuid.UUID] = None


class ComentarioCreate(BaseModel):
    """Request body for adding a comment to a Tarea (F8.2)."""

    model_config = ConfigDict(extra="forbid")

    contenido: str = Field(..., min_length=1, description="Comment text content.")


class ComentarioOut(BaseModel):
    """Response schema for ComentarioTarea."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    tarea_id: uuid.UUID
    autor_id: uuid.UUID
    contenido: str
    created_at: datetime
    updated_at: datetime
