"""tests/test_auditoria.py — TDD tests for C-19: panel-auditoria-metricas.

TDD cycles covered:
  6.2 / 6.3  acciones_por_dia: grouping by day, multi-day triangulation
  6.4 / 6.5  scope (propio): COORDINADOR sees own actions, ADMIN sees all
  6.6 / 6.7  log_paginado: date filters, limit/offset pagination
  6.8 / 6.9  comunicaciones_por_docente: state counts, COORDINADOR scope
  6.10 / 6.11 endpoint 403 (no permission) and 200 (with permission)

Safety net (task 6.1): baseline captured → 14 passed in test_audit_log.py.

Design constraints:
  - Uses a REAL PostgreSQL test DB (no DB mocking).
  - AuditoriaRepository is read-only — never flushes or commits.
  - All inserts go through AuditLogRepository.create() or direct ORM adds.
  - Scope logic is in AuditoriaService, not in AuditoriaRepository.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# Ensure encryption key is available before any app import
_TEST_ENCRYPTION_KEY = "0" * 64
os.environ.setdefault("ENCRYPTION_KEY", _TEST_ENCRYPTION_KEY)

# ── Shared constants ──────────────────────────────────────────────────────────

_TEST_SECRET = "test-secret-key-32-characters-ok!"


def _make_token(user_id: uuid.UUID, tenant_id: uuid.UUID, roles: list[str], permisos: set[str]) -> str:
    from app.core.security import create_access_token
    return create_access_token(
        data={
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "roles": roles,
            "permisos_efectivos": list(permisos),
        },
        expires_delta=timedelta(minutes=30),
    )


# ── Module-scoped fixture: DB tables ─────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def db_tables_auditoria(test_session_factory: async_sessionmaker[AsyncSession]):
    """Ensure all tables exist for auditoria tests; drop afterwards."""
    from app.core import database as db_module
    from app.models.base import Base

    engine = db_module.engine
    assert engine is not None

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── Module-scoped fixture: tenant + users ─────────────────────────────────────


@dataclass
class AuditoriaContext:
    tenant_id: uuid.UUID
    tenant_b_id: uuid.UUID       # separate tenant for isolation test
    admin_id: uuid.UUID
    coord_id: uuid.UUID
    other_id: uuid.UUID          # another actor in tenant A


@pytest_asyncio.fixture(scope="module")
async def auditoria_ctx(
    test_session_factory: async_sessionmaker[AsyncSession],
    db_tables_auditoria,
) -> AuditoriaContext:
    """Provision two tenants and three users for auditoria tests."""
    from app.models.tenant import Tenant
    from app.models.usuario import Usuario
    from app.core.security import hash_password
    from app.core.crypto import encrypt
    from app.core.security import email_hash as make_email_hash

    tenant_id = uuid.uuid4()
    tenant_b_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    coord_id = uuid.uuid4()
    other_id = uuid.uuid4()
    suffix = uuid.uuid4().hex[:8]

    async with test_session_factory() as session:
        session.add(Tenant(
            id=tenant_id,
            slug=f"aud-a-{suffix}",
            nombre="Auditoria Tenant A",
        ))
        session.add(Tenant(
            id=tenant_b_id,
            slug=f"aud-b-{suffix}",
            nombre="Auditoria Tenant B",
        ))

        pw = hash_password("pw")
        for uid, email in [
            (admin_id, f"admin-{suffix}@test.com"),
            (coord_id, f"coord-{suffix}@test.com"),
            (other_id, f"other-{suffix}@test.com"),
        ]:
            session.add(Usuario(
                id=uid,
                tenant_id=tenant_id,
                email_cifrado=encrypt(email),
                email_hash=make_email_hash(email),
                password_hash=pw,
                activo=True,
            ))

        await session.commit()

    return AuditoriaContext(
        tenant_id=tenant_id,
        tenant_b_id=tenant_b_id,
        admin_id=admin_id,
        coord_id=coord_id,
        other_id=other_id,
    )


# ── Helper: insert audit log entries ─────────────────────────────────────────


async def _insert_logs(
    factory: async_sessionmaker[AsyncSession],
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID,
    count: int,
    accion: str = "TEST_ACCION",
    fecha_hora: datetime | None = None,
    detalle: dict | None = None,
) -> list[Any]:
    """Insert N audit log entries and return them."""
    from app.repositories.audit_log import AuditLogRepository

    entries = []
    async with factory() as session:
        repo = AuditLogRepository(session, tenant_id)
        for _ in range(count):
            data: dict = {
                "actor_id": actor_id,
                "accion": accion,
                "filas_afectadas": 0,
                "ip": "127.0.0.1",
                "user_agent": "pytest",
            }
            if fecha_hora is not None:
                data["fecha_hora"] = fecha_hora
            if detalle is not None:
                data["detalle"] = detalle
            entry = await repo.create(data)
            entries.append(entry)
        await session.commit()
    return entries


# ═══════════════════════════════════════════════════════════════════════════════
# 6.2 / 6.3 — acciones_por_dia grouping
# ═══════════════════════════════════════════════════════════════════════════════


class TestAccionesPorDia:
    """AuditoriaRepository.acciones_por_dia groups correctly by calendar day."""

    @pytest.mark.asyncio
    async def test_acciones_por_dia_agrupa_correctamente(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        auditoria_ctx: AuditoriaContext,
    ):
        """RED — insert 3 logs on same day, expect single row with total=3."""
        ctx = auditoria_ctx
        day = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        actor_id = uuid.uuid4()  # fresh actor to avoid cross-test interference
        await _insert_logs(test_session_factory, ctx.tenant_id, actor_id, 3, fecha_hora=day)

        from app.repositories.auditoria_repository import AuditoriaRepository
        async with test_session_factory() as session:
            repo = AuditoriaRepository(session, ctx.tenant_id)
            rows = await repo.acciones_por_dia(actor_id=actor_id)

        assert len(rows) == 1
        assert rows[0]["total"] == 3
        assert rows[0]["fecha"] == date(2025, 1, 15)

    @pytest.mark.asyncio
    async def test_acciones_por_dia_dos_fechas_distintas(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        auditoria_ctx: AuditoriaContext,
    ):
        """GREEN + triangulation — 2 logs on day1, 5 on day2 → 2 rows with correct counts."""
        ctx = auditoria_ctx
        day1 = datetime(2025, 2, 10, 8, 0, 0, tzinfo=timezone.utc)
        day2 = datetime(2025, 2, 20, 8, 0, 0, tzinfo=timezone.utc)
        actor_id = uuid.uuid4()

        await _insert_logs(test_session_factory, ctx.tenant_id, actor_id, 2, fecha_hora=day1)
        await _insert_logs(test_session_factory, ctx.tenant_id, actor_id, 5, fecha_hora=day2)

        from app.repositories.auditoria_repository import AuditoriaRepository
        async with test_session_factory() as session:
            repo = AuditoriaRepository(session, ctx.tenant_id)
            rows = await repo.acciones_por_dia(actor_id=actor_id)

        by_date = {r["fecha"]: r["total"] for r in rows}
        assert by_date[date(2025, 2, 10)] == 2
        assert by_date[date(2025, 2, 20)] == 5
        assert len(rows) == 2


# ═══════════════════════════════════════════════════════════════════════════════
# 6.4 / 6.5 — scope (propio) via AuditoriaService
# ═══════════════════════════════════════════════════════════════════════════════


class TestScopeCoordinador:
    """AuditoriaService applies scope correctly: COORDINADOR sees own, ADMIN sees all."""

    @pytest.mark.asyncio
    async def test_scope_coordinador_solo_ve_propias_acciones(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        auditoria_ctx: AuditoriaContext,
    ):
        """RED — COORDINADOR panel only includes own actions."""
        from app.core.schemas import UsuarioAutenticado
        from app.services.auditoria_service import AuditoriaService

        ctx = auditoria_ctx
        day = datetime(2025, 3, 1, 9, 0, 0, tzinfo=timezone.utc)

        coord_actor = uuid.uuid4()
        other_actor = uuid.uuid4()

        await _insert_logs(test_session_factory, ctx.tenant_id, coord_actor, 4, fecha_hora=day)
        await _insert_logs(test_session_factory, ctx.tenant_id, other_actor, 7, fecha_hora=day)

        mock_coord = UsuarioAutenticado(
            user_id=coord_actor,
            tenant_id=ctx.tenant_id,
            roles=["COORDINADOR"],
            permisos_efectivos={"auditoria:ver"},
        )

        async with test_session_factory() as session:
            svc = AuditoriaService(session, ctx.tenant_id)
            panel = await svc.get_panel(mock_coord)

        # COORDINADOR sees only own 4 actions
        total_coord = sum(r.total for r in panel.acciones_por_dia)
        assert total_coord == 4

        # All per_docente entries belong to coord_actor
        docente_ids = {r.actor_id for r in panel.por_docente}
        assert docente_ids == {coord_actor}

    @pytest.mark.asyncio
    async def test_scope_admin_ve_todas_las_acciones(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        auditoria_ctx: AuditoriaContext,
    ):
        """GREEN + triangulation — ADMIN panel includes all actors' actions."""
        from app.core.schemas import UsuarioAutenticado
        from app.services.auditoria_service import AuditoriaService

        ctx = auditoria_ctx
        day = datetime(2025, 3, 2, 9, 0, 0, tzinfo=timezone.utc)

        actor_a = uuid.uuid4()
        actor_b = uuid.uuid4()

        await _insert_logs(test_session_factory, ctx.tenant_id, actor_a, 3, fecha_hora=day)
        await _insert_logs(test_session_factory, ctx.tenant_id, actor_b, 5, fecha_hora=day)

        mock_admin = UsuarioAutenticado(
            user_id=uuid.uuid4(),  # different user — ADMIN sees all
            tenant_id=ctx.tenant_id,
            roles=["ADMIN"],
            permisos_efectivos={"auditoria:ver"},
        )

        async with test_session_factory() as session:
            svc = AuditoriaService(session, ctx.tenant_id)
            panel = await svc.get_panel(mock_admin)

        # ADMIN panel must include both actors
        docente_ids = {r.actor_id for r in panel.por_docente}
        assert actor_a in docente_ids
        assert actor_b in docente_ids


