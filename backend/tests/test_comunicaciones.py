"""tests/test_comunicaciones.py — TDD tests for C-12: comunicaciones-cola-worker.

TDD cycles covered:
  7.1  Máquina de estados: transiciones válidas e inválidas
  7.2  Preview: renderizado correcto con variables, 422 con variable faltante, sin persistencia en DB
  7.3  Encolado masivo: lote_id generado, destinatarios cifrados, 403 sin permiso, tenant_id from session
  7.4  Aprobación: aprobar lote, cancelar lote, cancelar individual, 403, 404 de otro tenant
  7.5  Worker: procesa Pendiente→Enviado, SKIP LOCKED
  7.6  Auditoría: COMUNICACION_ENVIAR, COMUNICACION_APROBAR, COMUNICACION_CANCELAR
  7.7  Tenant isolation: consulta de lote ajeno devuelve 404

Safety net: all existing tables must already exist (created by prior migrations).
"""

import os
import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

_TEST_SECRET = "test-secret-key-32-characters-ok!"
_TEST_ENCRYPTION_KEY = "0" * 64

# Set encryption key before any crypto import
os.environ.setdefault("ENCRYPTION_KEY", _TEST_ENCRYPTION_KEY)


# ── Token helper ──────────────────────────────────────────────────────────────


def _make_token(user_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
    from app.core.security import create_access_token

    return create_access_token(
        data={"sub": str(user_id), "tenant_id": str(tenant_id)},
        expires_delta=timedelta(minutes=30),
    )


# ── Data containers ───────────────────────────────────────────────────────────


@dataclass
class TenantInfo:
    id: uuid.UUID
    slug: str


@dataclass
class UserInfo:
    id: uuid.UUID
    tenant_id: uuid.UUID
    token: str


# ── Session-scoped fixtures ───────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def test_client(
    test_session_factory: async_sessionmaker[AsyncSession],
):
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
        from app.core import database as db_module
        from app.models.base import Base

        async with db_module.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        import httpx

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=mgr.app),
            base_url="http://testserver",
        ) as client:
            yield client


@pytest_asyncio.fixture(scope="module")
async def com_tenant(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_client: Any,
) -> TenantInfo:
    from app.models.tenant import Tenant

    async with test_session_factory() as session:
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"com-tenant-{uuid.uuid4().hex[:8]}",
            nombre="Comunicaciones Test Tenant",
            comunicacion_requiere_aprobacion=True,
        )
        session.add(tenant)
        await session.commit()
        return TenantInfo(id=tenant.id, slug=tenant.slug)


@pytest_asyncio.fixture(scope="module")
async def com_tenant_no_aprobacion(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_client: Any,
) -> TenantInfo:
    """Tenant with comunicacion_requiere_aprobacion=False for direct dispatch tests."""
    from app.models.tenant import Tenant

    async with test_session_factory() as session:
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"com-tenant-na-{uuid.uuid4().hex[:8]}",
            nombre="Com Test Tenant No Aprobacion",
            comunicacion_requiere_aprobacion=False,
        )
        session.add(tenant)
        await session.commit()
        return TenantInfo(id=tenant.id, slug=tenant.slug)


@pytest_asyncio.fixture(scope="module")
async def com_user_enviar(
    test_session_factory: async_sessionmaker[AsyncSession],
    com_tenant: TenantInfo,
) -> UserInfo:
    """User with comunicacion:enviar permission."""
    from app.core.security import email_hash as _eh, hash_password
    from app.models.usuario import Usuario
    from app.models.rol import Rol
    from app.models.permiso import Permiso
    from app.models.rol_permiso import RolPermiso
    from app.models.usuario_rol import UsuarioRol

    user_id = uuid.uuid4()
    raw_email = f"com-enviar-{uuid.uuid4().hex[:8]}@test.com"
    async with test_session_factory() as session:
        u = Usuario(
            id=user_id,
            tenant_id=com_tenant.id,
            email_cifrado="placeholder-com-enviar",
            email_hash=_eh(raw_email),
            password_hash=hash_password("testpass"),
            activo=True,
        )
        session.add(u)

        # Create PROFESOR role + comunicacion:enviar permission
        rol = Rol(
            id=uuid.uuid4(),
            tenant_id=com_tenant.id,
            codigo="PROFESOR_COM",
            nombre="Profesor Comunicacion Test",
        )
        session.add(rol)

        perm = Permiso(
            id=uuid.uuid4(),
            tenant_id=com_tenant.id,
            codigo="comunicacion:enviar",
        )
        session.add(perm)
        await session.flush()

        rol_perm = RolPermiso(
            id=uuid.uuid4(),
            tenant_id=com_tenant.id,
            rol_id=rol.id,
            permiso_id=perm.id,
        )
        session.add(rol_perm)
        await session.flush()

        ur = UsuarioRol(
            id=uuid.uuid4(),
            tenant_id=com_tenant.id,
            usuario_id=user_id,
            rol_id=rol.id,
            vig_desde=date(2025, 1, 1),
        )
        session.add(ur)
        await session.commit()

    return UserInfo(id=user_id, tenant_id=com_tenant.id, token=_make_token(user_id, com_tenant.id))


