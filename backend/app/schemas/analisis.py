"""schemas/analisis.py — Pydantic response schemas for C-11 analisis endpoints.

All schemas use extra='forbid' (model_config = ConfigDict(extra='forbid')).

Schemas:
  AtrasadoOut        — one atrasado student with faltantes/no-aprobadas
  RankingItemOut     — ranking row (by approved activity count)
  NotaFinalOut       — student with calculated final grade
  MonitorItemOut     — monitor row with atrasado flag and activity counts
  ReporteMateriaOut  — aggregate metrics for a materia
  SinCorregirOut     — one textual activity finalised but not graded
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AtrasadoOut(BaseModel):
    """A student detected as atrasado (RN-06)."""

    model_config = ConfigDict(extra="forbid")

    entrada_padron_id: uuid.UUID
    nombre: str
    apellidos: str
    comision: str | None
    regional: str | None = None
    actividades_faltantes: list[str]
    actividades_no_aprobadas: list[str]


class RankingItemOut(BaseModel):
    """One row in the ranking of approved activities (RN-09)."""

    model_config = ConfigDict(extra="forbid")

    entrada_padron_id: uuid.UUID
    nombre: str
    apellidos: str
    comision: str | None
    cant_aprobadas: int


class NotaFinalOut(BaseModel):
    """Student with their calculated final grade (average of nota_numerica)."""

    model_config = ConfigDict(extra="forbid")

    entrada_padron_id: uuid.UUID
    nombre: str
    apellidos: str
    comision: str | None
    nota_final: float | None


class MonitorItemOut(BaseModel):
    """One row in the monitor view (F2.7 / F2.8 / F2.9)."""

    model_config = ConfigDict(extra="forbid")

    entrada_padron_id: uuid.UUID
    nombre: str
    apellidos: str
    comision: str | None
    regional: str | None
    materia_id: uuid.UUID
    cant_actividades: int
    cant_aprobadas: int
    cant_no_aprobadas: int
    cant_faltantes: int
    es_atrasado: bool


class ReporteMateriaOut(BaseModel):
    """Aggregate metrics report for a materia (F2.4)."""

    model_config = ConfigDict(extra="forbid")

    materia_id: uuid.UUID
    total_alumnos: int
    total_actividades: int
    alumnos_con_aprobada: int
    alumnos_atrasados: int
    porcentaje_aprobacion: float


class SinCorregirOut(BaseModel):
    """A textual activity that was finalized by the student but not yet graded (F2.6)."""

    model_config = ConfigDict(extra="forbid")

    entrada_padron_id: uuid.UUID
    nombre: str
    apellidos: str
    comision: str | None
    actividad: str
    importado_at: datetime
