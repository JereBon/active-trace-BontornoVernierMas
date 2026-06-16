"""api/v1/routers/coloquios.py — Coloquio/evaluacion endpoints (C-14).

Identity and tenant_id always come from the verified JWT (CurrentUser).

Permissions:
  evaluaciones:gestionar — COORDINADOR, ADMIN (create, patch, list, import, resultados)
  evaluaciones:reservar  — ALUMNO (reserve a slot)
  evaluaciones:resultado — COORDINADOR, ADMIN (register outcomes)

Endpoints:
  GET    /v1/coloquios/metricas              Panel metrics (F7.1)
  POST   /v1/coloquios                       Create coloquio call (F7.3)
  GET    /v1/coloquios                       List coloquio calls (F7.4)
  GET    /v1/coloquios/{id}                  Get single coloquio call
  PATCH  /v1/coloquios/{id}                  Update coloquio call
  DELETE /v1/coloquios/{id}                  Soft-delete coloquio call (ADMIN only)
  POST   /v1/coloquios/{id}/reservas         Alumno reserves a slot (FL-07)
  GET    /v1/coloquios/{id}/reservas         List reservas for a coloquio
  POST   /v1/coloquios/{id}/reservas/{rid}/cancelar  Cancel a reserva
  POST   /v1/coloquios/{id}/resultados       Register exam result
  GET    /v1/coloquios/{id}/resultados       List results for a coloquio
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.audit import audit_action
from app.core.dependencies import CurrentUser, DBSession
from app.core.permisos import (
    EVALUACIONES_GESTIONAR,
    EVALUACIONES_RESERVAR,
    EVALUACIONES_RESULTADO,
)
from app.core.rbac import require_permission
from app.repositories.evaluacion_repository import EvaluacionRepository
from app.schemas.evaluacion import (
    EvaluacionCreate,
    EvaluacionMetricas,
    EvaluacionOut,
    EvaluacionPatch,
    ReservaCreate,
    ReservaOut,
    ResultadoCreate,
    ResultadoOut,
)

router = APIRouter(
    prefix="/v1/coloquios",
    tags=["coloquios"],
)


# ── Metrics ───────────────────────────────────────────────────────────────────


@router.get(
    "/metricas",
    response_model=EvaluacionMetricas,
    dependencies=[Depends(require_permission(EVALUACIONES_GESTIONAR))],
)
async def get_metricas(
    session: DBSession,
    current_user: CurrentUser,
) -> EvaluacionMetricas:
    """Return F7.1 panel metrics: total convocatorias, reservas, resultados, cupos libres."""
    repo = EvaluacionRepository(session, current_user.tenant_id)
    data = await repo.get_metricas()
    return EvaluacionMetricas(**data)


# ── Evaluaciones CRUD ─────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=EvaluacionOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(EVALUACIONES_GESTIONAR))],
)
async def create_evaluacion(
    body: EvaluacionCreate,
    session: DBSession,
    current_user: CurrentUser,
) -> EvaluacionOut:
    """Create a coloquio call (F7.3). Requires evaluaciones:gestionar."""
    repo = EvaluacionRepository(session, current_user.tenant_id)
    evaluacion = await repo.create_evaluacion(body.model_dump())
    await audit_action(
        session=session,
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        accion="EVALUACION_CREAR",
        detalle={"evaluacion_id": str(evaluacion.id), "instancia": evaluacion.instancia},
    )
    await session.commit()
    await session.refresh(evaluacion)
    return EvaluacionOut.model_validate(evaluacion)


@router.get(
    "",
    response_model=list[EvaluacionOut],
    dependencies=[Depends(require_permission(EVALUACIONES_GESTIONAR))],
)
async def list_evaluaciones(
    session: DBSession,
    current_user: CurrentUser,
    materia_id: uuid.UUID | None = Query(default=None),
    cohorte_id: uuid.UUID | None = Query(default=None),
    estado: str | None = Query(default=None),
) -> list[EvaluacionOut]:
    """List coloquio calls (F7.4). Optionally filter by materia, cohorte, estado."""
    repo = EvaluacionRepository(session, current_user.tenant_id)
    items = await repo.list_evaluaciones(
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        estado=estado,
    )
    return [EvaluacionOut.model_validate(e) for e in items]


@router.get(
    "/{evaluacion_id}",
    response_model=EvaluacionOut,
    dependencies=[Depends(require_permission(EVALUACIONES_GESTIONAR))],
)
async def get_evaluacion(
    evaluacion_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> EvaluacionOut:
    """Get a single coloquio call by id."""
    repo = EvaluacionRepository(session, current_user.tenant_id)
    evaluacion = await repo.get_evaluacion(evaluacion_id)
    if evaluacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluacion not found")
    return EvaluacionOut.model_validate(evaluacion)


@router.patch(
    "/{evaluacion_id}",
    response_model=EvaluacionOut,
    dependencies=[Depends(require_permission(EVALUACIONES_GESTIONAR))],
)
async def patch_evaluacion(
    evaluacion_id: uuid.UUID,
    body: EvaluacionPatch,
    session: DBSession,
    current_user: CurrentUser,
) -> EvaluacionOut:
    """Update mutable fields of a coloquio call."""
    repo = EvaluacionRepository(session, current_user.tenant_id)
    evaluacion = await repo.patch_evaluacion(
        evaluacion_id,
        body.model_dump(exclude_none=True),
    )
    if evaluacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluacion not found")
    await audit_action(
        session=session,
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        accion="EVALUACION_ACTUALIZAR",
        detalle={"evaluacion_id": str(evaluacion_id)},
    )
    await session.commit()
    await session.refresh(evaluacion)
    return EvaluacionOut.model_validate(evaluacion)


@router.delete(
    "/{evaluacion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(EVALUACIONES_GESTIONAR))],
)
async def delete_evaluacion(
    evaluacion_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> None:
    """Soft-delete a coloquio call. Requires evaluaciones:gestionar."""
    repo = EvaluacionRepository(session, current_user.tenant_id)
    deleted = await repo.soft_delete_evaluacion(evaluacion_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluacion not found")
    await audit_action(
        session=session,
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        accion="EVALUACION_ELIMINAR",
        detalle={"evaluacion_id": str(evaluacion_id)},
    )
    await session.commit()


# ── Reservas ──────────────────────────────────────────────────────────────────


@router.post(
    "/{evaluacion_id}/reservas",
    response_model=ReservaOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(EVALUACIONES_RESERVAR))],
)
async def create_reserva(
    evaluacion_id: uuid.UUID,
    body: ReservaCreate,
    session: DBSession,
    current_user: CurrentUser,
) -> ReservaOut:
    """Alumno reserves a slot on a coloquio call (FL-07).

    Fails with 422 if:
      - The evaluacion is not found (404)
      - The evaluacion is not Abierta (409)
      - No cupos available (409)
      - Alumno already has an active reserva for this evaluacion (409)
    """
    repo = EvaluacionRepository(session, current_user.tenant_id)
    try:
        reserva = await repo.create_reserva(
            evaluacion_id=evaluacion_id,
            alumno_id=current_user.id,
            fecha_hora=body.fecha_hora,
        )
    except ValueError as exc:
        code = str(exc)
        if code == "evaluacion_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluacion not found")
        if code == "evaluacion_not_open":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La convocatoria no está abierta",
            )
        if code == "sin_cupos_disponibles":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Sin cupos disponibles",
            )
        if code == "reserva_ya_activa":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una reserva activa para esta convocatoria",
            )
        raise

    await audit_action(
        session=session,
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        accion="EVALUACION_RESERVAR",
        detalle={
            "evaluacion_id": str(evaluacion_id),
            "reserva_id": str(reserva.id),
            "alumno_id": str(current_user.id),
        },
    )
    await session.commit()
    await session.refresh(reserva)
    return ReservaOut.model_validate(reserva)


@router.get(
    "/{evaluacion_id}/reservas",
    response_model=list[ReservaOut],
    dependencies=[Depends(require_permission(EVALUACIONES_GESTIONAR))],
)
async def list_reservas(
    evaluacion_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
    estado: str | None = Query(default=None),
) -> list[ReservaOut]:
    """List all reservas for a coloquio call. Requires evaluaciones:gestionar."""
    repo = EvaluacionRepository(session, current_user.tenant_id)
    evaluacion = await repo.get_evaluacion(evaluacion_id)
    if evaluacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluacion not found")
    reservas = await repo.list_reservas_by_evaluacion(evaluacion_id, estado=estado)
    return [ReservaOut.model_validate(r) for r in reservas]


@router.post(
    "/{evaluacion_id}/reservas/{reserva_id}/cancelar",
    response_model=ReservaOut,
    status_code=status.HTTP_200_OK,
)
async def cancel_reserva(
    evaluacion_id: uuid.UUID,
    reserva_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> ReservaOut:
    """Cancel a reserva. Any authenticated user may cancel their own; GESTIONAR for others.

    Cancelling restores one cupo to the Evaluacion.
    """
    repo = EvaluacionRepository(session, current_user.tenant_id)
    # Verify evaluacion exists in this tenant
    evaluacion = await repo.get_evaluacion(evaluacion_id)
    if evaluacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluacion not found")

    reserva = await repo.get_reserva(reserva_id)
    if reserva is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva not found")

    # Authorization: alumno can only cancel own reserva; gestionar permits any
    can_manage = EVALUACIONES_GESTIONAR in current_user.permisos_efectivos
    if not can_manage and reserva.alumno_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

    reserva = await repo.cancel_reserva(reserva_id)
    await audit_action(
        session=session,
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        accion="EVALUACION_CANCELAR_RESERVA",
        detalle={"reserva_id": str(reserva_id), "evaluacion_id": str(evaluacion_id)},
    )
    await session.commit()
    await session.refresh(reserva)
    return ReservaOut.model_validate(reserva)


# ── Resultados ────────────────────────────────────────────────────────────────


@router.post(
    "/{evaluacion_id}/resultados",
    response_model=ResultadoOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(EVALUACIONES_RESULTADO))],
)
async def create_resultado(
    evaluacion_id: uuid.UUID,
    body: ResultadoCreate,
    session: DBSession,
    current_user: CurrentUser,
) -> ResultadoOut:
    """Register an exam outcome for an alumno. Requires evaluaciones:resultado."""
    repo = EvaluacionRepository(session, current_user.tenant_id)
    try:
        resultado = await repo.create_resultado(
            evaluacion_id=evaluacion_id,
            alumno_id=body.alumno_id,
            aprobado=body.aprobado,
            nota_final=body.nota_final,
            observaciones=body.observaciones,
        )
    except ValueError as exc:
        if str(exc) == "evaluacion_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluacion not found")
        raise

    await audit_action(
        session=session,
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        accion="EVALUACION_RESULTADO",
        detalle={
            "evaluacion_id": str(evaluacion_id),
            "alumno_id": str(body.alumno_id),
            "aprobado": body.aprobado,
        },
    )
    await session.commit()
    await session.refresh(resultado)
    return ResultadoOut.model_validate(resultado)


@router.get(
    "/{evaluacion_id}/resultados",
    response_model=list[ResultadoOut],
    dependencies=[Depends(require_permission(EVALUACIONES_RESULTADO))],
)
async def list_resultados(
    evaluacion_id: uuid.UUID,
    session: DBSession,
    current_user: CurrentUser,
) -> list[ResultadoOut]:
    """List all resultados for a coloquio call. Requires evaluaciones:resultado."""
    repo = EvaluacionRepository(session, current_user.tenant_id)
    evaluacion = await repo.get_evaluacion(evaluacion_id)
    if evaluacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluacion not found")
    resultados = await repo.list_resultados_by_evaluacion(evaluacion_id)
    return [ResultadoOut.model_validate(r) for r in resultados]
