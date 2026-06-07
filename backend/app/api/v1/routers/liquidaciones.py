"""api/v1/routers/liquidaciones.py — Liquidaciones and grilla endpoints (C-18).

Identity and tenant_id ALWAYS come from the verified JWT (CurrentUser).
Never from URL params, body, or headers.

Endpoints:
  GET  /v1/liquidaciones/              — vista período segmentada (liquidaciones:operar)
  POST /v1/liquidaciones/calcular      — calcular registros     (liquidaciones:operar)
  POST /v1/liquidaciones/cerrar        — cerrar período          (liquidaciones:cerrar)
  GET  /v1/liquidaciones/historial     — liquidaciones cerradas  (liquidaciones:operar)
  GET  /v1/liquidaciones/grilla/base   — listar SalarioBase      (liquidaciones:operar)
  POST /v1/liquidaciones/grilla/base   — crear SalarioBase       (liquidaciones:operar)
  PUT  /v1/liquidaciones/grilla/base/{id} — actualizar SalarioBase (liquidaciones:operar)
  GET  /v1/liquidaciones/grilla/plus   — listar SalarioPlus      (liquidaciones:operar)
  POST /v1/liquidaciones/grilla/plus   — crear SalarioPlus       (liquidaciones:operar)
  PUT  /v1/liquidaciones/grilla/plus/{id} — actualizar SalarioPlus (liquidaciones:operar)
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.dependencies import CurrentUser, DBSession
from app.core.exceptions import ConflictError, NotFoundError
from app.core.permisos import LIQUIDACIONES_CERRAR, LIQUIDACIONES_OPERAR
from app.core.rbac import require_permission
from app.schemas.liquidacion import (
    CalcularRequest,
    CalcularResponse,
    CerrarRequest,
    CerrarResponse,
    LiquidacionOut,
    VistaPeriodoOut,
)
from app.schemas.salario import (
    SalarioBaseCreate,
    SalarioBaseOut,
    SalarioBaseUpdate,
    SalarioPlusCreate,
    SalarioPlusOut,
    SalarioPlusUpdate,
)
from app.services.liquidacion_service import LiquidacionService
from app.services.salario_grilla_service import SalarioGrillaService

router = APIRouter(
    prefix="/v1/liquidaciones",
    tags=["liquidaciones"],
)

_PERM_OPERAR = Depends(require_permission(LIQUIDACIONES_OPERAR))
_PERM_CERRAR = Depends(require_permission(LIQUIDACIONES_CERRAR))


# ── GET / — vista período segmentada ─────────────────────────────────────────


@router.get(
    "/",
    dependencies=[_PERM_OPERAR],
    summary="Vista segmentada (general / NEXO / facturantes) con KPIs",
)
async def vista_periodo(
    cohorte_id: uuid.UUID,
    periodo: str,
    session: DBSession,
    current_user: CurrentUser,
) -> dict:
    svc = LiquidacionService(session, current_user.tenant_id)
    return await svc.vista_periodo(cohorte_id, periodo)


# ── POST /calcular ────────────────────────────────────────────────────────────


@router.post(
    "/calcular",
    response_model=CalcularResponse,
    dependencies=[_PERM_OPERAR],
    summary="Calcular liquidaciones para (cohorte, periodo)",
)
async def calcular_liquidaciones(
    body: CalcularRequest,
    session: DBSession,
    current_user: CurrentUser,
) -> CalcularResponse:
    svc = LiquidacionService(session, current_user.tenant_id)
    try:
        records = await svc.calcular(body.cohorte_id, body.periodo)
    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc
    return CalcularResponse(
        registros_creados=len(records),
        periodo=body.periodo,
        cohorte_id=body.cohorte_id,
    )


# ── POST /cerrar ──────────────────────────────────────────────────────────────


@router.post(
    "/cerrar",
    response_model=CerrarResponse,
    dependencies=[_PERM_CERRAR],
    summary="Cerrar período (Abierta → Cerrada, inmutable tras cierre)",
)
async def cerrar_periodo(
    body: CerrarRequest,
    request: Request,
    session: DBSession,
    current_user: CurrentUser,
) -> CerrarResponse:
    svc = LiquidacionService(session, current_user.tenant_id)
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")
    try:
        count = await svc.cerrar(
            body.cohorte_id,
            body.periodo,
            actor_id=current_user.user_id,
            ip=ip,
            user_agent=ua,
        )
    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc
    return CerrarResponse(
        registros_cerrados=count,
        periodo=body.periodo,
        cohorte_id=body.cohorte_id,
    )


# ── GET /historial ────────────────────────────────────────────────────────────


@router.get(
    "/historial",
    response_model=list[LiquidacionOut],
    dependencies=[_PERM_OPERAR],
    summary="Liquidaciones cerradas (historial)",
)
async def historial(
    session: DBSession,
    current_user: CurrentUser,
    cohorte_id: uuid.UUID | None = None,
    periodo: str | None = None,
) -> list[LiquidacionOut]:
    svc = LiquidacionService(session, current_user.tenant_id)
    records = await svc.historial(cohorte_id=cohorte_id, periodo=periodo)
    return [LiquidacionOut.model_validate(r) for r in records]


# ── Grilla Base ───────────────────────────────────────────────────────────────


@router.get(
    "/grilla/base",
    response_model=list[SalarioBaseOut],
    dependencies=[_PERM_OPERAR],
    summary="Listar grilla SalarioBase",
)
async def listar_base(session: DBSession, current_user: CurrentUser) -> list[SalarioBaseOut]:
    svc = SalarioGrillaService(session, current_user.tenant_id)
    return [SalarioBaseOut.model_validate(r) for r in await svc.listar_base()]


@router.post(
    "/grilla/base",
    response_model=SalarioBaseOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_PERM_OPERAR],
    summary="Crear registro SalarioBase",
)
async def crear_base(
    body: SalarioBaseCreate, session: DBSession, current_user: CurrentUser
) -> SalarioBaseOut:
    svc = SalarioGrillaService(session, current_user.tenant_id)
    return SalarioBaseOut.model_validate(await svc.crear_base(body.model_dump()))


@router.put(
    "/grilla/base/{id}",
    response_model=SalarioBaseOut,
    dependencies=[_PERM_OPERAR],
    summary="Actualizar SalarioBase",
)
async def actualizar_base(
    id: uuid.UUID,
    body: SalarioBaseUpdate,
    session: DBSession,
    current_user: CurrentUser,
) -> SalarioBaseOut:
    svc = SalarioGrillaService(session, current_user.tenant_id)
    record = await svc.actualizar_base(id, body.model_dump(exclude_none=True))
    if record is None:
        raise HTTPException(status_code=404, detail="SalarioBase not found.")
    return SalarioBaseOut.model_validate(record)


# ── Grilla Plus ───────────────────────────────────────────────────────────────


@router.get(
    "/grilla/plus",
    response_model=list[SalarioPlusOut],
    dependencies=[_PERM_OPERAR],
    summary="Listar grilla SalarioPlus",
)
async def listar_plus(session: DBSession, current_user: CurrentUser) -> list[SalarioPlusOut]:
    svc = SalarioGrillaService(session, current_user.tenant_id)
    return [SalarioPlusOut.model_validate(r) for r in await svc.listar_plus()]


@router.post(
    "/grilla/plus",
    response_model=SalarioPlusOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_PERM_OPERAR],
    summary="Crear registro SalarioPlus",
)
async def crear_plus(
    body: SalarioPlusCreate, session: DBSession, current_user: CurrentUser
) -> SalarioPlusOut:
    svc = SalarioGrillaService(session, current_user.tenant_id)
    return SalarioPlusOut.model_validate(await svc.crear_plus(body.model_dump()))


@router.put(
    "/grilla/plus/{id}",
    response_model=SalarioPlusOut,
    dependencies=[_PERM_OPERAR],
    summary="Actualizar SalarioPlus",
)
async def actualizar_plus(
    id: uuid.UUID,
    body: SalarioPlusUpdate,
    session: DBSession,
    current_user: CurrentUser,
) -> SalarioPlusOut:
    svc = SalarioGrillaService(session, current_user.tenant_id)
    record = await svc.actualizar_plus(id, body.model_dump(exclude_none=True))
    if record is None:
        raise HTTPException(status_code=404, detail="SalarioPlus not found.")
    return SalarioPlusOut.model_validate(record)
