"""api/v1/routers/tareas.py — Tarea endpoints (C-16).

All endpoints require 'tareas:gestionar' permission.
Identity and tenant_id always come from the verified JWT (CurrentUser).
No business logic here — only HTTP translation → service calls.

Endpoints:
  GET    /v1/tareas/            List my tasks (asignado_a = me) with filters (F8.1)
  POST   /v1/tareas/            Create and assign a task (F8.1)
  GET    /v1/tareas/todas       Admin: all tenant tasks with filters (F8.1)
  PATCH  /v1/tareas/{id}/estado Change task estado with transition validation (F8.2)
  POST   /v1/tareas/{id}/comentarios  Add a comment to the task thread (F8.2)
  GET    /v1/tareas/{id}/comentarios  Read the chronological comment thread (F8.2)
  POST   /v1/tareas/{id}/delegar      Reassign task to another user (F8.3)
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CurrentUser, DBSession
from app.core.permisos import TAREAS_GESTIONAR
from app.core.rbac import require_permission
from app.schemas.tarea import (
    ComentarioCreate,
    ComentarioOut,
    TareaCreate,
    TareaEstadoUpdate,
    TareaFilter,
    TareaDelegarUpdate,
    TareaOut,
)
from app.services.tarea_service import TareaService

router = APIRouter(prefix="/v1/tareas", tags=["tareas"])

_GUARD = [Depends(require_permission(TAREAS_GESTIONAR))]


# ── GET / — list my tasks ─────────────────────────────────────────────────────


@router.get(
    "/",
    response_model=list[TareaOut],
    summary="Listar mis tareas (F8.1)",
    dependencies=_GUARD,
)
async def list_mis_tareas(
    session: DBSession,
    current_user: CurrentUser,
    estado: Optional[str] = Query(default=None),
    materia_id: Optional[uuid.UUID] = Query(default=None),
) -> list[TareaOut]:
    """Return tasks assigned to the current authenticated user with optional filters."""
    filters = TareaFilter(estado=estado, materia_id=materia_id)
    svc = TareaService(session, current_user.tenant_id)
    tareas = await svc.list_mis_tareas(
        current_user_id=current_user.user_id,
        filters=filters,
    )
    return [TareaOut.model_validate(t) for t in tareas]


# ── POST / — create task ──────────────────────────────────────────────────────


@router.post(
    "/",
    response_model=TareaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear y asignar tarea (F8.1)",
    dependencies=_GUARD,
)
async def crear_tarea(
    body: TareaCreate,
    session: DBSession,
    current_user: CurrentUser,
) -> TareaOut:
    """Create a new task and assign it to the target user.

    asignado_por is always set from the JWT identity, never from the request body.
    """
    svc = TareaService(session, current_user.tenant_id)
    tarea = await svc.crear_tarea(body, actor_id=current_user.user_id)
    await session.commit()
    return TareaOut.model_validate(tarea)


# ── GET /todas — admin: all tenant tasks ──────────────────────────────────────


@router.get(
    "/todas",
    response_model=list[TareaOut],
    summary="Admin: todas las tareas del tenant con filtros (F8.1)",
    dependencies=_GUARD,
)
async def list_todas_tareas(
    session: DBSession,
    current_user: CurrentUser,
    estado: Optional[str] = Query(default=None),
    asignado_a: Optional[uuid.UUID] = Query(default=None),
    materia_id: Optional[uuid.UUID] = Query(default=None),
) -> list[TareaOut]:
    """Return all tasks for the current tenant. Admin-level view.

    Supports filtering by estado, asignado_a, and materia_id.
    """
    filters = TareaFilter(estado=estado, asignado_a=asignado_a, materia_id=materia_id)
    svc = TareaService(session, current_user.tenant_id)
    tareas = await svc.list_todas_las_tareas(filters)
    return [TareaOut.model_validate(t) for t in tareas]


# ── PATCH /{id}/estado — change estado ───────────────────────────────────────


@router.patch(
    "/{tarea_id}/estado",
    response_model=TareaOut,
    summary="Cambiar estado de tarea (F8.2)",
    dependencies=_GUARD,
)
async def cambiar_estado(
    tarea_id: uuid.UUID,
    body: TareaEstadoUpdate,
    session: DBSession,
    current_user: CurrentUser,
) -> TareaOut:
    """Change the estado of a task with valid-transition enforcement.

    Invalid transitions return HTTP 422 with the allowed transitions listed.
    """
    svc = TareaService(session, current_user.tenant_id)
    tarea = await svc.cambiar_estado(
        tarea_id=tarea_id,
        nuevo_estado=body.estado,
        actor_id=current_user.user_id,
    )
    await session.commit()
    return TareaOut.model_validate(tarea)


# ── POST /{id}/comentarios — add comment ──────────────────────────────────────


@router.post(
    "/{tarea_id}/comentarios",
    response_model=ComentarioOut,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar comentario a tarea (F8.2)",
    dependencies=_GUARD,
)
async def agregar_comentario(
    tarea_id: uuid.UUID,
    body: ComentarioCreate,
    session: DBSession,
    current_user: CurrentUser,
) -> ComentarioOut:
    """Add a comment to a task's thread."""
    svc = TareaService(session, current_user.tenant_id)
    comentario = await svc.agregar_comentario(
        tarea_id=tarea_id,
        data=body,
        actor_id=current_user.user_id,
    )
    await session.commit()
    return ComentarioOut.model_validate(comentario)


# ── GET /{id}/comentarios — read thread ──────────────────────────────────────


@router.get(
    "/{tarea_id}/comentarios",
    response_model=list[ComentarioOut],
    summary="Obtener hilo de comentarios (F8.2)",
    dependencies=_GUARD,
)
async def get_comentarios(
    tarea_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> list[ComentarioOut]:
    """Return the chronological comment thread for a task (oldest first)."""
    svc = TareaService(session, current_user.tenant_id)
    comentarios = await svc.get_comentarios(tarea_id)
    return [ComentarioOut.model_validate(c) for c in comentarios]


# ── POST /{id}/delegar — delegate task ───────────────────────────────────────


@router.post(
    "/{tarea_id}/delegar",
    response_model=TareaOut,
    summary="Delegar tarea a otro usuario (F8.3)",
    dependencies=_GUARD,
)
async def delegar_tarea(
    tarea_id: uuid.UUID,
    body: TareaDelegarUpdate,
    session: DBSession,
    current_user: CurrentUser,
) -> TareaOut:
    """Reassign a task to a different user.

    The original asignado_por is preserved — only asignado_a is updated.
    """
    svc = TareaService(session, current_user.tenant_id)
    tarea = await svc.delegar_tarea(
        tarea_id=tarea_id,
        nuevo_asignado_a=body.asignado_a,
        actor_id=current_user.user_id,
    )
    await session.commit()
    return TareaOut.model_validate(tarea)