# ═══════════════════════════════════════════════════════════════════════════════
# 6.6 / 6.7 — log_paginado: date filters and pagination
# ═══════════════════════════════════════════════════════════════════════════════


class TestLogPaginado:
    """AuditoriaRepository.log_paginado filters by date and supports limit/offset."""

    @pytest.mark.asyncio
    async def test_log_paginado_filtro_fecha(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        auditoria_ctx: AuditoriaContext,
    ):
        """RED — only entries inside the date range are returned."""
        ctx = auditoria_ctx
        actor_id = uuid.uuid4()

        inside = datetime(2025, 4, 15, 12, 0, tzinfo=timezone.utc)
        outside = datetime(2025, 4, 20, 12, 0, tzinfo=timezone.utc)

        await _insert_logs(test_session_factory, ctx.tenant_id, actor_id, 3, fecha_hora=inside)
        await _insert_logs(test_session_factory, ctx.tenant_id, actor_id, 2, fecha_hora=outside)

        from app.repositories.auditoria_repository import AuditoriaRepository
        async with test_session_factory() as session:
            repo = AuditoriaRepository(session, ctx.tenant_id)
            items, total = await repo.log_paginado(
                actor_id=actor_id,
                fecha_desde=date(2025, 4, 14),
                fecha_hasta=date(2025, 4, 16),
            )

        assert total == 3
        assert len(items) == 3

    @pytest.mark.asyncio
    async def test_log_paginado_limit_offset(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        auditoria_ctx: AuditoriaContext,
    ):
        """GREEN + triangulation — limit and offset paginate correctly."""
        ctx = auditoria_ctx
        actor_id = uuid.uuid4()
        base_day = datetime(2025, 5, 1, 12, 0, tzinfo=timezone.utc)

        await _insert_logs(test_session_factory, ctx.tenant_id, actor_id, 10, fecha_hora=base_day)

        from app.repositories.auditoria_repository import AuditoriaRepository
        async with test_session_factory() as session:
            repo = AuditoriaRepository(session, ctx.tenant_id)

            # First page: limit=4, offset=0
            items_p1, total = await repo.log_paginado(actor_id=actor_id, limit=4, offset=0)
            # Second page: limit=4, offset=4
            items_p2, total2 = await repo.log_paginado(actor_id=actor_id, limit=4, offset=4)

        assert total == 10
        assert len(items_p1) == 4
        assert len(items_p2) == 4
        # Pages must not overlap
        ids_p1 = {i.id for i in items_p1}
        ids_p2 = {i.id for i in items_p2}
        assert ids_p1.isdisjoint(ids_p2)


