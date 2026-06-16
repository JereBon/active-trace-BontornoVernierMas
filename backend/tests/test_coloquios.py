"""tests/test_coloquios.py — Tests for C-14: evaluaciones-y-coloquios.

TDD cycles:
  RED→GREEN  1: Create evaluacion with permission → 201, stored in DB
  TRIANGULATE: Create evaluacion without permission → 403
  RED→GREEN  2: Reserva decrements cupo
  TRIANGULATE: No cupo available → 409
  RED→GREEN  3: Metricas: convocadas/reservas/libres correct counts
  TRIANGULATE: Cancel reserva restores cupo
  RED→GREEN  4: Resultado consolidated
  RED→GREEN  5: Multi-tenancy: tenant A cannot see evaluacion from tenant B
  TRIANGULATE: List evaluaciones filtered by materia_id
  RED→GREEN  6: Alumno already has Activa reserva → 409 on second booking

Uses real PostgreSQL test DB. No DB mocking.
Module-scoped fixtures share DB setup and app client.
"""

import os
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.permisos import (
    EVALUACIONES_GESTIONAR,
    EVALUACIONES_RESERVAR,
    EVALUACIONES_RESULTADO,
)
from app.models.base import Base
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.tenant import Tenant  # noqa: F401 — needed for metadata
from app.models.usuario import Usuario
from app.models.usuario_rol import UsuarioRol

_TEST_SECRET = "test-secret-key-32-characters-ok!"
_TEST_ENCRYPTION_KEY = "0" * 64


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


@dataclass
class TenantInfo:
    id: uuid.UUID
    slug: str


# ── Module-scoped setup ───────────────────────────────────────────────────────


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


def _usuario_kwargs(tenant_id: uuid.UUID) -> dict:
    from app.core.security import email_hash as _eh, hash_password

    raw = f"user-{uuid.uuid4().hex[:8]}@coloquio-test.com"
    return {
        "id": uuid.uuid4(),
        "tenant_id": tenant_id,
        "email_cifrado": "placeholder-encrypted",
        "email_hash": _eh(raw),
        "password_hash": hash_password("testpassword123"),
        "activo": True,
    }


async def _make_tenant(
    session_factory: async_sessionmaker[AsyncSession],
) -> TenantInfo:
    async with session_factory() as session:
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"col-tenant-{uuid.uuid4().hex[:8]}",
            nombre="Coloquios Test Tenant",
        )
        session.add(tenant)
        await session.commit()
    return TenantInfo(id=tenant.id, slug=tenant.slug)


async def _make_user_with_permissions(
    session_factory: async_sessionmaker[AsyncSession],
    tenant_id: uuid.UUID,
    permission_codes: list[str],
    rol_codigo: str,
) -> UserInfo:
    """Create a user with specified permissions via a new role."""
    async with session_factory() as session:
        # Create permissions (upsert-style: fetch existing or create new)
        from sqlalchemy import select as _select

        permisos = []
        for codigo in permission_codes:
            existing_stmt = _select(Permiso).where(
                Permiso.tenant_id == tenant_id,
                Permiso.codigo == codigo,
            )
            existing_result = await session.execute(existing_stmt)
            existing_p = existing_result.scalar_one_or_none()
            if existing_p is not None:
                permisos.append(existing_p)
                continue
            p = Permiso(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                codigo=codigo,
                descripcion=f"Test perm {codigo}",
            )
            session.add(p)
            permisos.append(p)
        await session.flush()

        # Create role
        rol = Rol(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            codigo=rol_codigo,
            nombre=f"Test Role {rol_codigo}",
        )
        session.add(rol)
        await session.flush()

        # Assign permissions to role
        for p in permisos:
            rp = RolPermiso(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                rol_id=rol.id,
                permiso_id=p.id,
            )
            session.add(rp)
        await session.flush()

        # Create user
        kwargs = _usuario_kwargs(tenant_id)
        user_id = kwargs["id"]
        u = Usuario(**kwargs)
        session.add(u)
        await session.flush()

        # Assign role to user
        ur = UsuarioRol(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            usuario_id=user_id,
            rol_id=rol.id,
            vig_desde=date.today() - timedelta(days=30),
            vig_hasta=None,
        )
        session.add(ur)
        await session.commit()

    token = _make_token(user_id, tenant_id)
    return UserInfo(id=user_id, tenant_id=tenant_id, token=token)


# ── Module-scoped tenants and users ──────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def col_tenant(
    test_session_factory: async_sessionmaker[AsyncSession],
    db_tables,
) -> TenantInfo:
    return await _make_tenant(test_session_factory)


