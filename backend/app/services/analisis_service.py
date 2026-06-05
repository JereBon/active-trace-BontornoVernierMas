"""services/analisis_service.py — AnalisisService (C-11: analisis-atrasados-reportes).

Pure functions for academic analysis computations (testable without DB).
AnalisisService orchestrates DB reads via AnalisisRepository and applies
the pure functions.

Pure functions (no DB, no side effects):
  calcular_atrasados          — detect atrasados per RN-06
  calcular_ranking            — ranking of approved activities per RN-09
  calcular_notas_finales      — average nota_numerica per student
  calcular_reporte_materia    — aggregate metrics for a materia

AnalisisService methods (async, use repository):
  get_atrasados(materia_id)
  get_ranking(materia_id)
  get_notas_finales(materia_id)
  get_reporte(materia_id)
  get_sin_corregir(materia_id)
  get_monitor(materia_ids_or_all, filtros, usuario_id, roles)

Design decisions (C-11 design.md D1, D2):
- Business logic (atrasado detection, ranking) is in pure functions.
- Service calls repository; repository calls DB. No SQL in service.
- aprobado field is trusted as stored (pre-computed by CalificacionService).
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


# ── Pure computation functions ────────────────────────────────────────────────


def calcular_atrasados(
    entradas: list[dict[str, Any]],
    cals_por_entrada: dict[uuid.UUID, list[dict[str, Any]]],
    all_actividades: set[str],
) -> list[dict[str, Any]]:
    """Detect atrasados according to RN-06.

    A student is atrasado if:
      (a) has missing activities (not in their calificaciones)
      (b) has any calificacion with aprobado=False

    Args:
        entradas:          List of entry dicts with keys: id, nombre, apellidos, comision.
        cals_por_entrada:  Mapping entrada_id → list of cal dicts {actividad, aprobado}.
        all_actividades:   Universe of activity names for the materia.

    Returns:
        List of atrasado dicts with: entrada_padron_id, nombre, apellidos, comision,
        regional, actividades_faltantes, actividades_no_aprobadas.
    """
    result: list[dict[str, Any]] = []

    for entrada in entradas:
        entry_id = entrada["id"]
        cals = cals_por_entrada.get(entry_id, [])
        entry_actividades = {c["actividad"] for c in cals}
        faltantes = sorted(all_actividades - entry_actividades)
        no_aprobadas = sorted(c["actividad"] for c in cals if not c["aprobado"])

        if faltantes or no_aprobadas:
            result.append({
                "entrada_padron_id": entry_id,
                "nombre": entrada["nombre"],
                "apellidos": entrada["apellidos"],
                "comision": entrada.get("comision"),
                "regional": entrada.get("regional"),
                "actividades_faltantes": faltantes,
                "actividades_no_aprobadas": no_aprobadas,
            })

    return result


def calcular_ranking(
    entradas: list[dict[str, Any]],
    cals_por_entrada: dict[uuid.UUID, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Build ranking of approved activities per student (RN-09).

    Only includes students with >= 1 approved activity.
    Sorted descending by cant_aprobadas; ties broken alphabetically by apellidos.

    Args:
        entradas:         List of entry dicts with keys: id, nombre, apellidos, comision.
        cals_por_entrada: Mapping entrada_id → list of cal dicts {actividad, aprobado}.

    Returns:
        List of ranking dicts sorted by cant_aprobadas desc, apellidos asc.
    """
    rows: list[dict[str, Any]] = []

    for entrada in entradas:
        entry_id = entrada["id"]
        cals = cals_por_entrada.get(entry_id, [])
        cant_aprobadas = sum(1 for c in cals if c["aprobado"])

        if cant_aprobadas >= 1:
            rows.append({
                "entrada_padron_id": entry_id,
                "nombre": entrada["nombre"],
                "apellidos": entrada["apellidos"],
                "comision": entrada.get("comision"),
                "cant_aprobadas": cant_aprobadas,
            })

    # Sort: desc by cant_aprobadas, then asc by apellidos for ties
    rows.sort(key=lambda r: (-r["cant_aprobadas"], r["apellidos"]))
    return rows