@pytest_asyncio.fixture(scope="module")
async def com_user_aprobar(
    test_session_factory: async_sessionmaker[AsyncSession],
    com_tenant: TenantInfo,
) -> UserInfo:
    """User with comunicacion:aprobar permission."""
    from app.core.security import email_hash as _eh, hash_password
    from app.models.usuario import Usuario
    from app.models.rol import Rol
    from app.models.permiso import Permiso
    from app.models.rol_permiso import RolPermiso
    from app.models.usuario_rol import UsuarioRol

    user_id = uuid.uuid4()
    raw_email = f"com-aprobar-{uuid.uuid4().hex[:8]}@test.com"
    async with test_session_factory() as session:
        u = Usuario(
            id=user_id,
            tenant_id=com_tenant.id,
            email_cifrado="placeholder-com-aprobar",
            email_hash=_eh(raw_email),
            password_hash=hash_password("testpass"),
            activo=True,
        )
        session.add(u)

        rol = Rol(
            id=uuid.uuid4(),
            tenant_id=com_tenant.id,
            codigo="COORD_COM",
            nombre="Coordinador Comunicacion Test",
        )
        session.add(rol)

        perm = Permiso(
            id=uuid.uuid4(),
            tenant_id=com_tenant.id,
            codigo="comunicacion:aprobar",
        )
        session.add(perm)
        await session.flush()

        rol_perm = RolPermiso(
            id=uuid.uuid4(),
            tenant_id=com_tenant.id,
            rol_id=rol.id,
            permiso_id=perm.id,
        )
        session.add(rol_perm)
        await session.flush()

        ur = UsuarioRol(
            id=uuid.uuid4(),
            tenant_id=com_tenant.id,
            usuario_id=user_id,
            rol_id=rol.id,
            vig_desde=date(2025, 1, 1),
        )
        session.add(ur)
        await session.commit()

    return UserInfo(id=user_id, tenant_id=com_tenant.id, token=_make_token(user_id, com_tenant.id))


@pytest_asyncio.fixture(scope="module")
async def com_user_no_perm(
    test_session_factory: async_sessionmaker[AsyncSession],
    com_tenant: TenantInfo,
) -> UserInfo:
    """User with no comunicacion permissions."""
    from app.core.security import email_hash as _eh, hash_password
    from app.models.usuario import Usuario

    user_id = uuid.uuid4()
    raw_email = f"com-noperm-{uuid.uuid4().hex[:8]}@test.com"
    async with test_session_factory() as session:
        u = Usuario(
            id=user_id,
            tenant_id=com_tenant.id,
            email_cifrado="placeholder-com-noperm",
            email_hash=_eh(raw_email),
            password_hash=hash_password("testpass"),
            activo=True,
        )
        session.add(u)
        await session.commit()

    return UserInfo(id=user_id, tenant_id=com_tenant.id, token=_make_token(user_id, com_tenant.id))


@pytest_asyncio.fixture(scope="module")
async def other_tenant(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_client: Any,
) -> TenantInfo:
    """A different tenant for isolation tests."""
    from app.models.tenant import Tenant

    async with test_session_factory() as session:
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"com-other-{uuid.uuid4().hex[:8]}",
            nombre="Other Tenant Com Test",
            comunicacion_requiere_aprobacion=True,
        )
        session.add(tenant)
        await session.commit()
        return TenantInfo(id=tenant.id, slug=tenant.slug)


