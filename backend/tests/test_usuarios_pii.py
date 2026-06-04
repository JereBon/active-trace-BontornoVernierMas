"""tests/test_usuarios_pii.py — Tests for C-07: Usuario PII + RBAC + /me.

TDD cycles:
  9.1  RED:        PII fields encrypted in DB (raw column != plaintext)
  9.2  TRIANGULATE: PII decrypted in API response (response contains plaintext)
  9.3  RED→GREEN:  GET /v1/me → own profile; 401 if unauthenticated
  9.4  TRIANGULATE: POST /v1/users without usuarios:gestionar → 403
  9.6  TRIANGULATE: multi-tenant isolation — tenant A cannot see tenant B users
"""

import os
import uuid
from dataclasses import dataclass
from datetime import date, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.permisos import USUARIOS_GESTIONAR
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
async def up_tenant(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_client: AsyncClient,
) -> TenantInfo:
    async with test_session_factory() as session:
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"up-tenant-{uuid.uuid4().hex[:8]}",
            nombre="PII Test Tenant",
        )
        session.add(tenant)
        await session.commit()
        return TenantInfo(id=tenant.id, slug=tenant.slug)


@pytest_asyncio.fixture(scope="module")
async def up_seed(
    test_session_factory: async_sessionmaker[AsyncSession],
    up_tenant: TenantInfo,
    test_client: AsyncClient,
) -> dict:
    async with test_session_factory() as session:
        p = Permiso(
            id=uuid.uuid4(),
            tenant_id=up_tenant.id,
            codigo=USUARIOS_GESTIONAR,
            descripcion="Gestionar usuarios",
        )
        session.add(p)
        await session.flush()
        r = Rol(
            id=uuid.uuid4(),
            tenant_id=up_tenant.id,
            codigo="ADMIN_UP",
            nombre="Admin UP",
        )
        session.add(r)
        await session.flush()
        rp = RolPermiso(
            id=uuid.uuid4(),
            tenant_id=up_tenant.id,
            rol_id=r.id,
            permiso_id=p.id,
        )
        session.add(rp)
        await session.commit()
        return {"rol_id": r.id}


def _usuario_base_kwargs(tenant_id: uuid.UUID) -> dict:
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
async def up_admin(
    test_session_factory: async_sessionmaker[AsyncSession],
    up_tenant: TenantInfo,
    up_seed: dict,
) -> UserInfo:
    kwargs = _usuario_base_kwargs(up_tenant.id)
    user_id = kwargs["id"]
    async with test_session_factory() as session:
        u = Usuario(**kwargs)
        session.add(u)
        await session.flush()
        ur = UsuarioRol(
            id=uuid.uuid4(),
            tenant_id=up_tenant.id,
            usuario_id=user_id,
            rol_id=up_seed["rol_id"],
            vig_desde=date.today() - timedelta(days=30),
            vig_hasta=None,
        )
        session.add(ur)
        await session.commit()
    return UserInfo(id=user_id, tenant_id=up_tenant.id, token=_make_token(user_id, up_tenant.id))


@pytest_asyncio.fixture(scope="module")
async def up_noauth(
    test_session_factory: async_sessionmaker[AsyncSession],
    up_tenant: TenantInfo,
    up_seed: dict,
) -> UserInfo:
    kwargs = _usuario_base_kwargs(up_tenant.id)
    user_id = kwargs["id"]
    async with test_session_factory() as session:
        u = Usuario(**kwargs)
        session.add(u)
        await session.commit()
    return UserInfo(id=user_id, tenant_id=up_tenant.id, token=_make_token(user_id, up_tenant.id))


# ── 9.1 RED: PII encrypted at rest ───────────────────────────────────────────

@pytest.mark.anyio
async def test_pii_encrypted_at_rest(
    test_client: AsyncClient,
    test_session_factory: async_sessionmaker[AsyncSession],
    up_admin: UserInfo,
):
    """RED→GREEN: PII fields stored as ciphertext in DB (not plaintext)."""
    from sqlalchemy import text

    resp = await test_client.post(
        "/v1/users",
        json={
            "email": f"pii-{uuid.uuid4().hex[:8]}@test.com",
            "password": "test1234pass",
            "nombre": "Juan",
            "apellidos": "Pérez",
            "dni": "30123456",
        },
        headers={"Authorization": f"Bearer {up_admin.token}"},
    )
    assert resp.status_code == 201, resp.text
    user_id = resp.json()["id"]

    # Verify DNI is NOT stored as plaintext in DB
    async with test_session_factory() as session:
        row = await session.execute(
            text("SELECT dni_cifrado FROM usuarios WHERE id = :id"),
            {"id": user_id},
        )
        raw_dni = row.scalar_one()

    assert raw_dni is not None
    assert raw_dni != "30123456", "DNI must be stored encrypted, not as plaintext"
    # The ciphertext should be a base64 string (longer than plaintext)
    assert len(raw_dni) > 10


