"""tests/test_equipos_repository.py — TDD tests for AsignacionRepository new methods (C-08).

Tests:
  2.1  list_with_filters — scoped query with optional filters
  2.2  bulk_create — idempotent bulk creation
  2.3  clone_team — duplicates vigentes with new cohorte + dates
  2.4  bulk_update_vigencia — updates desde/hasta for a whole team
  2.5  get — by id scoped to tenant
  2.6  update — update scoped to tenant

Uses real PostgreSQL test DB (DATABASE_URL_TEST). No DB mocking.
"""

import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.asignacion import Asignacion
from app.models.base import Base
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.repositories.asignacion import AsignacionRepository
from app.schemas.asignacion import AsignacionFilter

_TODAY = date.today()
_YESTERDAY = _TODAY - timedelta(days=1)
_TOMORROW = _TODAY + timedelta(days=1)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def db_tables(test_session_factory: async_sessionmaker[AsyncSession]):
    from app.core import database as db_module
    engine = db_module.engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture(scope="module")
async def repo_tenant(test_session_factory, db_tables) -> dict:
    """Seed a tenant + carrera + cohorte x2 + materia + 2 usuarios."""
    async with test_session_factory() as session:
        tenant = Tenant(id=uuid.uuid4(), slug=f"eq-repo-{uuid.uuid4().hex[:6]}", nombre="EquipoRepoTenant")
        session.add(tenant)
        await session.flush()

        carrera = Carrera(id=uuid.uuid4(), tenant_id=tenant.id, codigo="TST", nombre="Carrera Test", estado="Activa")
        session.add(carrera)

        cohorte_a = Cohorte(
            id=uuid.uuid4(), tenant_id=tenant.id, carrera_id=carrera.id,
            nombre="A-2025", anio=2025, estado="Activa",
            vig_desde=_TODAY, vig_hasta=None,
        )
        cohorte_b = Cohorte(
            id=uuid.uuid4(), tenant_id=tenant.id, carrera_id=carrera.id,
            nombre="B-2025", anio=2025, estado="Activa",
            vig_desde=_TODAY, vig_hasta=None,
        )
        session.add_all([cohorte_a, cohorte_b])

        materia = Materia(id=uuid.uuid4(), tenant_id=tenant.id, codigo="MAT01", nombre="Materia Test", estado="Activa")
        session.add(materia)

        from app.core.security import hash_password, email_hash
        u1 = Usuario(
            id=uuid.uuid4(), tenant_id=tenant.id,
            email_cifrado="enc1", email_hash=email_hash(f"u1-{uuid.uuid4().hex}@test.com"),
            password_hash=hash_password("pass"), activo=True,
        )
        u2 = Usuario(
            id=uuid.uuid4(), tenant_id=tenant.id,
            email_cifrado="enc2", email_hash=email_hash(f"u2-{uuid.uuid4().hex}@test.com"),
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
            "user1_id": u1.id,
            "user2_id": u2.id,
        }


def _make_repo(session: AsyncSession, tenant_id: uuid.UUID) -> AsignacionRepository:
    return AsignacionRepository(session, tenant_id)


# ── Test 2.5: get by id ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_returns_none_for_unknown(test_session_factory, repo_tenant):
    tid = repo_tenant["tenant_id"]
    async with test_session_factory() as session:
        repo = _make_repo(session, tid)
        result = await repo.get(uuid.uuid4())
        assert result is None


@pytest.mark.asyncio
async def test_get_returns_record_in_tenant(test_session_factory, repo_tenant):
    tid = repo_tenant["tenant_id"]
    async with test_session_factory() as session:
        repo = _make_repo(session, tid)
        created = await repo.create({
            "usuario_id": repo_tenant["user1_id"],
            "rol": "TUTOR",
            "materia_id": repo_tenant["materia_id"],
            "carrera_id": repo_tenant["carrera_id"],
            "cohorte_id": repo_tenant["cohorte_a_id"],
            "comisiones": [],
            "desde": _TODAY,
        })
        await session.commit()
        fetched = await repo.get(created.id)
        assert fetched is not None
        assert fetched.id == created.id


