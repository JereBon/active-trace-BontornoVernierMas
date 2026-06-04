"""schemas/asignacion.py — Pydantic schemas for Asignacion (C-07).

All schemas use extra='forbid'. tenant_id is always sourced from the JWT.
"""

import uuid
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

_FORBID = ConfigDict(extra="forbid")
_FORBID_FROM_ATTRS = ConfigDict(extra="forbid", from_attributes=True)

# Valid role codes from the domain model (knowledge-base/03_actores_y_roles.md)
ROLES_VALIDOS = {"ALUMNO", "TUTOR", "PROFESOR", "COORDINADOR", "NEXO", "ADMIN", "FINANZAS"}


class AsignacionCreate(BaseModel):
    """Request body for POST /v1/asignaciones."""

    model_config = _FORBID

    usuario_id: uuid.UUID = Field(..., description="UUID of the user to assign")
    rol: str = Field(..., description="Role code: ALUMNO|TUTOR|PROFESOR|COORDINADOR|NEXO|ADMIN|FINANZAS")
    materia_id: Optional[uuid.UUID] = Field(default=None, description="Scope to a materia (optional)")
    carrera_id: Optional[uuid.UUID] = Field(default=None, description="Scope to a carrera (optional)")
    cohorte_id: Optional[uuid.UUID] = Field(default=None, description="Scope to a cohorte (optional)")
    comisiones: List[str] = Field(default_factory=list, description="List of comision codes")
    responsable_id: Optional[uuid.UUID] = Field(default=None, description="Supervising coordinator UUID")
    desde: date = Field(..., description="Start date of validity")
    hasta: Optional[date] = Field(default=None, description="End date; None = open-ended")


class AsignacionOut(BaseModel):
    """Response schema for Asignacion resources."""

    model_config = _FORBID_FROM_ATTRS

    id: uuid.UUID
    tenant_id: uuid.UUID
    usuario_id: uuid.UUID
    rol: str
    materia_id: Optional[uuid.UUID] = None
    carrera_id: Optional[uuid.UUID] = None
    cohorte_id: Optional[uuid.UUID] = None
    comisiones: List[str]
    responsable_id: Optional[uuid.UUID] = None
    desde: date
    hasta: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
