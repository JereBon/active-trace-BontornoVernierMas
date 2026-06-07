"""api/v1/routers/facturas.py — Facturas endpoints (C-18).

Identity and tenant_id ALWAYS come from the verified JWT (CurrentUser).

Endpoints:
  GET    /v1/facturas/           — listar facturas (facturas:gestionar)
  POST   /v1/facturas/           — crear factura   (facturas:gestionar)
  PATCH  /v1/facturas/{id}/estado — cambiar estado  (facturas:gestionar)
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import CurrentUser, DBSession
from app.core.exceptions import NotFoundError
from app.core.permisos import FACTURAS_GESTIONAR
from app.core.rbac import require_permission
from app.schemas.factura import FacturaCreate, FacturaEstadoUpdate, FacturaOut
from app.services.factura_service import FacturaService

router = APIRouter(
    prefix="/v1/facturas",
    tags=["facturas"],
)

_PERM_GESTIONAR = Depends(require_permission(FACTURAS_GESTIONAR))


# ── GET / ─────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    response_model=list[FacturaOut],
    dependencies=[_PERM_GESTIONAR],
    summary="Listar facturas (con filtros opcionales)",
)
async def listar_facturas(
    session: DBSession,
    current_user: CurrentUser,
    usuario_id: uuid.UUID | None = None,
    periodo: str | None = None,
    estado: str | None = None,
) -> list[FacturaOut]:
    svc = FacturaService(session, current_user.tenant_id)
    records = await svc.listar(usuario_id=usuario_id, periodo=periodo, estado=estado)
    return [FacturaOut.model_validate(r) for r in records]


# ── POST / ────────────────────────────────────────────────────────────────────


@router.post(
    "/",
    response_model=FacturaOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_PERM_GESTIONAR],
    summary="Crear nueva factura",
)
async def crear_factura(
    body: FacturaCreate,
    session: DBSession,
    current_user: CurrentUser,
) -> FacturaOut:
    svc = FacturaService(session, current_user.tenant_id)
    record = await svc.crear(body.model_dump())
    return FacturaOut.model_validate(record)


# ── PATCH /{id}/estado ────────────────────────────────────────────────────────


@router.patch(
    "/{id}/estado",
    response_model=FacturaOut,
    dependencies=[_PERM_GESTIONAR],
    summary="Cambiar estado de factura (Pendiente ↔ Abonada)",
)
async def cambiar_estado_factura(
    id: uuid.UUID,
    body: FacturaEstadoUpdate,
    session: DBSession,
    current_user: CurrentUser,
) -> FacturaOut:
    svc = FacturaService(session, current_user.tenant_id)
    try:
        record = await svc.cambiar_estado(id, body.estado)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc
    return FacturaOut.model_validate(record)
