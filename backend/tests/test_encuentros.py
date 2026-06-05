"""tests/test_encuentros.py — TDD tests for C-13: Encuentros y Guardias.

Strict TDD: tests written BEFORE production code.
Each test describes expected behavior per spec scenarios.

Tests:
  1. crear_slot_recurrente — 3 semanas genera 3 instancias
  2. crear_slot_recurrente — 1 semana genera 1 instancia (triangulation)
  3. encuentro_unico (cant_semanas=0) genera exactamente 1 instancia
  4. editar_instancia — estado + video_url actualizados
  5. generar_html — retorna string con contenido de tabla
  6. list_admin — retorna todas las instancias del tenant
  7. crear_guardia — persiste guardia y retorna objeto
  8. list_guardias — retorna guardias del tenant
  9. exportar_csv — CSV con headers siempre presente
  10. tenant_isolation — instancias de otro tenant no visibles

Uses real PostgreSQL test DB. No DB mocking.
"""

import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.base import Base
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.tenant import Tenant
from app.models.usuario import Usuario

_TODAY = date.today()
_MONDAY = _TODAY - timedelta(days=_TODAY.weekday())  # most recent Monday


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def db_tables(test_session_factory: async_sessionmaker[AsyncSession]):
    from app.core import database as db_module

    engine = db_module.engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture(scope="module")
async def enc_tenant(test_session_factory, db_tables) -> dict:
    """Module-scoped tenant context: two tenants, one carrera, cohorte, materia, asignacion."""
    async with test_session_factory() as session:
        from app.core.security import hash_password, email_hash

        # Primary tenant
        tenant = Tenant(id=uuid.uuid4(), slug=f"enc-{uuid.uuid4().hex[:6]}", nombre="EncTenant")
        tenant2 = Tenant(id=uuid.uuid4(), slug=f"enc2-{uuid.uuid4().hex[:6]}", nombre="EncTenant2")
        session.add_all([tenant, tenant2])
        await session.flush()

        carrera = Carrera(
            id=uuid.uuid4(), tenant_id=tenant.id,
            codigo="ENCC", nombre="Carrera Enc", estado="Activa",
        )
        session.add(carrera)

        cohorte = Cohorte(
            id=uuid.uuid4(), tenant_id=tenant.id, carrera_id=carrera.id,
            nombre="ENC-A", anio=2026, estado="Activa",
            vig_desde=_TODAY, vig_hasta=None,
        )
        session.add(cohorte)

        materia = Materia(
            id=uuid.uuid4(), tenant_id=tenant.id,
            codigo="ENCM01", nombre="Mat Enc", estado="Activa",
        )
        materia2 = Materia(
            id=uuid.uuid4(), tenant_id=tenant2.id,
            codigo="ENCM01", nombre="Mat Enc T2", estado="Activa",
        )
        session.add_all([materia, materia2])

        actor = Usuario(
            id=uuid.uuid4(), tenant_id=tenant.id,
            email_cifrado="enc-actor",
            email_hash=email_hash(f"enc-actor-{uuid.uuid4().hex}@test.com"),
            password_hash=hash_password("pass"), activo=True,
        )
        actor2 = Usuario(
            id=uuid.uuid4(), tenant_id=tenant2.id,
            email_cifrado="enc-actor2",
            email_hash=email_hash(f"enc-actor2-{uuid.uuid4().hex}@test.com"),
            password_hash=hash_password("pass"), activo=True,
        )
        session.add_all([actor, actor2])
        await session.flush()

        # Create asignaciones for both tenants
        from app.models.asignacion import Asignacion

        asig = Asignacion(
            id=uuid.uuid4(), tenant_id=tenant.id,
            usuario_id=actor.id, rol="PROFESOR",
            materia_id=materia.id, carrera_id=carrera.id,
            cohorte_id=cohorte.id, comisiones=[],
            desde=_TODAY, hasta=None,
        )
        asig2 = Asignacion(
            id=uuid.uuid4(), tenant_id=tenant2.id,
            usuario_id=actor2.id, rol="PROFESOR",
            materia_id=materia2.id,
            comisiones=[], desde=_TODAY, hasta=None,
        )
        session.add_all([asig, asig2])
        await session.commit()

        return {
            "tenant_id": tenant.id,
            "tenant2_id": tenant2.id,
            "materia_id": materia.id,
            "materia2_id": materia2.id,
            "carrera_id": carrera.id,
            "cohorte_id": cohorte.id,
            "asig_id": asig.id,
            "asig2_id": asig2.id,
            "actor_id": actor.id,
        }


@pytest_asyncio.fixture
async def enc_session(test_session_factory, enc_tenant) -> AsyncSession:
    async with test_session_factory() as session:
        yield session


