"""tests/test_avisos.py — Tests for C-15: avisos-y-acknowledgment.

TDD cycles:
  6.2  RED→GREEN:  create aviso with permission → 201, aviso in DB
  6.4  TRIANGULATE: create aviso without permission → 403
                    vig_hasta <= vig_desde → 422
  6.5  RED:        list vigentes → only active, in-window notices
  6.6  TRIANGULATE: deactivated not listed; out-of-window not listed
  6.7  RED→GREEN:  POST /ack first time → 200, record in DB
  6.8  TRIANGULATE: second ack → 200, no duplicate
  6.9  RED:        GET /acks with permission → list; without → 403

Uses a real PostgreSQL test DB. No DB mocking.
Module-scoped fixtures share the DB setup and app client.
"""

import os
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.permisos import AVISOS_CONFIRMAR, AVISOS_PUBLICAR
from app.models.base import Base
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.tenant import Tenant  # noqa: F401 — needed for metadata/create_all
from app.models.usuario import Usuario
from app.models.usuario_rol import UsuarioRol

# ── Helpers ───────────────────────────────────────────────────────────────────

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
    nombre: str


# ── Module-scoped DB + app setup ──────────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def db_tables(test_session_factory: async_sessionmaker[AsyncSession]):
    """Ensure all tables exist in the test DB (idempotent create_all)."""
    from app.core import database as db_module

    engine = db_module.engine
    assert engine is not None
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture(scope="module")
async def test_client(
    test_session_factory: async_sessionmaker[AsyncSession],
    db_tables,
) -> AsyncClient:
    """httpx client pointing at the FastAPI app with test DB."""
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
        async with AsyncClient(
            transport=__import__("httpx").ASGITransport(app=mgr.app),
            base_url="http://testserver",
        ) as client:
            yield client


@pytest_asyncio.fixture(scope="module")
async def av_tenant(
    test_session_factory: async_sessionmaker[AsyncSession],
    db_tables,
) -> TenantInfo:
    """Create a tenant for avisos tests."""
    async with test_session_factory() as session:
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"av-tenant-{uuid.uuid4().hex[:8]}",
            nombre="Avisos Test Tenant",
        )
        session.add(tenant)
        await session.commit()
        return TenantInfo(id=tenant.id, slug=tenant.slug, nombre=tenant.nombre)


@pytest_asyncio.fixture(scope="module")
async def av_seed(
    test_session_factory: async_sessionmaker[AsyncSession],
    av_tenant: TenantInfo,
) -> dict:
    """Seed avisos permissions and roles for av_tenant."""
    async with test_session_factory() as session:
        p_publicar = Permiso(
            id=uuid.uuid4(),
            tenant_id=av_tenant.id,
            codigo=AVISOS_PUBLICAR,
            descripcion="Publicar avisos",
        )
        p_confirmar = Permiso(
            id=uuid.uuid4(),
            tenant_id=av_tenant.id,
            codigo=AVISOS_CONFIRMAR,
            descripcion="Confirmar avisos",
        )
        session.add_all([p_publicar, p_confirmar])
        await session.flush()

        r_admin = Rol(
            id=uuid.uuid4(),
            tenant_id=av_tenant.id,
            codigo="ADMIN_AV",
            nombre="Admin Avisos",
        )
        r_alumno = Rol(
            id=uuid.uuid4(),
            tenant_id=av_tenant.id,
            codigo="ALUMNO_AV",
            nombre="Alumno Avisos",
        )
        session.add_all([r_admin, r_alumno])
        await session.flush()

        rp_admin_publicar = RolPermiso(
            id=uuid.uuid4(),
            tenant_id=av_tenant.id,
            rol_id=r_admin.id,
            permiso_id=p_publicar.id,
        )
        rp_alumno_confirmar = RolPermiso(
            id=uuid.uuid4(),
            tenant_id=av_tenant.id,
            rol_id=r_alumno.id,
            permiso_id=p_confirmar.id,
        )
        session.add_all([rp_admin_publicar, rp_alumno_confirmar])
        await session.commit()
        return {
            "admin_rol_id": r_admin.id,
            "alumno_rol_id": r_alumno.id,
        }


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
async def admin_user(
    test_session_factory: async_sessionmaker[AsyncSession],
    av_tenant: TenantInfo,
    av_seed: dict,
) -> UserInfo:
    """Create a user with ADMIN_AV role (has avisos:publicar)."""
    kwargs = _usuario_kwargs(av_tenant.id)
    user_id = kwargs["id"]
    async with test_session_factory() as session:
        u = Usuario(**kwargs)
        session.add(u)
        await session.flush()
        ur = UsuarioRol(
            id=uuid.uuid4(),
            tenant_id=av_tenant.id,
            usuario_id=user_id,
            rol_id=av_seed["admin_rol_id"],
            vig_desde=date.today() - timedelta(days=30),
            vig_hasta=None,
        )
        session.add(ur)
        await session.commit()
    token = _make_token(user_id, av_tenant.id)
    return UserInfo(id=user_id, tenant_id=av_tenant.id, token=token)


