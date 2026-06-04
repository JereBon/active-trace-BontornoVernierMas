"""schemas/aviso.py — Pydantic schemas for Aviso and AvisoAck (C-15).

All schemas use extra='forbid' to reject undeclared fields per project rules.
tenant_id and publicado_por are NEVER in request schemas — always from the JWT.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.aviso import AvisoScope

_FORBID = ConfigDict(extra="forbid")
_FORBID_FROM_ATTRS = ConfigDict(extra="forbid", from_attributes=True)


class AvisoCreate(BaseModel):
    """Request body for POST /v1/avisos."""

    model_config = _FORBID

    titulo: str = Field(..., min_length=1, max_length=300, description="Título del aviso")
    cuerpo: str = Field(..., min_length=1, description="Cuerpo del aviso")
    scope: AvisoScope = Field(
        default=AvisoScope.TODOS,
        description="Audiencia: TODOS | ROL | USUARIO",
    )
    scope_valor: str | None = Field(
        default=None,
        description="Código de rol (cuando scope=ROL) o UUID de usuario (cuando scope=USUARIO)",
    )
    vig_desde: datetime = Field(..., description="Inicio de vigencia (inclusive)")
    vig_hasta: datetime = Field(..., description="Fin de vigencia (inclusive, > vig_desde)")

    @model_validator(mode="after")
    def _vig_hasta_posterior(self) -> "AvisoCreate":
        if self.vig_hasta <= self.vig_desde:
            raise ValueError("vig_hasta debe ser posterior a vig_desde")
        return self


class AvisoPatch(BaseModel):
    """Request body for PATCH /v1/avisos/{id}. Only allows toggling activo."""

    model_config = _FORBID

    activo: bool = Field(..., description="False para desactivar (soft delete)")


class AvisoOut(BaseModel):
    """Response schema for Aviso resources."""

    model_config = _FORBID_FROM_ATTRS

    id: uuid.UUID
    tenant_id: uuid.UUID
    titulo: str
    cuerpo: str
    scope: str
    scope_valor: str | None
    vig_desde: datetime
    vig_hasta: datetime
    activo: bool
    publicado_por: uuid.UUID
    created_at: datetime
    updated_at: datetime


class AvisoAckOut(BaseModel):
    """Response schema for AvisoAck records (who acknowledged an Aviso)."""

    model_config = _FORBID_FROM_ATTRS

    usuario_id: uuid.UUID
    leido_en: datetime
