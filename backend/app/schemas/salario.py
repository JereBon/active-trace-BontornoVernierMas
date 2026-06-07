"""schemas/salario.py — Pydantic v2 schemas for SalarioBase and SalarioPlus (C-18).

All schemas use extra='forbid' (project rule).
"""

import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ── SalarioBase ───────────────────────────────────────────────────────────────


class SalarioBaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rol: str = Field(..., description="Role code (e.g. PROFESOR, TUTOR, NEXO).")
    monto: Decimal = Field(..., gt=Decimal("0"), description="Base salary amount.")
    desde: date = Field(..., description="First valid date (inclusive).")
    hasta: date | None = Field(None, description="Last valid date; NULL = open-ended.")
    descripcion: str | None = Field(None, description="Optional note.")


class SalarioBaseUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    monto: Decimal | None = Field(None, gt=Decimal("0"))
    desde: date | None = None
    hasta: date | None = None
    descripcion: str | None = None


class SalarioBaseOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    rol: str
    monto: Decimal
    desde: date
    hasta: date | None
    descripcion: str | None


# ── SalarioPlus ───────────────────────────────────────────────────────────────


class SalarioPlusCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grupo: str = Field(..., description="Category key matching Materia.categoria_clave.")
    rol: str = Field(..., description="Role code this plus applies to.")
    descripcion: str | None = Field(None, description="Optional label.")
    monto: Decimal = Field(..., gt=Decimal("0"), description="Plus amount per commission unit.")
    desde: date = Field(..., description="First valid date (inclusive).")
    hasta: date | None = Field(None, description="Last valid date; NULL = open-ended.")


class SalarioPlusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    monto: Decimal | None = Field(None, gt=Decimal("0"))
    desde: date | None = None
    hasta: date | None = None
    descripcion: str | None = None


class SalarioPlusOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    grupo: str
    rol: str
    descripcion: str | None
    monto: Decimal
    desde: date
    hasta: date | None