# ═══════════════════════════════════════════════════════════════════════════════
# 6.8 / 6.9 — comunicaciones_por_docente
# ═══════════════════════════════════════════════════════════════════════════════


class TestComunicacionesPorDocente:
    """AuditoriaRepository.comunicaciones_por_docente counts states correctly."""

    @pytest_asyncio.fixture(scope="class")
    async def comun_actor(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        auditoria_ctx: AuditoriaContext,
    ) -> uuid.UUID:
        """Insert comunicaciones with different states for a fresh actor."""
        from app.models.comunicacion import Comunicacion
        from app.core.crypto import encrypt

        ctx = auditoria_ctx
        actor_id = uuid.uuid4()
        lote_id = uuid.uuid4()

        estados_counts = {
            "Pendiente": 2,
            "Enviado": 3,
            "Error": 1,
        }

        async with test_session_factory() as session:
            for estado, count in estados_counts.items():
                for _ in range(count):
                    session.add(Comunicacion(
                        tenant_id=ctx.tenant_id,
                        enviado_por=actor_id,
                        materia_id=None,
                        destinatario=encrypt("dest@test.com"),
                        asunto="Test asunto",
                        cuerpo="Test cuerpo",
                        estado=estado,
                        aprobado=True,
                        lote_id=lote_id,
                    ))
            await session.commit()

        return actor_id

    @pytest.mark.asyncio
    async def test_comunicaciones_por_docente_conteo_por_estado(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        auditoria_ctx: AuditoriaContext,
        comun_actor: uuid.UUID,
    ):
        """RED — counts per estado are correct for the actor."""
        from app.repositories.auditoria_repository import AuditoriaRepository

        ctx = auditoria_ctx
        async with test_session_factory() as session:
            repo = AuditoriaRepository(session, ctx.tenant_id)
            rows = await repo.comunicaciones_por_docente(docente_id=comun_actor)

        assert len(rows) == 1
        row = rows[0]
        assert row["docente_id"] == comun_actor
        assert row["pendiente"] == 2
        assert row["enviado"] == 3
        assert row["error"] == 1
        assert row["cancelado"] == 0

    @pytest.mark.asyncio
    async def test_scope_coordinador_comunicaciones(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        auditoria_ctx: AuditoriaContext,
        comun_actor: uuid.UUID,
    ):
        """GREEN + triangulation — COORDINADOR scope returns only own comuns."""
        from app.core.schemas import UsuarioAutenticado
        from app.services.auditoria_service import AuditoriaService

        ctx = auditoria_ctx
        mock_coord = UsuarioAutenticado(
            user_id=comun_actor,
            tenant_id=ctx.tenant_id,
            roles=["COORDINADOR"],
            permisos_efectivos={"auditoria:ver"},
        )

        async with test_session_factory() as session:
            svc = AuditoriaService(session, ctx.tenant_id)
            result = await svc.get_comunicaciones(mock_coord)

        assert len(result) == 1
        assert result[0].docente_id == comun_actor
        assert result[0].enviado == 3


