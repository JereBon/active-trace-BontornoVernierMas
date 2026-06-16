"""tests/test_rbac.py — RBAC tests (C-04: rbac-permisos-finos).

TDD cycles:
  7.1  Fixtures: tenant, usuario with PROFESOR role, usuario with COORDINADOR
       role, usuario with no roles, test endpoint guarded with
       require_permission.
  7.2  RED→GREEN: user with correct permission → HTTP 200
  7.3  RED→GREEN: user without permission → HTTP 403
  7.4  RED→GREEN: user with two active roles → permisos_efectivos is the union
  7.5  RED→GREEN: expired role (vig_hasta < today) → no permissions → HTTP 403
  7.6  RED→GREEN: seed idempotency — running seed twice does not duplicate rows
  7.7  Triangulation: user with no roles → empty permisos_efectivos → HTTP 403

Uses a real PostgreSQL test DB (DATABASE_URL_TEST). No DB mocking.
Fixtures are module-scoped to share the DB setup.
"""

import uuid
from dataclasses import dataclass
from datetime import date, timedelta

import pytest
import pytest_asyncio
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.permisos import CALIFICACIONES_IMPORTAR, COMUNICACION_APROBAR
from app.core.rbac import require_permission
from app.models.base import Base
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.tenant import Tenant  # noqa: F401 — needed for metadata/create_all
from app.models.usuario import Usuario
from app.models.usuario_rol import UsuarioRol


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_token(user_id: uuid.UUID) -> str:
    """Create a valid access token for *user_id* using test settings."""
    from datetime import timedelta

    from app.core.security import create_access_token

    return create_access_token(
        data={"sub": str(user_id), "tenant_id": str(uuid.uuid4())},
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


# ── Module-scoped DB setup ────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def db_tables(test_session_factory: async_sessionmaker[AsyncSession]):
    """Ensure all tables exist in the test DB."""
    from app.core import database as db_module

    engine = db_module.engine
    assert engine is not None

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Do NOT drop tables here — shared across all test modules.
    # Tables are recreated by create_all (idempotent).


@pytest_asyncio.fixture(scope="module")
async def rbac_tenant(
    test_session_factory: async_sessionmaker[AsyncSession],
    db_tables,
) -> TenantInfo:
    """Create a tenant for RBAC tests."""
    async with test_session_factory() as session:
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"rbac-tenant-{uuid.uuid4().hex[:8]}",
            nombre="RBAC Test Tenant",
        )
        session.add(tenant)
        await session.commit()
        return TenantInfo(id=tenant.id, slug=tenant.slug, nombre=tenant.nombre)


@pytest_asyncio.fixture(scope="module")
async def rbac_seed(
    test_session_factory: async_sessionmaker[AsyncSession],
    rbac_tenant: TenantInfo,
) -> dict:
    """Seed roles and permissions for the rbac_tenant.

    Returns a dict with:
      - rol_ids: {codigo: uuid}
      - permiso_ids: {codigo: uuid}
    """
    # Permisos to seed (subset relevant to tests)
    permisos_data = [
        (CALIFICACIONES_IMPORTAR, "Importar calificaciones"),
        (COMUNICACION_APROBAR, "Aprobar comunicaciones"),
        ("comunicacion:enviar", "Enviar comunicaciones"),
    ]
    roles_data = {
        "PROFESOR": [CALIFICACIONES_IMPORTAR, "comunicacion:enviar"],
        "COORDINADOR": [CALIFICACIONES_IMPORTAR, COMUNICACION_APROBAR, "comunicacion:enviar"],
    }

    rol_ids: dict[str, uuid.UUID] = {}
    permiso_ids: dict[str, uuid.UUID] = {}

    async with test_session_factory() as session:
        # Insert permisos
        for codigo, desc in permisos_data:
            p = Permiso(
                id=uuid.uuid4(),
                tenant_id=rbac_tenant.id,
                codigo=codigo,
                descripcion=desc,
            )
            session.add(p)
            permiso_ids[codigo] = p.id

        await session.flush()

        # Insert roles
        for rol_codigo, perm_codigos in roles_data.items():
            r = Rol(
                id=uuid.uuid4(),
                tenant_id=rbac_tenant.id,
                codigo=rol_codigo,
                nombre=rol_codigo.capitalize(),
            )
            session.add(r)
            await session.flush()
            rol_ids[rol_codigo] = r.id

            for perm_codigo in perm_codigos:
                rp = RolPermiso(
                    id=uuid.uuid4(),
                    tenant_id=rbac_tenant.id,
                    rol_id=r.id,
                    permiso_id=permiso_ids[perm_codigo],
                )
                session.add(rp)

        await session.commit()

    return {"rol_ids": rol_ids, "permiso_ids": permiso_ids}


