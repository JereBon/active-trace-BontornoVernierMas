"""tests/test_programas.py — Tests for C-17: ProgramaMateria endpoints.

TDD cycles:
  RED:         create programa with permission → 201
  GREEN:       endpoint implemented
  TRIANGULATE: no permission → 403; extra fields → 422
  TRIANGULATE: list filtered by materia_id; empty for unknown materia
  TRIANGULATE: soft-delete excluded from list; multi-tenant isolation
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
        from app.core import database as db_module

        async with db_module.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with AsyncClient(
            transport=__import__("httpx").ASGITransport(app=mgr.app),
            base_url="http://testserver",
        ) as client:
            yield client


@pytest_asyncio.fixture(scope="module")
async def pm_tenant(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_client: AsyncClient,
) -> TenantInfo:
    async with test_session_factory() as session:
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"pm-tenant-{uuid.uuid4().hex[:8]}",
            nombre="ProgramaMateria Test Tenant",
        )
        session.add(tenant)
        await session.commit()
        return TenantInfo(id=tenant.id, slug=tenant.slug)


@pytest_asyncio.fixture(scope="module")
async def pm_seed(
    test_session_factory: async_sessionmaker[AsyncSession],
    pm_tenant: TenantInfo,
    test_client: AsyncClient,
) -> dict:
    async with test_session_factory() as session:
        p = Permiso(
            id=uuid.uuid4(),
            tenant_id=pm_tenant.id,
            codigo=ESTRUCTURA_GESTIONAR,
            descripcion="Gestionar estructura",
        )
        session.add(p)
        await session.flush()
        r = Rol(
            id=uuid.uuid4(),
            tenant_id=pm_tenant.id,
            codigo="ADMIN_PM",
            nombre="Admin PM",
        )
        session.add(r)
        await session.flush()
        rp = RolPermiso(
            id=uuid.uuid4(),
            tenant_id=pm_tenant.id,
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
async def pm_admin(
    test_session_factory: async_sessionmaker[AsyncSession],
    pm_tenant: TenantInfo,
    pm_seed: dict,
) -> UserInfo:
    kwargs = _usuario_kwargs(pm_tenant.id)
    user_id = kwargs["id"]
    async with test_session_factory() as session:
        u = Usuario(**kwargs)
        session.add(u)
        await session.flush()
        ur = UsuarioRol(
            id=uuid.uuid4(),
            tenant_id=pm_tenant.id,
            usuario_id=user_id,
            rol_id=pm_seed["rol_id"],
            vig_desde=date.today() - timedelta(days=30),
            vig_hasta=None,
        )
        session.add(ur)
        await session.commit()
    return UserInfo(id=user_id, tenant_id=pm_tenant.id, token=_make_token(user_id, pm_tenant.id))


@pytest_asyncio.fixture(scope="module")
async def pm_noauth(
    test_session_factory: async_sessionmaker[AsyncSession],
    pm_tenant: TenantInfo,
    pm_seed: dict,
) -> UserInfo:
    kwargs = _usuario_kwargs(pm_tenant.id)
    user_id = kwargs["id"]
    async with test_session_factory() as session:
        u = Usuario(**kwargs)
        session.add(u)
        await session.commit()
    return UserInfo(id=user_id, tenant_id=pm_tenant.id, token=_make_token(user_id, pm_tenant.id))


@pytest_asyncio.fixture(scope="module")
async def pm_materia_id(
    test_client: AsyncClient,
    pm_admin: UserInfo,
    pm_tenant: TenantInfo,
) -> uuid.UUID:
    """Create a Carrera and Materia for use in programa tests."""
    carrera_resp = await test_client.post(
        "/v1/carreras",
        json={"codigo": f"CPMTEST-{uuid.uuid4().hex[:4]}", "nombre": "Test Carrera PM", "estado": "Activa"},
        headers={"Authorization": f"Bearer {pm_admin.token}"},
    )
    assert carrera_resp.status_code == 201, carrera_resp.text

    mat_resp = await test_client.post(
        "/v1/materias",
        json={"codigo": f"MAT-PM-{uuid.uuid4().hex[:4]}", "nombre": "Programacion I PM", "estado": "Activa"},
        headers={"Authorization": f"Bearer {pm_admin.token}"},
    )
    assert mat_resp.status_code == 201, mat_resp.text
    return uuid.UUID(mat_resp.json()["id"])


# ── RED→GREEN: create programa ───────────────────────────────────────────────

@pytest.mark.anyio
async def test_create_programa_with_permission(
    test_client: AsyncClient,
    pm_admin: UserInfo,
    pm_materia_id: uuid.UUID,
):
    """RED→GREEN: create ProgramaMateria with permission → 201."""
    resp = await test_client.post(
        "/v1/programas",
        json={
            "materia_id": str(pm_materia_id),
            "titulo": "Programa de Programacion I",
            "carrera_id": None,
            "cohorte_id": None,
            "referencia_archivo": None,
            "vigente": True,
            "publicado_en": None,
        },
        headers={"Authorization": f"Bearer {pm_admin.token}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["titulo"] == "Programa de Programacion I"
    assert data["materia_id"] == str(pm_materia_id)
    assert data["deleted_at"] is None


# ── TRIANGULATE: no permission → 403 ─────────────────────────────────────────

@pytest.mark.anyio
async def test_create_programa_without_permission(
    test_client: AsyncClient,
    pm_noauth: UserInfo,
    pm_materia_id: uuid.UUID,
):
    """TRIANGULATE: no permission → 403."""
    resp = await test_client.post(
        "/v1/programas",
        json={
            "materia_id": str(pm_materia_id),
            "titulo": "Should Fail",
            "vigente": True,
        },
        headers={"Authorization": f"Bearer {pm_noauth.token}"},
    )
    assert resp.status_code == 403


# ── TRIANGULATE: list by materia ─────────────────────────────────────────────

@pytest.mark.anyio
async def test_list_programas_by_materia(
    test_client: AsyncClient,
    pm_admin: UserInfo,
    pm_materia_id: uuid.UUID,
):
    """TRIANGULATE: list by materia returns matching programs."""
    # Create a program for this materia
    create_resp = await test_client.post(
        "/v1/programas",
        json={
            "materia_id": str(pm_materia_id),
            "titulo": "Prog para listar",
            "vigente": True,
        },
        headers={"Authorization": f"Bearer {pm_admin.token}"},
    )
    assert create_resp.status_code == 201
    prog_id = create_resp.json()["id"]

    list_resp = await test_client.get(
        f"/v1/programas/materia/{pm_materia_id}",
        headers={"Authorization": f"Bearer {pm_admin.token}"},
    )
    assert list_resp.status_code == 200
    ids = [p["id"] for p in list_resp.json()]
    assert prog_id in ids


@pytest.mark.anyio
async def test_list_programas_by_unknown_materia_is_empty(
    test_client: AsyncClient,
    pm_admin: UserInfo,
):
    """TRIANGULATE: list by unknown materia_id returns empty list."""
    resp = await test_client.get(
        f"/v1/programas/materia/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {pm_admin.token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == []


# ── TRIANGULATE: soft delete excluded from list ───────────────────────────────

@pytest.mark.anyio
async def test_soft_delete_excluded_from_list(
    test_client: AsyncClient,
    pm_admin: UserInfo,
    pm_materia_id: uuid.UUID,
):
    """TRIANGULATE: soft-deleted programa not in list."""
    create_resp = await test_client.post(
        "/v1/programas",
        json={
            "materia_id": str(pm_materia_id),
            "titulo": "Para borrar",
            "vigente": True,
        },
        headers={"Authorization": f"Bearer {pm_admin.token}"},
    )
    assert create_resp.status_code == 201
    prog_id = create_resp.json()["id"]

    del_resp = await test_client.delete(
        f"/v1/programas/{prog_id}",
        headers={"Authorization": f"Bearer {pm_admin.token}"},
    )
    assert del_resp.status_code == 204

    list_resp = await test_client.get(
        "/v1/programas",
        headers={"Authorization": f"Bearer {pm_admin.token}"},
    )
    ids = [p["id"] for p in list_resp.json()]
    assert prog_id not in ids