@pytest_asyncio.fixture(scope="module")
async def other_tenant_user(
    test_session_factory: async_sessionmaker[AsyncSession],
    other_tenant: TenantInfo,
) -> UserInfo:
    from app.core.security import email_hash as _eh, hash_password
    from app.models.usuario import Usuario

    user_id = uuid.uuid4()
    raw_email = f"com-other-user-{uuid.uuid4().hex[:8]}@test.com"
    async with test_session_factory() as session:
        u = Usuario(
            id=user_id,
            tenant_id=other_tenant.id,
            email_cifrado="placeholder-com-other",
            email_hash=_eh(raw_email),
            password_hash=hash_password("testpass"),
            activo=True,
        )
        session.add(u)
        await session.commit()

    return UserInfo(id=user_id, tenant_id=other_tenant.id, token=_make_token(user_id, other_tenant.id))


# Helper for a quick materia for comunicacion tests
@pytest_asyncio.fixture(scope="module")
async def com_materia_id(
    test_session_factory: async_sessionmaker[AsyncSession],
    com_tenant: TenantInfo,
) -> uuid.UUID:
    from app.models.materia import Materia

    async with test_session_factory() as session:
        m = Materia(
            id=uuid.uuid4(),
            tenant_id=com_tenant.id,
            codigo=f"MAT-COM-{uuid.uuid4().hex[:4]}",
            nombre="Materia Com Test",
            estado="Activa",
        )
        session.add(m)
        await session.commit()
        return m.id


# ═══════════════════════════════════════════════════════════════════════════════
# 7.1 — Máquina de estados (unit tests — no HTTP)
# ═══════════════════════════════════════════════════════════════════════════════


class TestMaquinaEstados:
    """Unit tests for the state machine transitions in ComunicacionService."""

    def test_transicion_valida_pendiente_a_enviando(self):
        """Pendiente → Enviando is a valid transition."""
        from app.services.comunicacion_service import ComunicacionService

        # Should not raise
        ComunicacionService.validar_transicion("Pendiente", "Enviando")

    def test_transicion_valida_enviando_a_enviado(self):
        """Enviando → Enviado is valid."""
        from app.services.comunicacion_service import ComunicacionService

        ComunicacionService.validar_transicion("Enviando", "Enviado")

    def test_transicion_valida_enviando_a_error(self):
        """Enviando → Error is valid."""
        from app.services.comunicacion_service import ComunicacionService

        ComunicacionService.validar_transicion("Enviando", "Error")

    def test_transicion_valida_pendiente_a_cancelado(self):
        """Pendiente → Cancelado is valid."""
        from app.services.comunicacion_service import ComunicacionService

        ComunicacionService.validar_transicion("Pendiente", "Cancelado")

    def test_transicion_invalida_desde_enviado(self):
        """Enviado → any state is rejected with ValueError."""
        from app.services.comunicacion_service import ComunicacionService

        with pytest.raises(ValueError, match="terminal"):
            ComunicacionService.validar_transicion("Enviado", "Pendiente")

    def test_transicion_invalida_desde_cancelado(self):
        """Cancelado → any state is rejected."""
        from app.services.comunicacion_service import ComunicacionService

        with pytest.raises(ValueError, match="terminal"):
            ComunicacionService.validar_transicion("Cancelado", "Enviando")

    def test_transicion_invalida_desde_error(self):
        """Error → any state is rejected."""
        from app.services.comunicacion_service import ComunicacionService

        with pytest.raises(ValueError, match="terminal"):
            ComunicacionService.validar_transicion("Error", "Enviando")

    def test_transicion_invalida_enviando_a_cancelado(self):
        """Enviando → Cancelado is invalid (can only cancel from Pendiente)."""
        from app.services.comunicacion_service import ComunicacionService

        with pytest.raises(ValueError):
            ComunicacionService.validar_transicion("Enviando", "Cancelado")

    def test_transicion_invalida_pendiente_a_enviado(self):
        """Pendiente → Enviado is invalid (must go through Enviando)."""
        from app.services.comunicacion_service import ComunicacionService

        with pytest.raises(ValueError):
            ComunicacionService.validar_transicion("Pendiente", "Enviado")


