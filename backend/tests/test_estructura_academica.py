"""tests/test_estructura_academica.py — Tests for C-06: estructura-academica.

TDD cycles:
  7.2  RED→GREEN: create Carrera → 201; verify in DB
  7.3  RED→GREEN: create Carrera with duplicate codigo → 409
  7.4  RED→GREEN: soft delete Carrera → 204; not visible in list
  7.5  RED→GREEN: access without estructura:gestionar → 403
  7.6  RED→GREEN: create Cohorte → 201; duplicate (tenant, carrera, nombre) → 409
  7.7  RED→GREEN: create Cohorte with carrera_id from another tenant → 404
  7.8  RED→GREEN: create Materia → 201; duplicate codigo → 409; soft delete → 204

Uses a real PostgreSQL test DB (DATABASE_URL_TEST). No DB mocking.
Fixtures are module-scoped to share the DB setup.
"""

import uuid
from dataclasses import dataclass
from datetime import date, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.permisos import ESTRUCTURA_GESTIONAR
from app.models.base import Base
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.tenant import Tenant  # noqa: F401 — needed for metadata/create_all
from app.models.usuario import Usuario
from app.models.usuario_rol import UsuarioRol


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_token(user_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
    """Create a valid access token for *user_id* with the correct *tenant_id*."""
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


# ── Module-scoped DB setup ────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def db_tables(test_session_factory: async_sessionmaker[AsyncSession]):
    """Ensure all tables exist in the test DB (idempotent create_all)."""
    from app.core import database as db_module

    engine = db_module.engine
    assert engine is not None

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield
    # Do NOT drop here — shared across test modules


@pytest_asyncio.fixture(scope="module")
async def ea_tenant(
    test_session_factory: async_sessionmaker[AsyncSession],
    db_tables,
) -> TenantInfo:
    """Create a tenant for estructura-academica tests."""
    async with test_session_factory() as session:
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"ea-tenant-{uuid.uuid4().hex[:8]}",
            nombre="EA Test Tenant",
        )
        session.add(tenant)
        await session.commit()
        return TenantInfo(id=tenant.id, slug=tenant.slug, nombre=tenant.nombre)


@pytest_asyncio.fixture(scope="module")
async def ea_seed(
    test_session_factory: async_sessionmaker[AsyncSession],
    ea_tenant: TenantInfo,
) -> dict:
    """Seed 'estructura:gestionar' permission and an ADMIN role for ea_tenant."""
    async with test_session_factory() as session:
        p = Permiso(
            id=uuid.uuid4(),
            tenant_id=ea_tenant.id,
            codigo=ESTRUCTURA_GESTIONAR,
            descripcion="Gestionar estructura académica",
        )
        session.add(p)
        await session.flush()

        r = Rol(
            id=uuid.uuid4(),
            tenant_id=ea_tenant.id,
            codigo="ADMIN",
            nombre="Administrador",
        )
        session.add(r)
        await session.flush()

        rp = RolPermiso(
            id=uuid.uuid4(),
            tenant_id=ea_tenant.id,
            rol_id=r.id,
            permiso_id=p.id,
        )
        session.add(rp)
        await session.commit()
        return {"rol_id": r.id, "permiso_id": p.id}


def _create_usuario_kwargs(tenant_id: uuid.UUID) -> dict:
    """Build minimal Usuario kwargs."""
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
async def admin_user(
    test_session_factory: async_sessionmaker[AsyncSession],
    ea_tenant: TenantInfo,
    ea_seed: dict,
) -> UserInfo:
    """Create a user with ADMIN role (has estructura:gestionar)."""
    kwargs = _create_usuario_kwargs(ea_tenant.id)
    user_id = kwargs["id"]

    async with test_session_factory() as session:
        u = Usuario(**kwargs)
        session.add(u)
        await session.flush()

        ur = UsuarioRol(
            id=uuid.uuid4(),
            tenant_id=ea_tenant.id,
            usuario_id=user_id,
            rol_id=ea_seed["rol_id"],
            vig_desde=date.today() - timedelta(days=30),
            vig_hasta=None,
        )
        session.add(ur)
        await session.commit()

    token = _make_token(user_id, ea_tenant.id)
    return UserInfo(id=user_id, tenant_id=ea_tenant.id, token=token)


