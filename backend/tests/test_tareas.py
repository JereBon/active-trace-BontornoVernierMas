"""tests/test_tareas.py — TDD tests for C-16: Tareas Internas.

Tests describe expected behavior per spec (F8.1, F8.2, F8.3) and KB §E12.

Test scenarios:
  1. crear_tarea — asignado_por is always set from JWT actor, not from body
  2. crear_tarea — triangulation: different assignees create separate tasks
  3. delegacion_preserva_asignado_por — asignado_por unchanged after delegation
  4. transicion_valida_pendiente_a_en_progreso — valid state transition
  5. transicion_valida_en_progreso_a_resuelta — valid state transition
  6. transicion_invalida_resuelta_a_pendiente — terminal state raises 422
  7. transicion_invalida_cancelada_a_en_progreso — terminal state raises 422
  8. comentarios_orden_cronologico — thread returned oldest-first
  9. filtro_estado — list_mis_tareas filters by estado correctly
  10. filtro_admin_asignado_a — list_todas filters by asignado_a
  11. multi_tenancy — tenant2 cannot see tenant1 tasks
  12. profesor_ve_solo_sus_tareas — list_mis_tareas scoped to current user

Uses real PostgreSQL test DB. No DB mocking.
"""

import uuid

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.base import Base
from app.models.tenant import Tenant
from app.models.usuario import Usuario


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def db_tables(test_session_factory: async_sessionmaker[AsyncSession]):
    """Ensure all tables exist in the test DB."""
    from app.core import database as db_module

    engine = db_module.engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture(scope="module")
async def tarea_tenant(test_session_factory, db_tables) -> dict:
    """Module-scoped tenant context: two tenants, two users each."""
    async with test_session_factory() as session:
        from app.core.security import hash_password, email_hash

        # Two tenants
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"tarea-{uuid.uuid4().hex[:6]}",
            nombre="TareaTenant",
        )
        tenant2 = Tenant(
            id=uuid.uuid4(),
            slug=f"tarea2-{uuid.uuid4().hex[:6]}",
            nombre="TareaTenant2",
        )
        session.add_all([tenant, tenant2])
        await session.flush()

        # Two users in tenant1: actor (assignor) and asignee
        actor = Usuario(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email_cifrado="tarea-actor",
            email_hash=email_hash(f"tarea-actor-{uuid.uuid4().hex}@test.com"),
            password_hash=hash_password("pass"),
            activo=True,
        )
        asignee = Usuario(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email_cifrado="tarea-asignee",
            email_hash=email_hash(f"tarea-asignee-{uuid.uuid4().hex}@test.com"),
            password_hash=hash_password("pass"),
            activo=True,
        )
        asignee2 = Usuario(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email_cifrado="tarea-asignee2",
            email_hash=email_hash(f"tarea-asignee2-{uuid.uuid4().hex}@test.com"),
            password_hash=hash_password("pass"),
            activo=True,
        )

        # One user in tenant2
        actor2 = Usuario(
            id=uuid.uuid4(),
            tenant_id=tenant2.id,
            email_cifrado="tarea-actor2",
            email_hash=email_hash(f"tarea-actor2-{uuid.uuid4().hex}@test.com"),
            password_hash=hash_password("pass"),
            activo=True,
        )
        session.add_all([actor, asignee, asignee2, actor2])
        await session.commit()

        return {
            "tenant_id": tenant.id,
            "tenant2_id": tenant2.id,
            "actor_id": actor.id,
            "asignee_id": asignee.id,
            "asignee2_id": asignee2.id,
            "actor2_id": actor2.id,
        }


@pytest_asyncio.fixture
async def tarea_session(test_session_factory, tarea_tenant) -> AsyncSession:
    async with test_session_factory() as session:
        yield session


# ── Helper ────────────────────────────────────────────────────────────────────


def _make_create(asignado_a: uuid.UUID, titulo: str = "Test task") -> "TareaCreate":  # type: ignore[name-defined]
    from app.schemas.tarea import TareaCreate

    return TareaCreate(titulo=titulo, asignado_a=asignado_a)