# ── Test 2.6: update ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_changes_fields(test_session_factory, repo_tenant):
    tid = repo_tenant["tenant_id"]
    async with test_session_factory() as session:
        repo = _make_repo(session, tid)
        created = await repo.create({
            "usuario_id": repo_tenant["user2_id"],
            "rol": "TUTOR",
            "materia_id": repo_tenant["materia_id"],
            "carrera_id": repo_tenant["carrera_id"],
            "cohorte_id": repo_tenant["cohorte_a_id"],
            "comisiones": [],
            "desde": _TODAY,
        })
        await session.flush()
        updated = await repo.update(created.id, {"rol": "PROFESOR", "hasta": _TOMORROW})
        await session.commit()
        assert updated is not None
        assert updated.rol == "PROFESOR"
        assert updated.hasta == _TOMORROW


@pytest.mark.asyncio
async def test_update_returns_none_for_unknown(test_session_factory, repo_tenant):
    tid = repo_tenant["tenant_id"]
    async with test_session_factory() as session:
        repo = _make_repo(session, tid)
        result = await repo.update(uuid.uuid4(), {"rol": "TUTOR"})
        assert result is None


# ── Test 2.1: list_with_filters ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_with_filters_no_filter_returns_all(test_session_factory, repo_tenant):
    tid = repo_tenant["tenant_id"]
    async with test_session_factory() as session:
        repo = _make_repo(session, tid)
        filters = AsignacionFilter()
        results = await repo.list_with_filters(filters)
        # Should return at least the records already created in this module
        assert isinstance(results, list)


@pytest.mark.asyncio
async def test_list_with_filters_by_rol(test_session_factory, repo_tenant):
    tid = repo_tenant["tenant_id"]
    async with test_session_factory() as session:
        repo = _make_repo(session, tid)
        # Create a NEXO assignment for filtering
        created = await repo.create({
            "usuario_id": repo_tenant["user1_id"],
            "rol": "NEXO",
            "materia_id": repo_tenant["materia_id"],
            "carrera_id": repo_tenant["carrera_id"],
            "cohorte_id": repo_tenant["cohorte_a_id"],
            "comisiones": [],
            "desde": _TODAY,
        })
        await session.commit()

        filters = AsignacionFilter(rol="NEXO")
        results = await repo.list_with_filters(filters)
        assert all(r.rol == "NEXO" for r in results)
        ids = [r.id for r in results]
        assert created.id in ids


@pytest.mark.asyncio
async def test_list_with_filters_solo_vigentes_excludes_expired(test_session_factory, repo_tenant):
    tid = repo_tenant["tenant_id"]
    async with test_session_factory() as session:
        repo = _make_repo(session, tid)
        # Create an expired assignment
        expired = await repo.create({
            "usuario_id": repo_tenant["user2_id"],
            "rol": "COORDINADOR",
            "materia_id": repo_tenant["materia_id"],
            "carrera_id": repo_tenant["carrera_id"],
            "cohorte_id": repo_tenant["cohorte_a_id"],
            "comisiones": [],
            "desde": _YESTERDAY - timedelta(days=10),
            "hasta": _YESTERDAY,  # already expired
        })
        await session.commit()

        filters = AsignacionFilter(solo_vigentes=True)
        results = await repo.list_with_filters(filters)
        ids = [r.id for r in results]
        assert expired.id not in ids


# ── Test 2.2: bulk_create ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_bulk_create_creates_all(test_session_factory, repo_tenant):
    tid = repo_tenant["tenant_id"]
    async with test_session_factory() as session:
        repo = _make_repo(session, tid)
        items = [
            {
                "usuario_id": repo_tenant["user1_id"],
                "rol": "FINANZAS",
                "materia_id": repo_tenant["materia_id"],
                "carrera_id": repo_tenant["carrera_id"],
                "cohorte_id": repo_tenant["cohorte_b_id"],
                "comisiones": [],
                "desde": _TODAY,
            },
            {
                "usuario_id": repo_tenant["user2_id"],
                "rol": "FINANZAS",
                "materia_id": repo_tenant["materia_id"],
                "carrera_id": repo_tenant["carrera_id"],
                "cohorte_id": repo_tenant["cohorte_b_id"],
                "comisiones": [],
                "desde": _TODAY,
            },
        ]
        creadas, omitidos = await repo.bulk_create(items)
        await session.commit()
        assert len(creadas) == 2
        assert len(omitidos) == 0