@pytest_asyncio.fixture(scope="module")
async def alumno_user(
    test_session_factory: async_sessionmaker[AsyncSession],
    av_tenant: TenantInfo,
    av_seed: dict,
) -> UserInfo:
    """Create a user with ALUMNO_AV role (has avisos:confirmar only)."""
    kwargs = _usuario_kwargs(av_tenant.id)
    user_id = kwargs["id"]
    async with test_session_factory() as session:
        u = Usuario(**kwargs)
        session.add(u)
        await session.flush()
        ur = UsuarioRol(
            id=uuid.uuid4(),
            tenant_id=av_tenant.id,
            usuario_id=user_id,
            rol_id=av_seed["alumno_rol_id"],
            vig_desde=date.today() - timedelta(days=30),
            vig_hasta=None,
        )
        session.add(ur)
        await session.commit()
    token = _make_token(user_id, av_tenant.id)
    return UserInfo(id=user_id, tenant_id=av_tenant.id, token=token)


@pytest_asyncio.fixture(scope="module")
async def noauth_user(
    test_session_factory: async_sessionmaker[AsyncSession],
    av_tenant: TenantInfo,
    av_seed: dict,
) -> UserInfo:
    """User with no roles (no permissions)."""
    kwargs = _usuario_kwargs(av_tenant.id)
    user_id = kwargs["id"]
    async with test_session_factory() as session:
        u = Usuario(**kwargs)
        session.add(u)
        await session.commit()
    token = _make_token(user_id, av_tenant.id)
    return UserInfo(id=user_id, tenant_id=av_tenant.id, token=token)


def _aviso_payload(
    scope: str = "TODOS",
    scope_valor: str | None = None,
    vig_offset_h: int = -1,
    vig_dur_h: int = 48,
) -> dict:
    """Build a valid AvisoCreate payload (window currently active)."""
    now = datetime.now(tz=timezone.utc)
    vig_desde = now + timedelta(hours=vig_offset_h)
    vig_hasta = vig_desde + timedelta(hours=vig_dur_h)
    return {
        "titulo": "Aviso de prueba",
        "cuerpo": "Contenido del aviso de prueba.",
        "scope": scope,
        "scope_valor": scope_valor,
        "vig_desde": vig_desde.isoformat(),
        "vig_hasta": vig_hasta.isoformat(),
    }


# ── 6.2 / 6.3 — POST /avisos with permission → 201 ──────────────────────────