# ── Tests: EncuentrosService ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_crear_slot_recurrente_3_semanas(enc_session, enc_tenant):
    """SC-01: 3 semanas → 3 instancias con fechas correctas."""
    from app.schemas.encuentro import SlotCreate
    from app.services.encuentros import EncuentrosService

    data = SlotCreate(
        asignacion_id=enc_tenant["asig_id"],
        materia_id=enc_tenant["materia_id"],
        titulo="Clase de Programación",
        hora="18:00",
        dia_semana="Lunes",
        fecha_inicio=_MONDAY,
        cant_semanas=3,
        meet_url="https://meet.example.com/prog",
    )

    svc = EncuentrosService(enc_session, enc_tenant["tenant_id"])
    result = await svc.crear_slot_recurrente(data, actor_id=enc_tenant["actor_id"])
    await enc_session.commit()

    assert result.slot is not None
    assert len(result.instancias) == 3

    fechas = [inst.fecha for inst in result.instancias]
    assert fechas[0] == _MONDAY
    assert fechas[1] == _MONDAY + timedelta(days=7)
    assert fechas[2] == _MONDAY + timedelta(days=14)

    # All instancias belong to the correct tenant
    for inst in result.instancias:
        assert inst.tenant_id == enc_tenant["tenant_id"]
        assert inst.estado == "Programado"


@pytest.mark.asyncio
async def test_crear_slot_recurrente_1_semana(enc_session, enc_tenant):
    """SC-01 triangulation: 1 semana → 1 instancia."""
    from app.schemas.encuentro import SlotCreate
    from app.services.encuentros import EncuentrosService

    data = SlotCreate(
        asignacion_id=enc_tenant["asig_id"],
        materia_id=enc_tenant["materia_id"],
        titulo="Clase única recurrente",
        hora="10:00",
        dia_semana="Martes",
        fecha_inicio=_MONDAY + timedelta(days=1),
        cant_semanas=1,
        meet_url="https://meet.example.com/single",
    )

    svc = EncuentrosService(enc_session, enc_tenant["tenant_id"])
    result = await svc.crear_slot_recurrente(data, actor_id=enc_tenant["actor_id"])
    await enc_session.commit()

    assert len(result.instancias) == 1
    assert result.instancias[0].fecha == _MONDAY + timedelta(days=1)


@pytest.mark.asyncio
async def test_crear_encuentro_unico(enc_session, enc_tenant):
    """SC-02: cant_semanas=0 con fecha_unica → 1 instancia."""
    from app.schemas.encuentro import SlotCreate
    from app.services.encuentros import EncuentrosService

    fecha_unica = _TODAY + timedelta(days=5)
    data = SlotCreate(
        asignacion_id=enc_tenant["asig_id"],
        materia_id=enc_tenant["materia_id"],
        titulo="Encuentro único especial",
        hora="14:00",
        dia_semana="Viernes",
        fecha_inicio=fecha_unica,
        cant_semanas=0,
        fecha_unica=fecha_unica,
        meet_url="https://meet.example.com/unico",
    )

    svc = EncuentrosService(enc_session, enc_tenant["tenant_id"])
    result = await svc.crear_slot_recurrente(data, actor_id=enc_tenant["actor_id"])
    await enc_session.commit()

    assert len(result.instancias) == 1
    assert result.instancias[0].fecha == fecha_unica
    assert result.slot.fecha_unica == fecha_unica


@pytest.mark.asyncio
async def test_editar_instancia(enc_session, enc_tenant):
    """SC-03: editar estado y video_url de una instancia."""
    from app.schemas.encuentro import SlotCreate, InstanciaUpdate
    from app.services.encuentros import EncuentrosService

    data = SlotCreate(
        asignacion_id=enc_tenant["asig_id"],
        materia_id=enc_tenant["materia_id"],
        titulo="Clase editable",
        hora="19:00",
        dia_semana="Miercoles",
        fecha_inicio=_TODAY + timedelta(days=2),
        cant_semanas=1,
        meet_url="https://meet.example.com/edit",
    )
    svc = EncuentrosService(enc_session, enc_tenant["tenant_id"])
    created = await svc.crear_slot_recurrente(data, actor_id=enc_tenant["actor_id"])
    await enc_session.commit()

    instancia = created.instancias[0]
    update_data = InstanciaUpdate(
        estado="Realizado",
        video_url="https://video.example.com/rec1",
        comentario="Muy buena clase",
    )
    updated = await svc.editar_instancia(instancia.id, update_data, actor_id=enc_tenant["actor_id"])
    await enc_session.commit()

    assert updated.estado == "Realizado"
    assert updated.video_url == "https://video.example.com/rec1"
    assert updated.comentario == "Muy buena clase"