# ═══════════════════════════════════════════════════════════════════════════════
# 6.10 / 6.11 — Endpoint authorization
# ═══════════════════════════════════════════════════════════════════════════════


@pytest_asyncio.fixture(scope="module")
async def auditoria_http_client(
    test_session_factory: async_sessionmaker[AsyncSession],
):
    """HTTP client wired to the full FastAPI app."""
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
    from httpx import ASGITransport, AsyncClient

    async with LifespanManager(app) as manager:
        async with AsyncClient(
            transport=ASGITransport(app=manager.app),
            base_url="http://testserver",
        ) as client:
            yield client, manager.app


def _make_app_with_perm(
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
    roles: list[str],
    permisos: set[str],
):
    """Create a FastAPI app with a mock user injected via dependency_overrides."""
    from app.core.config import _reset_settings
    from app.core.schemas import UsuarioAutenticado
    from app.core import dependencies as deps
    from app.main import create_application

    test_db_url = os.environ.get(
        "DATABASE_URL_TEST",
        "postgresql+asyncpg://activia:changeme@localhost:5432/activia_trace_test",
    )
    os.environ["DATABASE_URL"] = test_db_url
    os.environ["SECRET_KEY"] = _TEST_SECRET
    os.environ["ENCRYPTION_KEY"] = _TEST_ENCRYPTION_KEY
    _reset_settings()

    mock_user = UsuarioAutenticado(
        user_id=user_id,
        tenant_id=tenant_id,
        roles=roles,
        permisos_efectivos=permisos,
    )

    async def mock_get_current_user(token=None, session=None):
        return mock_user

    app = create_application()
    app.dependency_overrides[deps.get_current_user] = mock_get_current_user
    return app


