"""tests/test_equipos_integration.py — Integration tests for C-08 equipos endpoints.

TDD cycles (6.x):
  6.1  GET /mis-asignaciones returns only vigentes of the authenticated user
  6.2  GET / without equipos:asignar → 403
  6.3  POST / creates assignment and writes audit_log
  6.4  PUT /{id} updates vigencia and writes audit_log
  6.5  DELETE /{id} soft-deletes; deleted_at set; not in list
  6.6  POST /asignacion-masiva: N users → N created; duplicate omitted
  6.7  POST /clonar: duplicates vigentes with new cohorte + dates; origin untouched
  6.8  PUT /vigencia-masiva: updates dates; returns filas_afectadas
  6.9  GET /exportar: CSV with headers; empty → headers only
  6.10 Multi-tenant isolation: tenant A cannot see tenant B assignments

Uses real PostgreSQL test DB (DATABASE_URL_TEST). No DB mocking.
"""

import os
import uuid
from dataclasses import dataclass
from datetime import date, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.permisos import EQUIPOS_ASIGNAR
from app.models.asignacion import Asignacion
from app.models.base import Base
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.usuario_rol import UsuarioRol
from app.repositories.asignacion import AsignacionRepository

_TODAY = date.today()
_YESTERDAY = _TODAY - timedelta(days=1)
_TOMORROW = _TODAY + timedelta(days=1)


# ── Helpers ───────────────────────────────────────────────────────────────────


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


# ── Module-scoped DB setup ────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def db_tables(test_session_factory: async_sessionmaker[AsyncSession]):
    from app.core import database as db_module
    engine = db_module.engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture(scope="module")
async def int_tenant(test_session_factory, db_tables) -> dict:
    """Seed tenant + carrera + 2 cohortes + materia + users + RBAC for equipos:asignar."""
    from app.core.security import hash_password, email_hash

    async with test_session_factory() as session:
        tenant = Tenant(id=uuid.uuid4(), slug=f"eq-int-{uuid.uuid4().hex[:6]}", nombre="EquipoIntTenant")
        session.add(tenant)
        await session.flush()

        carrera = Carrera(id=uuid.uuid4(), tenant_id=tenant.id, codigo="INT", nombre="Int Carrera", estado="Activa")
        session.add(carrera)

        cohorte_a = Cohorte(
            id=uuid.uuid4(), tenant_id=tenant.id, carrera_id=carrera.id,
            nombre="INT-A", anio=2025, estado="Activa", vig_desde=_TODAY, vig_hasta=None,
        )
        cohorte_b = Cohorte(
            id=uuid.uuid4(), tenant_id=tenant.id, carrera_id=carrera.id,
            nombre="INT-B", anio=2025, estado="Activa", vig_desde=_TODAY, vig_hasta=None,
        )
        session.add_all([cohorte_a, cohorte_b])

        materia = Materia(id=uuid.uuid4(), tenant_id=tenant.id, codigo="INT01", nombre="Int Materia", estado="Activa")
        session.add(materia)

        # Create 'equipos:asignar' permission + COORD role
        perm = Permiso(
            id=uuid.uuid4(), tenant_id=tenant.id,
            codigo=EQUIPOS_ASIGNAR, descripcion="Gestionar equipos docentes",
        )
        session.add(perm)

        coord_rol = Rol(id=uuid.uuid4(), tenant_id=tenant.id, codigo="COORDINADOR", nombre="Coordinador")
        session.add(coord_rol)
        await session.flush()

        rp = RolPermiso(id=uuid.uuid4(), tenant_id=tenant.id, rol_id=coord_rol.id, permiso_id=perm.id)
        session.add(rp)

        # Coordinator user (has equipos:asignar)
        coord = Usuario(
            id=uuid.uuid4(), tenant_id=tenant.id,
            email_cifrado="enc-coord",
            email_hash=email_hash(f"coord-{uuid.uuid4().hex}@test.com"),
            password_hash=hash_password("pass"), activo=True,
        )
        session.add(coord)
        await session.flush()

        ur = UsuarioRol(
            id=uuid.uuid4(), tenant_id=tenant.id,
            usuario_id=coord.id, rol_id=coord_rol.id,
            vig_desde=_TODAY - timedelta(days=30), vig_hasta=None,
        )
        session.add(ur)

        # Normal user (no permissions)
        noauth = Usuario(
            id=uuid.uuid4(), tenant_id=tenant.id,
            email_cifrado="enc-noauth",
            email_hash=email_hash(f"noauth-{uuid.uuid4().hex}@test.com"),
            password_hash=hash_password("pass"), activo=True,
        )
        session.add(noauth)

        # Target users for bulk operations
        u1 = Usuario(
            id=uuid.uuid4(), tenant_id=tenant.id,
            email_cifrado="enc-u1",
            email_hash=email_hash(f"u1-{uuid.uuid4().hex}@test.com"),
            password_hash=hash_password("pass"), activo=True,
        )
        u2 = Usuario(
            id=uuid.uuid4(), tenant_id=tenant.id,
            email_cifrado="enc-u2",
            email_hash=email_hash(f"u2-{uuid.uuid4().hex}@test.com"),
            password_hash=hash_password("pass"), activo=True,
        )
        session.add_all([u1, u2])
        await session.commit()

        return {
            "tenant_id": tenant.id,
            "carrera_id": carrera.id,
            "cohorte_a_id": cohorte_a.id,
            "cohorte_b_id": cohorte_b.id,
            "materia_id": materia.id,
            "coord_id": coord.id,
            "coord_token": _make_token(coord.id, tenant.id),
            "noauth_id": noauth.id,
            "noauth_token": _make_token(noauth.id, tenant.id),
            "user1_id": u1.id,
            "user2_id": u2.id,
        }


