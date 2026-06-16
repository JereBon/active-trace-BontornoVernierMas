"""api/v1/routers/calificaciones.py — Calificaciones endpoints (C-10).

Identity and tenant_id ALWAYS come from the verified JWT (CurrentUser).
Never from URL params, body, or headers.

Endpoints:
  POST  /v1/calificaciones/{materia_id}/preview    — parse LMS file, return preview (no DB write)
  POST  /v1/calificaciones/{materia_id}/importar   — confirm import, persist calificaciones
  PUT   /v1/calificaciones/{materia_id}/umbral      — configure umbral for docente's asignacion
"""

import json
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status

from app.core.dependencies import CurrentUser, DBSession
from app.core.permisos import CALIFICACIONES_IMPORTAR, CALIFICACIONES_UMBRAL
from app.core.rbac import require_permission
from app.schemas.calificacion import (
    CalificacionPreviewResponse,
    ImportarCalificacionesResponse,
    UmbralMateriaRequest,
    UmbralMateriaResponse,
)
from app.services.calificacion_parser import CalificacionParseError
from app.services.calificacion_service import CalificacionService

router = APIRouter(
    prefix="/v1/calificaciones",
    tags=["calificaciones"],
)


# ── POST /{materia_id}/preview ────────────────────────────────────────────────


@router.post(
    "/{materia_id}/preview",
    response_model=CalificacionPreviewResponse,
    dependencies=[Depends(require_permission(CALIFICACIONES_IMPORTAR))],
    summary="Preview LMS file — detect activities without persisting",
)
async def preview_calificaciones(
    materia_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
    file: UploadFile = File(..., description="LMS export file (.xlsx or .csv)"),
) -> CalificacionPreviewResponse:
    """Parse an LMS export and return detected activities without persisting.

    Raises 422 if the required 'Email address' column is missing.
    """
    file_bytes = await file.read()
    filename = file.filename or "upload.xlsx"

    from app.services.calificacion_parser import CalificacionParser  # noqa: PLC0415

    parser = CalificacionParser()
    try:
        preview = parser.parse_preview(file_bytes, filename)
    except CalificacionParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": exc.detail},
        ) from exc

    return CalificacionPreviewResponse(
        actividades_numericas=preview["actividades_numericas"],
        actividades_textuales=preview["actividades_textuales"],
        alumnos_preview=preview["alumnos_preview"],
    )


# ── POST /{materia_id}/importar ───────────────────────────────────────────────


@router.post(
    "/{materia_id}/importar",
    response_model=ImportarCalificacionesResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(CALIFICACIONES_IMPORTAR))],
    summary="Import calificaciones from LMS file — confirm and persist",
)
async def importar_calificaciones(
    request: Request,
    materia_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
    file: UploadFile = File(..., description="LMS export file (.xlsx or .csv)"),
    asignacion_id: str = Form(..., description="UUID of the docente's asignacion"),
    actividades_seleccionadas: str = Form(..., description="JSON array of activity names to import"),
) -> ImportarCalificacionesResponse:
    """Confirm and persist calificaciones from an LMS file.

    The file is the same as provided to /preview. The caller selects which
    activities to import via actividades_seleccionadas (JSON array).
    Identity and tenant come exclusively from the JWT.
    """
    # Parse form fields
    try:
        asig_id = uuid.UUID(asignacion_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": f"Invalid asignacion_id: {asignacion_id}"},
        ) from exc

    try:
        actividades: list[str] = json.loads(actividades_seleccionadas)
        if not isinstance(actividades, list) or not actividades:
            raise ValueError("actividades_seleccionadas must be a non-empty JSON array")
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": str(exc)},
        ) from exc

    file_bytes = await file.read()
    filename = file.filename or "upload.xlsx"

    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    svc = CalificacionService(session, current_user.tenant_id)
    try:
        calificaciones = await svc.importar(
            actor_id=current_user.user_id,
            materia_id=materia_id,
            asignacion_id=asig_id,
            file_bytes=file_bytes,
            filename=filename,
            actividades_seleccionadas=actividades,
            ip=ip,
            user_agent=user_agent,
        )
    except CalificacionParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": exc.detail},
        ) from exc

    await session.commit()
    return ImportarCalificacionesResponse(
        calificaciones_importadas=len(calificaciones),
        mensaje=f"Se importaron {len(calificaciones)} calificaciones correctamente.",
    )


# ── PUT /{materia_id}/umbral ──────────────────────────────────────────────────


@router.put(
    "/{materia_id}/umbral",
    response_model=UmbralMateriaResponse,
    dependencies=[Depends(require_permission(CALIFICACIONES_UMBRAL))],
    summary="Configure passing threshold for docente's asignacion in a materia",
)
async def configurar_umbral(
    materia_id: uuid.UUID,
    body: UmbralMateriaRequest,
    session: DBSession,
    current_user: CurrentUser,
) -> UmbralMateriaResponse:
    """Create or update the umbral de aprobación for the docente's asignacion×materia pair.

    Also recalculates `aprobado` on all existing calificaciones for this materia
    in the current tenant. Identity comes exclusively from JWT.
    """
    svc = CalificacionService(session, current_user.tenant_id)
    umbral = await svc.configurar_umbral(
        actor_id=current_user.user_id,
        asignacion_id=body.asignacion_id,
        materia_id=materia_id,
        umbral_pct=body.umbral_pct,
        valores_aprobatorios=body.valores_aprobatorios,
    )
    await session.commit()
    return UmbralMateriaResponse(
        id=umbral.id,
        asignacion_id=umbral.asignacion_id,
        materia_id=materia_id,
        umbral_pct=umbral.umbral_pct,
        valores_aprobatorios=umbral.valores_aprobatorios or [],
    )