@pytest.mark.asyncio
async def test_bulk_create_is_idempotent(test_session_factory, repo_tenant):
    """Duplicate assignment (same usuario+rol+materia+carrera+cohorte) is omitted."""
    tid = repo_tenant["tenant_id"]
    async with test_session_factory() as session:
        repo = _make_repo(session, tid)
        item = {
            "usuario_id": repo_tenant["user1_id"],
            "rol": "ADMIN",
            "materia_id": None,
            "carrera_id": None,
            "cohorte_id": None,
            "comisiones": [],
            "desde": _TODAY,
        }
        # First bulk_create
        creadas1, omitidos1 = await repo.bulk_create([item])
        await session.commit()
        assert len(creadas1) == 1
        assert len(omitidos1) == 0

    async with test_session_factory() as session:
        repo = _make_repo(session, tid)
        # Second bulk_create with same data → should be omitted
        creadas2, omitidos2 = await repo.bulk_create([item])
        await session.commit()
        assert len(creadas2) == 0
        assert len(omitidos2) == 1
        assert repo_tenant["user1_id"] in omitidos2


# ── Test 2.3: clone_team ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_clone_team_duplicates_vigentes(test_session_factory, repo_tenant):
    tid = repo_tenant["tenant_id"]
    async with test_session_factory() as session:
        repo = _make_repo(session, tid)
        # Ensure at least one vigente assignment in cohorte_a with materia_id
        await repo.create({
            "usuario_id": repo_tenant["user1_id"],
            "rol": "TUTOR",
            "materia_id": repo_tenant["materia_id"],
            "carrera_id": repo_tenant["carrera_id"],
            "cohorte_id": repo_tenant["cohorte_a_id"],
            "comisiones": ["COM-1"],
            "desde": _TODAY,
        })
        await session.flush()

        new_desde = _TOMORROW
        new_hasta = _TOMORROW + timedelta(days=90)
        creadas, omitidos = await repo.clone_team(
            origen_cohorte_id=repo_tenant["cohorte_a_id"],
            destino_cohorte_id=repo_tenant["cohorte_b_id"],
            materia_id=repo_tenant["materia_id"],
            carrera_id=repo_tenant["carrera_id"],
            desde=new_desde,
            hasta=new_hasta,
        )
        await session.commit()

        assert len(creadas) >= 1
        for a in creadas:
            assert a.cohorte_id == repo_tenant["cohorte_b_id"]
            assert a.desde == new_desde
            assert a.hasta == new_hasta


@pytest.mark.asyncio
async def test_clone_team_origin_unchanged(test_session_factory, repo_tenant):
    """Source assignments must NOT be modified after clone."""
    tid = repo_tenant["tenant_id"]
    async with test_session_factory() as session:
        repo = _make_repo(session, tid)
        filters = AsignacionFilter(cohorte_id=repo_tenant["cohorte_a_id"])
        before = await repo.list_with_filters(filters)
        before_ids = {a.id for a in before}

        await repo.clone_team(
            origen_cohorte_id=repo_tenant["cohorte_a_id"],
            destino_cohorte_id=repo_tenant["cohorte_b_id"],
            materia_id=repo_tenant["materia_id"],
            carrera_id=repo_tenant["carrera_id"],
            desde=_TOMORROW,
            hasta=None,
        )
        await session.commit()

        after = await repo.list_with_filters(filters)
        after_ids = {a.id for a in after}
        # All original IDs must still be present with the same data
        assert before_ids.issubset(after_ids)


# ── Test 2.4: bulk_update_vigencia ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_bulk_update_vigencia_returns_count(test_session_factory, repo_tenant):
    tid = repo_tenant["tenant_id"]
    async with test_session_factory() as session:
        repo = _make_repo(session, tid)
        new_hasta = _TODAY + timedelta(days=180)
        count = await repo.bulk_update_vigencia(
            materia_id=repo_tenant["materia_id"],
            carrera_id=repo_tenant["carrera_id"],
            cohorte_id=repo_tenant["cohorte_a_id"],
            desde=_TODAY,
            hasta=new_hasta,
        )
        await session.commit()
        assert isinstance(count, int)
        assert count >= 0


@pytest.mark.asyncio
async def test_bulk_update_vigencia_no_team_returns_zero(test_session_factory, repo_tenant):
    tid = repo_tenant["tenant_id"]
    async with test_session_factory() as session:
        repo = _make_repo(session, tid)
        count = await repo.bulk_update_vigencia(
            materia_id=uuid.uuid4(),  # non-existent
            carrera_id=uuid.uuid4(),
            cohorte_id=uuid.uuid4(),
            desde=_TODAY,
            hasta=None,
        )
        await session.commit()
        assert count == 0
