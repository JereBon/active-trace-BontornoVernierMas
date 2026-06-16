"""api/v1/routers/analisis.py — Analisis endpoints (C-11: analisis-atrasados-reportes).

Identity and tenant_id ALWAYS come from the verified JWT (CurrentUser).
Never from URL params, body, or headers.

Endpoints:
  GET /v1/analisis/atrasados?materia_id=    — list of atrasados (RN-06)
  GET /v1/analisis/ranking?materia_id=      — ranking of approved activities (RN-09)
  GET /v1/analisis/notas-finales?materia_id= — final grades per student
  GET /v1/analisis/reporte-materia?materia_id= — aggregate metrics
  GET /v1/analisis/sin-corregir?materia_id= — textual TPs finalised but ungraded
  GET /v1/analisis/monitor                  — monitor view with optional filters

All endpoints require permission: atrasados:ver
"""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import CurrentUser, DBSession
from app.core.permisos import ATRASADOS_VER
from app.core.rbac import require_permission
from app.schemas.analisis import (
    AtrasadoOut,
    MonitorItemOut,
    NotaFinalOut,
    RankingItemOut,
    ReporteMateriaOut,
    SinCorregirOut,
)
from app.services.analisis_service import AnalisisService

router = APIRouter(
    prefix="/v1/analisis",
    tags=["analisis"],
)

_PERM = Depends(require_permission(ATRASADOS_VER))


# ── GET /atrasados ────────────────────────────────────────────────────────────


@router.get(
    "/atrasados",
    response_model=list[AtrasadoOut],
    dependencies=[_PERM],
    summary="List atrasados — students with missing or failed activities (RN-06)",
)
async def get_atrasados(
    materia_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> list[dict[str, Any]]:
    """Return students that are atrasados for the given materia.

    Identity and tenant are resolved exclusively from the JWT.
    """
    svc = AnalisisService(session, current_user.tenant_id)
    return await svc.get_atrasados(materia_id)


# ── GET /ranking ──────────────────────────────────────────────────────────────


@router.get(
    "/ranking",
    response_model=list[RankingItemOut],
    dependencies=[_PERM],
    summary="Ranking of approved activities per student (RN-09)",
)
async def get_ranking(
    materia_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> list[dict[str, Any]]:
    svc = AnalisisService(session, current_user.tenant_id)
    return await svc.get_ranking(materia_id)


# ── GET /notas-finales ────────────────────────────────────────────────────────


@router.get(
    "/notas-finales",
    response_model=list[NotaFinalOut],
    dependencies=[_PERM],
    summary="Final grades per student (simple average of nota_numerica)",
)
async def get_notas_finales(
    materia_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> list[dict[str, Any]]:
    svc = AnalisisService(session, current_user.tenant_id)
    return await svc.get_notas_finales(materia_id)


# ── GET /reporte-materia ──────────────────────────────────────────────────────


@router.get(
    "/reporte-materia",
    response_model=ReporteMateriaOut,
    dependencies=[_PERM],
    summary="Aggregate metrics report for a materia (F2.4)",
)
async def get_reporte_materia(
    materia_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> dict[str, Any]:
    svc = AnalisisService(session, current_user.tenant_id)
    return await svc.get_reporte(materia_id)


# ── GET /sin-corregir ─────────────────────────────────────────────────────────


@router.get(
    "/sin-corregir",
    response_model=list[SinCorregirOut],
    dependencies=[_PERM],
    summary="Textual TPs finalised by student but not yet graded (F2.6 / RN-07/RN-08)",
)
async def get_sin_corregir(
    materia_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> list[Any]:
    """Return list of ungraded textual activities.

    Only includes activities where:
      - finalizado_lms = True (student submitted in LMS)
      - nota_textual IS NULL (not graded yet)
      - nota_numerica IS NULL (textual activity per RN-08)
    """
    from app.repositories.analisis_repository import AnalisisRepository  # noqa: PLC0415
    from app.models.entrada_padron import EntradaPadron  # noqa: PLC0415
    from sqlalchemy import select  # noqa: PLC0415

    repo = AnalisisRepository(session, current_user.tenant_id)
    cals = await repo.list_sin_corregir(materia_id)

    # Enrich with student name (join not done in repo to keep it simple)
    if not cals:
        return []

    entrada_ids = list({c.entrada_padron_id for c in cals})
    stmt = select(EntradaPadron).where(
        EntradaPadron.id.in_(entrada_ids),
        EntradaPadron.tenant_id == current_user.tenant_id,
        EntradaPadron.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    entradas = {e.id: e for e in result.scalars().all()}

    rows = []
    for cal in cals:
        entrada = entradas.get(cal.entrada_padron_id)
        rows.append({
            "entrada_padron_id": cal.entrada_padron_id,
            "nombre": entrada.nombre if entrada else "",
            "apellidos": entrada.apellidos if entrada else "",
            "comision": entrada.comision if entrada else None,
            "actividad": cal.actividad,
            "importado_at": cal.importado_at,
        })
    return rows


# ── GET /monitor ──────────────────────────────────────────────────────────────


@router.get(
    "/monitor",
    response_model=list[MonitorItemOut],
    dependencies=[_PERM],
    summary="Monitor view — student activity status (F2.7/F2.8/F2.9)",
)
async def get_monitor(
    session: DBSession,
    current_user: CurrentUser,
    materia_id: uuid.UUID | None = Query(default=None),
    comision: str | None = Query(default=None),
    regional: str | None = Query(default=None),
    alumno_nombre: str | None = Query(default=None),
    solo_atrasados: bool = Query(default=False),
    fecha_desde: datetime | None = Query(default=None),
    fecha_hasta: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[dict[str, Any]]:
    """Return monitor rows with optional filters.

    COORDINADOR/ADMIN roles see all materias of the tenant.
    TUTOR/PROFESOR see only their assigned materias.
    Date range filters (fecha_desde/fecha_hasta) apply to calificacion.importado_at.
    """
    from app.repositories.analisis_repository import AnalisisRepository  # noqa: PLC0415
    from app.models.materia import Materia  # noqa: PLC0415
    from sqlalchemy import select  # noqa: PLC0415

    repo = AnalisisRepository(session, current_user.tenant_id)

    # Determine which materia_ids to include
    roles_amplios = {"COORDINADOR", "ADMIN"}
    user_roles = set(current_user.roles)

    if materia_id is not None:
        materia_ids = [materia_id]
    elif user_roles & roles_amplios:
        # COORDINADOR/ADMIN — all materias in tenant
        stmt = select(Materia.id).where(
            Materia.tenant_id == current_user.tenant_id,
            Materia.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        materia_ids = [row[0] for row in result.fetchall()]
    else:
        # TUTOR/PROFESOR — only assigned materias
        materia_ids = await repo.list_materia_ids_por_usuario(current_user.user_id)

    if not materia_ids:
        return []

    filtros: dict[str, Any] = {
        "comision": comision,
        "regional": regional,
        "alumno_nombre": alumno_nombre,
        "solo_atrasados": solo_atrasados,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
    }
    # Remove None values to avoid unintentional filtering
    filtros = {k: v for k, v in filtros.items() if v is not None and v is not False}
    if solo_atrasados:
        filtros["solo_atrasados"] = True

    rows = await repo.list_monitor(materia_ids=materia_ids, filtros=filtros)

    # Apply pagination
    return rows[offset: offset + limit]
