"""tests/test_perfil_y_mensajeria.py — Tests for C-20: perfil-y-mensajeria-interna.

TDD cycles:
  20.1  RED→GREEN:    GET /v1/perfil — own profile from JWT, not from param
  20.2  TRIANGULATE:  PATCH /v1/perfil — update nombre/apellidos/regional
  20.3  RED→GREEN:    PATCH /v1/perfil with 'cuil' field → 422 (read-only)
  20.4  RED→GREEN:    POST /v1/inbox — send message to same-tenant user
  20.5  TRIANGULATE:  GET /v1/inbox — inbox scoped to recipient only
  20.6  RED→GREEN:    GET /v1/inbox{id} — marks as leido on read
  20.7  TRIANGULATE:  POST /v1/inbox{id}/responder — hilo_id propagates
  20.8  RED→GREEN:    GET /v1/inboxenviados — sent messages scoped to sender
  20.9  RED→GREEN:    Multi-tenant: user A cannot send to user B in tenant B
  20.10 TRIANGULATE:  User A cannot read user B's inbox messages
"""

import os
import uuid
from dataclasses import dataclass
from datetime import timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.base import Base
from app.models.tenant import Tenant
from app.models.usuario import Usuario

_TEST_SECRET = "test-secret-key-32-characters-ok!"
_TEST_ENCRYPTION_KEY = "0" * 64


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_token(user_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
    from app.core.security import create_access_token

    return create_access_token(
        data={"sub": str(user_id), "tenant_id": str(tenant_id)},
        expires_delta=timedelta(minutes=30),
    )


def _usuario_kwargs(tenant_id: uuid.UUID) -> dict:
    from app.core.security import email_hash as _eh, hash_password

    raw = f"user-{uuid.uuid4().hex[:8]}@test.com"
    return {
        "id": uuid.uuid4(),
        "tenant_id": tenant_id,
        "email_cifrado": "placeholder-encrypted",
        "email_hash": _eh(raw),
        "password_hash": hash_password("testpassword123"),
        "activo": True,
    }


@dataclass
class UserInfo:
    id: uuid.UUID
    tenant_id: uuid.UUID
    token: str


@dataclass
class TenantInfo:
    id: uuid.UUID
    slug: str


# ── Module-scoped client ──────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def test_client(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncClient:
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

        async with db_module.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with AsyncClient(
            transport=__import__("httpx").ASGITransport(app=mgr.app),
            base_url="http://testserver",
        ) as client:
            yield client


# ── Tenant + users fixtures ───────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def tenant_a(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_client: AsyncClient,
) -> TenantInfo:
    async with test_session_factory() as session:
        t = Tenant(
            id=uuid.uuid4(),
            slug=f"pm-tenant-a-{uuid.uuid4().hex[:6]}",
            nombre="Tenant A (perfil-mensajeria)",
        )
        session.add(t)
        await session.commit()
    return TenantInfo(id=t.id, slug=t.slug)


@pytest_asyncio.fixture(scope="module")
async def tenant_b(
    test_session_factory: async_sessionmaker[AsyncSession],
    test_client: AsyncClient,
) -> TenantInfo:
    async with test_session_factory() as session:
        t = Tenant(
            id=uuid.uuid4(),
            slug=f"pm-tenant-b-{uuid.uuid4().hex[:6]}",
            nombre="Tenant B (perfil-mensajeria)",
        )
        session.add(t)
        await session.commit()
    return TenantInfo(id=t.id, slug=t.slug)


@pytest_asyncio.fixture(scope="module")
async def user_a1(
    test_session_factory: async_sessionmaker[AsyncSession],
    tenant_a: TenantInfo,
    test_client: AsyncClient,
) -> UserInfo:
    """Primary user in tenant A."""
    kwargs = _usuario_kwargs(tenant_a.id)
    user_id = kwargs["id"]
    async with test_session_factory() as session:
        session.add(Usuario(**kwargs))
        await session.commit()
    return UserInfo(id=user_id, tenant_id=tenant_a.id, token=_make_token(user_id, tenant_a.id))


@pytest_asyncio.fixture(scope="module")
async def user_a2(
    test_session_factory: async_sessionmaker[AsyncSession],
    tenant_a: TenantInfo,
    test_client: AsyncClient,
) -> UserInfo:
    """Second user in tenant A — to send/receive messages between."""
    kwargs = _usuario_kwargs(tenant_a.id)
    user_id = kwargs["id"]
    async with test_session_factory() as session:
        session.add(Usuario(**kwargs))
        await session.commit()
    return UserInfo(id=user_id, tenant_id=tenant_a.id, token=_make_token(user_id, tenant_a.id))