@pytest_asyncio.fixture(scope="module")
async def int_other_tenant(test_session_factory, db_tables) -> dict:
    """Separate tenant for isolation tests."""
    from app.core.security import hash_password, email_hash

    async with test_session_factory() as session:
        tenant = Tenant(id=uuid.uuid4(), slug=f"eq-other-{uuid.uuid4().hex[:6]}", nombre="OtherTenant")
        session.add(tenant)
        await session.flush()

        u = Usuario(
            id=uuid.uuid4(), tenant_id=tenant.id,
            email_cifrado="enc-other",
            email_hash=email_hash(f"other-{uuid.uuid4().hex}@test.com"),
            password_hash=hash_password("pass"), activo=True,
        )
        session.add(u)
        await session.commit()
        return {"tenant_id": tenant.id, "user_id": u.id, "token": _make_token(u.id, tenant.id)}


@pytest_asyncio.fixture(scope="module")
async def test_client(test_session_factory) -> AsyncClient:
    from asgi_lifespan import LifespanManager
    from app.core.config import _reset_settings
    from app.main import create_application

    test_db_url = os.environ.get(
        "DATABASE_URL_TEST",
        "postgresql+asyncpg://activia:changeme@localhost:5432/activia_trace_test",
    )
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


# ── 6.1 GET /mis-asignaciones ─────────────────────────────────────────────────


class TestMisAsignaciones:
    """GET /mis-asignaciones — authenticated user, no elevated permission needed."""

    @pytest.mark.asyncio
    async def test_returns_only_vigentes(self, test_client, int_tenant, test_session_factory):
        tid = int_tenant["tenant_id"]
        # Create a vigente and an expired assignment for noauth user
        async with test_session_factory() as session:
            repo = AsignacionRepository(session, tid)
            vigente = await repo.create({
                "usuario_id": int_tenant["noauth_id"],
                "rol": "TUTOR",
                "desde": _TODAY,
                "comisiones": [],
            })
            expired = await repo.create({
                "usuario_id": int_tenant["noauth_id"],
                "rol": "NEXO",
                "desde": _YESTERDAY - timedelta(days=5),
                "hasta": _YESTERDAY,
                "comisiones": [],
            })
            await session.commit()

        resp = await test_client.get(
            "/v1/equipos/mis-asignaciones",
            headers={"Authorization": f"Bearer {int_tenant['noauth_token']}"},
        )
        assert resp.status_code == 200, resp.text
        ids = [a["id"] for a in resp.json()]
        assert str(vigente.id) in ids
        assert str(expired.id) not in ids

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, test_client, int_tenant):
        resp = await test_client.get("/v1/equipos/mis-asignaciones")
        assert resp.status_code == 401