@pytest_asyncio.fixture(scope="module")
async def other_tenant(
    test_session_factory: async_sessionmaker[AsyncSession],
    db_tables,
) -> TenantInfo:
    """A second tenant to verify cross-tenant isolation."""
    return await _make_tenant(test_session_factory)


@pytest_asyncio.fixture(scope="module")
async def coordinator_user(
    test_session_factory: async_sessionmaker[AsyncSession],
    col_tenant: TenantInfo,
) -> UserInfo:
    """User with evaluaciones:gestionar + evaluaciones:resultado."""
    return await _make_user_with_permissions(
        test_session_factory,
        col_tenant.id,
        [EVALUACIONES_GESTIONAR, EVALUACIONES_RESULTADO],
        "COORD_COL",
    )


@pytest_asyncio.fixture(scope="module")
async def alumno_user(
    test_session_factory: async_sessionmaker[AsyncSession],
    col_tenant: TenantInfo,
) -> UserInfo:
    """User with evaluaciones:reservar (alumno role)."""
    return await _make_user_with_permissions(
        test_session_factory,
        col_tenant.id,
        [EVALUACIONES_RESERVAR],
        "ALUMNO_COL",
    )


@pytest_asyncio.fixture(scope="module")
async def alumno_user2(
    test_session_factory: async_sessionmaker[AsyncSession],
    col_tenant: TenantInfo,
) -> UserInfo:
    """Second alumno for multi-user tests."""
    return await _make_user_with_permissions(
        test_session_factory,
        col_tenant.id,
        [EVALUACIONES_RESERVAR],
        f"ALUMNO_COL2_{uuid.uuid4().hex[:4]}",
    )


@pytest_asyncio.fixture(scope="module")
async def noauth_user(
    test_session_factory: async_sessionmaker[AsyncSession],
    col_tenant: TenantInfo,
) -> UserInfo:
    """User with no permissions."""
    async with test_session_factory() as session:
        kwargs = _usuario_kwargs(col_tenant.id)
        user_id = kwargs["id"]
        u = Usuario(**kwargs)
        session.add(u)
        await session.commit()
    token = _make_token(user_id, col_tenant.id)
    return UserInfo(id=user_id, tenant_id=col_tenant.id, token=token)


@pytest_asyncio.fixture(scope="module")
async def coordinator_other_tenant(
    test_session_factory: async_sessionmaker[AsyncSession],
    other_tenant: TenantInfo,
) -> UserInfo:
    """Coordinator in the OTHER tenant — must not see col_tenant data."""
    return await _make_user_with_permissions(
        test_session_factory,
        other_tenant.id,
        [EVALUACIONES_GESTIONAR, EVALUACIONES_RESULTADO],
        "COORD_OTHER",
    )


# ── Payload factory ───────────────────────────────────────────────────────────


def _evaluacion_payload(
    materia_id: uuid.UUID | None = None,
    cohorte_id: uuid.UUID | None = None,
    cupos: int = 5,
) -> dict:
    return {
        "materia_id": str(materia_id or uuid.uuid4()),
        "cohorte_id": str(cohorte_id or uuid.uuid4()),
        "tipo": "Coloquio",
        "instancia": "Coloquio Final",
        "dias_disponibles": 7,
        "cupos_disponibles": cupos,
    }


def _reserva_payload(offset_hours: int = 48) -> dict:
    fecha_hora = datetime.now(tz=timezone.utc) + timedelta(hours=offset_hours)
    return {"fecha_hora": fecha_hora.isoformat()}


# ── Test 1 RED→GREEN: create evaluacion with permission → 201 ─────────────────