@pytest.mark.anyio
async def test_create_aviso_with_permission(
    test_client: AsyncClient,
    test_session_factory: async_sessionmaker[AsyncSession],
    admin_user: UserInfo,
    av_tenant: TenantInfo,
):
    """RED→GREEN: admin creates an aviso → 201, stored in DB."""
    from app.models.aviso import Aviso

    resp = await test_client.post(
        "/v1/avisos",
        json=_aviso_payload(),
        headers={"Authorization": f"Bearer {admin_user.token}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["titulo"] == "Aviso de prueba"
    assert data["tenant_id"] == str(av_tenant.id)
    assert data["activo"] is True

    # Verify in DB
    aviso_id = uuid.UUID(data["id"])
    async with test_session_factory() as session:
        aviso = await session.get(Aviso, aviso_id)
    assert aviso is not None
    assert str(aviso.tenant_id) == str(av_tenant.id)


# ── 6.4 — TRIANGULATE: no permission → 403; bad dates → 422 ─────────────────

@pytest.mark.anyio
async def test_create_aviso_without_permission(
    test_client: AsyncClient,
    noauth_user: UserInfo,
):
    """TRIANGULATE: user without avisos:publicar → 403."""
    resp = await test_client.post(
        "/v1/avisos",
        json=_aviso_payload(),
        headers={"Authorization": f"Bearer {noauth_user.token}"},
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_create_aviso_invalid_dates(
    test_client: AsyncClient,
    admin_user: UserInfo,
):
    """TRIANGULATE: vig_hasta <= vig_desde → 422."""
    now = datetime.now(tz=timezone.utc)
    bad_payload = {
        "titulo": "Bad dates",
        "cuerpo": "body",
        "scope": "TODOS",
        "scope_valor": None,
        "vig_desde": (now + timedelta(hours=2)).isoformat(),
        "vig_hasta": (now + timedelta(hours=1)).isoformat(),  # before vig_desde
    }
    resp = await test_client.post(
        "/v1/avisos",
        json=bad_payload,
        headers={"Authorization": f"Bearer {admin_user.token}"},
    )
    assert resp.status_code == 422


# ── 6.5 — GET /avisos lists vigentes ─────────────────────────────────────────

@pytest.mark.anyio
async def test_list_avisos_vigentes(
    test_client: AsyncClient,
    admin_user: UserInfo,
):
    """RED: active aviso within window appears in list."""
    create_resp = await test_client.post(
        "/v1/avisos",
        json=_aviso_payload(vig_offset_h=-1, vig_dur_h=48),
        headers={"Authorization": f"Bearer {admin_user.token}"},
    )
    assert create_resp.status_code == 201
    aviso_id = create_resp.json()["id"]

    list_resp = await test_client.get(
        "/v1/avisos",
        headers={"Authorization": f"Bearer {admin_user.token}"},
    )
    assert list_resp.status_code == 200
    ids = [a["id"] for a in list_resp.json()]
    assert aviso_id in ids


# ── 6.6 — TRIANGULATE: deactivated + out-of-window excluded ──────────────────

@pytest.mark.anyio
async def test_list_avisos_excludes_deactivated(
    test_client: AsyncClient,
    admin_user: UserInfo,
):
    """TRIANGULATE: deactivated aviso does not appear in list."""
    create_resp = await test_client.post(
        "/v1/avisos",
        json=_aviso_payload(vig_offset_h=-1, vig_dur_h=48),
        headers={"Authorization": f"Bearer {admin_user.token}"},
    )
    assert create_resp.status_code == 201
    aviso_id = create_resp.json()["id"]

    patch_resp = await test_client.patch(
        f"/v1/avisos/{aviso_id}",
        json={"activo": False},
        headers={"Authorization": f"Bearer {admin_user.token}"},
    )
    assert patch_resp.status_code == 200

    list_resp = await test_client.get(
        "/v1/avisos",
        headers={"Authorization": f"Bearer {admin_user.token}"},
    )
    ids = [a["id"] for a in list_resp.json()]
    assert aviso_id not in ids


@pytest.mark.anyio
async def test_list_avisos_excludes_out_of_window(
    test_client: AsyncClient,
    admin_user: UserInfo,
):
    """TRIANGULATE: aviso outside vigencia window does not appear in list."""
    now = datetime.now(tz=timezone.utc)
    past_payload = {
        "titulo": "Past aviso",
        "cuerpo": "body",
        "scope": "TODOS",
        "scope_valor": None,
        "vig_desde": (now - timedelta(hours=10)).isoformat(),
        "vig_hasta": (now - timedelta(hours=1)).isoformat(),
    }
    create_resp = await test_client.post(
        "/v1/avisos",
        json=past_payload,
        headers={"Authorization": f"Bearer {admin_user.token}"},
    )
    assert create_resp.status_code == 201
    aviso_id = create_resp.json()["id"]

    list_resp = await test_client.get(
        "/v1/avisos",
        headers={"Authorization": f"Bearer {admin_user.token}"},
    )
    ids = [a["id"] for a in list_resp.json()]
    assert aviso_id not in ids


# ── 6.7 — POST /avisos/{id}/ack ──────────────────────────────────────────────

@pytest.mark.anyio
async def test_ack_first_time(
    test_client: AsyncClient,
    test_session_factory: async_sessionmaker[AsyncSession],
    admin_user: UserInfo,
    alumno_user: UserInfo,
):
    """RED→GREEN: first ack → 200, record stored in DB."""
    from app.models.aviso_ack import AvisoAck
    from sqlalchemy import select

    create_resp = await test_client.post(
        "/v1/avisos",
        json=_aviso_payload(),
        headers={"Authorization": f"Bearer {admin_user.token}"},
    )
    assert create_resp.status_code == 201
    aviso_id = create_resp.json()["id"]

    ack_resp = await test_client.post(
        f"/v1/avisos/{aviso_id}/ack",
        headers={"Authorization": f"Bearer {alumno_user.token}"},
    )
    assert ack_resp.status_code == 200
    data = ack_resp.json()
    assert data["usuario_id"] == str(alumno_user.id)

    # Verify in DB
    async with test_session_factory() as session:
        stmt = select(AvisoAck).where(
            AvisoAck.aviso_id == uuid.UUID(aviso_id),
            AvisoAck.usuario_id == alumno_user.id,
        )
        result = await session.execute(stmt)
        ack = result.scalar_one_or_none()
    assert ack is not None


# ── 6.8 — TRIANGULATE: idempotent ack ────────────────────────────────────────

@pytest.mark.anyio
async def test_ack_idempotent(
    test_client: AsyncClient,
    test_session_factory: async_sessionmaker[AsyncSession],
    admin_user: UserInfo,
    alumno_user: UserInfo,
):
    """TRIANGULATE: second ack → 200, no duplicate row."""
    from app.models.aviso_ack import AvisoAck
    from sqlalchemy import func, select

    create_resp = await test_client.post(
        "/v1/avisos",
        json=_aviso_payload(),
        headers={"Authorization": f"Bearer {admin_user.token}"},
    )
    aviso_id = create_resp.json()["id"]

    ack1 = await test_client.post(
        f"/v1/avisos/{aviso_id}/ack",
        headers={"Authorization": f"Bearer {alumno_user.token}"},
    )
    ack2 = await test_client.post(
        f"/v1/avisos/{aviso_id}/ack",
        headers={"Authorization": f"Bearer {alumno_user.token}"},
    )

    assert ack1.status_code == 200
    assert ack2.status_code == 200

    async with test_session_factory() as session:
        stmt = select(func.count()).select_from(AvisoAck).where(
            AvisoAck.aviso_id == uuid.UUID(aviso_id),
            AvisoAck.usuario_id == alumno_user.id,
        )
        result = await session.execute(stmt)
        count = result.scalar_one()
    assert count == 1


# ── 6.9 — GET /avisos/{id}/acks ──────────────────────────────────────────────

@pytest.mark.anyio
async def test_list_acks_with_permission(
    test_client: AsyncClient,
    admin_user: UserInfo,
    alumno_user: UserInfo,
):
    """RED: GET /acks with avisos:publicar → list of acks."""
    create_resp = await test_client.post(
        "/v1/avisos",
        json=_aviso_payload(),
        headers={"Authorization": f"Bearer {admin_user.token}"},
    )
    aviso_id = create_resp.json()["id"]

    await test_client.post(
        f"/v1/avisos/{aviso_id}/ack",
        headers={"Authorization": f"Bearer {alumno_user.token}"},
    )

    acks_resp = await test_client.get(
        f"/v1/avisos/{aviso_id}/acks",
        headers={"Authorization": f"Bearer {admin_user.token}"},
    )
    assert acks_resp.status_code == 200
    acks = acks_resp.json()
    assert any(a["usuario_id"] == str(alumno_user.id) for a in acks)


@pytest.mark.anyio
async def test_list_acks_without_permission(
    test_client: AsyncClient,
    admin_user: UserInfo,
    alumno_user: UserInfo,
):
    """TRIANGULATE: GET /acks without avisos:publicar → 403."""
    create_resp = await test_client.post(
        "/v1/avisos",
        json=_aviso_payload(),
        headers={"Authorization": f"Bearer {admin_user.token}"},
    )
    aviso_id = create_resp.json()["id"]

    acks_resp = await test_client.get(
        f"/v1/avisos/{aviso_id}/acks",
        headers={"Authorization": f"Bearer {alumno_user.token}"},
    )
    assert acks_resp.status_code == 403