# ── Tests: crear_tarea ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_crear_tarea_asignado_por_del_actor(tarea_session, tarea_tenant):
    """SC-01: asignado_por is always set from JWT actor_id, never from body."""
    from app.services.tarea_service import TareaService

    svc = TareaService(tarea_session, tarea_tenant["tenant_id"])
    data = _make_create(asignado_a=tarea_tenant["asignee_id"], titulo="Tarea SC-01")
    tarea = await svc.crear_tarea(data, actor_id=tarea_tenant["actor_id"])
    await tarea_session.commit()

    assert tarea.id is not None
    assert tarea.tenant_id == tarea_tenant["tenant_id"]
    assert tarea.asignado_a == tarea_tenant["asignee_id"]
    # asignado_por must always be the JWT actor, regardless of body
    assert tarea.asignado_por == tarea_tenant["actor_id"]
    assert tarea.estado == "Pendiente"


@pytest.mark.asyncio
async def test_crear_tarea_diferente_asignee(tarea_session, tarea_tenant):
    """SC-01 triangulation: different assignee creates a separate task."""
    from app.services.tarea_service import TareaService

    svc = TareaService(tarea_session, tarea_tenant["tenant_id"])
    data = _make_create(asignado_a=tarea_tenant["asignee2_id"], titulo="Tarea SC-01b")
    tarea = await svc.crear_tarea(data, actor_id=tarea_tenant["actor_id"])
    await tarea_session.commit()

    assert tarea.asignado_a == tarea_tenant["asignee2_id"]
    assert tarea.asignado_por == tarea_tenant["actor_id"]


# ── Tests: delegacion ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delegacion_preserva_asignado_por(tarea_session, tarea_tenant):
    """SC-02: asignado_por is unchanged after delegating to a new user."""
    from app.services.tarea_service import TareaService

    svc = TareaService(tarea_session, tarea_tenant["tenant_id"])
    data = _make_create(asignado_a=tarea_tenant["asignee_id"], titulo="Tarea delegable")
    tarea = await svc.crear_tarea(data, actor_id=tarea_tenant["actor_id"])
    await tarea_session.commit()

    asignado_por_original = tarea.asignado_por

    # Delegate to asignee2
    delegada = await svc.delegar_tarea(
        tarea_id=tarea.id,
        nuevo_asignado_a=tarea_tenant["asignee2_id"],
        actor_id=tarea_tenant["actor_id"],
    )
    await tarea_session.commit()

    # asignado_a changed to new user
    assert delegada.asignado_a == tarea_tenant["asignee2_id"]
    # asignado_por was preserved — not overwritten
    assert delegada.asignado_por == asignado_por_original
    assert delegada.asignado_por == tarea_tenant["actor_id"]


# ── Tests: transiciones de estado ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_transicion_pendiente_a_en_progreso(tarea_session, tarea_tenant):
    """SC-03: Pendiente → En_progreso is a valid transition."""
    from app.services.tarea_service import TareaService

    svc = TareaService(tarea_session, tarea_tenant["tenant_id"])
    tarea = await svc.crear_tarea(
        _make_create(tarea_tenant["asignee_id"], "Tarea transicion 1"),
        actor_id=tarea_tenant["actor_id"],
    )
    await tarea_session.commit()

    assert tarea.estado == "Pendiente"
    updated = await svc.cambiar_estado(
        tarea_id=tarea.id,
        nuevo_estado="En_progreso",
        actor_id=tarea_tenant["actor_id"],
    )
    await tarea_session.commit()

    assert updated.estado == "En_progreso"


@pytest.mark.asyncio
async def test_transicion_en_progreso_a_resuelta(tarea_session, tarea_tenant):
    """SC-03 triangulation: En_progreso → Resuelta is valid."""
    from app.services.tarea_service import TareaService

    svc = TareaService(tarea_session, tarea_tenant["tenant_id"])
    tarea = await svc.crear_tarea(
        _make_create(tarea_tenant["asignee_id"], "Tarea transicion 2"),
        actor_id=tarea_tenant["actor_id"],
    )
    await tarea_session.commit()

    # First: Pendiente → En_progreso
    tarea = await svc.cambiar_estado(tarea.id, "En_progreso", tarea_tenant["actor_id"])
    await tarea_session.commit()

    # Then: En_progreso → Resuelta
    tarea = await svc.cambiar_estado(tarea.id, "Resuelta", tarea_tenant["actor_id"])
    await tarea_session.commit()

    assert tarea.estado == "Resuelta"