@pytest.mark.anyio
async def test_create_evaluacion_with_permission(
    test_client: AsyncClient,
    test_session_factory: async_sessionmaker[AsyncSession],
    coordinator_user: UserInfo,
    col_tenant: TenantInfo,
):
    """RED→GREEN: coordinator creates evaluacion → 201, stored in DB with correct tenant."""
    from app.models.evaluacion import Evaluacion

    payload = _evaluacion_payload()
    resp = await test_client.post(
        "/v1/coloquios",
        json=payload,
        headers={"Authorization": f"Bearer {coordinator_user.token}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["instancia"] == "Coloquio Final"
    assert data["cupos_disponibles"] == 5
    assert data["estado"] == "Abierta"
    assert data["tenant_id"] == str(col_tenant.id)

    # Verify in DB
    ev_id = uuid.UUID(data["id"])
    async with test_session_factory() as session:
        ev = await session.get(Evaluacion, ev_id)
    assert ev is not None
    assert ev.tenant_id == col_tenant.id
    assert ev.cupos_disponibles == 5


# ── TRIANGULATE: create without permission → 403 ─────────────────────────────


@pytest.mark.anyio
async def test_create_evaluacion_without_permission(
    test_client: AsyncClient,
    noauth_user: UserInfo,
):
    """TRIANGULATE: user without evaluaciones:gestionar → 403."""
    resp = await test_client.post(
        "/v1/coloquios",
        json=_evaluacion_payload(),
        headers={"Authorization": f"Bearer {noauth_user.token}"},
    )
    assert resp.status_code == 403


# ── Test 2 RED→GREEN: reserva decrements cupo ────────────────────────────────


@pytest.mark.anyio
async def test_reserva_decrements_cupo(
    test_client: AsyncClient,
    test_session_factory: async_sessionmaker[AsyncSession],
    coordinator_user: UserInfo,
    alumno_user: UserInfo,
    col_tenant: TenantInfo,
):
    """RED→GREEN: alumno reserves slot → cupos_disponibles decremented by 1."""
    from app.models.evaluacion import Evaluacion

    # Create evaluacion with 3 cupos
    create_resp = await test_client.post(
        "/v1/coloquios",
        json=_evaluacion_payload(cupos=3),
        headers={"Authorization": f"Bearer {coordinator_user.token}"},
    )
    assert create_resp.status_code == 201
    ev_id = create_resp.json()["id"]

    # Alumno reserves
    reserva_resp = await test_client.post(
        f"/v1/coloquios/{ev_id}/reservas",
        json=_reserva_payload(),
        headers={"Authorization": f"Bearer {alumno_user.token}"},
    )
    assert reserva_resp.status_code == 201, reserva_resp.text
    reserva_data = reserva_resp.json()
    assert reserva_data["estado"] == "Activa"
    assert reserva_data["alumno_id"] == str(alumno_user.id)

    # Verify cupo decremented in DB
    async with test_session_factory() as session:
        ev = await session.get(Evaluacion, uuid.UUID(ev_id))
    assert ev is not None
    assert ev.cupos_disponibles == 2  # was 3, now 2


# ── TRIANGULATE: no cupos → 409 ──────────────────────────────────────────────


@pytest.mark.anyio
async def test_reserva_sin_cupos_409(
    test_client: AsyncClient,
    coordinator_user: UserInfo,
    alumno_user: UserInfo,
    alumno_user2: UserInfo,
):
    """TRIANGULATE: evaluacion with 1 cupo, two alumnos try to book → second gets 409."""
    # Create evaluacion with 1 cupo
    create_resp = await test_client.post(
        "/v1/coloquios",
        json=_evaluacion_payload(cupos=1),
        headers={"Authorization": f"Bearer {coordinator_user.token}"},
    )
    assert create_resp.status_code == 201
    ev_id = create_resp.json()["id"]

    # First alumno reserves successfully
    resp1 = await test_client.post(
        f"/v1/coloquios/{ev_id}/reservas",
        json=_reserva_payload(),
        headers={"Authorization": f"Bearer {alumno_user.token}"},
    )
    assert resp1.status_code == 201

    # Second alumno fails — no cupos
    resp2 = await test_client.post(
        f"/v1/coloquios/{ev_id}/reservas",
        json=_reserva_payload(),
        headers={"Authorization": f"Bearer {alumno_user2.token}"},
    )
    assert resp2.status_code == 409
    assert "cupos" in resp2.json()["detail"].lower()


# ── Test 3 RED→GREEN: metrics ─────────────────────────────────────────────────


@pytest.mark.anyio
async def test_metricas_correct_counts(
    test_client: AsyncClient,
    coordinator_user: UserInfo,
    alumno_user: UserInfo,
):
    """RED→GREEN: metricas endpoint returns correct aggregate counts."""
    # Get baseline metricas
    base_resp = await test_client.get(
        "/v1/coloquios/metricas",
        headers={"Authorization": f"Bearer {coordinator_user.token}"},
    )
    assert base_resp.status_code == 200, base_resp.text
    base = base_resp.json()

    # Create a new evaluacion with 5 cupos
    create_resp = await test_client.post(
        "/v1/coloquios",
        json=_evaluacion_payload(cupos=5),
        headers={"Authorization": f"Bearer {coordinator_user.token}"},
    )
    assert create_resp.status_code == 201
    ev_id = create_resp.json()["id"]

    # Alumno reserves one slot
    await test_client.post(
        f"/v1/coloquios/{ev_id}/reservas",
        json=_reserva_payload(),
        headers={"Authorization": f"Bearer {alumno_user.token}"},
    )

    # Check metricas increased correctly
    metricas_resp = await test_client.get(
        "/v1/coloquios/metricas",
        headers={"Authorization": f"Bearer {coordinator_user.token}"},
    )
    assert metricas_resp.status_code == 200
    metricas = metricas_resp.json()

    assert metricas["total_convocatorias"] >= base["total_convocatorias"] + 1
    assert metricas["total_reservas_activas"] >= base["total_reservas_activas"] + 1
    assert metricas["total_cupos_libres"] >= base["total_cupos_libres"] + 4  # 5 cupos - 1 reserva


# ── TRIANGULATE: cancel reserva restores cupo ────────────────────────────────


@pytest.mark.anyio
async def test_cancel_reserva_restores_cupo(
    test_client: AsyncClient,
    test_session_factory: async_sessionmaker[AsyncSession],
    coordinator_user: UserInfo,
    alumno_user: UserInfo,
):
    """TRIANGULATE: cancelling a reserva restores one cupo to the evaluacion."""
    from app.models.evaluacion import Evaluacion

    # Create evaluacion with 2 cupos
    create_resp = await test_client.post(
        "/v1/coloquios",
        json=_evaluacion_payload(cupos=2),
        headers={"Authorization": f"Bearer {coordinator_user.token}"},
    )
    assert create_resp.status_code == 201
    ev_id = create_resp.json()["id"]

    # Alumno reserves
    reserva_resp = await test_client.post(
        f"/v1/coloquios/{ev_id}/reservas",
        json=_reserva_payload(),
        headers={"Authorization": f"Bearer {alumno_user.token}"},
    )
    assert reserva_resp.status_code == 201
    reserva_id = reserva_resp.json()["id"]

    # Verify cupo decremented
    async with test_session_factory() as session:
        ev = await session.get(Evaluacion, uuid.UUID(ev_id))
    assert ev is not None
    assert ev.cupos_disponibles == 1

    # Cancel the reserva
    cancel_resp = await test_client.post(
        f"/v1/coloquios/{ev_id}/reservas/{reserva_id}/cancelar",
        headers={"Authorization": f"Bearer {alumno_user.token}"},
    )
    assert cancel_resp.status_code == 200, cancel_resp.text
    assert cancel_resp.json()["estado"] == "Cancelada"

    # Verify cupo restored — re-fetch in a fresh session
    async with test_session_factory() as session2:
        ev_after = await session2.get(Evaluacion, uuid.UUID(ev_id))
    assert ev_after is not None
    assert ev_after.cupos_disponibles == 2  # restored


# ── Test 4 RED→GREEN: resultado consolidated ─────────────────────────────────


@pytest.mark.anyio
async def test_create_and_list_resultado(
    test_client: AsyncClient,
    coordinator_user: UserInfo,
    alumno_user: UserInfo,
):
    """RED→GREEN: coordinator registers resultado → 201; list_resultados returns it."""
    # Create evaluacion
    create_resp = await test_client.post(
        "/v1/coloquios",
        json=_evaluacion_payload(cupos=5),
        headers={"Authorization": f"Bearer {coordinator_user.token}"},
    )
    assert create_resp.status_code == 201
    ev_id = create_resp.json()["id"]

    # Register resultado
    resultado_payload = {
        "alumno_id": str(alumno_user.id),
        "aprobado": True,
        "nota_final": "8",
        "observaciones": "Buen desempeño",
    }
    resultado_resp = await test_client.post(
        f"/v1/coloquios/{ev_id}/resultados",
        json=resultado_payload,
        headers={"Authorization": f"Bearer {coordinator_user.token}"},
    )
    assert resultado_resp.status_code == 201, resultado_resp.text
    data = resultado_resp.json()
    assert data["aprobado"] is True
    assert data["nota_final"] == "8"
    assert data["alumno_id"] == str(alumno_user.id)

    # List resultados
    list_resp = await test_client.get(
        f"/v1/coloquios/{ev_id}/resultados",
        headers={"Authorization": f"Bearer {coordinator_user.token}"},
    )
    assert list_resp.status_code == 200
    resultados = list_resp.json()
    ids = [r["id"] for r in resultados]
    assert data["id"] in ids


# ── Test 5 RED→GREEN: multi-tenancy isolation ─────────────────────────────────


@pytest.mark.anyio
async def test_multitenant_isolation(
    test_client: AsyncClient,
    coordinator_user: UserInfo,
    coordinator_other_tenant: UserInfo,
):
    """RED→GREEN: evaluacion created in tenant A is NOT visible to tenant B."""
    # Create evaluacion in tenant A
    create_resp = await test_client.post(
        "/v1/coloquios",
        json=_evaluacion_payload(cupos=5),
        headers={"Authorization": f"Bearer {coordinator_user.token}"},
    )
    assert create_resp.status_code == 201
    ev_id = create_resp.json()["id"]

    # Tenant B cannot retrieve it
    get_resp = await test_client.get(
        f"/v1/coloquios/{ev_id}",
        headers={"Authorization": f"Bearer {coordinator_other_tenant.token}"},
    )
    assert get_resp.status_code == 404, (
        f"Expected 404 for cross-tenant access, got {get_resp.status_code}: {get_resp.text}"
    )

    # Tenant B's list does NOT include it
    list_resp = await test_client.get(
        "/v1/coloquios",
        headers={"Authorization": f"Bearer {coordinator_other_tenant.token}"},
    )
    assert list_resp.status_code == 200
    ids = [e["id"] for e in list_resp.json()]
    assert ev_id not in ids, "Tenant B should NOT see Tenant A's evaluacion"


# ── TRIANGULATE: list evaluaciones filtered by materia_id ────────────────────


@pytest.mark.anyio
async def test_list_evaluaciones_filtered_by_materia(
    test_client: AsyncClient,
    coordinator_user: UserInfo,
):
    """TRIANGULATE: list with materia_id filter returns only matching evaluaciones."""
    materia_a = uuid.uuid4()
    materia_b = uuid.uuid4()

    # Create two evaluaciones, each for a different materia
    for m in [materia_a, materia_b]:
        r = await test_client.post(
            "/v1/coloquios",
            json=_evaluacion_payload(materia_id=m),
            headers={"Authorization": f"Bearer {coordinator_user.token}"},
        )
        assert r.status_code == 201

    # Filter by materia_a
    list_resp = await test_client.get(
        f"/v1/coloquios?materia_id={materia_a}",
        headers={"Authorization": f"Bearer {coordinator_user.token}"},
    )
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert all(e["materia_id"] == str(materia_a) for e in items), (
        "Filtered list should only contain evaluaciones for materia_a"
    )
    materia_b_ids = [e["id"] for e in items if e["materia_id"] == str(materia_b)]
    assert len(materia_b_ids) == 0


# ── Test 6 RED→GREEN: duplicate active reserva → 409 ─────────────────────────


@pytest.mark.anyio
async def test_duplicate_reserva_409(
    test_client: AsyncClient,
    coordinator_user: UserInfo,
    alumno_user: UserInfo,
):
    """RED→GREEN: alumno with existing Activa reserva tries to book again → 409."""
    # Create evaluacion with 10 cupos (enough for multiple attempts)
    create_resp = await test_client.post(
        "/v1/coloquios",
        json=_evaluacion_payload(cupos=10),
        headers={"Authorization": f"Bearer {coordinator_user.token}"},
    )
    assert create_resp.status_code == 201
    ev_id = create_resp.json()["id"]

    # First booking — success
    first_resp = await test_client.post(
        f"/v1/coloquios/{ev_id}/reservas",
        json=_reserva_payload(),
        headers={"Authorization": f"Bearer {alumno_user.token}"},
    )
    assert first_resp.status_code == 201

    # Second booking by same alumno for same evaluacion — conflict
    second_resp = await test_client.post(
        f"/v1/coloquios/{ev_id}/reservas",
        json=_reserva_payload(offset_hours=72),
        headers={"Authorization": f"Bearer {alumno_user.token}"},
    )
    assert second_resp.status_code == 409
    assert "reserva" in second_resp.json()["detail"].lower()


# ── TRIANGULATE: metricas - noauth → 403 ─────────────────────────────────────


@pytest.mark.anyio
async def test_metricas_without_permission(
    test_client: AsyncClient,
    noauth_user: UserInfo,
):
    """TRIANGULATE: GET /metricas without evaluaciones:gestionar → 403."""
    resp = await test_client.get(
        "/v1/coloquios/metricas",
        headers={"Authorization": f"Bearer {noauth_user.token}"},
    )
    assert resp.status_code == 403
