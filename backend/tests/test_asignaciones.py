"""tests/test_asignaciones.py — Tests for C-07: Asignacion vigencia.

TDD cycles:
  9.5  RED→GREEN:  vigente assignment grants normal operation
  9.5  TRIANGULATE: expired assignment (hasta < today) not in vigentes list
"""

import os
import uuid
from dataclasses import dataclass
from datetime import date, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.asignacion import Asignacion
from app.models.base import Base
from app.models.tenant import Tenant  # noqa: F401
from app.models.usuario import Usuario

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
async def as_tenant(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_client: AsyncClient,
) -> TenantInfo:
    async with test_session_factory() as session:
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"as-tenant-{uuid.uuid4().hex[:8]}",
            nombre="Asignacion Test Tenant",
        )
        session.add(tenant)
        await session.commit()
        return TenantInfo(id=tenant.id, slug=tenant.slug)


@pytest_asyncio.fixture(scope="module")
async def as_user(
    test_session_factory: async_sessionmaker[AsyncSession],
    as_tenant: TenantInfo,
) -> UserInfo:
    from app.core.security import email_hash as _eh, hash_password

    raw = f"as-user-{uuid.uuid4().hex[:8]}@test.com"
    user_id = uuid.uuid4()
    async with test_session_factory() as session:
        u = Usuario(
            id=user_id,
            tenant_id=as_tenant.id,
            email_cifrado="placeholder-as",
            email_hash=_eh(raw),
            password_hash=hash_password("testpass"),
            activo=True,
        )
        session.add(u)
        await session.commit()
    return UserInfo(id=user_id, tenant_id=as_tenant.id, token=_make_token(user_id, as_tenant.id))


# ── 9.5 Vigencia tests (via repository directly) ─────────────────────────────

@pytest.mark.anyio
async def test_vigente_assignment_returned(
    test_session_factory: async_sessionmaker[AsyncSession],
    as_tenant: TenantInfo,
    as_user: UserInfo,
):
    """RED→GREEN: active assignment (hasta IS NULL) appears in get_vigentes_by_usuario."""
    from app.repositories.asignacion import AsignacionRepository

    today = date.today()
    async with test_session_factory() as session:
        # Create a vigente assignment (open-ended)
        asig = Asignacion(
            id=uuid.uuid4(),
            tenant_id=as_tenant.id,
            usuario_id=as_user.id,
            rol="PROFESOR",
            comisiones=[],
            desde=today - timedelta(days=30),
            hasta=None,  # open-ended = vigente
        )
        session.add(asig)
        await session.commit()
        asig_id = asig.id

    async with test_session_factory() as session:
        repo = AsignacionRepository(session, as_tenant.id)
        vigentes = await repo.get_vigentes_by_usuario(as_user.id)

    ids = [str(a.id) for a in vigentes]
    assert str(asig_id) in ids


@pytest.mark.anyio
async def test_expired_assignment_not_in_vigentes(
    test_session_factory: async_sessionmaker[AsyncSession],
    as_tenant: TenantInfo,
    as_user: UserInfo,
):
    """TRIANGULATE: expired assignment (hasta < today) NOT in get_vigentes_by_usuario."""
    from app.repositories.asignacion import AsignacionRepository

    today = date.today()
    async with test_session_factory() as session:
        # Create an expired assignment
        asig_expired = Asignacion(
            id=uuid.uuid4(),
            tenant_id=as_tenant.id,
            usuario_id=as_user.id,
            rol="TUTOR",
            comisiones=[],
            desde=today - timedelta(days=60),
            hasta=today - timedelta(days=1),  # expired yesterday
        )
        session.add(asig_expired)
        await session.commit()
        expired_id = asig_expired.id

    async with test_session_factory() as session:
        repo = AsignacionRepository(session, as_tenant.id)
        vigentes = await repo.get_vigentes_by_usuario(as_user.id)

    ids = [str(a.id) for a in vigentes]
    assert str(expired_id) not in ids


@pytest.mark.anyio
async def test_future_assignment_not_in_vigentes_today(
    test_session_factory: async_sessionmaker[AsyncSession],
    as_tenant: TenantInfo,
    as_user: UserInfo,
):
    """TRIANGULATE: assignment that hasn't started yet is NOT vigente today."""
    from app.repositories.asignacion import AsignacionRepository

    today = date.today()
    async with test_session_factory() as session:
        asig_future = Asignacion(
            id=uuid.uuid4(),
            tenant_id=as_tenant.id,
            usuario_id=as_user.id,
            rol="ALUMNO",
            comisiones=[],
            desde=today + timedelta(days=10),  # starts in the future
            hasta=None,
        )
        session.add(asig_future)
        await session.commit()
        future_id = asig_future.id

    async with test_session_factory() as session:
        repo = AsignacionRepository(session, as_tenant.id)
        vigentes = await repo.get_vigentes_by_usuario(as_user.id)

    ids = [str(a.id) for a in vigentes]
    assert str(future_id) not in ids


@pytest.mark.anyio
async def test_list_by_usuario_includes_expired(
    test_session_factory: async_sessionmaker[AsyncSession],
    as_tenant: TenantInfo,
    as_user: UserInfo,
):
    """TRIANGULATE: list_by_usuario returns ALL assignments including expired."""
    from app.repositories.asignacion import AsignacionRepository

    today = date.today()
    async with test_session_factory() as session:
        asig = Asignacion(
            id=uuid.uuid4(),
            tenant_id=as_tenant.id,
            usuario_id=as_user.id,
            rol="COORDINADOR",
            comisiones=[],
            desde=today - timedelta(days=90),
            hasta=today - timedelta(days=30),  # expired
        )
        session.add(asig)
        await session.commit()
        old_id = asig.id

    async with test_session_factory() as session:
        repo = AsignacionRepository(session, as_tenant.id)
        all_asigs = await repo.list_by_usuario(as_user.id)

    ids = [str(a.id) for a in all_asigs]
    assert str(old_id) in ids
