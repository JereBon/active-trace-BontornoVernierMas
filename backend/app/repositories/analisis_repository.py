"""repositories/analisis_repository.py — AnalisisRepository (C-11).

Tenant-scoped repository for analysis queries. All methods filter by tenant_id.
NO business logic here — only data access. Computation lives in AnalisisService.

Methods:
  list_calificaciones_por_version  — all calificaciones for entries of a version
  list_calificaciones_por_materia  — all calificaciones for a materia (flat)
  list_entradas_por_version        — entries of a VersionPadron
  list_version_activa              — find the active version for a materia
  list_sin_corregir                — finalizado_lms=True + no nota (RN-07/RN-08)
  list_monitor                     — filtered monitor view (F2.7/F2.8/F2.9)
  list_materia_ids_por_usuario     — materia IDs assigned to a user (for PROFESOR scope)

Design decisions (C-11 design.md D1, D4):
- One repository for all analisis queries to avoid over-proliferation.
- Returns raw dicts or ORM objects depending on what the service needs.
- All queries enforce tenant_id and deleted_at IS NULL.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calificacion import Calificacion
from app.models.entrada_padron import EntradaPadron
from app.models.version_padron import VersionPadron


class AnalisisRepository:
    """Tenant-scoped repository for C-11 analisis queries."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    # ── Version and Entry helpers ─────────────────────────────────────────────

    async def list_version_activa(self, materia_id: uuid.UUID) -> VersionPadron | None:
        """Return the active VersionPadron for this tenant×materia, or None."""
        stmt = select(VersionPadron).where(
            VersionPadron.tenant_id == self._tenant_id,
            VersionPadron.materia_id == materia_id,
            VersionPadron.activa.is_(True),
            VersionPadron.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_entradas_por_version(
        self,
        version_id: uuid.UUID,
    ) -> list[EntradaPadron]:
        """Return all active EntradaPadron rows for a version."""
        stmt = select(EntradaPadron).where(
            EntradaPadron.tenant_id == self._tenant_id,
            EntradaPadron.version_id == version_id,
            EntradaPadron.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ── Calificacion queries ──────────────────────────────────────────────────

    async def list_calificaciones_por_version(
        self,
        materia_id: uuid.UUID,
        version_id: uuid.UUID,
    ) -> list[Calificacion]:
        """Return all active calificaciones for entries belonging to a version.

        Joins Calificacion → EntradaPadron to filter by version_id.
        Always tenant-scoped.
        """
        stmt = (
            select(Calificacion)
            .join(
                EntradaPadron,
                and_(
                    Calificacion.entrada_padron_id == EntradaPadron.id,
                    EntradaPadron.version_id == version_id,
                    EntradaPadron.tenant_id == self._tenant_id,
                    EntradaPadron.deleted_at.is_(None),
                ),
            )
            .where(
                Calificacion.tenant_id == self._tenant_id,
                Calificacion.materia_id == materia_id,
                Calificacion.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_calificaciones_por_materia(
        self,
        materia_id: uuid.UUID,
    ) -> list[Calificacion]:
        """Return all active calificaciones for a materia in this tenant."""
        stmt = select(Calificacion).where(
            Calificacion.tenant_id == self._tenant_id,
            Calificacion.materia_id == materia_id,
            Calificacion.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_sin_corregir(
        self,
        materia_id: uuid.UUID,
    ) -> list[Calificacion]:
        """Return textual activities finalised by student but not yet graded (RN-07/RN-08).

        Criteria:
          - finalizado_lms = True
          - nota_textual IS NULL  (not graded)
          - nota_numerica IS NULL (textual activity, per RN-08)
        """
        stmt = select(Calificacion).where(
            Calificacion.tenant_id == self._tenant_id,
            Calificacion.materia_id == materia_id,
            Calificacion.finalizado_lms.is_(True),
            Calificacion.nota_textual.is_(None),
            Calificacion.nota_numerica.is_(None),
            Calificacion.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_monitor(
        self,
        materia_ids: list[uuid.UUID],
        filtros: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Return monitor rows for the given materia_ids with optional filters.

        Each row is a dict with student info + activity counts + es_atrasado flag.
        Filters supported: comision, regional, alumno_nombre, solo_atrasados,
                           fecha_desde, fecha_hasta (applied to Calificacion.importado_at).

        Returns list of dicts (not ORM objects) because each row aggregates
        data from EntradaPadron + Calificacion.
        """
        if not materia_ids:
            return []

        # Build base query: one row per (entrada_padron, materia)
        # We fetch entradas and their calificaciones, then aggregate in Python
        # to avoid complex SQL that's hard to filter + maintain.

        # Get all entradas for the matching materias via active versions
        versions_stmt = select(VersionPadron).where(
            VersionPadron.tenant_id == self._tenant_id,
            VersionPadron.materia_id.in_(materia_ids),
            VersionPadron.activa.is_(True),
            VersionPadron.deleted_at.is_(None),
        )
        versions_result = await self._session.execute(versions_stmt)
        versions = list(versions_result.scalars().all())
        version_map: dict[uuid.UUID, uuid.UUID] = {v.id: v.materia_id for v in versions}
        version_ids = list(version_map.keys())

        if not version_ids:
            return []

        entradas_stmt = select(EntradaPadron).where(
            EntradaPadron.tenant_id == self._tenant_id,
            EntradaPadron.version_id.in_(version_ids),
            EntradaPadron.deleted_at.is_(None),
        )

        # Apply comision filter
        if comision := filtros.get("comision"):
            entradas_stmt = entradas_stmt.where(EntradaPadron.comision == comision)

        # Apply regional filter
        if regional := filtros.get("regional"):
            entradas_stmt = entradas_stmt.where(EntradaPadron.regional == regional)

        # Apply alumno_nombre text search
        if nombre := filtros.get("alumno_nombre"):
            like_patt = f"%{nombre}%"
            entradas_stmt = entradas_stmt.where(
                or_(
                    EntradaPadron.nombre.ilike(like_patt),
                    EntradaPadron.apellidos.ilike(like_patt),
                )
            )

        entradas_result = await self._session.execute(entradas_stmt)
        entradas = list(entradas_result.scalars().all())

        if not entradas:
            return []

        entrada_ids = [e.id for e in entradas]
        entrada_map: dict[uuid.UUID, EntradaPadron] = {e.id: e for e in entradas}
        # Map entrada → materia via version
        entrada_version_map: dict[uuid.UUID, uuid.UUID] = {
            e.id: version_map[e.version_id] for e in entradas
        }

        # Get calificaciones for these entradas in the relevant materias
        cals_stmt = select(Calificacion).where(
            Calificacion.tenant_id == self._tenant_id,
            Calificacion.entrada_padron_id.in_(entrada_ids),
            Calificacion.materia_id.in_(materia_ids),
            Calificacion.deleted_at.is_(None),
        )

        # Apply date range filters
        if fecha_desde := filtros.get("fecha_desde"):
            if isinstance(fecha_desde, str):
                from datetime import date as _date
                fecha_desde = datetime.fromisoformat(fecha_desde)
            cals_stmt = cals_stmt.where(Calificacion.importado_at >= fecha_desde)

        if fecha_hasta := filtros.get("fecha_hasta"):
            if isinstance(fecha_hasta, str):
                fecha_hasta = datetime.fromisoformat(fecha_hasta)
            cals_stmt = cals_stmt.where(Calificacion.importado_at <= fecha_hasta)

        cals_result = await self._session.execute(cals_stmt)
        cals = list(cals_result.scalars().all())

        # Build per-entry activity set (universe)
        all_actividades: set[str] = {c.actividad for c in cals}

        # Group calificaciones by entrada_padron_id
        cals_by_entrada: dict[uuid.UUID, list[Calificacion]] = {}
        for cal in cals:
            cals_by_entrada.setdefault(cal.entrada_padron_id, []).append(cal)

        # Build result rows
        rows: list[dict[str, Any]] = []
        for entrada in entradas:
            materia_id = entrada_version_map[entrada.id]
            entry_cals = cals_by_entrada.get(entrada.id, [])
            entry_actividades = {c.actividad for c in entry_cals}
            faltantes = all_actividades - entry_actividades
            aprobadas = [c for c in entry_cals if c.aprobado]
            no_aprobadas = [c for c in entry_cals if not c.aprobado]
            es_atrasado = bool(faltantes) or bool(no_aprobadas)

            row = {
                "entrada_padron_id": entrada.id,
                "nombre": entrada.nombre,
                "apellidos": entrada.apellidos,
                "comision": entrada.comision,
                "regional": entrada.regional,
                "materia_id": materia_id,
                "cant_actividades": len(all_actividades),
                "cant_aprobadas": len(aprobadas),
                "cant_no_aprobadas": len(no_aprobadas),
                "cant_faltantes": len(faltantes),
                "es_atrasado": es_atrasado,
            }
            rows.append(row)

        # Apply solo_atrasados filter (post-aggregation)
        if filtros.get("solo_atrasados"):
            rows = [r for r in rows if r["es_atrasado"]]

        return rows

    async def list_materia_ids_por_usuario(
        self,
        usuario_id: uuid.UUID,
    ) -> list[uuid.UUID]:
        """Return materia IDs where the user has an active assignment.

        Used for PROFESOR/TUTOR scope on the monitor endpoint.
        """
        from app.models.asignacion import Asignacion
        from datetime import date

        today = date.today()
        stmt = (
            select(Asignacion.materia_id)
            .where(
                Asignacion.tenant_id == self._tenant_id,
                Asignacion.usuario_id == usuario_id,
                Asignacion.materia_id.is_not(None),
                Asignacion.desde <= today,
                Asignacion.deleted_at.is_(None),
                or_(
                    Asignacion.hasta.is_(None),
                    Asignacion.hasta >= today,
                ),
            )
            .distinct()
        )
        result = await self._session.execute(stmt)
        return [row[0] for row in result.fetchall() if row[0] is not None]