class TestAuditoriaEndpointAuth:
    """Endpoint guard: auditoria:ver required; correct HTTP codes returned."""

    @pytest.mark.asyncio
    async def test_panel_endpoint_403_sin_permiso(
        self,
        auditoria_http_client,
        auditoria_ctx: AuditoriaContext,
    ):
        """RED — GET /v1/auditoria/panel without auditoria:ver → 403.

        Uses a mock user with empty permisos so RBAC guard fires.
        """
        client, _ = auditoria_http_client
        ctx = auditoria_ctx

        token = _make_token(
            ctx.admin_id, ctx.tenant_id, roles=["ADMIN"], permisos=set()  # no auditoria:ver
        )
        resp = await client.get(
            "/v1/auditoria/panel",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_panel_endpoint_200_con_permiso(
        self,
        auditoria_ctx: AuditoriaContext,
    ):
        """GREEN — GET /v1/auditoria/panel with auditoria:ver → 200.

        Uses dependency_overrides to inject a mock user with the permission.
        """
        import httpx
        from asgi_lifespan import LifespanManager

        ctx = auditoria_ctx
        app = _make_app_with_perm(
            ctx.admin_id, ctx.tenant_id, ["ADMIN"], {"auditoria:ver"}
        )
        try:
            async with LifespanManager(app) as mgr:
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=mgr.app),
                    base_url="http://testserver",
                ) as client:
                    resp = await client.get("/v1/auditoria/panel")
            assert resp.status_code == 200
            data = resp.json()
            assert "acciones_por_dia" in data
            assert "por_docente" in data
            assert "por_materia" in data
        finally:
            app.dependency_overrides.clear()
