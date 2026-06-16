"""api/v1/routers/equipos.py — Equipos Docentes endpoints (C-08).

All write operations require the 'equipos:asignar' permission (COORDINADOR, ADMIN).
GET / and GET /exportar also require 'equipos:asignar'.
GET /mis-asignaciones only requires a valid authenticated session.

Identity and tenant_id always come from the verified JWT (CurrentUser).
No business logic lives here — only HTTP translation → service calls.

Endpoints:
  GET    /v1/equipos/mis-asignaciones   Own assignments (no elevated permission)
  GET    /v1/equipos/exportar           Export team as CSV
  GET    /v1/equipos/                   List all assignments with optional filters
  POST   /v1/equipos/                   Create a single assignment
  PUT    /v1/equipos/vigencia-masiva     Bulk update vigencia for a team
  POST   /v1/equipos/asignacion-masiva  Bulk create assignments
  POST   /v1/equipos/clonar             Clone team between cohortes
  GET    /v1/equipos/{id}               Get a single assignment
  PUT    /v1/equipos/{id}               Update a single assignment
  DELETE /v1/equipos/{id}               Soft-delete a single assignment
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse

from app.core.dependencies import CurrentUser, DBSession
from app.core.permisos import EQUIPOS_ASIGNAR
from app.core.rbac import require_permission
from app.schemas.asignacion import (
    AsignacionCreate,
    AsignacionFilter,
    AsignacionMasivaCreate,
    AsignacionMasivaOut,
    AsignacionOut,
    AsignacionUpdate,
    ClonarEquipoRequest,
    VigenciaMasivaOut,
    VigenciaMasivaRequest,
)
from app.services.equipos import EquiposService

router = APIRouter(prefix="/v1/equipos", tags=["equipos"])

_GUARD = [Depends(require_permission(EQUIPOS_ASIGNAR))]


# ── GET /mis-asignaciones — authenticated user only, no elevated permission ──


@router.get(
    "/mis-asignaciones",
    response_model=list[AsignacionOut],
    summary="Mis asignaciones vigentes (docente autenticado)",
)
async def mis_asignaciones(
    session: DBSession,
    current_user: CurrentUser,
) -> list[AsignacionOut]:
    """Return the active assignments for the currently authenticated user.

    Identity comes exclusively from the JWT — no user_id in query params.
    """
    svc = EquiposService(session, current_user.tenant_id)
    asignaciones = await svc.mis_asignaciones(current_user.user_id)
    return [AsignacionOut.model_validate(a) for a in asignaciones]


# ── GET /exportar — CSV download (requires equipos:asignar) ──────────────────


@router.get(
    "/exportar",
    summary="Exportar equipo docente a CSV",
    dependencies=_GUARD,
    response_class=StreamingResponse,
)
async def exportar_equipo(
    session: DBSession,
    current_user: CurrentUser,
    materia_id: Optional[uuid.UUID] = Query(default=None),
    carrera_id: Optional[uuid.UUID] = Query(default=None),
    cohorte_id: Optional[uuid.UUID] = Query(default=None),
    usuario_id: Optional[uuid.UUID] = Query(default=None),
    rol: Optional[str] = Query(default=None),
    solo_vigentes: bool = Query(default=False),
) -> StreamingResponse:
    """Download team assignments as a CSV file."""
    filters = AsignacionFilter(
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        usuario_id=usuario_id,
        rol=rol,
        solo_vigentes=solo_vigentes,
    )
    svc = EquiposService(session, current_user.tenant_id)
    csv_content = await svc.exportar_csv(filters)

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="equipo.csv"'},
    )


# ── GET / — list assignments (requires equipos:asignar) ──────────────────────


@router.get(
    "/",
    response_model=list[AsignacionOut],
    summary="Listar asignaciones del tenant",
    dependencies=_GUARD,
)
async def list_asignaciones(
    session: DBSession,
    current_user: CurrentUser,
    materia_id: Optional[uuid.UUID] = Query(default=None),
    carrera_id: Optional[uuid.UUID] = Query(default=None),
    cohorte_id: Optional[uuid.UUID] = Query(default=None),
    usuario_id: Optional[uuid.UUID] = Query(default=None),
    rol: Optional[str] = Query(default=None),
    solo_vigentes: bool = Query(default=False),
) -> list[AsignacionOut]:
    """List all assignments in the current tenant, with optional filters."""
    filters = AsignacionFilter(
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        usuario_id=usuario_id,
        rol=rol,
        solo_vigentes=solo_vigentes,
    )
    svc = EquiposService(session, current_user.tenant_id)
    asignaciones = await svc.list_asignaciones(filters)
    return [AsignacionOut.model_validate(a) for a in asignaciones]


# ── POST / — create single assignment ────────────────────────────────────────


@router.post(
    "/",
    response_model=AsignacionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear asignación individual",
    dependencies=_GUARD,
)
async def create_asignacion(
    body: AsignacionCreate,
    session: DBSession,
    current_user: CurrentUser,
) -> AsignacionOut:
    """Create a new assignment for a user within the current tenant."""
    svc = EquiposService(session, current_user.tenant_id)
    created = await svc.create_asignacion(body, actor_id=current_user.user_id)
    await session.commit()
    return AsignacionOut.model_validate(created)


# ── PUT /vigencia-masiva — bulk update vigencia ───────────────────────────────


@router.put(
    "/vigencia-masiva",
    response_model=VigenciaMasivaOut,
    summary="Modificar vigencia masiva del equipo",
    dependencies=_GUARD,
)
async def vigencia_masiva(
    body: VigenciaMasivaRequest,
    session: DBSession,
    current_user: CurrentUser,
) -> VigenciaMasivaOut:
    """Update desde/hasta for all assignments of a team atomically."""
    svc = EquiposService(session, current_user.tenant_id)
    result = await svc.vigencia_masiva(body, actor_id=current_user.user_id)
    await session.commit()
    return result


# ── POST /asignacion-masiva — bulk create ─────────────────────────────────────


@router.post(
    "/asignacion-masiva",
    response_model=AsignacionMasivaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Asignación masiva de docentes",
    dependencies=_GUARD,
)
async def asignacion_masiva(
    body: AsignacionMasivaCreate,
    session: DBSession,
    current_user: CurrentUser,
) -> AsignacionMasivaOut:
    """Assign multiple users to a context+rol in bulk (idempotent)."""
    svc = EquiposService(session, current_user.tenant_id)
    result = await svc.asignacion_masiva(body, actor_id=current_user.user_id)
    await session.commit()
    return result


# ── POST /clonar — clone team between cohortes ────────────────────────────────


@router.post(
    "/clonar",
    response_model=AsignacionMasivaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Clonar equipo docente entre cohortes",
    dependencies=_GUARD,
)
async def clonar_equipo(
    body: ClonarEquipoRequest,
    session: DBSession,
    current_user: CurrentUser,
) -> AsignacionMasivaOut:
    """Clone all vigente assignments from one cohorte to another."""
    svc = EquiposService(session, current_user.tenant_id)
    result = await svc.clonar_equipo(body, actor_id=current_user.user_id)
    await session.commit()
    return result


# ── GET /{id} — single assignment ─────────────────────────────────────────────


@router.get(
    "/{asignacion_id}",
    response_model=AsignacionOut,
    summary="Obtener asignación por ID",
    dependencies=_GUARD,
)
async def get_asignacion(
    asignacion_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> AsignacionOut:
    """Return a single assignment scoped to the current tenant."""
    from app.repositories.asignacion import AsignacionRepository
    from fastapi import HTTPException

    repo = AsignacionRepository(session, current_user.tenant_id)
    asignacion = await repo.get(asignacion_id)
    if asignacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignacion no encontrada")
    return AsignacionOut.model_validate(asignacion)


# ── PUT /{id} — update single assignment ──────────────────────────────────────


@router.put(
    "/{asignacion_id}",
    response_model=AsignacionOut,
    summary="Actualizar asignación",
    dependencies=_GUARD,
)
async def update_asignacion(
    asignacion_id: uuid.UUID,
    body: AsignacionUpdate,
    session: DBSession,
    current_user: CurrentUser,
) -> AsignacionOut:
    """Update fields on an existing assignment."""
    from app.core.exceptions import NotFoundError
    from fastapi import HTTPException

    svc = EquiposService(session, current_user.tenant_id)
    try:
        updated = await svc.update_asignacion(asignacion_id, body, actor_id=current_user.user_id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignacion no encontrada")
    await session.commit()
    return AsignacionOut.model_validate(updated)


# ── DELETE /{id} — soft delete ────────────────────────────────────────────────


@router.delete(
    "/{asignacion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar asignación (soft delete)",
    dependencies=_GUARD,
)
async def delete_asignacion(
    asignacion_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> None:
    """Soft-delete an assignment (sets deleted_at, never removes from DB)."""
    from app.core.exceptions import NotFoundError
    from fastapi import HTTPException

    svc = EquiposService(session, current_user.tenant_id)
    try:
        await svc.delete_asignacion(asignacion_id, actor_id=current_user.user_id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignacion no encontrada")
    await session.commit()
