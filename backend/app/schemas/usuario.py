"""schemas/usuario.py — Pydantic schemas for Usuario (C-07: usuarios-y-asignaciones).

All schemas use extra='forbid'. PII is exposed as plaintext in responses (the
repository decrypts before returning). Sensitive fields are never in request
payloads as ciphertext — callers supply plaintext, encryption is done at the
repository layer.

Security note: email and PII (_cifrado) fields never appear as ciphertext
in API responses — the response always contains decrypted values.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

_FORBID = ConfigDict(extra="forbid")
_FORBID_FROM_ATTRS = ConfigDict(extra="forbid", from_attributes=True)


class UsuarioCreate(BaseModel):
    """Request body for POST /v1/users."""

    model_config = _FORBID

    email: EmailStr = Field(..., description="Email address (will be encrypted at rest)")
    password: str = Field(..., min_length=8, description="Plaintext password (will be hashed)")
    nombre: Optional[str] = Field(default=None, max_length=200, description="First name")
    apellidos: Optional[str] = Field(default=None, max_length=200, description="Last name(s)")
    dni: Optional[str] = Field(default=None, max_length=20, description="National ID (will be encrypted)")
    cuil: Optional[str] = Field(default=None, max_length=20, description="Tax ID (will be encrypted)")
    cbu: Optional[str] = Field(default=None, max_length=30, description="Bank account key (will be encrypted)")
    alias_cbu: Optional[str] = Field(default=None, max_length=100, description="CBU alias (will be encrypted)")
    banco: Optional[str] = Field(default=None, max_length=100, description="Bank name")
    regional: Optional[str] = Field(default=None, max_length=100, description="Institutional branch")
    legajo: Optional[str] = Field(default=None, max_length=50, description="Institutional record number")
    legajo_profesional: Optional[str] = Field(default=None, max_length=50, description="Professional registry number")
    facturador: Optional[bool] = Field(default=None, description="True if user issues invoices")


class UsuarioUpdate(BaseModel):
    """Request body for PUT /v1/users/{id}. All fields optional."""

    model_config = _FORBID

    nombre: Optional[str] = Field(default=None, max_length=200)
    apellidos: Optional[str] = Field(default=None, max_length=200)
    dni: Optional[str] = Field(default=None, max_length=20)
    cuil: Optional[str] = Field(default=None, max_length=20)
    cbu: Optional[str] = Field(default=None, max_length=30)
    alias_cbu: Optional[str] = Field(default=None, max_length=100)
    banco: Optional[str] = Field(default=None, max_length=100)
    regional: Optional[str] = Field(default=None, max_length=100)
    legajo: Optional[str] = Field(default=None, max_length=50)
    legajo_profesional: Optional[str] = Field(default=None, max_length=50)
    facturador: Optional[bool] = None


class UsuarioOut(BaseModel):
    """Response schema for a Usuario — PII fields are decrypted plaintext."""

    model_config = _FORBID_FROM_ATTRS

    id: uuid.UUID
    tenant_id: uuid.UUID
    email: Optional[str] = Field(default=None, description="Decrypted email")
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    dni: Optional[str] = Field(default=None, description="Decrypted DNI")
    cuil: Optional[str] = Field(default=None, description="Decrypted CUIL")
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


class UsuarioListItem(BaseModel):
    """Minimal response for listing users (no PII except name)."""

    model_config = ConfigDict(extra="ignore", from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    legajo: Optional[str] = None
    activo: bool
    created_at: datetime