def _create_usuario_sync(tenant_id: uuid.UUID) -> dict:
    """Build the kwargs dict for a minimal Usuario."""
    from app.core.security import hash_password, email_hash as _email_hash

    raw_email = f"user-{uuid.uuid4().hex[:8]}@test.com"
    return {
        "id": uuid.uuid4(),
        "tenant_id": tenant_id,
        "email_cifrado": "placeholder-encrypted",
        "email_hash": _email_hash(raw_email),
        "password_hash": hash_password("testpassword123"),
        "activo": True,
    }


@pytest_asyncio.fixture(scope="module")
async def user_profesor(
    test_session_factory: async_sessionmaker[AsyncSession],
    rbac_tenant: TenantInfo,
    rbac_seed: dict,
) -> UserInfo:
    """Usuario with active PROFESOR role."""
    kwargs = _create_usuario_sync(rbac_tenant.id)
    user_id = kwargs["id"]

    async with test_session_factory() as session:
        u = Usuario(**kwargs)
        session.add(u)
        await session.flush()

        ur = UsuarioRol(
            id=uuid.uuid4(),
            tenant_id=rbac_tenant.id,
            usuario_id=user_id,
            rol_id=rbac_seed["rol_ids"]["PROFESOR"],
            vig_desde=date.today() - timedelta(days=30),
            vig_hasta=None,  # no expiry
        )
        session.add(ur)
        await session.commit()

    token = _make_token(user_id)
    return UserInfo(id=user_id, tenant_id=rbac_tenant.id, token=token)


@pytest_asyncio.fixture(scope="module")
async def user_coordinador(
    test_session_factory: async_sessionmaker[AsyncSession],
    rbac_tenant: TenantInfo,
    rbac_seed: dict,
) -> UserInfo:
    """Usuario with active COORDINADOR role."""
    kwargs = _create_usuario_sync(rbac_tenant.id)
    user_id = kwargs["id"]

    async with test_session_factory() as session:
        u = Usuario(**kwargs)
        session.add(u)
        await session.flush()

        ur = UsuarioRol(
            id=uuid.uuid4(),
            tenant_id=rbac_tenant.id,
            usuario_id=user_id,
            rol_id=rbac_seed["rol_ids"]["COORDINADOR"],
            vig_desde=date.today() - timedelta(days=30),
            vig_hasta=None,
        )
        session.add(ur)
        await session.commit()

    token = _make_token(user_id)
    return UserInfo(id=user_id, tenant_id=rbac_tenant.id, token=token)


@pytest_asyncio.fixture(scope="module")
async def user_sin_roles(
    test_session_factory: async_sessionmaker[AsyncSession],
    rbac_tenant: TenantInfo,
) -> UserInfo:
    """Usuario with no role assignments."""
    kwargs = _create_usuario_sync(rbac_tenant.id)
    user_id = kwargs["id"]

    async with test_session_factory() as session:
        u = Usuario(**kwargs)
        session.add(u)
        await session.commit()

    token = _make_token(user_id)
    return UserInfo(id=user_id, tenant_id=rbac_tenant.id, token=token)


@pytest_asyncio.fixture(scope="module")
async def user_dos_roles(
    test_session_factory: async_sessionmaker[AsyncSession],
    rbac_tenant: TenantInfo,
    rbac_seed: dict,
) -> UserInfo:
    """Usuario with both PROFESOR and COORDINADOR roles active."""
    kwargs = _create_usuario_sync(rbac_tenant.id)
    user_id = kwargs["id"]

    async with test_session_factory() as session:
        u = Usuario(**kwargs)
        session.add(u)
        await session.flush()

        for rol_codigo in ("PROFESOR", "COORDINADOR"):
            ur = UsuarioRol(
                id=uuid.uuid4(),
                tenant_id=rbac_tenant.id,
                usuario_id=user_id,
                rol_id=rbac_seed["rol_ids"][rol_codigo],
                vig_desde=date.today() - timedelta(days=30),
                vig_hasta=None,
            )
            session.add(ur)

        await session.commit()

    token = _make_token(user_id)
    return UserInfo(id=user_id, tenant_id=rbac_tenant.id, token=token)


