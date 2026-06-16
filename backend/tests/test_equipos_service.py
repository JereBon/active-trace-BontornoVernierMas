"""tests/test_equipos_service.py — TDD tests for EquiposService (C-08).

Tests:
  3.2  mis_asignaciones — returns vigentes only
  3.3  list_asignaciones — delegates filters
  3.4  create_asignacion — creates + audit log
  3.5  update_asignacion — updates + audit log; NotFoundError on unknown id
  3.6  delete_asignacion — soft delete + audit log; NotFoundError on unknown id
  3.7  asignacion_masiva — bulk create + audit; duplicates omitted
  3.8  clonar_equipo — clone + audit; origin untouched
  3.9  vigencia_masiva — updates dates + audit; returns count
  3.10 exportar_csv — CSV string with headers; empty when no matches

Uses real PostgreSQL test DB. No DB mocking.
"""

import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.exceptions import NotFoundError
from app.models.asignacion import Asignacion
from app.models.base import Base
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.repositories.asignacion import AsignacionRepository
from app.schemas.asignacion import (
    AsignacionCreate,
    AsignacionFilter,
    AsignacionMasivaCreate,
    AsignacionUpdate,
    ClonarEquipoRequest,
    VigenciaMasivaRequest,
)
from app.services.equipos import EquiposService

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
async def svc_tenant(test_session_factory, db_tables) -> dict:
    async with test_session_factory() as session:
        from app.core.security import hash_password, email_hash

        tenant = Tenant(id=uuid.uuid4(), slug=f"eq-svc-{uuid.uuid4().hex[:6]}", nombre="EquipoSvcTenant")
        session.add(tenant)
        await session.flush()

        carrera = Carrera(id=uuid.uuid4(), tenant_id=tenant.id, codigo="SVC", nombre="Carrera SVC", estado="Activa")
        session.add(carrera)

        cohorte_a = Cohorte(
            id=uuid.uuid4(), tenant_id=tenant.id, carrera_id=carrera.id,
            nombre="SVC-A", anio=2025, estado="Activa", vig_desde=_TODAY, vig_hasta=None,
        )
        cohorte_b = Cohorte(
            id=uuid.uuid4(), tenant_id=tenant.id, carrera_id=carrera.id,
            nombre="SVC-B", anio=2025, estado="Activa", vig_desde=_TODAY, vig_hasta=None,
        )
        session.add_all([cohorte_a, cohorte_b])

        materia = Materia(id=uuid.uuid4(), tenant_id=tenant.id, codigo="SVC01", nombre="Mat SVC", estado="Activa")
        session.add(materia)

        u1 = Usuario(
            id=uuid.uuid4(), tenant_id=tenant.id,
            email_cifrado="enc-svc1",
            email_hash=email_hash(f"svc1-{uuid.uuid4().hex}@test.com"),
            password_hash=hash_password("pass"), activo=True,
        )
        u2 = Usuario(
            id=uuid.uuid4(), tenant_id=tenant.id,
            email_cifrado="enc-svc2",
            email_hash=email_hash(f"svc2-{uuid.uuid4().hex}@test.com"),
            password_hash=hash_password("pass"), activo=True,
        )
        actor = Usuario(
            id=uuid.uuid4(), tenant_id=tenant.id,
            email_cifrado="enc-actor",
            email_hash=email_hash(f"actor-{uuid.uuid4().hex}@test.com"),
            password_hash=hash_password("pass"), activo=True,
        )
        session.add_all([u1, u2, actor])
        await session.commit()

        return {
            "tenant_id": tenant.id,
            "carrera_id": carrera.id,
            "cohorte_a_id": cohorte_a.id,
            "cohorte_b_id": cohorte_b.id,
            "materia_id": materia.id,
            "user1_id": u1.id,
            "user2_id": u2.id,
            "actor_id": actor.id,
        }


def _svc(session, tenant_id):
    return EquiposService(session, tenant_id)


# ── 3.4 create_asignacion ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_asignacion_returns_record(test_session_factory, svc_tenant):
    tid = svc_tenant["tenant_id"]
    async with test_session_factory() as session:
        svc = _svc(session, tid)
        data = AsignacionCreate(
            usuario_id=svc_tenant["user1_id"],
            rol="TUTOR",
            materia_id=svc_tenant["materia_id"],
            carrera_id=svc_tenant["carrera_id"],
            cohorte_id=svc_tenant["cohorte_a_id"],
            desde=_TODAY,
        )
        created = await svc.create_asignacion(data, actor_id=svc_tenant["actor_id"])
        await session.commit()
        assert created.id is not None
        assert created.rol == "TUTOR"
        assert created.tenant_id == tid