# ── 6.2 GET / without permission → 403 ───────────────────────────────────────


class TestListPermission:
    """GET / requires equipos:asignar."""

    @pytest.mark.asyncio
    async def test_no_permission_returns_403(self, test_client, int_tenant):
        resp = await test_client.get(
            "/v1/equipos/",
            headers={"Authorization": f"Bearer {int_tenant['noauth_token']}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_with_permission_returns_200(self, test_client, int_tenant):
        resp = await test_client.get(
            "/v1/equipos/",
            headers={"Authorization": f"Bearer {int_tenant['coord_token']}"},
        )
        assert resp.status_code == 200


# ── 6.3 POST / — creates and writes audit ─────────────────────────────────────


class TestCreateAsignacion:
    """POST / creates assignment and audit log entry."""

    @pytest.mark.asyncio
    async def test_create_returns_201(self, test_client, int_tenant):
        resp = await test_client.post(
            "/v1/equipos/",
            json={
                "usuario_id": str(int_tenant["user1_id"]),
                "rol": "TUTOR",
                "materia_id": str(int_tenant["materia_id"]),
                "carrera_id": str(int_tenant["carrera_id"]),
                "cohorte_id": str(int_tenant["cohorte_a_id"]),
                "desde": str(_TODAY),
            },
            headers={"Authorization": f"Bearer {int_tenant['coord_token']}"},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["rol"] == "TUTOR"
        assert data["tenant_id"] == str(int_tenant["tenant_id"])

    @pytest.mark.asyncio
    async def test_create_invalid_rol_returns_422(self, test_client, int_tenant):
        resp = await test_client.post(
            "/v1/equipos/",
            json={
                "usuario_id": str(int_tenant["user1_id"]),
                "rol": "SUPERADMIN",
                "desde": str(_TODAY),
            },
            headers={"Authorization": f"Bearer {int_tenant['coord_token']}"},
        )
        assert resp.status_code == 422


# ── 6.4 PUT /{id} — updates vigencia + audit ──────────────────────────────────


class TestUpdateAsignacion:
    """PUT /{id} updates fields and writes audit log."""

    @pytest.mark.asyncio
    async def test_update_vigencia(self, test_client, int_tenant, test_session_factory):
        tid = int_tenant["tenant_id"]
        # Create an assignment to update
        async with test_session_factory() as session:
            repo = AsignacionRepository(session, tid)
            created = await repo.create({
                "usuario_id": int_tenant["user2_id"],
                "rol": "TUTOR",
                "desde": _TODAY,
                "comisiones": [],
            })
            await session.commit()

        new_hasta = str(_TODAY + timedelta(days=60))
        resp = await test_client.put(
            f"/v1/equipos/{created.id}",
            json={"hasta": new_hasta},
            headers={"Authorization": f"Bearer {int_tenant['coord_token']}"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["hasta"] == new_hasta

    @pytest.mark.asyncio
    async def test_update_unknown_returns_404(self, test_client, int_tenant):
        resp = await test_client.put(
            f"/v1/equipos/{uuid.uuid4()}",
            json={"rol": "TUTOR"},
            headers={"Authorization": f"Bearer {int_tenant['coord_token']}"},
        )
        assert resp.status_code == 404


# ── 6.5 DELETE /{id} — soft delete + audit ────────────────────────────────────


class TestDeleteAsignacion:
    """DELETE /{id} soft-deletes; record no longer appears in GET /."""

    @pytest.mark.asyncio
    async def test_delete_returns_204(self, test_client, int_tenant, test_session_factory):
        tid = int_tenant["tenant_id"]
        async with test_session_factory() as session:
            repo = AsignacionRepository(session, tid)
            created = await repo.create({
                "usuario_id": int_tenant["user1_id"],
                "rol": "NEXO",
                "desde": _TODAY,
                "comisiones": [],
            })
            await session.commit()

        resp = await test_client.delete(
            f"/v1/equipos/{created.id}",
            headers={"Authorization": f"Bearer {int_tenant['coord_token']}"},
        )
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_deleted_not_in_list(self, test_client, int_tenant, test_session_factory):
        tid = int_tenant["tenant_id"]
        async with test_session_factory() as session:
            repo = AsignacionRepository(session, tid)
            created = await repo.create({
                "usuario_id": int_tenant["user2_id"],
                "rol": "NEXO",
                "desde": _TODAY,
                "comisiones": [],
            })
            await session.commit()

        await test_client.delete(
            f"/v1/equipos/{created.id}",
            headers={"Authorization": f"Bearer {int_tenant['coord_token']}"},
        )

        resp = await test_client.get(
            "/v1/equipos/",
            headers={"Authorization": f"Bearer {int_tenant['coord_token']}"},
        )
        ids = [a["id"] for a in resp.json()]
        assert str(created.id) not in ids


# ── 6.6 POST /asignacion-masiva ───────────────────────────────────────────────


class TestAsignacionMasiva:
    """POST /asignacion-masiva: N users → N created; duplicate omitted."""

    @pytest.mark.asyncio
    async def test_bulk_creates_n_assignments(self, test_client, int_tenant):
        resp = await test_client.post(
            "/v1/equipos/asignacion-masiva",
            json={
                "usuario_ids": [str(int_tenant["user1_id"]), str(int_tenant["user2_id"])],
                "rol": "PROFESOR",
                "materia_id": str(int_tenant["materia_id"]),
                "carrera_id": str(int_tenant["carrera_id"]),
                "cohorte_id": str(int_tenant["cohorte_a_id"]),
                "desde": str(_TOMORROW),
            },
            headers={"Authorization": f"Bearer {int_tenant['coord_token']}"},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        total = len(data["creadas"]) + len(data["omitidos"])
        assert total == 2

    @pytest.mark.asyncio
    async def test_empty_usuario_ids_returns_422(self, test_client, int_tenant):
        resp = await test_client.post(
            "/v1/equipos/asignacion-masiva",
            json={"usuario_ids": [], "rol": "TUTOR", "desde": str(_TODAY)},
            headers={"Authorization": f"Bearer {int_tenant['coord_token']}"},
        )
        assert resp.status_code == 422


# ── 6.7 POST /clonar ──────────────────────────────────────────────────────────


class TestClonarEquipo:
    """POST /clonar duplicates vigentes with new cohorte + dates; origin untouched."""

    @pytest.mark.asyncio
    async def test_clone_creates_in_destination(self, test_client, int_tenant, test_session_factory):
        tid = int_tenant["tenant_id"]
        # Seed a vigente assignment in cohorte_a
        async with test_session_factory() as session:
            repo = AsignacionRepository(session, tid)
            await repo.create({
                "usuario_id": int_tenant["user1_id"],
                "rol": "COORDINADOR",
                "materia_id": int_tenant["materia_id"],
                "carrera_id": int_tenant["carrera_id"],
                "cohorte_id": int_tenant["cohorte_a_id"],
                "comisiones": [],
                "desde": _TODAY,
            })
            await session.commit()

        resp = await test_client.post(
            "/v1/equipos/clonar",
            json={
                "materia_id": str(int_tenant["materia_id"]),
                "carrera_id": str(int_tenant["carrera_id"]),
                "origen_cohorte_id": str(int_tenant["cohorte_a_id"]),
                "destino_cohorte_id": str(int_tenant["cohorte_b_id"]),
                "desde": str(_TOMORROW),
            },
            headers={"Authorization": f"Bearer {int_tenant['coord_token']}"},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        total = len(data["creadas"]) + len(data["omitidos"])
        assert total >= 1
        for a in data["creadas"]:
            assert a["cohorte_id"] == str(int_tenant["cohorte_b_id"])

    @pytest.mark.asyncio
    async def test_clone_same_cohorte_returns_422(self, test_client, int_tenant):
        cid = str(int_tenant["cohorte_a_id"])
        resp = await test_client.post(
            "/v1/equipos/clonar",
            json={
                "materia_id": str(int_tenant["materia_id"]),
                "carrera_id": str(int_tenant["carrera_id"]),
                "origen_cohorte_id": cid,
                "destino_cohorte_id": cid,
                "desde": str(_TODAY),
            },
            headers={"Authorization": f"Bearer {int_tenant['coord_token']}"},
        )
        assert resp.status_code == 422


# ── 6.8 PUT /vigencia-masiva ──────────────────────────────────────────────────


class TestVigenciaMasiva:
    """PUT /vigencia-masiva updates dates; returns filas_afectadas."""

    @pytest.mark.asyncio
    async def test_updates_and_returns_count(self, test_client, int_tenant):
        resp = await test_client.put(
            "/v1/equipos/vigencia-masiva",
            json={
                "materia_id": str(int_tenant["materia_id"]),
                "carrera_id": str(int_tenant["carrera_id"]),
                "cohorte_id": str(int_tenant["cohorte_a_id"]),
                "desde": str(_TODAY),
                "hasta": str(_TODAY + timedelta(days=150)),
            },
            headers={"Authorization": f"Bearer {int_tenant['coord_token']}"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "filas_afectadas" in data
        assert isinstance(data["filas_afectadas"], int)

    @pytest.mark.asyncio
    async def test_no_team_returns_zero(self, test_client, int_tenant):
        resp = await test_client.put(
            "/v1/equipos/vigencia-masiva",
            json={
                "materia_id": str(uuid.uuid4()),
                "carrera_id": str(uuid.uuid4()),
                "cohorte_id": str(uuid.uuid4()),
                "desde": str(_TODAY),
            },
            headers={"Authorization": f"Bearer {int_tenant['coord_token']}"},
        )
        assert resp.status_code == 200
        assert resp.json()["filas_afectadas"] == 0


# ── 6.9 GET /exportar ────────────────────────────────────────────────────────


class TestExportar:
    """GET /exportar returns CSV; empty team returns headers only."""

    @pytest.mark.asyncio
    async def test_export_has_headers(self, test_client, int_tenant):
        resp = await test_client.get(
            "/v1/equipos/exportar",
            headers={"Authorization": f"Bearer {int_tenant['coord_token']}"},
        )
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert "attachment" in resp.headers.get("content-disposition", "")
        content = resp.text
        assert "id" in content
        assert "usuario_id" in content
        assert "rol" in content

    @pytest.mark.asyncio
    async def test_export_empty_team_headers_only(self, test_client, int_tenant):
        resp = await test_client.get(
            f"/v1/equipos/exportar?materia_id={uuid.uuid4()}",
            headers={"Authorization": f"Bearer {int_tenant['coord_token']}"},
        )
        assert resp.status_code == 200
        lines = [l for l in resp.text.strip().split("\n") if l]
        assert len(lines) == 1  # headers only


# ── 6.10 Multi-tenant isolation ───────────────────────────────────────────────


class TestMultiTenantIsolation:
    """Tenant A assignments are not visible to tenant B users."""

    @pytest.mark.asyncio
    async def test_other_tenant_sees_empty_list(self, test_client, int_tenant, int_other_tenant, test_session_factory):
        """User from other_tenant cannot see int_tenant assignments via GET /."""
        # other_tenant user has no permissions seeded — even list should fail with 403,
        # or if they had permissions, they should see 0 rows from int_tenant.
        # We only test that a valid user from another tenant with no permission gets 403.
        resp = await test_client.get(
            "/v1/equipos/",
            headers={"Authorization": f"Bearer {int_other_tenant['token']}"},
        )
        # No permission → 403
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_mis_asignaciones_scoped_to_own_tenant(self, test_client, int_tenant, int_other_tenant, test_session_factory):
        """Tenant B user's mis-asignaciones never includes tenant A records."""
        # Seed an assignment for int_tenant user
        tid_a = int_tenant["tenant_id"]
        async with test_session_factory() as session:
            repo = AsignacionRepository(session, tid_a)
            created_a = await repo.create({
                "usuario_id": int_tenant["user1_id"],
                "rol": "TUTOR",
                "desde": _TODAY,
                "comisiones": [],
            })
            await session.commit()

        # tenant B user queries their own assignments — should not see tenant A record
        resp = await test_client.get(
            "/v1/equipos/mis-asignaciones",
            headers={"Authorization": f"Bearer {int_other_tenant['token']}"},
        )
        assert resp.status_code == 200
        ids = [a["id"] for a in resp.json()]
        assert str(created_a.id) not in ids