@pytest_asyncio.fixture(scope="module")
async def user_rol_vencido(
    test_session_factory: async_sessionmaker[AsyncSession],
    rbac_tenant: TenantInfo,
    rbac_seed: dict,
) -> UserInfo:
    """Usuario whose PROFESOR role expired yesterday."""
    kwargs = _create_usuario_sync(rbac_tenant.id)
    user_id = kwargs["id"]

    async with test_session_factory() as session:
        u = Usuario(**kwargs)
        session.add(u)
        await session.flush()

        ur = UsuarioRol(
            id=uuid.uuid4(),
            tenant_id=rbac_tenant.id,
            usuario_id=user_id,
            rol_id=rbac_seed["rol_ids"]["PROFESOR"],
            vig_desde=date.today() - timedelta(days=30),
            vig_hasta=date.today() - timedelta(days=1),  # expired yesterday
        )
        session.add(ur)
        await session.commit()

    token = _make_token(user_id)
    return UserInfo(id=user_id, tenant_id=rbac_tenant.id, token=token)


# ── Test FastAPI app with guarded endpoint ────────────────────────────────────


def _build_test_app(test_database_url: str) -> FastAPI:
    """Build a minimal FastAPI app with a guarded endpoint for RBAC tests."""
    import os

    os.environ.setdefault("DATABASE_URL", test_database_url)
    os.environ.setdefault("SECRET_KEY", "test-secret-key-32-characters-ok!")
    os.environ.setdefault("ENCRYPTION_KEY", "0" * 64)

    from app.core.config import _reset_settings

    _reset_settings()

    from app.main import create_application

    app = create_application()

    # Add a test-only endpoint guarded by require_permission
    @app.get(
        "/test/calificaciones",
        dependencies=[Depends(require_permission(CALIFICACIONES_IMPORTAR))],
    )
    async def _endpoint_calificaciones():
        return {"ok": True}

    @app.get(
        "/test/aprobar",
        dependencies=[Depends(require_permission(COMUNICACION_APROBAR))],
    )
    async def _endpoint_aprobar():
        return {"ok": True}

    return app


@pytest_asyncio.fixture(scope="module")
async def rbac_client(
    test_database_url: str,
) -> AsyncClient:
    """httpx AsyncClient wired to the test app with guarded endpoints."""
    from asgi_lifespan import LifespanManager

    app = _build_test_app(test_database_url)

    async with LifespanManager(app) as manager:
        async with AsyncClient(
            transport=ASGITransport(app=manager.app),
            base_url="http://testserver",
        ) as client:
            yield client


# ── 7.2 User with correct permission → HTTP 200 ───────────────────────────────


class TestPermisoOtorga200:
    """RED→GREEN: usuario with the required permission gets through."""

    @pytest.mark.asyncio
    async def test_profesor_puede_importar_calificaciones(
        self,
        rbac_client: AsyncClient,
        user_profesor: UserInfo,
    ):
        """PROFESOR has calificaciones:importar → endpoint returns 200."""
        response = await rbac_client.get(
            "/test/calificaciones",
            headers={"Authorization": f"Bearer {user_profesor.token}"},
        )
        assert response.status_code == 200, response.text


# ── 7.3 User without permission → HTTP 403 ───────────────────────────────────


class TestPermisoFaltante403:
    """RED→GREEN: usuario without permission is denied."""

    @pytest.mark.asyncio
    async def test_profesor_no_puede_aprobar_comunicacion(
        self,
        rbac_client: AsyncClient,
        user_profesor: UserInfo,
    ):
        """PROFESOR does NOT have comunicacion:aprobar → endpoint returns 403."""
        response = await rbac_client.get(
            "/test/aprobar",
            headers={"Authorization": f"Bearer {user_profesor.token}"},
        )
        assert response.status_code == 403, response.text

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(
        self,
        rbac_client: AsyncClient,
    ):
        """No Bearer token → 401 before permission check."""
        response = await rbac_client.get("/test/calificaciones")
        assert response.status_code == 401, response.text


# ── 7.4 Two active roles → union of permissions ───────────────────────────────


class TestDosRolesUnion:
    """RED→GREEN: effective permissions are the union of both roles."""

    @pytest.mark.asyncio
    async def test_dos_roles_otorgan_union_de_permisos(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        user_dos_roles: UserInfo,
        rbac_tenant: TenantInfo,
    ):
        """User with PROFESOR + COORDINADOR has union of both roles' permissions."""
        from app.repositories.usuario_rol import UsuarioRolRepository

        async with test_session_factory() as session:
            repo = UsuarioRolRepository(session, rbac_tenant.id)
            permisos = await repo.get_permisos_efectivos(user_dos_roles.id)

        # COORDINADOR has comunicacion:aprobar; PROFESOR does not
        assert COMUNICACION_APROBAR in permisos
        # Both roles have calificaciones:importar
        assert CALIFICACIONES_IMPORTAR in permisos

    @pytest.mark.asyncio
    async def test_dos_roles_http_200_para_permiso_solo_coordinador(
        self,
        rbac_client: AsyncClient,
        user_dos_roles: UserInfo,
    ):
        """User with PROFESOR+COORDINADOR can access endpoint guarded by
        comunicacion:aprobar (which only COORDINADOR has)."""
        response = await rbac_client.get(
            "/test/aprobar",
            headers={"Authorization": f"Bearer {user_dos_roles.token}"},
        )
        assert response.status_code == 200, response.text