@pytest.mark.asyncio
async def test_generar_html(enc_session, enc_tenant):
    """SC-04: generar_html retorna string HTML con contenido."""
    from app.services.encuentros import EncuentrosService

    svc = EncuentrosService(enc_session, enc_tenant["tenant_id"])
    html = await svc.generar_html(
        materia_id=enc_tenant["materia_id"],
        asignacion_id=enc_tenant["asig_id"],
    )

    assert isinstance(html, str)
    # Must contain at least one table row
    assert "<tr>" in html or "<table" in html


@pytest.mark.asyncio
async def test_list_admin(enc_session, enc_tenant):
    """SC-05: list_admin retorna instancias del tenant."""
    from app.services.encuentros import EncuentrosService

    svc = EncuentrosService(enc_session, enc_tenant["tenant_id"])
    instancias = await svc.list_admin(materia_id=enc_tenant["materia_id"])

    assert len(instancias) >= 1
    for inst in instancias:
        assert inst.tenant_id == enc_tenant["tenant_id"]


# ── Tests: GuardiasService ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_crear_guardia(enc_session, enc_tenant):
    """SC-01 guardias: crear guardia persiste y retorna objeto."""
    from app.schemas.guardia import GuardiaCreate
    from app.services.guardias import GuardiasService

    data = GuardiaCreate(
        asignacion_id=enc_tenant["asig_id"],
        materia_id=enc_tenant["materia_id"],
        carrera_id=enc_tenant["carrera_id"],
        cohorte_id=enc_tenant["cohorte_id"],
        dia="Lunes",
        horario="14:00-14:45",
        estado="Pendiente",
        comentarios="Primera guardia",
    )

    svc = GuardiasService(enc_session, enc_tenant["tenant_id"])
    guardia = await svc.crear_guardia(data, actor_id=enc_tenant["actor_id"])
    await enc_session.commit()

    assert guardia.id is not None
    assert guardia.tenant_id == enc_tenant["tenant_id"]
    assert guardia.dia == "Lunes"
    assert guardia.horario == "14:00-14:45"
    assert guardia.estado == "Pendiente"


@pytest.mark.asyncio
async def test_list_guardias(enc_session, enc_tenant):
    """SC-02 guardias: listar guardias del tenant."""
    from app.schemas.guardia import GuardiaCreate, GuardiaFilter
    from app.services.guardias import GuardiasService

    # Ensure there is at least one guardia (from previous test isolation risk)
    data = GuardiaCreate(
        asignacion_id=enc_tenant["asig_id"],
        materia_id=enc_tenant["materia_id"],
        carrera_id=enc_tenant["carrera_id"],
        cohorte_id=enc_tenant["cohorte_id"],
        dia="Martes",
        horario="10:00-10:45",
        estado="Pendiente",
    )
    svc = GuardiasService(enc_session, enc_tenant["tenant_id"])
    await svc.crear_guardia(data, actor_id=enc_tenant["actor_id"])
    await enc_session.commit()

    filters = GuardiaFilter(materia_id=enc_tenant["materia_id"])
    guardias = await svc.list_guardias(filters)

    assert len(guardias) >= 1
    for g in guardias:
        assert g.tenant_id == enc_tenant["tenant_id"]


@pytest.mark.asyncio
async def test_exportar_csv_guardias(enc_session, enc_tenant):
    """SC-03 guardias: CSV tiene headers siempre."""
    from app.schemas.guardia import GuardiaFilter
    from app.services.guardias import GuardiasService

    svc = GuardiasService(enc_session, enc_tenant["tenant_id"])
    filters = GuardiaFilter()
    csv_str = await svc.exportar_csv(filters)

    assert isinstance(csv_str, str)
    # CSV must have header row even if empty
    lines = csv_str.strip().splitlines()
    assert len(lines) >= 1
    # Header should contain expected column names
    assert "id" in lines[0]
    assert "dia" in lines[0]


@pytest.mark.asyncio
async def test_tenant_isolation_instancias(enc_session, enc_tenant):
    """Tenant isolation: instancias de tenant2 no visibles desde tenant1."""
    from app.schemas.encuentro import SlotCreate
    from app.services.encuentros import EncuentrosService

    # Create instance in tenant2
    svc2 = EncuentrosService(enc_session, enc_tenant["tenant2_id"])
    data2 = SlotCreate(
        asignacion_id=enc_tenant["asig2_id"],
        materia_id=enc_tenant["materia2_id"],
        titulo="Clase Tenant2",
        hora="08:00",
        dia_semana="Lunes",
        fecha_inicio=_TODAY,
        cant_semanas=1,
        meet_url="https://meet.example.com/t2",
    )
    await svc2.crear_slot_recurrente(data2, actor_id=enc_tenant["actor_id"])
    await enc_session.commit()

    # Query from tenant1 — should not see tenant2 instances
    svc1 = EncuentrosService(enc_session, enc_tenant["tenant_id"])
    instancias = await svc1.list_admin()

    for inst in instancias:
        assert inst.tenant_id == enc_tenant["tenant_id"]
