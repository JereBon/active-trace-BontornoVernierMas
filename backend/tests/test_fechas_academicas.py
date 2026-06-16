"""tests/test_fechas_academicas.py — Tests for C-17: FechaAcademica endpoints.

TDD cycles:
  RED:         create fecha with permission → 201
  GREEN:       endpoint implemented
  TRIANGULATE: no permission → 403; invalid tipo → 422
  TRIANGULATE: list with materia_id filter
  TRIANGULATE: soft-delete excluded; multi-tenant isolation
"""

import os
import uuid
from dataclasses import dataclass
from datetime import date, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.permisos import ESTRUCTURA_GESTIONAR
from app.models.base import Base
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.tenant import Tenant  # noqa: F401
from app.models.usuario import Usuario
from app.models.usuario_rol import UsuarioRol

_TEST_SECRET = "test-secret-key-32-characters-ok!"
_TEST_ENCRYPTION_KEY = "0" * 64


def _make_token(user_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
    from app.core.security import create_access_token

    return create_access_token(
        data={"sub": str(user_id), "tenant_id": str(tenant_id)},
        expires_delta=timedelta(minutes=30),
    )


@dataclass
class UserInfo:
    id: uuid.UUID
    tenant_id: uuid.UUID
    token: str


@dataclass
class TenantInfo:
    id: uuid.UUID
    slug: str


@pytest_asyncio.fixture(scope="module")
async def test_client(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncClient:
    from asgi_lifespan import LifespanManager
    from app.core.config import _reset_settings
    from app.main import create_application

    test_db_url = os.environ.get(
        "DATABASE_URL_TEST",
        "postgresql+asyncpg://activia:changeme@localhost:5432/activia_trace_test",
    )
    os.environ["DATABASE_URL"] = test_db_url
    os.environ["SECRET_KEY"] = _TEST_SECRET
    os.environ["ENCRYPTION_KEY"] = _TEST_ENCRYPTION_KEY
    _reset_settings()

    app = create_application()

    async with LifespanManager(app) as mgr:
        # Ensure tables exist within the app's own engine
        from app.core import database as db_module
        from app.models.base import Base

        async with db_module.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with AsyncClient(
            transport=__import__("httpx").ASGITransport(app=mgr.app),
            base_url="http://testserver",
        ) as client:
            yield client


@pytest_asyncio.fixture(scope="module")
async def fa_tenant(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_client: AsyncClient,
) -> TenantInfo:
    async with test_session_factory() as session:
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"fa-tenant-{uuid.uuid4().hex[:8]}",
            nombre="FechaAcademica Test Tenant",
        )
        session.add(tenant)
        await session.commit()
        return TenantInfo(id=tenant.id, slug=tenant.slug)


@pytest_asyncio.fixture(scope="module")
async def fa_seed(
    test_session_factory: async_sessionmaker[AsyncSession],
    fa_tenant: TenantInfo,
) -> dict:
    async with test_session_factory() as session:
        p = Permiso(
            id=uuid.uuid4(),
            tenant_id=fa_tenant.id,
            codigo=ESTRUCTURA_GESTIONAR,
            descripcion="Gestionar estructura",
        )
        session.add(p)
        await session.flush()
        r = Rol(
            id=uuid.uuid4(),
            tenant_id=fa_tenant.id,
            codigo="ADMIN_FA",
            nombre="Admin FA",
        )
        session.add(r)
        await session.flush()
        rp = RolPermiso(
            id=uuid.uuid4(),
            tenant_id=fa_tenant.id,
            rol_id=r.id,
            permiso_id=p.id,
        )
        session.add(rp)
        await session.commit()
        return {"rol_id": r.id}


def _usuario_kwargs(tenant_id: uuid.UUID) -> dict:
    from app.core.security import email_hash as _eh, hash_password

    raw = f"user-{uuid.uuid4().hex[:8]}@test.com"
    return {
        "id": uuid.uuid4(),
        "tenant_id": tenant_id,
        "email_cifrado": "placeholder-encrypted",
        "email_hash": _eh(raw),
        "password_hash": hash_password("testpassword123"),
        "activo": True,
    }


@pytest_asyncio.fixture(scope="module")
async def fa_admin(
    test_session_factory: async_sessionmaker[AsyncSession],
    fa_tenant: TenantInfo,
    fa_seed: dict,
) -> UserInfo:
    kwargs = _usuario_kwargs(fa_tenant.id)
    user_id = kwargs["id"]
    async with test_session_factory() as session:
        u = Usuario(**kwargs)
        session.add(u)
        await session.flush()
        ur = UsuarioRol(
            id=uuid.uuid4(),
            tenant_id=fa_tenant.id,
            usuario_id=user_id,
            rol_id=fa_seed["rol_id"],
            vig_desde=date.today() - timedelta(days=30),
            vig_hasta=None,
        )
        session.add(ur)
        await session.commit()
    return UserInfo(id=user_id, tenant_id=fa_tenant.id, token=_make_token(user_id, fa_tenant.id))


@pytest_asyncio.fixture(scope="module")
async def fa_noauth(
    test_session_factory: async_sessionmaker[AsyncSession],
    fa_tenant: TenantInfo,
    fa_seed: dict,
) -> UserInfo:
    kwargs = _usuario_kwargs(fa_tenant.id)
    user_id = kwargs["id"]
    async with test_session_factory() as session:
        u = Usuario(**kwargs)
        session.add(u)
        await session.commit()
    return UserInfo(id=user_id, tenant_id=fa_tenant.id, token=_make_token(user_id, fa_tenant.id))


@pytest_asyncio.fixture(scope="module")
async def fa_resources(
    test_client: AsyncClient,
    fa_admin: UserInfo,
) -> dict:
    """Create Carrera, Cohorte, and Materia for FechaAcademica tests."""
    carrera_resp = await test_client.post(
        "/v1/carreras",
        json={"codigo": f"CFA-{uuid.uuid4().hex[:4]}", "nombre": "Carrera FA", "estado": "Activa"},
        headers={"Authorization": f"Bearer {fa_admin.token}"},
    )
    assert carrera_resp.status_code == 201, carrera_resp.text
    carrera_id = uuid.UUID(carrera_resp.json()["id"])

    cohorte_resp = await test_client.post(
        "/v1/cohortes",
        json={
            "carrera_id": str(carrera_id),
            "nombre": "MAR-2026",
            "anio": 2026,
            "vig_desde": "2026-03-01",
        },
        headers={"Authorization": f"Bearer {fa_admin.token}"},
    )
    assert cohorte_resp.status_code == 201, cohorte_resp.text
    cohorte_id = uuid.UUID(cohorte_resp.json()["id"])

    mat_resp = await test_client.post(
        "/v1/materias",
        json={"codigo": f"MAT-FA-{uuid.uuid4().hex[:4]}", "nombre": "Prog I FA", "estado": "Activa"},
        headers={"Authorization": f"Bearer {fa_admin.token}"},
    )
    assert mat_resp.status_code == 201, mat_resp.text
    materia_id = uuid.UUID(mat_resp.json()["id"])

    return {"materia_id": materia_id, "cohorte_id": cohorte_id, "carrera_id": carrera_id}


def _fecha_payload(materia_id: uuid.UUID, cohorte_id: uuid.UUID, tipo: str = "PARCIAL") -> dict:
    return {
        "materia_id": str(materia_id),
        "cohorte_id": str(cohorte_id),
        "tipo": tipo,
        "numero": 1,
        "periodo": "2026-1",
        "fecha": "2026-05-10",
        "titulo": f"1er {tipo} Prog I FA",
    }


# ── RED→GREEN: create fecha ───────────────────────────────────────────────────

@pytest.mark.anyio
async def test_create_fecha_with_permission(
    test_client: AsyncClient,
    fa_admin: UserInfo,
    fa_resources: dict,
):
    """RED→GREEN: create FechaAcademica with permission → 201."""
    resp = await test_client.post(
        "/v1/fechas-academicas",
        json=_fecha_payload(fa_resources["materia_id"], fa_resources["cohorte_id"]),
        headers={"Authorization": f"Bearer {fa_admin.token}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["tipo"] == "PARCIAL"
    assert data["deleted_at"] is None


# ── TRIANGULATE: no permission → 403 ─────────────────────────────────────────

@pytest.mark.anyio
async def test_create_fecha_without_permission(
    test_client: AsyncClient,
    fa_noauth: UserInfo,
    fa_resources: dict,
):
    """TRIANGULATE: no permission → 403."""
    resp = await test_client.post(
        "/v1/fechas-academicas",
        json=_fecha_payload(fa_resources["materia_id"], fa_resources["cohorte_id"]),
        headers={"Authorization": f"Bearer {fa_noauth.token}"},
    )
    assert resp.status_code == 403


# ── TRIANGULATE: invalid tipo → 422 ──────────────────────────────────────────

@pytest.mark.anyio
async def test_create_fecha_invalid_tipo(
    test_client: AsyncClient,
    fa_admin: UserInfo,
    fa_resources: dict,
):
    """TRIANGULATE: invalid tipo enum value → 422."""
    payload = _fecha_payload(fa_resources["materia_id"], fa_resources["cohorte_id"])
    payload["tipo"] = "INVALIDO"
    resp = await test_client.post(
        "/v1/fechas-academicas",
        json=payload,
        headers={"Authorization": f"Bearer {fa_admin.token}"},
    )
    assert resp.status_code == 422


# ── TRIANGULATE: list with materia_id filter ──────────────────────────────────

@pytest.mark.anyio
async def test_list_fechas_with_materia_filter(
    test_client: AsyncClient,
    fa_admin: UserInfo,
    fa_resources: dict,
):
    """TRIANGULATE: list with materia_id filter returns only matching records."""
    create_resp = await test_client.post(
        "/v1/fechas-academicas",
        json=_fecha_payload(fa_resources["materia_id"], fa_resources["cohorte_id"], "TP"),
        headers={"Authorization": f"Bearer {fa_admin.token}"},
    )
    assert create_resp.status_code == 201
    fecha_id = create_resp.json()["id"]

    list_resp = await test_client.get(
        f"/v1/fechas-academicas?materia_id={fa_resources['materia_id']}",
        headers={"Authorization": f"Bearer {fa_admin.token}"},
    )
    assert list_resp.status_code == 200
    ids = [f["id"] for f in list_resp.json()]
    assert fecha_id in ids


@pytest.mark.anyio
async def test_list_fechas_unknown_materia_empty(
    test_client: AsyncClient,
    fa_admin: UserInfo,
):
    """TRIANGULATE: list with unknown materia_id returns empty list."""
    resp = await test_client.get(
        f"/v1/fechas-academicas?materia_id={uuid.uuid4()}",
        headers={"Authorization": f"Bearer {fa_admin.token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == []


# ── TRIANGULATE: soft-delete excluded from list ───────────────────────────────

@pytest.mark.anyio
async def test_soft_delete_fecha_excluded_from_list(
    test_client: AsyncClient,
    fa_admin: UserInfo,
    fa_resources: dict,
):
    """TRIANGULATE: soft-deleted fecha does not appear in list."""
    create_resp = await test_client.post(
        "/v1/fechas-academicas",
        json=_fecha_payload(fa_resources["materia_id"], fa_resources["cohorte_id"], "COLOQUIO"),
        headers={"Authorization": f"Bearer {fa_admin.token}"},
    )
    assert create_resp.status_code == 201
    fecha_id = create_resp.json()["id"]

    del_resp = await test_client.delete(
        f"/v1/fechas-academicas/{fecha_id}",
        headers={"Authorization": f"Bearer {fa_admin.token}"},
    )
    assert del_resp.status_code == 204

    list_resp = await test_client.get(
        "/v1/fechas-academicas",
        headers={"Authorization": f"Bearer {fa_admin.token}"},
    )
    ids = [f["id"] for f in list_resp.json()]
    assert fecha_id not in ids