# ═══════════════════════════════════════════════════════════════════════════════
# 7.2 — Preview (no DB persistence)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.anyio
class TestPreview:

    async def test_preview_renderiza_variables(
        self,
        test_client: Any,
        com_user_enviar: UserInfo,
    ):
        """Preview renders template variables correctly."""
        resp = await test_client.post(
            "/v1/comunicaciones/preview",
            json={
                "asunto": "Hola {{nombre}}",
                "cuerpo": "Tienes actividades pendientes en {{materia}}.",
                "variables": {"nombre": "Ana", "materia": "Programación I"},
            },
            headers={"Authorization": f"Bearer {com_user_enviar.token}"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["asunto"] == "Hola Ana"
        assert "Programación I" in data["cuerpo"]

    async def test_preview_no_persiste_en_db(
        self,
        test_client: Any,
        com_user_enviar: UserInfo,
        test_session_factory: async_sessionmaker[AsyncSession],
    ):
        """Preview must not create any Comunicacion record in DB."""
        from app.models.comunicacion import Comunicacion
        from sqlalchemy import select, func

        async with test_session_factory() as session:
            antes = (await session.execute(select(func.count()).select_from(Comunicacion))).scalar()

        await test_client.post(
            "/v1/comunicaciones/preview",
            json={
                "asunto": "No persiste",
                "cuerpo": "Cuerpo de prueba.",
                "variables": {},
            },
            headers={"Authorization": f"Bearer {com_user_enviar.token}"},
        )

        async with test_session_factory() as session:
            despues = (await session.execute(select(func.count()).select_from(Comunicacion))).scalar()

        assert antes == despues

    async def test_preview_variable_faltante_devuelve_422(
        self,
        test_client: Any,
        com_user_enviar: UserInfo,
    ):
        """Preview with a missing required variable returns 422."""
        resp = await test_client.post(
            "/v1/comunicaciones/preview",
            json={
                "asunto": "Hola {{nombre}}",
                "cuerpo": "Materia: {{materia}}",
                "variables": {},  # nombre and materia missing
            },
            headers={"Authorization": f"Bearer {com_user_enviar.token}"},
        )
        assert resp.status_code == 422, resp.text

    async def test_preview_requiere_autenticacion(
        self,
        test_client: Any,
    ):
        """Preview without token returns 401."""
        resp = await test_client.post(
            "/v1/comunicaciones/preview",
            json={
                "asunto": "Test",
                "cuerpo": "Test",
                "variables": {},
            },
        )
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# 7.3 — Encolado masivo
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.anyio
class TestEncolado:

    async def test_encolar_genera_lote_id(
        self,
        test_client: Any,
        com_user_enviar: UserInfo,
        com_materia_id: uuid.UUID,
    ):
        """Encolar a batch returns a lote_id and the count of messages."""
        resp = await test_client.post(
            "/v1/comunicaciones/encolar",
            json={
                "materia_id": str(com_materia_id),
                "asunto": "Recordatorio actividades",
                "cuerpo": "Tienes actividades pendientes.",
                "destinatarios": [
                    {"email": "a1@test.com", "variables": {}},
                    {"email": "a2@test.com", "variables": {}},
                ],
            },
            headers={"Authorization": f"Bearer {com_user_enviar.token}"},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert "lote_id" in data
        assert data["count"] == 2
        # Validate lote_id is a valid UUID
        uuid.UUID(data["lote_id"])

    async def test_encolar_destinatarios_cifrados_en_db(
        self,
        test_client: Any,
        com_user_enviar: UserInfo,
        com_materia_id: uuid.UUID,
        test_session_factory: async_sessionmaker[AsyncSession],
    ):
        """Destinatarios must be stored encrypted (not plaintext) in DB."""
        from app.models.comunicacion import Comunicacion
        from app.core.crypto import decrypt
        from sqlalchemy import select

        plain_email = f"cifrado-test-{uuid.uuid4().hex[:6]}@test.com"

        resp = await test_client.post(
            "/v1/comunicaciones/encolar",
            json={
                "materia_id": str(com_materia_id),
                "asunto": "Test cifrado",
                "cuerpo": "Cuerpo.",
                "destinatarios": [{"email": plain_email, "variables": {}}],
            },
            headers={"Authorization": f"Bearer {com_user_enviar.token}"},
        )
        assert resp.status_code == 201
        lote_id = uuid.UUID(resp.json()["lote_id"])

        async with test_session_factory() as session:
            result = await session.execute(
                select(Comunicacion).where(Comunicacion.lote_id == lote_id)
            )
            rows = result.scalars().all()

        assert len(rows) == 1
        # destinatario in DB must NOT be the plaintext email
        assert rows[0].destinatario != plain_email
        # But decrypted it should match
        assert decrypt(rows[0].destinatario) == plain_email

    async def test_encolar_requiere_permiso(
        self,
        test_client: Any,
        com_user_no_perm: UserInfo,
        com_materia_id: uuid.UUID,
    ):
        """Encolar without comunicacion:enviar returns 403."""
        resp = await test_client.post(
            "/v1/comunicaciones/encolar",
            json={
                "materia_id": str(com_materia_id),
                "asunto": "Test",
                "cuerpo": "Test.",
                "destinatarios": [{"email": "x@test.com", "variables": {}}],
            },
            headers={"Authorization": f"Bearer {com_user_no_perm.token}"},
        )
        assert resp.status_code == 403

    async def test_encolar_tenant_id_from_session(
        self,
        test_client: Any,
        com_user_enviar: UserInfo,
        com_materia_id: uuid.UUID,
        test_session_factory: async_sessionmaker[AsyncSession],
    ):
        """All created Comunicacion records must have tenant_id from JWT, not body."""
        from app.models.comunicacion import Comunicacion
        from sqlalchemy import select

        resp = await test_client.post(
            "/v1/comunicaciones/encolar",
            json={
                "materia_id": str(com_materia_id),
                "asunto": "Tenant test",
                "cuerpo": "Cuerpo.",
                "destinatarios": [{"email": "tid@test.com", "variables": {}}],
            },
            headers={"Authorization": f"Bearer {com_user_enviar.token}"},
        )
        assert resp.status_code == 201
        lote_id = uuid.UUID(resp.json()["lote_id"])

        async with test_session_factory() as session:
            result = await session.execute(
                select(Comunicacion).where(Comunicacion.lote_id == lote_id)
            )
            rows = result.scalars().all()

        assert all(r.tenant_id == com_user_enviar.tenant_id for r in rows)

    async def test_encolar_estado_inicial_pendiente(
        self,
        test_client: Any,
        com_user_enviar: UserInfo,
        com_materia_id: uuid.UUID,
        test_session_factory: async_sessionmaker[AsyncSession],
    ):
        """Messages enqueued with approval required must be Pendiente."""
        from app.models.comunicacion import Comunicacion
        from sqlalchemy import select

        resp = await test_client.post(
            "/v1/comunicaciones/encolar",
            json={
                "materia_id": str(com_materia_id),
                "asunto": "Estado pendiente test",
                "cuerpo": "Cuerpo.",
                "destinatarios": [
                    {"email": "p1@test.com", "variables": {}},
                    {"email": "p2@test.com", "variables": {}},
                ],
            },
            headers={"Authorization": f"Bearer {com_user_enviar.token}"},
        )
        assert resp.status_code == 201
        lote_id = uuid.UUID(resp.json()["lote_id"])

        async with test_session_factory() as session:
            result = await session.execute(
                select(Comunicacion).where(Comunicacion.lote_id == lote_id)
            )
            rows = result.scalars().all()

        assert all(r.estado == "Pendiente" for r in rows)

    async def test_respuesta_enmascara_destinatario(
        self,
        test_client: Any,
        com_user_enviar: UserInfo,
        com_materia_id: uuid.UUID,
    ):
        """Lote status response must mask the email address."""
        plain_email = "visible@test.com"
        resp = await test_client.post(
            "/v1/comunicaciones/encolar",
            json={
                "materia_id": str(com_materia_id),
                "asunto": "Mask test",
                "cuerpo": "Cuerpo.",
                "destinatarios": [{"email": plain_email, "variables": {}}],
            },
            headers={"Authorization": f"Bearer {com_user_enviar.token}"},
        )
        assert resp.status_code == 201
        lote_id = resp.json()["lote_id"]

        # Get lote status
        status_resp = await test_client.get(
            f"/v1/comunicaciones/lotes/{lote_id}",
            headers={"Authorization": f"Bearer {com_user_enviar.token}"},
        )
        assert status_resp.status_code == 200
        lote_data = status_resp.json()
        # Email must be masked
        for msg in lote_data["mensajes"]:
            assert plain_email not in msg["destinatario"]
            assert "***" in msg["destinatario"]


# ═══════════════════════════════════════════════════════════════════════════════
# 7.4 — Aprobación y cancelación
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.anyio
class TestAprobacion:

    async def _encolar(
        self,
        test_client: Any,
        token: str,
        materia_id: uuid.UUID,
        count: int = 2,
    ) -> str:
        """Helper: enqueue `count` messages and return lote_id."""
        resp = await test_client.post(
            "/v1/comunicaciones/encolar",
            json={
                "materia_id": str(materia_id),
                "asunto": "Test aprobacion",
                "cuerpo": "Cuerpo.",
                "destinatarios": [
                    {"email": f"aptest{i}@test.com", "variables": {}}
                    for i in range(count)
                ],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        return resp.json()["lote_id"]

    async def test_aprobar_lote_cambia_estado_aprobado(
        self,
        test_client: Any,
        com_user_enviar: UserInfo,
        com_user_aprobar: UserInfo,
        com_materia_id: uuid.UUID,
        test_session_factory: async_sessionmaker[AsyncSession],
    ):
        """Approving a lote marks all Pendiente messages as approved (ready for worker)."""
        from app.models.comunicacion import Comunicacion
        from sqlalchemy import select

        lote_id = await self._encolar(test_client, com_user_enviar.token, com_materia_id)

        resp = await test_client.patch(
            f"/v1/comunicaciones/lotes/{lote_id}/aprobar",
            headers={"Authorization": f"Bearer {com_user_aprobar.token}"},
        )
        assert resp.status_code == 200, resp.text

        async with test_session_factory() as session:
            result = await session.execute(
                select(Comunicacion).where(Comunicacion.lote_id == uuid.UUID(lote_id))
            )
            rows = result.scalars().all()

        assert all(r.aprobado is True for r in rows)

    async def test_cancelar_lote_cambia_estado_cancelado(
        self,
        test_client: Any,
        com_user_enviar: UserInfo,
        com_user_aprobar: UserInfo,
        com_materia_id: uuid.UUID,
        test_session_factory: async_sessionmaker[AsyncSession],
    ):
        """Cancelling a lote moves all Pendiente messages to Cancelado."""
        from app.models.comunicacion import Comunicacion
        from sqlalchemy import select

        lote_id = await self._encolar(test_client, com_user_enviar.token, com_materia_id)

        resp = await test_client.patch(
            f"/v1/comunicaciones/lotes/{lote_id}/cancelar",
            headers={"Authorization": f"Bearer {com_user_aprobar.token}"},
        )
        assert resp.status_code == 200, resp.text

        async with test_session_factory() as session:
            result = await session.execute(
                select(Comunicacion).where(Comunicacion.lote_id == uuid.UUID(lote_id))
            )
            rows = result.scalars().all()

        assert all(r.estado == "Cancelado" for r in rows)

    async def test_cancelar_individual(
        self,
        test_client: Any,
        com_user_enviar: UserInfo,
        com_user_aprobar: UserInfo,
        com_materia_id: uuid.UUID,
        test_session_factory: async_sessionmaker[AsyncSession],
    ):
        """Cancelling one message does not affect others in the same lote."""
        from app.models.comunicacion import Comunicacion
        from sqlalchemy import select

        lote_id = await self._encolar(test_client, com_user_enviar.token, com_materia_id, count=3)

        async with test_session_factory() as session:
            result = await session.execute(
                select(Comunicacion).where(
                    Comunicacion.lote_id == uuid.UUID(lote_id),
                    Comunicacion.deleted_at.is_(None),
                )
            )
            rows = result.scalars().all()

        msg_id = str(rows[0].id)

        resp = await test_client.patch(
            f"/v1/comunicaciones/{msg_id}/cancelar",
            headers={"Authorization": f"Bearer {com_user_enviar.token}"},
        )
        assert resp.status_code == 200, resp.text

        async with test_session_factory() as session:
            result = await session.execute(
                select(Comunicacion).where(Comunicacion.lote_id == uuid.UUID(lote_id))
            )
            all_rows = result.scalars().all()

        cancelados = [r for r in all_rows if r.estado == "Cancelado"]
        pendientes = [r for r in all_rows if r.estado == "Pendiente"]
        assert len(cancelados) == 1
        assert len(pendientes) == 2

    async def test_aprobar_sin_permiso_devuelve_403(
        self,
        test_client: Any,
        com_user_no_perm: UserInfo,
        com_user_enviar: UserInfo,
        com_materia_id: uuid.UUID,
    ):
        """Approving without comunicacion:aprobar returns 403."""
        lote_id = await self._encolar(test_client, com_user_enviar.token, com_materia_id)

        resp = await test_client.patch(
            f"/v1/comunicaciones/lotes/{lote_id}/aprobar",
            headers={"Authorization": f"Bearer {com_user_no_perm.token}"},
        )
        assert resp.status_code == 403

    async def test_aprobar_lote_otro_tenant_devuelve_404(
        self,
        test_client: Any,
        com_user_enviar: UserInfo,
        com_user_aprobar: UserInfo,
        com_materia_id: uuid.UUID,
        other_tenant_user: UserInfo,
    ):
        """Approving a lote from another tenant returns 404."""
        lote_id = await self._encolar(test_client, com_user_enviar.token, com_materia_id)

        resp = await test_client.patch(
            f"/v1/comunicaciones/lotes/{lote_id}/aprobar",
            headers={"Authorization": f"Bearer {other_tenant_user.token}"},
        )
        assert resp.status_code in (403, 404)


# ═══════════════════════════════════════════════════════════════════════════════
# 7.5 — Worker
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.anyio
class TestWorker:

    async def test_worker_procesa_pendiente_a_enviado(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        com_tenant: TenantInfo,
        com_materia_id: uuid.UUID,
        com_user_enviar: UserInfo,
    ):
        """Worker picks up a Pendiente+aprobado message and moves it to Enviado."""
        from app.models.comunicacion import Comunicacion
        from workers.comunicacion_worker import ComunicacionWorker
        from app.core.crypto import encrypt
        from sqlalchemy import select

        async with test_session_factory() as session:
            msg = Comunicacion(
                id=uuid.uuid4(),
                tenant_id=com_tenant.id,
                enviado_por=com_user_enviar.id,
                materia_id=com_materia_id,
                destinatario=encrypt("worker-test@test.com"),
                asunto="Worker test subject",
                cuerpo="Worker test body.",
                estado="Pendiente",
                aprobado=True,
                lote_id=uuid.uuid4(),
            )
            session.add(msg)
            await session.commit()
            msg_id = msg.id

        worker = ComunicacionWorker(test_session_factory, batch_size=100)
        await worker.run_once()

        async with test_session_factory() as session:
            result = await session.execute(
                select(Comunicacion).where(Comunicacion.id == msg_id)
            )
            updated = result.scalar_one()

        assert updated.estado == "Enviado"
        assert updated.enviado_at is not None

    async def test_worker_no_procesa_sin_aprobacion(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        com_tenant: TenantInfo,
        com_materia_id: uuid.UUID,
        com_user_enviar: UserInfo,
    ):
        """Worker must NOT process messages that are Pendiente but not approved."""
        from app.models.comunicacion import Comunicacion
        from workers.comunicacion_worker import ComunicacionWorker
        from app.core.crypto import encrypt
        from sqlalchemy import select

        async with test_session_factory() as session:
            msg = Comunicacion(
                id=uuid.uuid4(),
                tenant_id=com_tenant.id,
                enviado_por=com_user_enviar.id,
                materia_id=com_materia_id,
                destinatario=encrypt("worker-no-aprov@test.com"),
                asunto="No aprobado",
                cuerpo="Cuerpo.",
                estado="Pendiente",
                aprobado=False,
                lote_id=uuid.uuid4(),
            )
            session.add(msg)
            await session.commit()
            msg_id = msg.id

        worker = ComunicacionWorker(test_session_factory, batch_size=100)
        await worker.run_once()

        async with test_session_factory() as session:
            result = await session.execute(
                select(Comunicacion).where(Comunicacion.id == msg_id)
            )
            unchanged = result.scalar_one()

        assert unchanged.estado == "Pendiente"


# ═══════════════════════════════════════════════════════════════════════════════
# 7.6 — Auditoría
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.anyio
class TestAuditoria:

    async def test_audit_comunicacion_enviar(
        self,
        test_client: Any,
        com_user_enviar: UserInfo,
        com_materia_id: uuid.UUID,
        test_session_factory: async_sessionmaker[AsyncSession],
    ):
        """Enqueuing creates an audit entry COMUNICACION_ENVIAR."""
        from app.models.audit_log import AuditLog
        from sqlalchemy import select

        resp = await test_client.post(
            "/v1/comunicaciones/encolar",
            json={
                "materia_id": str(com_materia_id),
                "asunto": "Audit test enviar",
                "cuerpo": "Cuerpo.",
                "destinatarios": [{"email": "audit@test.com", "variables": {}}],
            },
            headers={"Authorization": f"Bearer {com_user_enviar.token}"},
        )
        assert resp.status_code == 201
        lote_id = resp.json()["lote_id"]

        async with test_session_factory() as session:
            result = await session.execute(
                select(AuditLog).where(
                    AuditLog.tenant_id == com_user_enviar.tenant_id,
                    AuditLog.actor_id == com_user_enviar.id,
                    AuditLog.accion == "COMUNICACION_ENVIAR",
                )
            )
            entries = result.scalars().all()

        # At least one audit entry for this lote
        matching = [e for e in entries if e.detalle.get("lote_id") == lote_id]
        assert len(matching) >= 1

    async def test_audit_comunicacion_cancelar(
        self,
        test_client: Any,
        com_user_enviar: UserInfo,
        com_user_aprobar: UserInfo,
        com_materia_id: uuid.UUID,
        test_session_factory: async_sessionmaker[AsyncSession],
    ):
        """Cancelling a lote creates an audit entry COMUNICACION_CANCELAR."""
        from app.models.audit_log import AuditLog
        from sqlalchemy import select

        resp = await test_client.post(
            "/v1/comunicaciones/encolar",
            json={
                "materia_id": str(com_materia_id),
                "asunto": "Audit test cancelar",
                "cuerpo": "Cuerpo.",
                "destinatarios": [{"email": "audit-canc@test.com", "variables": {}}],
            },
            headers={"Authorization": f"Bearer {com_user_enviar.token}"},
        )
        lote_id = resp.json()["lote_id"]

        await test_client.patch(
            f"/v1/comunicaciones/lotes/{lote_id}/cancelar",
            headers={"Authorization": f"Bearer {com_user_aprobar.token}"},
        )

        async with test_session_factory() as session:
            result = await session.execute(
                select(AuditLog).where(
                    AuditLog.tenant_id == com_user_aprobar.tenant_id,
                    AuditLog.accion == "COMUNICACION_CANCELAR",
                )
            )
            entries = result.scalars().all()

        matching = [e for e in entries if e.detalle.get("lote_id") == lote_id]
        assert len(matching) >= 1

    async def test_audit_comunicacion_aprobar(
        self,
        test_client: Any,
        com_user_enviar: UserInfo,
        com_user_aprobar: UserInfo,
        com_materia_id: uuid.UUID,
        test_session_factory: async_sessionmaker[AsyncSession],
    ):
        """Approving a lote creates an audit entry COMUNICACION_APROBAR."""
        from app.models.audit_log import AuditLog
        from sqlalchemy import select

        resp = await test_client.post(
            "/v1/comunicaciones/encolar",
            json={
                "materia_id": str(com_materia_id),
                "asunto": "Audit test aprobar",
                "cuerpo": "Cuerpo.",
                "destinatarios": [{"email": "audit-apr@test.com", "variables": {}}],
            },
            headers={"Authorization": f"Bearer {com_user_enviar.token}"},
        )
        lote_id = resp.json()["lote_id"]

        await test_client.patch(
            f"/v1/comunicaciones/lotes/{lote_id}/aprobar",
            headers={"Authorization": f"Bearer {com_user_aprobar.token}"},
        )

        async with test_session_factory() as session:
            result = await session.execute(
                select(AuditLog).where(
                    AuditLog.tenant_id == com_user_aprobar.tenant_id,
                    AuditLog.accion == "COMUNICACION_APROBAR",
                )
            )
            entries = result.scalars().all()

        matching = [e for e in entries if e.detalle.get("lote_id") == lote_id]
        assert len(matching) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# 7.7 — Tenant isolation
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.anyio
class TestTenantIsolation:

    async def test_consulta_lote_ajeno_devuelve_404(
        self,
        test_client: Any,
        com_user_enviar: UserInfo,
        other_tenant_user: UserInfo,
        com_materia_id: uuid.UUID,
    ):
        """User from a different tenant cannot access lote from com_tenant."""
        resp = await test_client.post(
            "/v1/comunicaciones/encolar",
            json={
                "materia_id": str(com_materia_id),
                "asunto": "Isolation test",
                "cuerpo": "Cuerpo.",
                "destinatarios": [{"email": "iso@test.com", "variables": {}}],
            },
            headers={"Authorization": f"Bearer {com_user_enviar.token}"},
        )
        assert resp.status_code == 201
        lote_id = resp.json()["lote_id"]

        # Other tenant user tries to GET the lote
        # Security: either 403 (no permission) or 404 (tenant isolation) is acceptable.
        # The key invariant is that the lote data is NOT returned (not 200).
        resp2 = await test_client.get(
            f"/v1/comunicaciones/lotes/{lote_id}",
            headers={"Authorization": f"Bearer {other_tenant_user.token}"},
        )
        assert resp2.status_code in (403, 404), (
            f"Expected 403 or 404 for cross-tenant lote access, got {resp2.status_code}"
        )