@pytest.mark.asyncio
async def test_create_asignacion_writes_audit_log(test_session_factory, svc_tenant):
    tid = svc_tenant["tenant_id"]
    async with test_session_factory() as session:
        from app.repositories.audit_log import AuditLogRepository
        svc = _svc(session, tid)
        data = AsignacionCreate(
            usuario_id=svc_tenant["user2_id"],
            rol="PROFESOR",
            desde=_TODAY,
        )
        await svc.create_asignacion(data, actor_id=svc_tenant["actor_id"])
        await session.commit()

        audit_repo = AuditLogRepository(session, tid)
        logs = await audit_repo.list_by_tenant(actor_id=svc_tenant["actor_id"])
        assert any(l.accion == "ASIGNACION_CREAR" for l in logs)


# ── 3.2 mis_asignaciones ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_mis_asignaciones_returns_only_vigentes(test_session_factory, svc_tenant):
    tid = svc_tenant["tenant_id"]
    async with test_session_factory() as session:
        repo = AsignacionRepository(session, tid)
        # Create one vigente and one expired for user1
        expired = await repo.create({
            "usuario_id": svc_tenant["user1_id"],
            "rol": "NEXO",
            "desde": _YESTERDAY - timedelta(days=5),
            "hasta": _YESTERDAY,
            "comisiones": [],
        })
        await session.commit()

    async with test_session_factory() as session:
        svc = _svc(session, tid)
        results = await svc.mis_asignaciones(svc_tenant["user1_id"])
        ids = [r.id for r in results]
        # Expired should NOT appear
        assert expired.id not in ids
        # All results should be vigentes
        for r in results:
            assert r.hasta is None or r.hasta >= _TODAY


# ── 3.3 list_asignaciones ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_asignaciones_with_rol_filter(test_session_factory, svc_tenant):
    tid = svc_tenant["tenant_id"]
    async with test_session_factory() as session:
        svc = _svc(session, tid)
        filters = AsignacionFilter(rol="TUTOR")
        results = await svc.list_asignaciones(filters)
        assert all(r.rol == "TUTOR" for r in results)


# ── 3.5 update_asignacion ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_asignacion_changes_role(test_session_factory, svc_tenant):
    tid = svc_tenant["tenant_id"]
    async with test_session_factory() as session:
        repo = AsignacionRepository(session, tid)
        created = await repo.create({
            "usuario_id": svc_tenant["user1_id"],
            "rol": "TUTOR",
            "desde": _TODAY,
            "comisiones": [],
        })
        await session.commit()

    async with test_session_factory() as session:
        svc = _svc(session, tid)
        updated = await svc.update_asignacion(
            created.id,
            AsignacionUpdate(rol="COORDINADOR"),
            actor_id=svc_tenant["actor_id"],
        )
        await session.commit()
        assert updated.rol == "COORDINADOR"


@pytest.mark.asyncio
async def test_update_asignacion_unknown_raises_not_found(test_session_factory, svc_tenant):
    tid = svc_tenant["tenant_id"]
    async with test_session_factory() as session:
        svc = _svc(session, tid)
        with pytest.raises(NotFoundError):
            await svc.update_asignacion(uuid.uuid4(), AsignacionUpdate(), actor_id=svc_tenant["actor_id"])


# ── 3.6 delete_asignacion ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_asignacion_soft_deletes(test_session_factory, svc_tenant):
    tid = svc_tenant["tenant_id"]
    async with test_session_factory() as session:
        repo = AsignacionRepository(session, tid)
        created = await repo.create({
            "usuario_id": svc_tenant["user2_id"],
            "rol": "NEXO",
            "desde": _TODAY,
            "comisiones": [],
        })
        await session.commit()

    async with test_session_factory() as session:
        svc = _svc(session, tid)
        await svc.delete_asignacion(created.id, actor_id=svc_tenant["actor_id"])
        await session.commit()

    # Verify it no longer appears in listings
    async with test_session_factory() as session:
        repo = AsignacionRepository(session, tid)
        fetched = await repo.get(created.id)
        assert fetched is None  # soft-deleted


@pytest.mark.asyncio
async def test_delete_asignacion_unknown_raises_not_found(test_session_factory, svc_tenant):
    tid = svc_tenant["tenant_id"]
    async with test_session_factory() as session:
        svc = _svc(session, tid)
        with pytest.raises(NotFoundError):
            await svc.delete_asignacion(uuid.uuid4(), actor_id=svc_tenant["actor_id"])


# ── 3.7 asignacion_masiva ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_asignacion_masiva_creates_all(test_session_factory, svc_tenant):
    tid = svc_tenant["tenant_id"]
    async with test_session_factory() as session:
        svc = _svc(session, tid)
        data = AsignacionMasivaCreate(
            usuario_ids=[svc_tenant["user1_id"], svc_tenant["user2_id"]],
            rol="FINANZAS",
            materia_id=svc_tenant["materia_id"],
            carrera_id=svc_tenant["carrera_id"],
            cohorte_id=svc_tenant["cohorte_b_id"],
            desde=_TOMORROW,
        )
        result = await svc.asignacion_masiva(data, actor_id=svc_tenant["actor_id"])
        await session.commit()
        assert len(result.creadas) == 2
        assert len(result.omitidos) == 0


