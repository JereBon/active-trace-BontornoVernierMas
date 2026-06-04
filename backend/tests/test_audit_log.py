"""tests/test_audit_log.py — Tests for C-05: audit-log.

TDD cycles:
  6.1 Append-only contract: update() and delete() raise NotImplementedError.
      Create records successfully with all fields.
  6.2 Impersonation attribution: actor_id = real actor, actor_impersonado_id
      = impersonated user when action occurs under impersonation.
  6.3 Impersonation endpoints: POST /api/auth/impersonate (with / without
      permission) and POST /api/auth/impersonate/end.
  6.4 audit_action() helper: DB failure is silently swallowed; action with
      code + filas_afectadas persists correctly.

Design constraints:
  - Uses a real PostgreSQL test DB (no DB mocking).
  - AuditLog has no deleted_at — append-only by design.
  - actor_id is always the real actor, never the impersonated user.

Note on fixture scoping: all async fixtures use scope="module" to share the
same event loop. Function-scoped tests create sessions inline via the
module-scoped factory.
"""

import uuid
from dataclasses import dataclass, field
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.audit_log import AuditLog
from app.repositories.audit_log import AuditLogRepository


# ── Module-scoped fixtures ────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def db_tables_audit(test_session_factory: async_sessionmaker[AsyncSession]):
    """Create all tables (including audit_logs) at module start; drop at end."""
    from app.core import database as db_module
    from app.models.base import Base

    engine = db_module.engine
    assert engine is not None

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@dataclass
class TenantContext:
    """Minimal tenant + user UUIDs for audit tests."""
    tenant_id: uuid.UUID
    actor_id: uuid.UUID
    impersonated_id: uuid.UUID


@pytest_asyncio.fixture(scope="module")
async def audit_context(
    test_session_factory: async_sessionmaker[AsyncSession],
    db_tables_audit,
) -> TenantContext:
    """Provide a real Tenant + two Usuario rows for audit tests."""
    from app.models.tenant import Tenant
    from app.models.usuario import Usuario
    from app.core.security import hash_password

    tenant_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    impersonated_id = uuid.uuid4()

    async with test_session_factory() as session:
        tenant = Tenant(
            id=tenant_id,
            slug=f"audit-tenant-{uuid.uuid4().hex[:8]}",
            nombre="Audit Test Tenant",
        )
        # Use a unique email per test run to avoid conflicts
        suffix = uuid.uuid4().hex[:8]
        from app.core.crypto import encrypt
        from app.core.security import email_hash as make_email_hash

        actor_email = f"actor-{suffix}@test.com"
        imp_email = f"impersonated-{suffix}@test.com"

        actor = Usuario(
            id=actor_id,
            tenant_id=tenant_id,
            email_cifrado=encrypt(actor_email),
            email_hash=make_email_hash(actor_email),
            password_hash=hash_password("password"),
            activo=True,
        )
        impersonated = Usuario(
            id=impersonated_id,
            tenant_id=tenant_id,
            email_cifrado=encrypt(imp_email),
            email_hash=make_email_hash(imp_email),
            password_hash=hash_password("password"),
            activo=True,
        )
        session.add(tenant)
        session.add(actor)
        session.add(impersonated)
        await session.commit()

    return TenantContext(
        tenant_id=tenant_id,
        actor_id=actor_id,
        impersonated_id=impersonated_id,
    )


# ── 6.1 Append-only contract ──────────────────────────────────────────────────