@pytest_asyncio.fixture(scope="module")
async def nonadmin_user(
    test_session_factory: async_sessionmaker[AsyncSession],
    ea_tenant: TenantInfo,
    ea_seed: dict,
) -> UserInfo:
    """Create a user with no roles (no permissions)."""
    kwargs = _create_usuario_kwargs(ea_tenant.id)
    user_id = kwargs["id"]

    async with test_session_factory() as session:
        u = Usuario(**kwargs)
        session.add(u)
        await session.commit()

    token = _make_token(user_id, ea_tenant.id)
    return UserInfo(id=user_id, tenant_id=ea_tenant.id, token=token)


@pytest_asyncio.fixture(scope="module")
async def other_tenant(
    test_session_factory: async_sessionmaker[AsyncSession],
    db_tables,
) -> TenantInfo:
    """A second tenant used to test cross-tenant isolation."""
    async with test_session_factory() as session:
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"other-tenant-{uuid.uuid4().hex[:8]}",
            nombre="Other Tenant",
        )
        session.add(tenant)
        await session.commit()
        return TenantInfo(id=tenant.id, slug=tenant.slug, nombre=tenant.nombre)


# ── Test app client ───────────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def test_client(test_session_factory: async_sessionmaker[AsyncSession]) -> AsyncClient:
    """httpx client against the FastAPI app using the test DB."""
    import os
    from asgi_lifespan import LifespanManager
    from app.core.config import _reset_settings
    from app.main import create_application

    test_db_url = os.environ.get(
        "DATABASE_URL_TEST",
        "postgresql+asyncpg://activia:changeme@localhost:5432/activia_trace_test",
    )

    # Reset settings singleton to pick up the test DB URL
    os.environ["DATABASE_URL"] = test_db_url
    os.environ["SECRET_KEY"] = "test-secret-key-32-characters-ok!"
    os.environ["ENCRYPTION_KEY"] = "0" * 64
    _reset_settings()

    app = create_application()

    async with LifespanManager(app) as manager:
        async with AsyncClient(
            transport=ASGITransport(app=manager.app),
            base_url="http://testserver",
        ) as client:
            yield client


# ── 7.2 Create Carrera ────────────────────────────────────────────────────────


