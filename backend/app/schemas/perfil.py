"""schemas/perfil.py — Pydantic schemas for own-profile endpoints (C-20).

PerfilUpdate: editable fields for PATCH /api/perfil.
  - nombre, apellidos, regional, modalidad_cobro, cbu, alias_cbu, banco are editable.
  - CUIL is read-only; if supplied → 422 Unprocessable Entity.

PerfilOut: response schema (reuses UsuarioOut fields subset).
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

_FORBID = ConfigDict(extra="forbid")
_FORBID_FROM_ATTRS = ConfigDict(extra="forbid", from_attributes=True)


class PerfilUpdate(BaseModel):
    """Request body for PATCH /api/perfil.

    cuil is explicitly disallowed — 422 if supplied.
    All other PII/profile fields are optional.
    """

    model_config = _FORBID

    nombre: Optional[str] = Field(default=None, max_length=200, description="First name")
    apellidos: Optional[str] = Field(default=None, max_length=200, description="Last name(s)")
    regional: Optional[str] = Field(default=None, max_length=100, description="Institutional branch")
    cbu: Optional[str] = Field(default=None, max_length=30, description="Bank account key (will be encrypted)")
    alias_cbu: Optional[str] = Field(default=None, max_length=100, description="CBU alias (will be encrypted)")
    banco: Optional[str] = Field(default=None, max_length=100, description="Bank name")
    facturador: Optional[bool] = Field(default=None, description="True if user issues invoices")


class PerfilOut(BaseModel):
    """Response schema for GET /api/perfil and PATCH /api/perfil."""

    # from_attributes=True so we can pass ORM objects or dicts.
    # extra="ignore" because decrypt_usuario returns additional fields (dni, etc.)
    # that are not part of the own-profile response.
    model_config = ConfigDict(extra="ignore", from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    email: Optional[str] = Field(default=None, description="Decrypted email")
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    cuil: Optional[str] = Field(default=None, description="Decrypted CUIL (read-only)")
    cbu: Optional[str] = Field(default=None, description="Decrypted CBU")
    alias_cbu: Optional[str] = Field(default=None, description="Decrypted CBU alias")
    banco: Optional[str] = None
    regional: Optional[str] = None
    legajo: Optional[str] = None
    legajo_profesional: Optional[str] = None
    facturador: Optional[bool] = None
    activo: bool
    created_at: datetime
    updated_at: datetime