class TestAuditLogAppendOnly:
    """AuditLogRepository enforces append-only: update and delete raise."""

    @pytest.mark.asyncio
    async def test_create_persists_entry(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        audit_context: TenantContext,
    ):
        """Scenario: Create an audit log entry with all fields; it is persisted."""
        ctx = audit_context

        async with test_session_factory() as session:
            repo = AuditLogRepository(session, ctx.tenant_id)
            entry = await repo.create(
                {
                    "actor_id": ctx.actor_id,
                    "accion": "TEST_CREAR",
                    "detalle": {"key": "value"},
                    "filas_afectadas": 5,
                    "ip": "127.0.0.1",
                    "user_agent": "pytest/test",
                }
            )
            await session.commit()

        assert entry.id is not None
        assert entry.tenant_id == ctx.tenant_id
        assert entry.actor_id == ctx.actor_id
        assert entry.accion == "TEST_CREAR"
        assert entry.filas_afectadas == 5
        assert entry.detalle == {"key": "value"}
        assert entry.actor_impersonado_id is None

    @pytest.mark.asyncio
    async def test_create_sets_fecha_hora(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        audit_context: TenantContext,
    ):
        """Scenario: fecha_hora is auto-set (not NULL) on create."""
        ctx = audit_context

        async with test_session_factory() as session:
            repo = AuditLogRepository(session, ctx.tenant_id)
            entry = await repo.create(
                {
                    "actor_id": ctx.actor_id,
                    "accion": "TEST_TIMESTAMP",
                    "filas_afectadas": 0,
                    "ip": "127.0.0.1",
                    "user_agent": "",
                }
            )
            await session.commit()

        assert entry.fecha_hora is not None

    @pytest.mark.asyncio
    async def test_update_raises_not_implemented(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        audit_context: TenantContext,
    ):
        """Scenario: Calling update() raises NotImplementedError."""
        ctx = audit_context

        async with test_session_factory() as session:
            repo = AuditLogRepository(session, ctx.tenant_id)
            with pytest.raises(NotImplementedError):
                await repo.update(uuid.uuid4(), {"accion": "HACKED"})

    @pytest.mark.asyncio
    async def test_soft_delete_raises_not_implemented(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        audit_context: TenantContext,
    ):
        """Scenario: Calling soft_delete() raises NotImplementedError."""
        ctx = audit_context

        async with test_session_factory() as session:
            repo = AuditLogRepository(session, ctx.tenant_id)
            with pytest.raises(NotImplementedError):
                await repo.soft_delete(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_delete_raises_not_implemented(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        audit_context: TenantContext,
    ):
        """Scenario: Calling delete() raises NotImplementedError."""
        ctx = audit_context

        async with test_session_factory() as session:
            repo = AuditLogRepository(session, ctx.tenant_id)
            with pytest.raises(NotImplementedError):
                await repo.delete(uuid.uuid4())


# ── 6.2 Impersonation attribution ─────────────────────────────────────────────


class TestAuditLogImpersonationAttribution:
    """actor_id is always the real actor; actor_impersonado_id = impersonated."""

    @pytest.mark.asyncio
    async def test_entry_with_impersonation_sets_correct_fields(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        audit_context: TenantContext,
    ):
        """Scenario: Action under impersonation records actor_id = real actor,
        actor_impersonado_id = impersonated user."""
        ctx = audit_context

        async with test_session_factory() as session:
            repo = AuditLogRepository(session, ctx.tenant_id)
            entry = await repo.create(
                {
                    "actor_id": ctx.actor_id,
                    "actor_impersonado_id": ctx.impersonated_id,
                    "accion": "IMPERSONACION_INICIAR",
                    "detalle": {"impersonado_id": str(ctx.impersonated_id)},
                    "filas_afectadas": 0,
                    "ip": "10.0.0.1",
                    "user_agent": "test-agent",
                }
            )
            await session.commit()

        assert entry.actor_id == ctx.actor_id, "actor_id must be the real actor"
        assert entry.actor_impersonado_id == ctx.impersonated_id, (
            "actor_impersonado_id must be the impersonated user"
        )

    @pytest.mark.asyncio
    async def test_entry_without_impersonation_has_null_impersonado(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        audit_context: TenantContext,
    ):
        """Scenario: Normal action (no impersonation) has actor_impersonado_id = NULL."""
        ctx = audit_context

        async with test_session_factory() as session:
            repo = AuditLogRepository(session, ctx.tenant_id)
            entry = await repo.create(
                {
                    "actor_id": ctx.actor_id,
                    "accion": "CALIFICACIONES_IMPORTAR",
                    "filas_afectadas": 10,
                    "ip": "10.0.0.1",
                    "user_agent": "test-agent",
                }
            )
            await session.commit()

        assert entry.actor_impersonado_id is None


# ── 6.3 Impersonation endpoints ───────────────────────────────────────────────


class TestImpersonationEndpoints:
    """POST /api/auth/impersonate and /api/auth/impersonate/end."""

    @pytest.mark.asyncio
    async def test_impersonate_without_permission_returns_403(
        self,
        async_client,
        test_session_factory: async_sessionmaker[AsyncSession],
        audit_context: TenantContext,
    ):
        """Scenario: User without impersonacion:usar permission → HTTP 403."""
        ctx = audit_context

        # Create a normal access token without impersonacion:usar permission
        from app.core.security import create_access_token

        token = create_access_token(
            data={
                "sub": str(ctx.actor_id),
                "tenant_id": str(ctx.tenant_id),
            },
            expires_delta=timedelta(minutes=15),
        )

        response = await async_client.post(
            "/api/auth/impersonate",
            json={"user_id": str(ctx.impersonated_id)},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_impersonate_with_permission_returns_token_with_claim(
        self,
        app,
        test_session_factory: async_sessionmaker[AsyncSession],
        audit_context: TenantContext,
    ):
        """Scenario: User with impersonacion:usar starts impersonation → JWT with claim."""
        from httpx import ASGITransport, AsyncClient
        from asgi_lifespan import LifespanManager
        from app.core.schemas import UsuarioAutenticado
        from app.core.security import decode_access_token
        from app.core import dependencies as deps

        ctx = audit_context

        mock_user = UsuarioAutenticado(
            user_id=ctx.actor_id,
            tenant_id=ctx.tenant_id,
            roles=["ADMIN"],
            permisos_efectivos={"impersonacion:usar"},
        )

        async def mock_get_current_user(token=None, session=None):
            return mock_user

        app.dependency_overrides[deps.get_current_user] = mock_get_current_user

        try:
            async with LifespanManager(app) as manager:
                async with AsyncClient(
                    transport=ASGITransport(app=manager.app),
                    base_url="http://testserver",
                ) as client:
                    response = await client.post(
                        "/api/auth/impersonate",
                        json={"user_id": str(ctx.impersonated_id)},
                        headers={"Authorization": "Bearer faketoken"},
                    )
            assert response.status_code == 200, response.text
            data = response.json()
            assert "access_token" in data
            assert data["impersonating_user_id"] == str(ctx.impersonated_id)

            # Verify the returned JWT has the impersonating_user_id claim
            payload = decode_access_token(data["access_token"])
            assert payload["sub"] == str(ctx.actor_id)
            assert payload["impersonating_user_id"] == str(ctx.impersonated_id)
        finally:
            app.dependency_overrides.pop(deps.get_current_user, None)

    @pytest.mark.asyncio
    async def test_end_impersonation_without_active_session_returns_400(
        self,
        app,
        audit_context: TenantContext,
    ):
        """Scenario: End impersonation when no active session → HTTP 400."""
        from httpx import ASGITransport, AsyncClient
        from asgi_lifespan import LifespanManager
        from app.core.schemas import UsuarioAutenticado
        from app.core import dependencies as deps

        ctx = audit_context

        mock_user = UsuarioAutenticado(
            user_id=ctx.actor_id,
            tenant_id=ctx.tenant_id,
            roles=["ADMIN"],
            permisos_efectivos={"impersonacion:usar"},
            impersonando_id=None,
        )

        async def mock_get_current_user(token=None, session=None):
            return mock_user

        app.dependency_overrides[deps.get_current_user] = mock_get_current_user
        try:
            async with LifespanManager(app) as manager:
                async with AsyncClient(
                    transport=ASGITransport(app=manager.app),
                    base_url="http://testserver",
                ) as client:
                    response = await client.post(
                        "/api/auth/impersonate/end",
                        headers={"Authorization": "Bearer faketoken"},
                    )
            assert response.status_code == 400
        finally:
            app.dependency_overrides.pop(deps.get_current_user, None)

    @pytest.mark.asyncio
    async def test_end_impersonation_registers_finalizar_in_audit_log(
        self,
        app,
        test_session_factory: async_sessionmaker[AsyncSession],
        audit_context: TenantContext,
    ):
        """Scenario: End impersonation → IMPERSONACION_FINALIZAR is in audit log."""
        from httpx import ASGITransport, AsyncClient
        from asgi_lifespan import LifespanManager
        from app.core.schemas import UsuarioAutenticado
        from app.core import dependencies as deps

        ctx = audit_context

        mock_user = UsuarioAutenticado(
            user_id=ctx.actor_id,
            tenant_id=ctx.tenant_id,
            roles=["ADMIN"],
            permisos_efectivos={"impersonacion:usar"},
            impersonando_id=ctx.impersonated_id,
        )

        async def mock_get_current_user(token=None, session=None):
            return mock_user

        app.dependency_overrides[deps.get_current_user] = mock_get_current_user
        try:
            async with LifespanManager(app) as manager:
                async with AsyncClient(
                    transport=ASGITransport(app=manager.app),
                    base_url="http://testserver",
                ) as client:
                    response = await client.post(
                        "/api/auth/impersonate/end",
                        headers={"Authorization": "Bearer faketoken"},
                    )
            assert response.status_code == 200, response.text
        finally:
            app.dependency_overrides.pop(deps.get_current_user, None)

        # Verify audit log entry was created
        async with test_session_factory() as session:
            stmt = (
                select(AuditLog)
                .where(
                    AuditLog.tenant_id == ctx.tenant_id,
                    AuditLog.actor_id == ctx.actor_id,
                    AuditLog.accion == "IMPERSONACION_FINALIZAR",
                )
                .order_by(AuditLog.fecha_hora.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            log_entry = result.scalar_one_or_none()

        assert log_entry is not None, "IMPERSONACION_FINALIZAR entry must exist"
        assert log_entry.actor_id == ctx.actor_id
        assert log_entry.actor_impersonado_id == ctx.impersonated_id


# ── 6.4 audit_action() helper ─────────────────────────────────────────────────


class TestAuditActionHelper:
    """audit_action() helper behavior: best-effort and persistence."""

    @pytest.mark.asyncio
    async def test_audit_action_persists_entry(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        audit_context: TenantContext,
    ):
        """Scenario: audit_action() persists entry with code and filas_afectadas."""
        from app.core.audit import audit_action

        ctx = audit_context

        async with test_session_factory() as session:
            await audit_action(
                session,
                actor_id=ctx.actor_id,
                tenant_id=ctx.tenant_id,
                accion="CALIFICACIONES_IMPORTAR",
                detalle={"materia_id": "abc"},
                filas_afectadas=42,
                ip="192.168.1.1",
                user_agent="pytest/helper",
            )
            await session.commit()

        async with test_session_factory() as session:
            stmt = (
                select(AuditLog)
                .where(
                    AuditLog.tenant_id == ctx.tenant_id,
                    AuditLog.actor_id == ctx.actor_id,
                    AuditLog.accion == "CALIFICACIONES_IMPORTAR",
                    AuditLog.filas_afectadas == 42,
                )
                .limit(1)
            )
            result = await session.execute(stmt)
            entry = result.scalar_one_or_none()

        assert entry is not None
        assert entry.filas_afectadas == 42
        assert entry.accion == "CALIFICACIONES_IMPORTAR"

    @pytest.mark.asyncio
    async def test_audit_action_does_not_raise_on_db_failure(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        audit_context: TenantContext,
    ):
        """Scenario: DB write fails → helper logs error and does NOT propagate."""
        import logging
        from app.core.audit import audit_action

        ctx = audit_context

        # Create a mock session that raises on flush
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock(side_effect=RuntimeError("DB is down"))

        # Should NOT raise despite the DB error
        await audit_action(
            mock_session,
            actor_id=ctx.actor_id,
            tenant_id=ctx.tenant_id,
            accion="PADRON_CARGAR",
            filas_afectadas=0,
            ip="127.0.0.1",
            user_agent="pytest",
        )
        # If we get here without an exception, the test passes

    @pytest.mark.asyncio
    async def test_audit_action_with_impersonation_sets_impersonado_id(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        audit_context: TenantContext,
    ):
        """Scenario: audit_action with actor_impersonado_id stores it correctly."""
        from app.core.audit import audit_action

        ctx = audit_context

        async with test_session_factory() as session:
            await audit_action(
                session,
                actor_id=ctx.actor_id,
                tenant_id=ctx.tenant_id,
                accion="ASIGNACION_MODIFICAR",
                filas_afectadas=1,
                ip="10.1.1.1",
                user_agent="",
                actor_impersonado_id=ctx.impersonated_id,
            )
            await session.commit()

        async with test_session_factory() as session:
            stmt = (
                select(AuditLog)
                .where(
                    AuditLog.tenant_id == ctx.tenant_id,
                    AuditLog.actor_id == ctx.actor_id,
                    AuditLog.accion == "ASIGNACION_MODIFICAR",
                )
                .order_by(AuditLog.fecha_hora.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            entry = result.scalar_one_or_none()

        assert entry is not None
        assert entry.actor_impersonado_id == ctx.impersonated_id