def calcular_notas_finales(
    entradas: list[dict[str, Any]],
    cals_por_entrada: dict[uuid.UUID, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Calculate the final grade (simple average of nota_numerica) per student.

    Students with no numeric grades get nota_final = None.
    Results are sorted ascending by apellidos.

    Args:
        entradas:         List of entry dicts.
        cals_por_entrada: Mapping entrada_id → list of cal dicts {nota_numerica}.

    Returns:
        List of dicts sorted by apellidos with nota_final (float | None).
    """
    rows: list[dict[str, Any]] = []

    for entrada in entradas:
        entry_id = entrada["id"]
        cals = cals_por_entrada.get(entry_id, [])
        numericas = [c["nota_numerica"] for c in cals if c.get("nota_numerica") is not None]
        nota_final: float | None = sum(numericas) / len(numericas) if numericas else None

        rows.append({
            "entrada_padron_id": entry_id,
            "nombre": entrada["nombre"],
            "apellidos": entrada["apellidos"],
            "comision": entrada.get("comision"),
            "nota_final": nota_final,
        })

    rows.sort(key=lambda r: r["apellidos"])
    return rows


def calcular_reporte_materia(
    entradas: list[dict[str, Any]],
    calificaciones: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute aggregate metrics for a materia (F2.4).

    Args:
        entradas:       List of entry dicts for the materia.
        calificaciones: Flat list of cal dicts {entrada_padron_id, actividad, aprobado}.

    Returns:
        Dict with: total_alumnos, total_actividades, alumnos_con_aprobada,
                   alumnos_atrasados, porcentaje_aprobacion.
    """
    total_alumnos = len(entradas)
    entrada_ids = {e["id"] for e in entradas}

    all_actividades: set[str] = {c["actividad"] for c in calificaciones}
    total_actividades = len(all_actividades)

    # Group by entrada
    cals_por_entrada: dict[uuid.UUID, list[dict[str, Any]]] = {}
    for cal in calificaciones:
        eid = cal["entrada_padron_id"]
        cals_por_entrada.setdefault(eid, []).append(cal)

    alumnos_con_aprobada = 0
    alumnos_atrasados = 0

    for entrada in entradas:
        entry_id = entrada["id"]
        cals = cals_por_entrada.get(entry_id, [])
        entry_acts = {c["actividad"] for c in cals}
        faltantes = all_actividades - entry_acts
        no_aprobadas = [c for c in cals if not c["aprobado"]]
        has_aprobada = any(c["aprobado"] for c in cals)

        if has_aprobada:
            alumnos_con_aprobada += 1
        if faltantes or no_aprobadas:
            alumnos_atrasados += 1

    porcentaje = (alumnos_con_aprobada / total_alumnos * 100.0) if total_alumnos else 0.0

    return {
        "total_alumnos": total_alumnos,
        "total_actividades": total_actividades,
        "alumnos_con_aprobada": alumnos_con_aprobada,
        "alumnos_atrasados": alumnos_atrasados,
        "porcentaje_aprobacion": round(porcentaje, 2),
    }


# ── AnalisisService ───────────────────────────────────────────────────────────


class AnalisisService:
    """Orchestrates analysis queries and applies pure computation functions.

    All DB access goes through AnalisisRepository.
    No SQL here — only repository calls + pure function calls.
    """

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

        from app.repositories.analisis_repository import AnalisisRepository  # noqa: PLC0415

        self._repo = AnalisisRepository(session, tenant_id)

    def _entradas_to_dicts(self, entradas: list[Any]) -> list[dict[str, Any]]:
        return [
            {
                "id": e.id,
                "nombre": e.nombre,
                "apellidos": e.apellidos,
                "comision": e.comision,
                "regional": getattr(e, "regional", None),
            }
            for e in entradas
        ]

    def _cals_to_dict_by_entrada(
        self, cals: list[Any]
    ) -> dict[uuid.UUID, list[dict[str, Any]]]:
        grouped: dict[uuid.UUID, list[dict[str, Any]]] = {}
        for c in cals:
            grouped.setdefault(c.entrada_padron_id, []).append({
                "actividad": c.actividad,
                "aprobado": c.aprobado,
                "nota_numerica": c.nota_numerica,
                "nota_textual": c.nota_textual,
            })
        return grouped

    async def _get_version_and_entradas(self, materia_id: uuid.UUID) -> tuple[Any, list[Any]]:
        """Get the active version and its entries for a materia."""
        version = await self._repo.list_version_activa(materia_id)
        if version is None:
            return None, []
        entradas = await self._repo.list_entradas_por_version(version.id)
        return version, entradas

    async def get_atrasados(self, materia_id: uuid.UUID) -> list[dict[str, Any]]:
        """Return list of atrasados for the active padron version (RN-06)."""
        version, entradas = await self._get_version_and_entradas(materia_id)
        if not entradas:
            return []

        cals = await self._repo.list_calificaciones_por_materia(materia_id)
        all_actividades = {c.actividad for c in cals}
        cals_by_entrada = self._cals_to_dict_by_entrada(cals)
        entradas_dicts = self._entradas_to_dicts(entradas)

        return calcular_atrasados(entradas_dicts, cals_by_entrada, all_actividades)

    async def get_ranking(self, materia_id: uuid.UUID) -> list[dict[str, Any]]:
        """Return ranking of approved activities (RN-09)."""
        version, entradas = await self._get_version_and_entradas(materia_id)
        if not entradas:
            return []

        cals = await self._repo.list_calificaciones_por_materia(materia_id)
        cals_by_entrada = self._cals_to_dict_by_entrada(cals)
        entradas_dicts = self._entradas_to_dicts(entradas)

        return calcular_ranking(entradas_dicts, cals_by_entrada)

    async def get_notas_finales(self, materia_id: uuid.UUID) -> list[dict[str, Any]]:
        """Return final grades per student."""
        version, entradas = await self._get_version_and_entradas(materia_id)
        if not entradas:
            return []

        cals = await self._repo.list_calificaciones_por_materia(materia_id)
        cals_by_entrada = self._cals_to_dict_by_entrada(cals)
        entradas_dicts = self._entradas_to_dicts(entradas)

        return calcular_notas_finales(entradas_dicts, cals_by_entrada)

    async def get_reporte(self, materia_id: uuid.UUID) -> dict[str, Any]:
        """Return aggregate metrics for a materia."""
        version, entradas = await self._get_version_and_entradas(materia_id)

        cals_raw = await self._repo.list_calificaciones_por_materia(materia_id)
        cals_dicts = [
            {
                "entrada_padron_id": c.entrada_padron_id,
                "actividad": c.actividad,
                "aprobado": c.aprobado,
            }
            for c in cals_raw
        ]
        entradas_dicts = self._entradas_to_dicts(entradas)
        result = calcular_reporte_materia(entradas_dicts, cals_dicts)
        result["materia_id"] = materia_id
        return result

    async def get_sin_corregir(self, materia_id: uuid.UUID) -> list[Any]:
        """Return list of ungraded textual activities (RN-07/RN-08)."""
        return await self._repo.list_sin_corregir(materia_id)

    async def get_monitor(
        self,
        materia_ids: list[uuid.UUID],
        filtros: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Return monitor rows for the given materia IDs with optional filters."""
        return await self._repo.list_monitor(materia_ids=materia_ids, filtros=filtros)
