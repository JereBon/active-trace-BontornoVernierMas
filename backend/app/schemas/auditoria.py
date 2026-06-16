"""schemas/auditoria.py — Pydantic output schemas for C-19: panel-auditoria-metricas.

Design decisions (C-19 design.md):
  - All models use extra='forbid' to reject undeclared fields.
  - Schemas are output-only (no request bodies needed — all endpoints are GET).
  - AuditLogOut mirrors all AuditLog model columns.
  - ComunicacionDocenteOut uses the EstadoComunicacion values from C-12.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


# ── Shared base ───────────────────────────────────────────────────────────────

class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


# ── Panel metrics sub-schemas ─────────────────────────────────────────────────


class AccionPorDia(_Base):
    """Count of audit log actions grouped by calendar day."""

    fecha: date
    total: int


class InteraccionDocente(_Base):
    """Count of audit log actions per actor (docente)."""

    actor_id: uuid.UUID
    total: int


class InteraccionMateria(_Base):
    """Count of audit log actions per actor × materia.

    materia_id is nullable because not every action has a materia_id in
    the 'detalle' JSONB blob.
    """

    actor_id: uuid.UUID
    materia_id: uuid.UUID | None
    total: int


class PanelMetricasOut(_Base):
    """Aggregate metrics panel response.

    Returned by GET /v1/auditoria/panel.
    """

    acciones_por_dia: list[AccionPorDia]
    por_docente: list[InteraccionDocente]
    por_materia: list[InteraccionMateria]


# ── Audit log entry schema ────────────────────────────────────────────────────


class AuditLogOut(_Base):
    """Full audit log entry — mirrors all AuditLog model columns."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    fecha_hora: datetime
    actor_id: uuid.UUID
    actor_impersonado_id: uuid.UUID | None
    accion: str
    detalle: dict | None
    filas_afectadas: int
    ip: str
    user_agent: str


class LogPaginadoOut(_Base):
    """Paginated audit log response.

    Returned by GET /v1/auditoria/log.
    """

    items: list[AuditLogOut]
    total: int


# ── Comunicaciones por docente schema ─────────────────────────────────────────


class ComunicacionDocenteOut(_Base):
    """Communication counts by state for a docente.

    Each field counts the rows in the 'comunicaciones' table for this
    docente_id grouped by estado.  Possible estados: Pendiente, Enviando,
    Enviado, Error, Cancelado.  Missing states are reported as 0.

    Returned by GET /v1/auditoria/comunicaciones.
    """

    docente_id: uuid.UUID
    pendiente: int
    enviando: int
    enviado: int
    error: int
    cancelado: int
