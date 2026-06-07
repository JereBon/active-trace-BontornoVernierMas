"""schemas/liquidacion.py — Pydantic v2 schemas for Liquidacion (C-18).

All schemas use extra='forbid'. Decimal → str for JSON-safe precision.
"""

import uuid
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ── Requests ──────────────────────────────────────────────────────────────────


class CalcularRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cohorte_id: uuid.UUID = Field(..., description="Cohorte to calculate for.")
    periodo: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}$",
        description="Billing period in AAAA-MM format.",
    )


class CerrarRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cohorte_id: uuid.UUID = Field(..., description="Cohorte to close.")
    periodo: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}$",
        description="Billing period to close.",
    )


# ── Single record output ──────────────────────────────────────────────────────


class LiquidacionOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    cohorte_id: uuid.UUID
    periodo: str
    usuario_id: uuid.UUID
    rol: str
    comisiones: list[str]
    monto_base: Decimal
    monto_plus: Decimal
    total: Decimal
    es_nexo: bool
    excluido_por_factura: bool
    estado: str


# ── Segmented view with KPIs ──────────────────────────────────────────────────


class LiquidacionRowOut(BaseModel):
    """Row within a segmented view (ID-keyed dict, not ORM-backed)."""

    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    usuario_id: uuid.UUID
    rol: str
    comisiones: list[str]
    monto_base: Decimal
    monto_plus: Decimal
    total: Decimal
    es_nexo: bool
    excluido_por_factura: bool
    estado: str


class VistaPeriodoOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cohorte_id: uuid.UUID
    periodo: str
    general: list[LiquidacionRowOut]
    nexo: list[LiquidacionRowOut]
    facturantes: list[LiquidacionRowOut]
    total_sin_factura: Decimal
    total_con_factura: Decimal


# ── Calcular response ─────────────────────────────────────────────────────────


class CalcularResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    registros_creados: int
    periodo: str
    cohorte_id: uuid.UUID


class CerrarResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    registros_cerrados: int
    periodo: str
    cohorte_id: uuid.UUID
