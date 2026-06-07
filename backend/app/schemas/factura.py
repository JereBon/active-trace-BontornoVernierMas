"""schemas/factura.py — Pydantic v2 schemas for Factura (C-18).

All schemas use extra='forbid'.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class FacturaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario_id: uuid.UUID = Field(..., description="Docente who submitted the invoice.")
    periodo: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}$",
        description="Billing period AAAA-MM.",
    )
    detalle: str | None = Field(None, description="Free-form description.")
    referencia_archivo: str | None = Field(None, description="File reference (name/path).")
    tamano_kb: Decimal | None = Field(None, description="File size in kilobytes.")


class FacturaEstadoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: str = Field(..., description="New state: Pendiente | Abonada.")


class FacturaOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    usuario_id: uuid.UUID
    periodo: str
    detalle: str | None
    referencia_archivo: str | None
    tamano_kb: Decimal | None
    estado: str
    cargada_at: datetime | None
    abonada_at: datetime | None