class TestCarreraCreate:
    """Create Carrera → 201; verify record returned with correct fields."""

    @pytest.mark.asyncio
    async def test_create_carrera_success(
        self,
        test_client: AsyncClient,
        admin_user: UserInfo,
    ) -> None:
        """Scenario: Create Carrera with valid data → 201 and resource in response."""
        codigo = f"CAR-{uuid.uuid4().hex[:6].upper()}"
        resp = await test_client.post(
            "/v1/carreras",
            json={"codigo": codigo, "nombre": "Ingeniería en Sistemas", "estado": "Activa"},
            headers={"Authorization": f"Bearer {admin_user.token}"},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["codigo"] == codigo
        assert data["nombre"] == "Ingeniería en Sistemas"
        assert data["estado"] == "Activa"
        assert data["deleted_at"] is None
        assert uuid.UUID(data["id"])

    @pytest.mark.asyncio
    async def test_create_carrera_appears_in_list(
        self,
        test_client: AsyncClient,
        admin_user: UserInfo,
    ) -> None:
        """Triangulation: created Carrera appears in GET /v1/carreras."""
        codigo = f"LST-{uuid.uuid4().hex[:6].upper()}"
        await test_client.post(
            "/v1/carreras",
            json={"codigo": codigo, "nombre": "Licenciatura en Sistemas", "estado": "Activa"},
            headers={"Authorization": f"Bearer {admin_user.token}"},
        )
        resp = await test_client.get(
            "/v1/carreras",
            headers={"Authorization": f"Bearer {admin_user.token}"},
        )
        assert resp.status_code == 200
        codigos = [c["codigo"] for c in resp.json()]
        assert codigo in codigos


# ── 7.3 Carrera duplicate codigo → 409 ───────────────────────────────────────


class TestCarreraUniqueness:
    """Duplicate (tenant_id, codigo) must return 409 Conflict."""

    @pytest.mark.asyncio
    async def test_duplicate_codigo_returns_409(
        self,
        test_client: AsyncClient,
        admin_user: UserInfo,
    ) -> None:
        """Scenario: Segunda Carrera con mismo codigo → 409."""
        codigo = f"DUP-{uuid.uuid4().hex[:6].upper()}"
        await test_client.post(
            "/v1/carreras",
            json={"codigo": codigo, "nombre": "Primera"},
            headers={"Authorization": f"Bearer {admin_user.token}"},
        )
        resp = await test_client.post(
            "/v1/carreras",
            json={"codigo": codigo, "nombre": "Segunda"},
            headers={"Authorization": f"Bearer {admin_user.token}"},
        )
        assert resp.status_code == 409, resp.text


# ── 7.4 Soft delete Carrera ───────────────────────────────────────────────────


class TestCarreraSoftDelete:
    """DELETE /v1/carreras/{id} → 204; not visible in list."""

    @pytest.mark.asyncio
    async def test_soft_delete_returns_204(
        self,
        test_client: AsyncClient,
        admin_user: UserInfo,
    ) -> None:
        """Scenario: Soft-delete Carrera → 204 and removed from list."""
        # Create
        codigo = f"DEL-{uuid.uuid4().hex[:6].upper()}"
        create_resp = await test_client.post(
            "/v1/carreras",
            json={"codigo": codigo, "nombre": "To delete"},
            headers={"Authorization": f"Bearer {admin_user.token}"},
        )
        assert create_resp.status_code == 201
        carrera_id = create_resp.json()["id"]

        # Delete
        del_resp = await test_client.delete(
            f"/v1/carreras/{carrera_id}",
            headers={"Authorization": f"Bearer {admin_user.token}"},
        )
        assert del_resp.status_code == 204

        # Verify not in list
        list_resp = await test_client.get(
            "/v1/carreras",
            headers={"Authorization": f"Bearer {admin_user.token}"},
        )
        ids = [c["id"] for c in list_resp.json()]
        assert carrera_id not in ids

    @pytest.mark.asyncio
    async def test_soft_delete_same_codigo_can_be_reused(
        self,
        test_client: AsyncClient,
        admin_user: UserInfo,
    ) -> None:
        """Triangulation: After soft delete, the same codigo can be reused."""
        codigo = f"RSU-{uuid.uuid4().hex[:6].upper()}"
        create_resp = await test_client.post(
            "/v1/carreras",
            json={"codigo": codigo, "nombre": "First"},
            headers={"Authorization": f"Bearer {admin_user.token}"},
        )
        carrera_id = create_resp.json()["id"]
        await test_client.delete(
            f"/v1/carreras/{carrera_id}",
            headers={"Authorization": f"Bearer {admin_user.token}"},
        )
        # Create again with same codigo → should succeed
        resp2 = await test_client.post(
            "/v1/carreras",
            json={"codigo": codigo, "nombre": "Second"},
            headers={"Authorization": f"Bearer {admin_user.token}"},
        )
        assert resp2.status_code == 201, resp2.text


# ── 7.5 Access without permission → 403 ──────────────────────────────────────


class TestAccessControl:
    """Endpoints must return 403 for users without estructura:gestionar."""

    @pytest.mark.asyncio
    async def test_list_without_permission_returns_403(
        self,
        test_client: AsyncClient,
        nonadmin_user: UserInfo,
    ) -> None:
        """Scenario: User without estructura:gestionar → 403 on GET /v1/carreras."""
        resp = await test_client.get(
            "/v1/carreras",
            headers={"Authorization": f"Bearer {nonadmin_user.token}"},
        )
        assert resp.status_code == 403, resp.text

    @pytest.mark.asyncio
    async def test_create_without_permission_returns_403(
        self,
        test_client: AsyncClient,
        nonadmin_user: UserInfo,
    ) -> None:
        """Scenario: User without estructura:gestionar → 403 on POST /v1/carreras."""
        resp = await test_client.post(
            "/v1/carreras",
            json={"codigo": "NOPERM", "nombre": "No Permission"},
            headers={"Authorization": f"Bearer {nonadmin_user.token}"},
        )
        assert resp.status_code == 403, resp.text

    @pytest.mark.asyncio
    async def test_materias_without_permission_returns_403(
        self,
        test_client: AsyncClient,
        nonadmin_user: UserInfo,
    ) -> None:
        """Triangulation: same 403 guard applies to /v1/materias."""
        resp = await test_client.get(
            "/v1/materias",
            headers={"Authorization": f"Bearer {nonadmin_user.token}"},
        )
        assert resp.status_code == 403, resp.text


# ── 7.6 Cohorte create and uniqueness ─────────────────────────────────────────


class TestCohorteCreate:
    """Create Cohorte → 201; duplicate (tenant, carrera, nombre) → 409."""

    @pytest.mark.asyncio
    async def test_create_cohorte_success(
        self,
        test_client: AsyncClient,
        admin_user: UserInfo,
    ) -> None:
        """Scenario: Create Carrera then Cohorte → 201."""
        # Create parent Carrera
        car_resp = await test_client.post(
            "/v1/carreras",
            json={"codigo": f"COH-{uuid.uuid4().hex[:6].upper()}", "nombre": "Carrera para Cohorte"},
            headers={"Authorization": f"Bearer {admin_user.token}"},
        )
        assert car_resp.status_code == 201
        carrera_id = car_resp.json()["id"]

        # Create Cohorte
        resp = await test_client.post(
            "/v1/cohortes",
            json={
                "carrera_id": carrera_id,
                "nombre": "AGO-2025",
                "anio": 2025,
                "vig_desde": "2025-08-01",
            },
            headers={"Authorization": f"Bearer {admin_user.token}"},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["nombre"] == "AGO-2025"
        assert data["carrera_id"] == carrera_id

    @pytest.mark.asyncio
    async def test_duplicate_cohorte_returns_409(
        self,
        test_client: AsyncClient,
        admin_user: UserInfo,
    ) -> None:
        """Scenario: Duplicate (tenant, carrera, nombre) → 409."""
        car_resp = await test_client.post(
            "/v1/carreras",
            json={"codigo": f"CD2-{uuid.uuid4().hex[:6].upper()}", "nombre": "Carrera Dup Cohorte"},
            headers={"Authorization": f"Bearer {admin_user.token}"},
        )
        carrera_id = car_resp.json()["id"]

        payload = {
            "carrera_id": carrera_id,
            "nombre": "MAR-2026",
            "anio": 2026,
            "vig_desde": "2026-03-01",
        }
        await test_client.post(
            "/v1/cohortes", json=payload,
            headers={"Authorization": f"Bearer {admin_user.token}"},
        )
        resp2 = await test_client.post(
            "/v1/cohortes", json=payload,
            headers={"Authorization": f"Bearer {admin_user.token}"},
        )
        assert resp2.status_code == 409, resp2.text


# ── 7.7 Cohorte with carrera_id from other tenant → 404 ──────────────────────


class TestCohorteOtherTenant:
    """Creating a Cohorte with a carrera_id from another tenant must return 404."""

    @pytest_asyncio.fixture(scope="class")
    async def carrera_in_other_tenant(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        other_tenant: TenantInfo,
        db_tables,
    ) -> str:
        """Create a Carrera directly in the other_tenant (bypassing the API)."""
        from app.models.carrera import Carrera

        async with test_session_factory() as session:
            c = Carrera(
                id=uuid.uuid4(),
                tenant_id=other_tenant.id,
                codigo=f"XTC-{uuid.uuid4().hex[:6].upper()}",
                nombre="Carrera de otro tenant",
                estado="Activa",
            )
            session.add(c)
            await session.commit()
            return str(c.id)

    @pytest.mark.asyncio
    async def test_cohorte_with_foreign_carrera_returns_404(
        self,
        test_client: AsyncClient,
        admin_user: UserInfo,
        carrera_in_other_tenant: str,
    ) -> None:
        """Scenario: carrera_id from another tenant → 404 (not visible in tenant)."""
        resp = await test_client.post(
            "/v1/cohortes",
            json={
                "carrera_id": carrera_in_other_tenant,
                "nombre": "XTEN-2025",
                "anio": 2025,
                "vig_desde": "2025-01-01",
            },
            headers={"Authorization": f"Bearer {admin_user.token}"},
        )
        assert resp.status_code == 404, resp.text


# ── 7.8 Materia CRUD ──────────────────────────────────────────────────────────


class TestMateriaCRUD:
    """Create Materia → 201; duplicate codigo → 409; soft delete → 204."""

    @pytest.mark.asyncio
    async def test_create_materia_success(
        self,
        test_client: AsyncClient,
        admin_user: UserInfo,
    ) -> None:
        """Scenario: Create Materia with valid data → 201."""
        codigo = f"MAT-{uuid.uuid4().hex[:6].upper()}"
        resp = await test_client.post(
            "/v1/materias",
            json={"codigo": codigo, "nombre": "Programación I"},
            headers={"Authorization": f"Bearer {admin_user.token}"},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["codigo"] == codigo
        assert data["deleted_at"] is None

    @pytest.mark.asyncio
    async def test_duplicate_materia_codigo_returns_409(
        self,
        test_client: AsyncClient,
        admin_user: UserInfo,
    ) -> None:
        """Scenario: duplicate codigo for Materia → 409."""
        codigo = f"DMT-{uuid.uuid4().hex[:6].upper()}"
        await test_client.post(
            "/v1/materias",
            json={"codigo": codigo, "nombre": "First"},
            headers={"Authorization": f"Bearer {admin_user.token}"},
        )
        resp2 = await test_client.post(
            "/v1/materias",
            json={"codigo": codigo, "nombre": "Second"},
            headers={"Authorization": f"Bearer {admin_user.token}"},
        )
        assert resp2.status_code == 409, resp2.text

    @pytest.mark.asyncio
    async def test_soft_delete_materia_returns_204(
        self,
        test_client: AsyncClient,
        admin_user: UserInfo,
    ) -> None:
        """Scenario: soft delete Materia → 204; not in list."""
        codigo = f"SDM-{uuid.uuid4().hex[:6].upper()}"
        create_resp = await test_client.post(
            "/v1/materias",
            json={"codigo": codigo, "nombre": "To delete materia"},
            headers={"Authorization": f"Bearer {admin_user.token}"},
        )
        materia_id = create_resp.json()["id"]

        del_resp = await test_client.delete(
            f"/v1/materias/{materia_id}",
            headers={"Authorization": f"Bearer {admin_user.token}"},
        )
        assert del_resp.status_code == 204

        list_resp = await test_client.get(
            "/v1/materias",
            headers={"Authorization": f"Bearer {admin_user.token}"},
        )
        ids = [m["id"] for m in list_resp.json()]
        assert materia_id not in ids