# ── 7.5 Expired role → no permissions → HTTP 403 ─────────────────────────────


class TestRolVencidoNoOtorgaPermisos:
    """RED→GREEN: expired role assignment must NOT grant permissions."""

    @pytest.mark.asyncio
    async def test_rol_vencido_no_en_permisos_efectivos(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        user_rol_vencido: UserInfo,
        rbac_tenant: TenantInfo,
    ):
        """Expired role → permisos_efectivos is empty."""
        from app.repositories.usuario_rol import UsuarioRolRepository

        async with test_session_factory() as session:
            repo = UsuarioRolRepository(session, rbac_tenant.id)
            permisos = await repo.get_permisos_efectivos(user_rol_vencido.id)

        assert len(permisos) == 0

    @pytest.mark.asyncio
    async def test_rol_vencido_http_403(
        self,
        rbac_client: AsyncClient,
        user_rol_vencido: UserInfo,
    ):
        """User whose role expired → HTTP 403 on protected endpoint."""
        response = await rbac_client.get(
            "/test/calificaciones",
            headers={"Authorization": f"Bearer {user_rol_vencido.token}"},
        )
        assert response.status_code == 403, response.text


# ── 7.6 Seed idempotency ──────────────────────────────────────────────────────


class TestSeedIdempotencia:
    """RED→GREEN: running seed twice must not duplicate rows."""

    @pytest.mark.asyncio
    async def test_seed_dos_veces_no_duplica_filas(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        rbac_tenant: TenantInfo,
        rbac_seed: dict,
    ):
        """Inserting the same permissions + roles again must not create duplicates."""
        from sqlalchemy import select, func

        # Count rows before second seed
        async with test_session_factory() as session:
            result = await session.execute(
                select(func.count()).where(Permiso.tenant_id == rbac_tenant.id)
            )
            count_before = result.scalar_one()

        # "Seed again" by inserting the same rows (ON CONFLICT DO NOTHING)
        async with test_session_factory() as session:
            from sqlalchemy.dialects.postgresql import insert as pg_insert

            for codigo, desc in [
                (CALIFICACIONES_IMPORTAR, "Importar calificaciones"),
                (COMUNICACION_APROBAR, "Aprobar comunicaciones"),
            ]:
                stmt = pg_insert(Permiso).values(
                    id=uuid.uuid4(),
                    tenant_id=rbac_tenant.id,
                    codigo=codigo,
                    descripcion=desc,
                ).on_conflict_do_nothing(constraint="uq_permisos_tenant_codigo")
                await session.execute(stmt)
            await session.commit()

        # Count must be the same
        async with test_session_factory() as session:
            result = await session.execute(
                select(func.count()).where(Permiso.tenant_id == rbac_tenant.id)
            )
            count_after = result.scalar_one()

        assert count_after == count_before


# ── 7.7 Triangulation: no roles → empty permissions → 403 ────────────────────


class TestSinRoles403:
    """Triangulation: user with no roles → permisos_efectivos empty → HTTP 403."""

    @pytest.mark.asyncio
    async def test_sin_roles_permisos_efectivos_vacio(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        user_sin_roles: UserInfo,
        rbac_tenant: TenantInfo,
    ):
        """No role assignments → empty permisos_efectivos set."""
        from app.repositories.usuario_rol import UsuarioRolRepository

        async with test_session_factory() as session:
            repo = UsuarioRolRepository(session, rbac_tenant.id)
            permisos = await repo.get_permisos_efectivos(user_sin_roles.id)

        assert permisos == set()

    @pytest.mark.asyncio
    async def test_sin_roles_http_403_en_endpoint_guardado(
        self,
        rbac_client: AsyncClient,
        user_sin_roles: UserInfo,
    ):
        """User with no roles → HTTP 403 on any guarded endpoint."""
        response = await rbac_client.get(
            "/test/calificaciones",
            headers={"Authorization": f"Bearer {user_sin_roles.token}"},
        )
        assert response.status_code == 403, response.text

    @pytest.mark.asyncio
    async def test_sin_roles_http_403_en_otro_endpoint(
        self,
        rbac_client: AsyncClient,
        user_sin_roles: UserInfo,
    ):
        """User with no roles → HTTP 403 on a different guarded endpoint."""
        response = await rbac_client.get(
            "/test/aprobar",
            headers={"Authorization": f"Bearer {user_sin_roles.token}"},
        )
        assert response.status_code == 403, response.text