@pytest_asyncio.fixture(scope="module")
async def user_b1(
    test_session_factory: async_sessionmaker[AsyncSession],
    tenant_b: TenantInfo,
    test_client: AsyncClient,
) -> UserInfo:
    """User in tenant B — must never interact with tenant A users."""
    kwargs = _usuario_kwargs(tenant_b.id)
    user_id = kwargs["id"]
    async with test_session_factory() as session:
        session.add(Usuario(**kwargs))
        await session.commit()
    return UserInfo(id=user_id, tenant_id=tenant_b.id, token=_make_token(user_id, tenant_b.id))


# ── 20.1 GET /v1/perfil — own profile ────────────────────────────────────────


@pytest.mark.anyio
async def test_get_perfil_authenticated(
    test_client: AsyncClient,
    user_a1: UserInfo,
):
    """RED→GREEN: GET /v1/perfil returns own profile from JWT."""
    resp = await test_client.get(
        "/v1/perfil",
        headers={"Authorization": f"Bearer {user_a1.token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["id"] == str(user_a1.id)
    assert data["tenant_id"] == str(user_a1.tenant_id)


@pytest.mark.anyio
async def test_get_perfil_unauthenticated(test_client: AsyncClient):
    """TRIANGULATE: GET /v1/perfil without token → 401."""
    resp = await test_client.get("/v1/perfil")
    assert resp.status_code == 401


# ── 20.2 PATCH /v1/perfil — update editable fields ───────────────────────────


@pytest.mark.anyio
async def test_patch_perfil_nombre_apellidos(
    test_client: AsyncClient,
    user_a1: UserInfo,
):
    """RED→GREEN: PATCH /v1/perfil updates nombre, apellidos, regional."""
    resp = await test_client.patch(
        "/v1/perfil",
        json={"nombre": "Ana", "apellidos": "García", "regional": "Córdoba"},
        headers={"Authorization": f"Bearer {user_a1.token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["nombre"] == "Ana"
    assert data["apellidos"] == "García"
    assert data["regional"] == "Córdoba"
    assert data["id"] == str(user_a1.id)


@pytest.mark.anyio
async def test_patch_perfil_cbu(
    test_client: AsyncClient,
    user_a2: UserInfo,
):
    """TRIANGULATE: PATCH /v1/perfil with CBU updates banking data."""
    resp = await test_client.patch(
        "/v1/perfil",
        json={"cbu": "0000003100012345678901", "banco": "Galicia"},
        headers={"Authorization": f"Bearer {user_a2.token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["cbu"] == "0000003100012345678901"
    assert data["banco"] == "Galicia"


# ── 20.3 PATCH /v1/perfil with cuil → 422 ────────────────────────────────────


@pytest.mark.anyio
async def test_patch_perfil_cuil_rejected(
    test_client: AsyncClient,
    user_a1: UserInfo,
):
    """RED→GREEN: CUIL is read-only — sending it in PATCH body → 422."""
    resp = await test_client.patch(
        "/v1/perfil",
        json={"cuil": "20304050607"},
        headers={"Authorization": f"Bearer {user_a1.token}"},
    )
    assert resp.status_code == 422, resp.text


# ── 20.4 POST /v1/inbox — send message ──────────────────────────────────────


@pytest.mark.anyio
async def test_enviar_mensaje_mismo_tenant(
    test_client: AsyncClient,
    user_a1: UserInfo,
    user_a2: UserInfo,
):
    """RED→GREEN: user A1 sends message to A2 in the same tenant."""
    resp = await test_client.post(
        "/v1/inbox",
        json={
            "destinatario_id": str(user_a2.id),
            "asunto": "Hola equipo",
            "cuerpo": "Nos reunimos mañana a las 10.",
        },
        headers={"Authorization": f"Bearer {user_a1.token}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["remitente_id"] == str(user_a1.id)
    assert data["destinatario_id"] == str(user_a2.id)
    assert data["asunto"] == "Hola equipo"
    assert data["leido"] is False
    assert data["hilo_id"] is None


# ── 20.5 GET /v1/inbox — inbox scoped to recipient ──────────────────────────


@pytest.mark.anyio
async def test_inbox_scoped_to_recipient(
    test_client: AsyncClient,
    user_a1: UserInfo,
    user_a2: UserInfo,
):
    """TRIANGULATE: user A2 sees the message, user A1 does not see it in inbox."""
    # Send from A1 to A2
    send_resp = await test_client.post(
        "/v1/inbox",
        json={
            "destinatario_id": str(user_a2.id),
            "asunto": "Test inbox scope",
            "cuerpo": "Solo A2 debe verlo en su inbox.",
        },
        headers={"Authorization": f"Bearer {user_a1.token}"},
    )
    assert send_resp.status_code == 201, send_resp.text
    msg_id = send_resp.json()["id"]

    # A2's inbox contains the message
    inbox_a2 = await test_client.get(
        "/v1/inbox",
        headers={"Authorization": f"Bearer {user_a2.token}"},
    )
    assert inbox_a2.status_code == 200
    ids_a2 = [m["id"] for m in inbox_a2.json()]
    assert msg_id in ids_a2

    # A1's inbox does NOT contain the message (they are the sender)
    inbox_a1 = await test_client.get(
        "/v1/inbox",
        headers={"Authorization": f"Bearer {user_a1.token}"},
    )
    assert inbox_a1.status_code == 200
    ids_a1 = [m["id"] for m in inbox_a1.json()]
    assert msg_id not in ids_a1


# ── 20.6 GET /v1/inbox{id} — marks as leido ─────────────────────────────────


@pytest.mark.anyio
async def test_get_mensaje_marks_leido(
    test_client: AsyncClient,
    user_a1: UserInfo,
    user_a2: UserInfo,
):
    """RED→GREEN: reading a received message marks it as leido=True."""
    # Send from A1 to A2
    send_resp = await test_client.post(
        "/v1/inbox",
        json={
            "destinatario_id": str(user_a2.id),
            "asunto": "Marcar como leído",
            "cuerpo": "Este mensaje debe quedar marcado como leído al abrirse.",
        },
        headers={"Authorization": f"Bearer {user_a1.token}"},
    )
    assert send_resp.status_code == 201, send_resp.text
    msg_id = send_resp.json()["id"]
    assert send_resp.json()["leido"] is False

    # A2 reads the message
    read_resp = await test_client.get(
        f"/v1/inbox/{msg_id}",
        headers={"Authorization": f"Bearer {user_a2.token}"},
    )
    assert read_resp.status_code == 200, read_resp.text
    assert read_resp.json()["leido"] is True


# ── 20.7 POST /v1/inbox{id}/responder — hilo_id propagation ─────────────────


@pytest.mark.anyio
async def test_responder_propaga_hilo_id(
    test_client: AsyncClient,
    user_a1: UserInfo,
    user_a2: UserInfo,
):
    """TRIANGULATE: reply carries hilo_id of the root message."""
    # Root message A1 → A2
    root_resp = await test_client.post(
        "/v1/inbox",
        json={
            "destinatario_id": str(user_a2.id),
            "asunto": "Mensaje raíz",
            "cuerpo": "Soy el mensaje raíz del hilo.",
        },
        headers={"Authorization": f"Bearer {user_a1.token}"},
    )
    assert root_resp.status_code == 201, root_resp.text
    root_id = root_resp.json()["id"]
    assert root_resp.json()["hilo_id"] is None

    # A2 replies
    reply_resp = await test_client.post(
        f"/v1/inbox/{root_id}/responder",
        json={"cuerpo": "Respondo al mensaje raíz."},
        headers={"Authorization": f"Bearer {user_a2.token}"},
    )
    assert reply_resp.status_code == 201, reply_resp.text
    reply_data = reply_resp.json()
    assert reply_data["hilo_id"] == root_id  # hilo_id == root message id
    assert reply_data["remitente_id"] == str(user_a2.id)
    assert reply_data["destinatario_id"] == str(user_a1.id)


@pytest.mark.anyio
async def test_responder_a_reply_preserva_hilo_id(
    test_client: AsyncClient,
    user_a1: UserInfo,
    user_a2: UserInfo,
):
    """TRIANGULATE: replying to a reply preserves the original hilo_id."""
    # Root: A1 → A2
    root_resp = await test_client.post(
        "/v1/inbox",
        json={
            "destinatario_id": str(user_a2.id),
            "asunto": "Hilo anidado",
            "cuerpo": "Raíz del hilo anidado.",
        },
        headers={"Authorization": f"Bearer {user_a1.token}"},
    )
    root_id = root_resp.json()["id"]

    # First reply: A2 → A1
    reply1_resp = await test_client.post(
        f"/v1/inbox/{root_id}/responder",
        json={"cuerpo": "Primera respuesta."},
        headers={"Authorization": f"Bearer {user_a2.token}"},
    )
    reply1_id = reply1_resp.json()["id"]
    assert reply1_resp.json()["hilo_id"] == root_id

    # Second reply to first reply: A1 → A2
    reply2_resp = await test_client.post(
        f"/v1/inbox/{reply1_id}/responder",
        json={"cuerpo": "Segunda respuesta al hilo."},
        headers={"Authorization": f"Bearer {user_a1.token}"},
    )
    assert reply2_resp.status_code == 201, reply2_resp.text
    # hilo_id must still point to the original root, not reply1
    assert reply2_resp.json()["hilo_id"] == root_id


# ── 20.8 GET /v1/inboxenviados ──────────────────────────────────────────────


@pytest.mark.anyio
async def test_inbox_enviados_scoped_to_sender(
    test_client: AsyncClient,
    user_a1: UserInfo,
    user_a2: UserInfo,
):
    """RED→GREEN: /enviados shows only messages sent by the caller."""
    # Send from A1 to A2
    send_resp = await test_client.post(
        "/v1/inbox",
        json={
            "destinatario_id": str(user_a2.id),
            "asunto": "Mensaje enviado por A1",
            "cuerpo": "Chequeo enviados.",
        },
        headers={"Authorization": f"Bearer {user_a1.token}"},
    )
    assert send_resp.status_code == 201
    msg_id = send_resp.json()["id"]

    # A1's enviados contains the message
    env_a1 = await test_client.get(
        "/v1/inbox/enviados",
        headers={"Authorization": f"Bearer {user_a1.token}"},
    )
    assert env_a1.status_code == 200
    assert msg_id in [m["id"] for m in env_a1.json()]

    # A2's enviados does NOT contain the message
    env_a2 = await test_client.get(
        "/v1/inbox/enviados",
        headers={"Authorization": f"Bearer {user_a2.token}"},
    )
    assert env_a2.status_code == 200
    assert msg_id not in [m["id"] for m in env_a2.json()]


# ── 20.9 Multi-tenancy: cross-tenant send → 404 ───────────────────────────────


@pytest.mark.anyio
async def test_cross_tenant_send_rejected(
    test_client: AsyncClient,
    user_a1: UserInfo,
    user_b1: UserInfo,
):
    """RED→GREEN: user A1 cannot send a message to user B1 (different tenant)."""
    resp = await test_client.post(
        "/v1/inbox",
        json={
            "destinatario_id": str(user_b1.id),
            "asunto": "Cross-tenant message",
            "cuerpo": "Este mensaje no debería enviarse.",
        },
        headers={"Authorization": f"Bearer {user_a1.token}"},
    )
    # Recipient B1 is not found in tenant A → 404
    assert resp.status_code == 404, resp.text


# ── 20.10 User A cannot read user B's messages ────────────────────────────────


@pytest.mark.anyio
async def test_inbox_isolation_between_users(
    test_client: AsyncClient,
    user_a1: UserInfo,
    user_a2: UserInfo,
    user_b1: UserInfo,
):
    """TRIANGULATE: user A1 cannot GET a message that belongs only to A2."""
    # Send from A1 to A2 (so only A2 is recipient)
    send_resp = await test_client.post(
        "/v1/inbox",
        json={
            "destinatario_id": str(user_a2.id),
            "asunto": "Privado para A2",
            "cuerpo": "Solo A2 debe poder leer este mensaje.",
        },
        headers={"Authorization": f"Bearer {user_a1.token}"},
    )
    assert send_resp.status_code == 201, send_resp.text
    msg_id = send_resp.json()["id"]

    # A1 is the remitente so they CAN see it. Test that B1 (different tenant) cannot.
    read_as_b1 = await test_client.get(
        f"/v1/inbox/{msg_id}",
        headers={"Authorization": f"Bearer {user_b1.token}"},
    )
    # B1 is in a different tenant → 404
    assert read_as_b1.status_code == 404, read_as_b1.text


# ── solo_no_leidos filter ─────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_inbox_filter_solo_no_leidos(
    test_client: AsyncClient,
    user_a1: UserInfo,
    user_a2: UserInfo,
):
    """TRIANGULATE: ?solo_no_leidos=true filters to unread messages only."""
    # Send A1 → A2
    send_resp = await test_client.post(
        "/v1/inbox",
        json={
            "destinatario_id": str(user_a2.id),
            "asunto": "No leído",
            "cuerpo": "Soy un mensaje no leído.",
        },
        headers={"Authorization": f"Bearer {user_a1.token}"},
    )
    assert send_resp.status_code == 201
    unread_id = send_resp.json()["id"]

    # A2 checks inbox with filter
    resp = await test_client.get(
        "/v1/inbox?solo_no_leidos=true",
        headers={"Authorization": f"Bearer {user_a2.token}"},
    )
    assert resp.status_code == 200
    ids = [m["id"] for m in resp.json()]
    assert unread_id in ids
    # All returned messages must be unread
    for m in resp.json():
        assert m["leido"] is False


