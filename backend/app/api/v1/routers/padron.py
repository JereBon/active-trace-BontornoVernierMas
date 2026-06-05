"""api/v1/routers/padron.py — Padrón endpoints (C-09: padron-ingesta-moodle).

Identity and tenant_id ALWAYS come from the verified JWT (CurrentUser).
Never from URL params, body, or headers.

Endpoints:
  POST   /v1/padron/preview                    — parse file, return preview (no DB write)
  POST   /v1/padron/confirmar                  — confirm import, persist versioned padrón
  POST   /v1/padron/sync-moodle/{materia_id}   — sync from Moodle WS on-demand
  DELETE /v1/padron/materia/{materia_id}        — vaciar padrón (soft delete)
  GET    /v1/padron/materia/{materia_id}         — list versions (active + history)
"""

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status

from app.core.dependencies import CurrentUser, DBSession
from app.core.permisos import PADRON_CARGAR, PADRON_LEER, PADRON_VACIAR
from app.core.rbac import require_permission
from app.integrations.moodle_ws import MoodleWSError
from app.schemas.padron import (
    ConfirmarImportacionRequest,
    EntradaPreviewItem,
    EntradaPreviewOut,
    SyncMoodleRequest,
    VersionPadronOut,
    VaciarPadronOut,
)
from app.services.padron_parser import EntradaPadronRaw, PadronParseError
from app.services.padron_service import PadronService

router = APIRouter(
    prefix="/v1/padron",
    tags=["padron"],
)


# ── POST /preview ─────────────────────────────────────────────────────────────


@router.post(
    "/preview",
    response_model=list[EntradaPreviewOut],
    dependencies=[Depends(require_permission(PADRON_CARGAR))],
    summary="Preview file import without persisting",
)
async def preview_padron(
    request: Request,
    session: DBSession,
    current_user: CurrentUser,
    file: UploadFile = File(..., description="xlsx or csv file"),
) -> list[EntradaPreviewOut]:
    """Parse an .xlsx or .csv file and return a preview without persisting.

    Raises 422 if required columns are missing.
    """
    file_bytes = await file.read()
    content_type = file.content_type or ""

    svc = PadronService(session, current_user.tenant_id)
    try:
        entradas = svc.preview_desde_archivo(file_bytes, content_type)
    except PadronParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": exc.detail, "missing_columns": exc.missing_columns},
        ) from exc

    return [
        EntradaPreviewOut(
            nombre=e.nombre,
            apellidos=e.apellidos,
            email=e.email,
            comision=e.comision,
            regional=e.regional,
        )
        for e in entradas
    ]


# ── POST /confirmar ───────────────────────────────────────────────────────────


@router.post(
    "/confirmar",
    response_model=VersionPadronOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(PADRON_CARGAR))],
    summary="Confirm padrón import — creates a new versioned padrón",
)
async def confirmar_importacion(
    request: Request,
    body: ConfirmarImportacionRequest,
    session: DBSession,
    current_user: CurrentUser,
) -> VersionPadronOut:
    """Confirm a previewed import. Creates a new VersionPadron (deactivates previous)."""
    svc = PadronService(session, current_user.tenant_id)

    # Convert request items to EntradaPadronRaw
    entradas = [
        EntradaPadronRaw(
            nombre=e.nombre,
            apellidos=e.apellidos,
            email=e.email,
            comision=e.comision,
            regional=e.regional,
        )
        for e in body.entradas
    ]

    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    version = await svc.confirmar_importacion(
        materia_id=body.materia_id,
        cohorte_id=body.cohorte_id,
        entradas=entradas,
        usuario_id=current_user.user_id,
        ip=ip,
        user_agent=user_agent,
    )
    await session.commit()
    return VersionPadronOut.model_validate(version)


# ── POST /sync-moodle/{materia_id} ────────────────────────────────────────────


@router.post(
    "/sync-moodle/{materia_id}",
    response_model=VersionPadronOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(PADRON_CARGAR))],
    summary="Sync padrón from Moodle WS on-demand",
)
async def sync_moodle(
    request: Request,
    materia_id: uuid.UUID,
    body: SyncMoodleRequest,
    session: DBSession,
    current_user: CurrentUser,
) -> VersionPadronOut:
    """Sync padrón from Moodle Web Services. Returns 502 if Moodle is unavailable."""
    svc = PadronService(session, current_user.tenant_id)

    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    try:
        version = await svc.sync_desde_moodle(
            materia_id=materia_id,
            cohorte_id=body.cohorte_id,
            course_id=body.course_id,
            usuario_id=current_user.user_id,
            moodle_url=body.moodle_url,
            moodle_token=body.moodle_token,
            ip=ip,
            user_agent=user_agent,
        )
    except MoodleWSError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": "Moodle WS unavailable", "detail": exc.detail},
        ) from exc

    await session.commit()
    return VersionPadronOut.model_validate(version)


# ── DELETE /materia/{materia_id} ──────────────────────────────────────────────


@router.delete(
    "/materia/{materia_id}",
    response_model=VaciarPadronOut,
    dependencies=[Depends(require_permission(PADRON_VACIAR))],
    summary="Vaciar padrón de una materia (soft delete, scope-isolated)",
)
async def vaciar_padron(
    request: Request,
    materia_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> VaciarPadronOut:
    """Soft-delete all versions and entries for the given materia.

    Scope-isolated: only affects the current tenant's data (RN-04).
    """
    svc = PadronService(session, current_user.tenant_id)

    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    total = await svc.vaciar_padron(
        materia_id=materia_id,
        usuario_id=current_user.user_id,
        ip=ip,
        user_agent=user_agent,
    )
    await session.commit()
    return VaciarPadronOut(
        filas_afectadas=total,
        message=f"Padrón de materia {materia_id} vaciado ({total} filas).",
    )


# ── GET /materia/{materia_id} ─────────────────────────────────────────────────


@router.get(
    "/materia/{materia_id}",
    response_model=list[VersionPadronOut],
    dependencies=[Depends(require_permission(PADRON_LEER))],
    summary="List all padrón versions for a materia (active + history)",
)
async def listar_versiones(
    materia_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> list[VersionPadronOut]:
    """List all versions (active and historical) for a materia in this tenant."""
    svc = PadronService(session, current_user.tenant_id)
    versiones = await svc.listar_versiones(materia_id)
    return [VersionPadronOut.model_validate(v) for v in versiones]