@pytest.mark.asyncio
async def test_transicion_invalida_resuelta_a_pendiente(tarea_session, tarea_tenant):
    """SC-04: Resuelta → Pendiente must raise 422 (terminal state)."""
    from app.services.tarea_service import TareaService

    svc = TareaService(tarea_session, tarea_tenant["tenant_id"])
    tarea = await svc.crear_tarea(
        _make_create(tarea_tenant["asignee_id"], "Tarea terminal 1"),
        actor_id=tarea_tenant["actor_id"],
    )
    await tarea_session.commit()

    # Drive to Resuelta
    tarea = await svc.cambiar_estado(tarea.id, "En_progreso", tarea_tenant["actor_id"])
    tarea = await svc.cambiar_estado(tarea.id, "Resuelta", tarea_tenant["actor_id"])
    await tarea_session.commit()

    # Attempt invalid transition from terminal state
    with pytest.raises(HTTPException) as exc_info:
        await svc.cambiar_estado(tarea.id, "Pendiente", tarea_tenant["actor_id"])

    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_transicion_invalida_cancelada_a_en_progreso(tarea_session, tarea_tenant):
    """SC-04 triangulation: Cancelada → En_progreso must raise 422."""
    from app.services.tarea_service import TareaService

    svc = TareaService(tarea_session, tarea_tenant["tenant_id"])
    tarea = await svc.crear_tarea(
        _make_create(tarea_tenant["asignee_id"], "Tarea terminal 2"),
        actor_id=tarea_tenant["actor_id"],
    )
    await tarea_session.commit()

    # Cancel directly from Pendiente (valid)
    tarea = await svc.cambiar_estado(tarea.id, "Cancelada", tarea_tenant["actor_id"])
    await tarea_session.commit()

    # Attempt to re-open (invalid)
    with pytest.raises(HTTPException) as exc_info:
        await svc.cambiar_estado(tarea.id, "En_progreso", tarea_tenant["actor_id"])

    assert exc_info.value.status_code == 422


# ── Tests: comentarios ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_comentarios_orden_cronologico(tarea_session, tarea_tenant):
    """SC-05: Comment thread returned in chronological order (oldest first)."""
    from app.schemas.tarea import ComentarioCreate
    from app.services.tarea_service import TareaService

    svc = TareaService(tarea_session, tarea_tenant["tenant_id"])
    tarea = await svc.crear_tarea(
        _make_create(tarea_tenant["asignee_id"], "Tarea con comentarios"),
        actor_id=tarea_tenant["actor_id"],
    )
    await tarea_session.commit()

    # Add 3 comments in order
    c1 = await svc.agregar_comentario(
        tarea.id, ComentarioCreate(contenido="Primer comentario"), tarea_tenant["actor_id"]
    )
    c2 = await svc.agregar_comentario(
        tarea.id, ComentarioCreate(contenido="Segundo comentario"), tarea_tenant["asignee_id"]
    )
    c3 = await svc.agregar_comentario(
        tarea.id, ComentarioCreate(contenido="Tercer comentario"), tarea_tenant["actor_id"]
    )
    await tarea_session.commit()

    thread = await svc.get_comentarios(tarea.id)

    # Thread must be chronological (oldest first)
    assert len(thread) >= 3
    contenidos = [c.contenido for c in thread]
    assert "Primer comentario" in contenidos
    assert "Segundo comentario" in contenidos
    assert "Tercer comentario" in contenidos

    # Verify order: first comment created_at <= last comment created_at
    assert thread[0].created_at <= thread[-1].created_at