# ── 9.2 TRIANGULATE: PII decrypted in response ────────────────────────────────

@pytest.mark.anyio
async def test_pii_decrypted_in_response(
    test_client: AsyncClient,
    up_admin: UserInfo,
):
    """TRIANGULATE: response contains decrypted PII (plaintext, not ciphertext)."""
    dni_value = f"2{uuid.uuid4().int % 10_000_000:07d}"
    resp = await test_client.post(
        "/v1/users",
        json={
            "email": f"pii2-{uuid.uuid4().hex[:8]}@test.com",
            "password": "test1234pass",
            "nombre": "Maria",
            "dni": dni_value,
            "cuil": f"27{dni_value}9",
        },
        headers={"Authorization": f"Bearer {up_admin.token}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    # API response returns decrypted plaintext
    assert data["nombre"] == "Maria"
    assert data["dni"] == dni_value
    assert data["cuil"] == f"27{dni_value}9"


# ── 9.3 GET /v1/me ────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_get_me_authenticated(
    test_client: AsyncClient,
    up_admin: UserInfo,
):
    """RED→GREEN: GET /v1/me with valid JWT returns own profile."""
    resp = await test_client.get(
        "/v1/me",
        headers={"Authorization": f"Bearer {up_admin.token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["id"] == str(up_admin.id)
    assert data["tenant_id"] == str(up_admin.tenant_id)


@pytest.mark.anyio
async def test_get_me_unauthenticated(test_client: AsyncClient):
    """TRIANGULATE: GET /v1/me without token → 401."""
    resp = await test_client.get("/v1/me")
    assert resp.status_code == 401


# ── 9.4 RBAC: POST /v1/users without permission → 403 ────────────────────────

@pytest.mark.anyio
async def test_create_user_without_permission(
    test_client: AsyncClient,
    up_noauth: UserInfo,
):
    """TRIANGULATE: user without usuarios:gestionar → 403 on POST /v1/users."""
    resp = await test_client.post(
        "/v1/users",
        json={
            "email": f"noauth-{uuid.uuid4().hex[:8]}@test.com",
            "password": "test1234pass",
        },
        headers={"Authorization": f"Bearer {up_noauth.token}"},
    )
    assert resp.status_code == 403


# ── 9.6 Multi-tenant isolation ────────────────────────────────────────────────

@pytest.mark.anyio
async def test_multitenant_isolation(
    test_client: AsyncClient,
    test_session_factory: async_sessionmaker[AsyncSession],
    up_admin: UserInfo,
    up_tenant: TenantInfo,
):
    """TRIANGULATE: tenant A cannot see tenant B users in GET /v1/users."""
    # Create a second tenant and user
    async with test_session_factory() as session:
        tenant_b = Tenant(
            id=uuid.uuid4(),
            slug=f"tenant-b-{uuid.uuid4().hex[:8]}",
            nombre="Tenant B",
        )
        session.add(tenant_b)
        await session.flush()

        # Create user in tenant B
        from app.core.security import email_hash as _eh, hash_password

        raw = f"user-b-{uuid.uuid4().hex[:8]}@test.com"
        u_b = Usuario(
            id=uuid.uuid4(),
            tenant_id=tenant_b.id,
            email_cifrado="placeholder-b",
            email_hash=_eh(raw),
            password_hash=hash_password("testpass"),
            activo=True,
        )
        session.add(u_b)
        await session.commit()
        user_b_id = u_b.id

    # Admin of tenant A lists users — should not see tenant B user
    resp = await test_client.get(
        "/v1/users",
        headers={"Authorization": f"Bearer {up_admin.token}"},
    )
    assert resp.status_code == 200
    ids = [u["id"] for u in resp.json()]
    assert str(user_b_id) not in ids
