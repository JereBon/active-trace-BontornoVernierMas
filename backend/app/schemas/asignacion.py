"""schemas/asignacion.py — Pydantic schemas for Asignacion (C-07 / C-08).

All schemas use extra='forbid'. tenant_id is always sourced from the JWT.
"""

import uuid
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_FORBID = ConfigDict(extra="forbid")
_FORBID_FROM_ATTRS = ConfigDict(extra="forbid", from_attributes=True)

# Valid role codes from the domain model (knowledge-base/03_actores_y_roles.md)
ROLES_VALIDOS = {"ALUMNO", "TUTOR", "PROFESOR", "COORDINADOR", "NEXO", "ADMIN", "FINANZAS"}


class AsignacionCreate(BaseModel):
    """Request body for POST /v1/equipos/."""

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

    @field_validator("rol")
    @classmethod
    def validate_rol(cls, v: str) -> str:
        if v not in ROLES_VALIDOS:
            raise ValueError(f"rol must be one of: {', '.join(sorted(ROLES_VALIDOS))}")
        return v


class AsignacionUpdate(BaseModel):
    """Request body for PUT /v1/equipos/{id}. All fields optional."""

    model_config = _FORBID

    rol: Optional[str] = Field(default=None)
    materia_id: Optional[uuid.UUID] = Field(default=None)
    carrera_id: Optional[uuid.UUID] = Field(default=None)
    cohorte_id: Optional[uuid.UUID] = Field(default=None)
    comisiones: Optional[List[str]] = Field(default=None)
    responsable_id: Optional[uuid.UUID] = Field(default=None)
    desde: Optional[date] = Field(default=None)
    hasta: Optional[date] = Field(default=None)

    @field_validator("rol")
    @classmethod
    def validate_rol(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ROLES_VALIDOS:
            raise ValueError(f"rol must be one of: {', '.join(sorted(ROLES_VALIDOS))}")
        return v


class AsignacionFilter(BaseModel):
    """Query params for GET /v1/equipos/. All fields optional."""

    model_config = ConfigDict(extra="forbid")

    materia_id: Optional[uuid.UUID] = Field(default=None)
    carrera_id: Optional[uuid.UUID] = Field(default=None)
    cohorte_id: Optional[uuid.UUID] = Field(default=None)
    usuario_id: Optional[uuid.UUID] = Field(default=None)
    rol: Optional[str] = Field(default=None)
    solo_vigentes: bool = Field(default=False, description="If true, return only active assignments")


class AsignacionMasivaCreate(BaseModel):
    """Request body for POST /v1/equipos/asignacion-masiva."""

    model_config = _FORBID

    usuario_ids: List[uuid.UUID] = Field(..., min_length=1, description="List of user UUIDs to assign")
    rol: str = Field(..., description="Role code for all assignments")
    materia_id: Optional[uuid.UUID] = Field(default=None)
    carrera_id: Optional[uuid.UUID] = Field(default=None)
    cohorte_id: Optional[uuid.UUID] = Field(default=None)
    comisiones: List[str] = Field(default_factory=list)
    responsable_id: Optional[uuid.UUID] = Field(default=None)
    desde: date = Field(..., description="Start date of validity")
    hasta: Optional[date] = Field(default=None)

    @field_validator("rol")
    @classmethod
    def validate_rol(cls, v: str) -> str:
        if v not in ROLES_VALIDOS:
            raise ValueError(f"rol must be one of: {', '.join(sorted(ROLES_VALIDOS))}")
        return v


class ClonarEquipoRequest(BaseModel):
    """Request body for POST /v1/equipos/clonar."""

    model_config = _FORBID

    materia_id: uuid.UUID = Field(..., description="Materia being cloned")
    carrera_id: uuid.UUID = Field(..., description="Carrera being cloned")
    origen_cohorte_id: uuid.UUID = Field(..., description="Source cohorte")
    destino_cohorte_id: uuid.UUID = Field(..., description="Destination cohorte")
    desde: date = Field(..., description="Start date for cloned assignments")
    hasta: Optional[date] = Field(default=None, description="End date for cloned assignments")

    @model_validator(mode="after")
    def origen_distinto_destino(self) -> "ClonarEquipoRequest":
        if self.origen_cohorte_id == self.destino_cohorte_id:
            raise ValueError("origen_cohorte_id and destino_cohorte_id must be different")
        return self


class VigenciaMasivaRequest(BaseModel):
    """Request body for PUT /v1/equipos/vigencia-masiva."""

    model_config = _FORBID

    materia_id: uuid.UUID = Field(..., description="Materia of the team")
    carrera_id: uuid.UUID = Field(..., description="Carrera of the team")
    cohorte_id: uuid.UUID = Field(..., description="Cohorte of the team")
    desde: date = Field(..., description="New start date for all assignments in the team")
    hasta: Optional[date] = Field(default=None, description="New end date; None = open-ended")


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


class AsignacionMasivaOut(BaseModel):
    """Response schema for bulk operations (masiva/clonar)."""

    model_config = ConfigDict(extra="forbid", from_attributes=False)

    creadas: List[AsignacionOut] = Field(default_factory=list)
    omitidos: List[uuid.UUID] = Field(
        default_factory=list,
        description="usuario_ids that were skipped due to existing assignments",
    )


class VigenciaMasivaOut(BaseModel):
    """Response schema for PUT /v1/equipos/vigencia-masiva."""

    model_config = ConfigDict(extra="forbid")

    filas_afectadas: int