# ── Tests: filtros ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_filtro_estado_mis_tareas(tarea_session, tarea_tenant):
    """SC-06: list_mis_tareas filters by estado correctly."""
    from app.schemas.tarea import TareaFilter
    from app.services.tarea_service import TareaService

    svc = TareaService(tarea_session, tarea_tenant["tenant_id"])

    # Create two tasks for asignee: one Pendiente, one that we move to En_progreso
    t1 = await svc.crear_tarea(
        _make_create(tarea_tenant["asignee_id"], "Filtro pendiente"),
        actor_id=tarea_tenant["actor_id"],
    )
    t2 = await svc.crear_tarea(
        _make_create(tarea_tenant["asignee_id"], "Filtro en progreso"),
        actor_id=tarea_tenant["actor_id"],
    )
    await tarea_session.commit()

    await svc.cambiar_estado(t2.id, "En_progreso", tarea_tenant["actor_id"])
    await tarea_session.commit()

    # Filter: only Pendiente
    pendientes = await svc.list_mis_tareas(
        current_user_id=tarea_tenant["asignee_id"],
        filters=TareaFilter(estado="Pendiente"),
    )
    assert all(t.estado == "Pendiente" for t in pendientes)

    # Filter: only En_progreso
    en_progreso = await svc.list_mis_tareas(
        current_user_id=tarea_tenant["asignee_id"],
        filters=TareaFilter(estado="En_progreso"),
    )
    assert all(t.estado == "En_progreso" for t in en_progreso)


@pytest.mark.asyncio
async def test_filtro_admin_por_asignado_a(tarea_session, tarea_tenant):
    """SC-07: list_todas filters by asignado_a for admin view."""
    from app.schemas.tarea import TareaFilter
    from app.services.tarea_service import TareaService

    svc = TareaService(tarea_session, tarea_tenant["tenant_id"])

    # Create tasks for both asignees
    await svc.crear_tarea(
        _make_create(tarea_tenant["asignee_id"], "Admin filtro asignee1"),
        actor_id=tarea_tenant["actor_id"],
    )
    await svc.crear_tarea(
        _make_create(tarea_tenant["asignee2_id"], "Admin filtro asignee2"),
        actor_id=tarea_tenant["actor_id"],
    )
    await tarea_session.commit()

    # Admin filter for asignee_id only
    result = await svc.list_todas_las_tareas(
        filters=TareaFilter(asignado_a=tarea_tenant["asignee_id"])
    )
    assert all(t.asignado_a == tarea_tenant["asignee_id"] for t in result)


# ── Tests: multi-tenancy ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_multi_tenancy_tenant2_no_ve_tareas_tenant1(tarea_session, tarea_tenant):
    """SC-08: Tenant2 service cannot see tasks belonging to tenant1."""
    from app.schemas.tarea import TareaFilter
    from app.services.tarea_service import TareaService

    # Create a task in tenant1
    svc1 = TareaService(tarea_session, tarea_tenant["tenant_id"])
    await svc1.crear_tarea(
        _make_create(tarea_tenant["asignee_id"], "Tarea tenant1 privada"),
        actor_id=tarea_tenant["actor_id"],
    )
    await tarea_session.commit()

    # Query from tenant2 — should see zero tasks
    svc2 = TareaService(tarea_session, tarea_tenant["tenant2_id"])
    tareas_tenant2 = await svc2.list_todas_las_tareas(filters=TareaFilter())

    for t in tareas_tenant2:
        assert t.tenant_id == tarea_tenant["tenant2_id"]


@pytest.mark.asyncio
async def test_profesor_ve_solo_sus_tareas(tarea_session, tarea_tenant):
    """SC-09: list_mis_tareas only returns tasks where asignado_a = current user."""
    from app.schemas.tarea import TareaFilter
    from app.services.tarea_service import TareaService

    svc = TareaService(tarea_session, tarea_tenant["tenant_id"])

    # Create tasks for both users
    await svc.crear_tarea(
        _make_create(tarea_tenant["asignee_id"], "Para asignee1"),
        actor_id=tarea_tenant["actor_id"],
    )
    await svc.crear_tarea(
        _make_create(tarea_tenant["asignee2_id"], "Para asignee2"),
        actor_id=tarea_tenant["actor_id"],
    )
    await tarea_session.commit()

    # asignee_id sees only their tasks
    mis_tareas = await svc.list_mis_tareas(
        current_user_id=tarea_tenant["asignee_id"],
        filters=TareaFilter(),
    )
    for t in mis_tareas:
        assert t.asignado_a == tarea_tenant["asignee_id"]

    # asignee2_id sees only their tasks
    mis_tareas2 = await svc.list_mis_tareas(
        current_user_id=tarea_tenant["asignee2_id"],
        filters=TareaFilter(),
    )
    for t in mis_tareas2:
        assert t.asignado_a == tarea_tenant["asignee2_id"]