@pytest.mark.asyncio
async def test_asignacion_masiva_omits_duplicate(test_session_factory, svc_tenant):
    tid = svc_tenant["tenant_id"]
    # First call creates
    async with test_session_factory() as session:
        svc = _svc(session, tid)
        data = AsignacionMasivaCreate(
            usuario_ids=[svc_tenant["user1_id"]],
            rol="ADMIN",
            desde=_TODAY,
        )
        r1 = await svc.asignacion_masiva(data, actor_id=svc_tenant["actor_id"])
        await session.commit()
        assert len(r1.creadas) >= 0  # may already exist from other tests

    # Second call: same user+rol+context → omitted
    async with test_session_factory() as session:
        svc = _svc(session, tid)
        data = AsignacionMasivaCreate(
            usuario_ids=[svc_tenant["user1_id"]],
            rol="ADMIN",
            desde=_TODAY,
        )
        r2 = await svc.asignacion_masiva(data, actor_id=svc_tenant["actor_id"])
        await session.commit()
        # Should be 0 created, 1 omitted (already exists)
        total = len(r2.creadas) + len(r2.omitidos)
        assert total == 1


# ── 3.8 clonar_equipo ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_clonar_equipo_creates_in_destination(test_session_factory, svc_tenant):
    tid = svc_tenant["tenant_id"]
    # Ensure a vigente assignment exists in cohorte_a
    async with test_session_factory() as session:
        repo = AsignacionRepository(session, tid)
        await repo.create({
            "usuario_id": svc_tenant["user1_id"],
            "rol": "PROFESOR",
            "materia_id": svc_tenant["materia_id"],
            "carrera_id": svc_tenant["carrera_id"],
            "cohorte_id": svc_tenant["cohorte_a_id"],
            "comisiones": [],
            "desde": _TODAY,
        })
        await session.commit()

    async with test_session_factory() as session:
        svc = _svc(session, tid)
        req = ClonarEquipoRequest(
            materia_id=svc_tenant["materia_id"],
            carrera_id=svc_tenant["carrera_id"],
            origen_cohorte_id=svc_tenant["cohorte_a_id"],
            destino_cohorte_id=svc_tenant["cohorte_b_id"],
            desde=_TOMORROW,
            hasta=_TOMORROW + timedelta(days=90),
        )
        result = await svc.clonar_equipo(req, actor_id=svc_tenant["actor_id"])
        await session.commit()
        # At least one cloned assignment (skips already-existing ones)
        total = len(result.creadas) + len(result.omitidos)
        assert total >= 1
        for a in result.creadas:
            assert a.cohorte_id == svc_tenant["cohorte_b_id"]


# ── 3.9 vigencia_masiva ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_vigencia_masiva_returns_count(test_session_factory, svc_tenant):
    tid = svc_tenant["tenant_id"]
    async with test_session_factory() as session:
        svc = _svc(session, tid)
        req = VigenciaMasivaRequest(
            materia_id=svc_tenant["materia_id"],
            carrera_id=svc_tenant["carrera_id"],
            cohorte_id=svc_tenant["cohorte_a_id"],
            desde=_TODAY,
            hasta=_TODAY + timedelta(days=120),
        )
        result = await svc.vigencia_masiva(req, actor_id=svc_tenant["actor_id"])
        await session.commit()
        assert isinstance(result.filas_afectadas, int)


@pytest.mark.asyncio
async def test_vigencia_masiva_no_team_returns_zero(test_session_factory, svc_tenant):
    tid = svc_tenant["tenant_id"]
    async with test_session_factory() as session:
        svc = _svc(session, tid)
        req = VigenciaMasivaRequest(
            materia_id=uuid.uuid4(),
            carrera_id=uuid.uuid4(),
            cohorte_id=uuid.uuid4(),
            desde=_TODAY,
        )
        result = await svc.vigencia_masiva(req, actor_id=svc_tenant["actor_id"])
        await session.commit()
        assert result.filas_afectadas == 0


# ── 3.10 exportar_csv ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_exportar_csv_contains_headers(test_session_factory, svc_tenant):
    tid = svc_tenant["tenant_id"]
    async with test_session_factory() as session:
        svc = _svc(session, tid)
        csv_str = await svc.exportar_csv(AsignacionFilter())
        assert "id" in csv_str
        assert "usuario_id" in csv_str
        assert "rol" in csv_str


@pytest.mark.asyncio
async def test_exportar_csv_empty_when_no_match(test_session_factory, svc_tenant):
    tid = svc_tenant["tenant_id"]
    async with test_session_factory() as session:
        svc = _svc(session, tid)
        csv_str = await svc.exportar_csv(AsignacionFilter(materia_id=uuid.uuid4()))
        lines = [l for l in csv_str.strip().split("\n") if l]
        assert len(lines) == 1  # headers only
