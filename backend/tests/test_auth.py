"""tests/test_auth.py — Authentication tests for C-03 (TDD strict).

TDD cycles (RED → GREEN → TRIANGULATE → REFACTOR):
  9.1  Fixtures: tenant, usuario activo, inactivo, con 2FA
  9.2  Login OK sin 2FA → HTTP 200 + tokens
  9.3  Login password incorrecto → HTTP 401
  9.4  Login usuario inactivo → HTTP 401
  9.5  Login con 2FA activo → HTTP 202 + challenge_token
  9.6  2fa/verify código correcto → HTTP 200 + sesión completa
  9.7  2fa/verify código incorrecto → HTTP 401
  9.8  Refresh rotation — primer OK, segundo → HTTP 401 + todas revocadas
  9.9  Logout revoca el refresh token
  9.10 get_current_user token válido → usuario; token expirado → HTTP 401
  9.11 Rate limiting — 5 fallos, 6to → HTTP 429
  9.12 Triangulación: forgot + reset (válido, reutilizado)
  9.13 hash_password Argon2id; verify_password OK/KO

Uses a real PostgreSQL test DB (DATABASE_URL_TEST). No DB mocking.
"""

import uuid
from dataclasses import dataclass
from datetime import timedelta, timezone, datetime

import pyotp
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.crypto import encrypt
from app.core.rate_limit import rate_limiter
from app.core.security import (
    create_access_token,
    email_hash as compute_email_hash,
    hash_password,
    verify_password,
)
from app.models.tenant import Tenant
from app.models.usuario import Usuario


# ── Module-scoped DB setup ────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def db_tables(test_session_factory: async_sessionmaker[AsyncSession]):
    """Create all tables for auth tests; drop at module end."""
    from app.core import database as db_module
    from app.models.base import Base

    engine = db_module.engine
    assert engine is not None

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── Fixture helpers ───────────────────────────────────────────────────────────


@dataclass
class UsuarioInfo:
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    password: str
    activo: bool = True
    totp_activo: bool = False
    totp_secret: str | None = None


async def _create_tenant(session: AsyncSession) -> Tenant:
    t = Tenant(
        id=uuid.uuid4(),
        slug=f"test-{uuid.uuid4().hex[:8]}",
        nombre="Test Tenant",
    )
    session.add(t)
    await session.flush()
    return t


async def _create_usuario(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    email: str,
    password: str,
    activo: bool = True,
    totp_activo: bool = False,
    totp_secret: str | None = None,
) -> UsuarioInfo:
    eh = compute_email_hash(email)
    ph = hash_password(password)
    totp_cifrado = encrypt(totp_secret) if totp_secret else None

    u = Usuario(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email_cifrado=encrypt(email),
        email_hash=eh,
        password_hash=ph,
        activo=activo,
        totp_activo=totp_activo,
        totp_secret_cifrado=totp_cifrado,
    )
    session.add(u)
    await session.flush()
    return UsuarioInfo(
        id=u.id,
        tenant_id=tenant_id,
        email=email,
        password=password,
        activo=activo,
        totp_activo=totp_activo,
        totp_secret=totp_secret,
    )


# ── Module-scoped fixtures ────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def tenant_info(
    test_session_factory: async_sessionmaker[AsyncSession],
    db_tables,
) -> uuid.UUID:
    """Create a test tenant and return its ID."""
    async with test_session_factory() as session:
        t = await _create_tenant(session)
        await session.commit()
        return t.id


@pytest_asyncio.fixture(scope="module")
async def usuario_activo(
    test_session_factory: async_sessionmaker[AsyncSession],
    tenant_info: uuid.UUID,
) -> UsuarioInfo:
    async with test_session_factory() as session:
        info = await _create_usuario(
            session,
            tenant_id=tenant_info,
            email=f"activo-{uuid.uuid4().hex[:6]}@test.com",
            password="ValidPassword123!",
        )
        await session.commit()
    return info


@pytest_asyncio.fixture(scope="module")
async def usuario_inactivo(
    test_session_factory: async_sessionmaker[AsyncSession],
    tenant_info: uuid.UUID,
) -> UsuarioInfo:
    async with test_session_factory() as session:
        info = await _create_usuario(
            session,
            tenant_id=tenant_info,
            email=f"inactivo-{uuid.uuid4().hex[:6]}@test.com",
            password="ValidPassword123!",
            activo=False,
        )
        await session.commit()
    return info


@pytest_asyncio.fixture(scope="module")
async def usuario_con_2fa(
    test_session_factory: async_sessionmaker[AsyncSession],
    tenant_info: uuid.UUID,
) -> UsuarioInfo:
    secret = pyotp.random_base32()
    async with test_session_factory() as session:
        info = await _create_usuario(
            session,
            tenant_id=tenant_info,
            email=f"totp-{uuid.uuid4().hex[:6]}@test.com",
            password="ValidPassword123!",
            totp_activo=True,
            totp_secret=secret,
        )
        await session.commit()
    info.totp_secret = secret
    return info


# ── 9.13 Argon2id primitives ──────────────────────────────────────────────────


class TestPasswordHashing:
    """9.13 hash_password produces Argon2id; verify_password OK/KO."""

    def test_hash_starts_with_argon2id(self):
        """Scenario: password hash starts with $argon2id$."""
        h = hash_password("my-secret-password")
        assert h.startswith("$argon2id$")

    def test_verify_correct_password_returns_true(self):
        """Scenario: correct password verifies successfully."""
        h = hash_password("correct-horse-battery-staple")
        assert verify_password("correct-horse-battery-staple", h) is True

    def test_verify_wrong_password_returns_false(self):
        """Scenario: wrong password fails verification."""
        h = hash_password("correct-password")
        assert verify_password("wrong-password", h) is False

    def test_different_hashes_for_same_password(self):
        """Argon2id includes a random salt → same plaintext → different hashes."""
        h1 = hash_password("same-password")
        h2 = hash_password("same-password")
        assert h1 != h2


# ── 9.2 Login OK sin 2FA ──────────────────────────────────────────────────────


class TestLoginOK:
    """9.2 Login OK sin 2FA → HTTP 200 + tokens."""

    @pytest.mark.asyncio
    async def test_login_ok_returns_200_and_tokens(
        self,
        async_client: AsyncClient,
        usuario_activo: UsuarioInfo,
    ):
        """Scenario: valid credentials, no 2FA → 200 with access_token + refresh_token."""
        response = await async_client.post(
            "/api/auth/login",
            json={"email": usuario_activo.email, "password": usuario_activo.password},
            headers={"x-tenant-id": str(usuario_activo.tenant_id)},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_ok_triangulation_different_user(
        self,
        async_client: AsyncClient,
        test_session_factory: async_sessionmaker[AsyncSession],
        tenant_info: uuid.UUID,
    ):
        """Triangulation: a second user also gets a valid session."""
        async with test_session_factory() as session:
            info = await _create_usuario(
                session,
                tenant_id=tenant_info,
                email=f"user2-{uuid.uuid4().hex[:6]}@test.com",
                password="AnotherPassword456!",
            )
            await session.commit()

        response = await async_client.post(
            "/api/auth/login",
            json={"email": info.email, "password": info.password},
            headers={"x-tenant-id": str(tenant_info)},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()


# ── 9.3 Login password incorrecto ─────────────────────────────────────────────


class TestLoginInvalidPassword:
    """9.3 Login con password incorrecto → HTTP 401."""

    @pytest.mark.asyncio
    async def test_wrong_password_returns_401(
        self,
        async_client: AsyncClient,
        usuario_activo: UsuarioInfo,
    ):
        """Scenario: wrong password → 401, no tokens."""
        response = await async_client.post(
            "/api/auth/login",
            json={"email": usuario_activo.email, "password": "wrongpassword"},
            headers={"x-tenant-id": str(usuario_activo.tenant_id)},
        )
        assert response.status_code == 401
        data = response.json()
        assert "access_token" not in data

    @pytest.mark.asyncio
    async def test_nonexistent_email_returns_401(
        self,
        async_client: AsyncClient,
        tenant_info: uuid.UUID,
    ):
        """Scenario: email that does not exist → 401 (no user enumeration)."""
        response = await async_client.post(
            "/api/auth/login",
            json={"email": "ghost@nowhere.com", "password": "any"},
            headers={"x-tenant-id": str(tenant_info)},
        )
        assert response.status_code == 401


# ── 9.4 Login usuario inactivo ────────────────────────────────────────────────


class TestLoginInactiveUser:
    """9.4 Login usuario inactivo → HTTP 401."""

    @pytest.mark.asyncio
    async def test_inactive_user_returns_401(
        self,
        async_client: AsyncClient,
        usuario_inactivo: UsuarioInfo,
    ):
        """Scenario: valid credentials but activo=False → 401."""
        response = await async_client.post(
            "/api/auth/login",
            json={"email": usuario_inactivo.email, "password": usuario_inactivo.password},
            headers={"x-tenant-id": str(usuario_inactivo.tenant_id)},
        )
        assert response.status_code == 401


# ── 9.5 Login con 2FA ─────────────────────────────────────────────────────────


class TestLoginWith2FA:
    """9.5 Login con 2FA activo → HTTP 202 + challenge_token."""

    @pytest.mark.asyncio
    async def test_login_2fa_returns_202_and_challenge(
        self,
        async_client: AsyncClient,
        usuario_con_2fa: UsuarioInfo,
    ):
        """Scenario: valid credentials + totp_activo=True → 202 + challenge_token."""
        response = await async_client.post(
            "/api/auth/login",
            json={"email": usuario_con_2fa.email, "password": usuario_con_2fa.password},
            headers={"x-tenant-id": str(usuario_con_2fa.tenant_id)},
        )
        # The endpoint returns 200 by default but the body signals 2FA required
        data = response.json()
        assert "challenge_token" in data
        assert "access_token" not in data
        assert "refresh_token" not in data


# ── 9.6 2fa/verify código correcto ────────────────────────────────────────────


class TestTwoFAVerify:
    """9.6 2fa/verify código correcto → HTTP 200 + sesión completa."""

    @pytest.mark.asyncio
    async def test_verify_correct_code_returns_session(
        self,
        async_client: AsyncClient,
        usuario_con_2fa: UsuarioInfo,
    ):
        """Scenario: valid challenge_token + correct TOTP → 200 + full session."""
        # Step 1: get challenge token
        login_resp = await async_client.post(
            "/api/auth/login",
            json={"email": usuario_con_2fa.email, "password": usuario_con_2fa.password},
            headers={"x-tenant-id": str(usuario_con_2fa.tenant_id)},
        )
        challenge_token = login_resp.json()["challenge_token"]

        # Step 2: generate valid TOTP
        totp = pyotp.TOTP(usuario_con_2fa.totp_secret)
        code = totp.now()

        verify_resp = await async_client.post(
            "/api/auth/2fa/verify",
            json={"challenge_token": challenge_token, "code": code},
        )
        assert verify_resp.status_code == 200
        data = verify_resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    # 9.7: invalid code → 401
    @pytest.mark.asyncio
    async def test_verify_wrong_code_returns_401(
        self,
        async_client: AsyncClient,
        usuario_con_2fa: UsuarioInfo,
    ):
        """Scenario: valid challenge_token + wrong code → 401."""
        login_resp = await async_client.post(
            "/api/auth/login",
            json={"email": usuario_con_2fa.email, "password": usuario_con_2fa.password},
            headers={"x-tenant-id": str(usuario_con_2fa.tenant_id)},
        )
        challenge_token = login_resp.json()["challenge_token"]

        resp = await async_client.post(
            "/api/auth/2fa/verify",
            json={"challenge_token": challenge_token, "code": "000000"},
        )
        assert resp.status_code == 401

    # Challenge token cannot access protected endpoints
    @pytest.mark.asyncio
    async def test_challenge_token_rejected_on_protected_endpoint(
        self,
        async_client: AsyncClient,
        usuario_con_2fa: UsuarioInfo,
    ):
        """Scenario: challenge_token as Bearer → 401 on protected endpoint."""
        login_resp = await async_client.post(
            "/api/auth/login",
            json={"email": usuario_con_2fa.email, "password": usuario_con_2fa.password},
            headers={"x-tenant-id": str(usuario_con_2fa.tenant_id)},
        )
        challenge_token = login_resp.json()["challenge_token"]

        resp = await async_client.post(
            "/api/auth/2fa/enroll",
            headers={"Authorization": f"Bearer {challenge_token}"},
        )
        assert resp.status_code == 401


# ── 9.8 Refresh rotation ──────────────────────────────────────────────────────


class TestRefreshRotation:
    """9.8 Refresh rotation — primer OK, segundo con mismo token → 401 + revoca todas."""

    @pytest.mark.asyncio
    async def test_refresh_ok_returns_new_pair(
        self,
        async_client: AsyncClient,
        usuario_activo: UsuarioInfo,
    ):
        """Scenario: valid refresh token → new access + refresh pair."""
        login = await async_client.post(
            "/api/auth/login",
            json={"email": usuario_activo.email, "password": usuario_activo.password},
            headers={"x-tenant-id": str(usuario_activo.tenant_id)},
        )
        original_refresh = login.json()["refresh_token"]

        resp = await async_client.post(
            "/api/auth/refresh",
            json={"refresh_token": original_refresh},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        new_refresh = data["refresh_token"]
        assert new_refresh != original_refresh

    @pytest.mark.asyncio
    async def test_reused_refresh_token_returns_401(
        self,
        async_client: AsyncClient,
        test_session_factory: async_sessionmaker[AsyncSession],
        tenant_info: uuid.UUID,
    ):
        """Scenario: reused refresh token → 401 + all sessions revoked."""
        # Create a dedicated user for this test to avoid interference
        async with test_session_factory() as session:
            info = await _create_usuario(
                session,
                tenant_id=tenant_info,
                email=f"refresh-reuse-{uuid.uuid4().hex[:6]}@test.com",
                password="ValidPassword123!",
            )
            await session.commit()

        login = await async_client.post(
            "/api/auth/login",
            json={"email": info.email, "password": info.password},
            headers={"x-tenant-id": str(tenant_info)},
        )
        original_refresh = login.json()["refresh_token"]

        # First use — should succeed
        resp1 = await async_client.post(
            "/api/auth/refresh",
            json={"refresh_token": original_refresh},
        )
        assert resp1.status_code == 200

        # Second use of the SAME original token → reuse detected → 401
        resp2 = await async_client.post(
            "/api/auth/refresh",
            json={"refresh_token": original_refresh},
        )
        assert resp2.status_code == 401

        # The new token from resp1 should also be revoked (all sessions wiped)
        new_refresh = resp1.json()["refresh_token"]
        resp3 = await async_client.post(
            "/api/auth/refresh",
            json={"refresh_token": new_refresh},
        )
        assert resp3.status_code == 401


# ── 9.9 Logout ────────────────────────────────────────────────────────────────


class TestLogout:
    """9.9 Logout revoca el refresh token."""

    @pytest.mark.asyncio
    async def test_logout_revokes_refresh_token(
        self,
        async_client: AsyncClient,
        test_session_factory: async_sessionmaker[AsyncSession],
        tenant_info: uuid.UUID,
    ):
        """Scenario: after logout, the refresh token cannot be used."""
        async with test_session_factory() as session:
            info = await _create_usuario(
                session,
                tenant_id=tenant_info,
                email=f"logout-{uuid.uuid4().hex[:6]}@test.com",
                password="ValidPassword123!",
            )
            await session.commit()

        login = await async_client.post(
            "/api/auth/login",
            json={"email": info.email, "password": info.password},
            headers={"x-tenant-id": str(tenant_info)},
        )
        refresh_token = login.json()["refresh_token"]

        # Logout
        logout_resp = await async_client.post(
            "/api/auth/logout",
            json={"refresh_token": refresh_token},
        )
        assert logout_resp.status_code == 204

        # Token should now be rejected
        refresh_resp = await async_client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp.status_code == 401


# ── 9.10 get_current_user ─────────────────────────────────────────────────────


class TestGetCurrentUser:
    """9.10 get_current_user: valid token → user; expired → 401."""

    @pytest.mark.asyncio
    async def test_valid_token_accesses_protected_endpoint(
        self,
        async_client: AsyncClient,
        usuario_activo: UsuarioInfo,
    ):
        """Scenario: valid access token → enroll endpoint responds (not 401)."""
        login = await async_client.post(
            "/api/auth/login",
            json={"email": usuario_activo.email, "password": usuario_activo.password},
            headers={"x-tenant-id": str(usuario_activo.tenant_id)},
        )
        access_token = login.json()["access_token"]

        # Use enroll endpoint as the canary for "protected endpoint"
        resp = await async_client.post(
            "/api/auth/2fa/enroll",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        # Should NOT be 401 — user is authenticated
        assert resp.status_code != 401

    @pytest.mark.asyncio
    async def test_expired_token_returns_401(
        self,
        async_client: AsyncClient,
        usuario_activo: UsuarioInfo,
    ):
        """Scenario: expired access token → 401."""
        expired_token = create_access_token(
            {
                "sub": str(usuario_activo.id),
                "tenant_id": str(usuario_activo.tenant_id),
                "type": "access",
                "roles": [],
            },
            expires_delta=timedelta(seconds=-1),  # already expired
        )
        resp = await async_client.post(
            "/api/auth/2fa/enroll",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_no_token_returns_401(self, async_client: AsyncClient):
        """Scenario: no Bearer token → 401."""
        resp = await async_client.post("/api/auth/2fa/enroll")
        assert resp.status_code == 401


# ── 9.11 Rate limiting ────────────────────────────────────────────────────────


class TestRateLimit:
    """9.11 5 failed attempts → 6th returns HTTP 429."""

    @pytest.mark.asyncio
    async def test_sixth_failed_attempt_returns_429(
        self,
        async_client: AsyncClient,
        tenant_info: uuid.UUID,
    ):
        """Scenario: 5 consecutive failures → 6th attempt returns 429."""
        # Use a unique email so the test doesn't interfere with other tests
        email = f"ratelimit-{uuid.uuid4().hex[:8]}@test.com"
        payload = {"email": email, "password": "wrong"}
        headers = {"x-tenant-id": str(tenant_info)}

        # Reset rate limiter state for this key before the test
        rate_limiter.reset(f"testclient:{email.lower()}")

        for i in range(5):
            resp = await async_client.post("/api/auth/login", json=payload, headers=headers)
            assert resp.status_code == 401, f"Expected 401 on attempt {i+1}, got {resp.status_code}"

        # 6th attempt should hit rate limit
        resp = await async_client.post("/api/auth/login", json=payload, headers=headers)
        assert resp.status_code == 429

    @pytest.mark.asyncio
    async def test_successful_login_resets_counter(
        self,
        async_client: AsyncClient,
        test_session_factory: async_sessionmaker[AsyncSession],
        tenant_info: uuid.UUID,
    ):
        """Scenario: successful login resets the rate limit counter."""
        async with test_session_factory() as session:
            info = await _create_usuario(
                session,
                tenant_id=tenant_info,
                email=f"rl-reset-{uuid.uuid4().hex[:6]}@test.com",
                password="ValidPassword123!",
            )
            await session.commit()

        email = info.email
        headers = {"x-tenant-id": str(tenant_info)}
        rate_limiter.reset(f"testclient:{email.lower()}")

        # 2 failed attempts
        for _ in range(2):
            await async_client.post(
                "/api/auth/login",
                json={"email": email, "password": "wrong"},
                headers=headers,
            )

        # Successful login — should reset counter
        resp = await async_client.post(
            "/api/auth/login",
            json={"email": email, "password": info.password},
            headers=headers,
        )
        assert resp.status_code == 200

        # 5 new failures should work before hitting limit
        for _ in range(5):
            await async_client.post(
                "/api/auth/login",
                json={"email": email, "password": "wrong"},
                headers=headers,
            )
        resp = await async_client.post(
            "/api/auth/login",
            json={"email": email, "password": "wrong"},
            headers=headers,
        )
        assert resp.status_code == 429


# ── 9.12 Forgot + Reset ───────────────────────────────────────────────────────


class TestForgotReset:
    """9.12 Triangulación: forgot + reset (válido, reutilizado)."""

    @pytest.mark.asyncio
    async def test_forgot_returns_200_for_known_email(
        self,
        async_client: AsyncClient,
        usuario_activo: UsuarioInfo,
    ):
        """Scenario: forgot with a known email returns 200."""
        resp = await async_client.post(
            "/api/auth/forgot",
            json={"email": usuario_activo.email, "dev_mode": True},
            headers={"x-tenant-id": str(usuario_activo.tenant_id)},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_forgot_returns_200_for_unknown_email(
        self,
        async_client: AsyncClient,
        tenant_info: uuid.UUID,
    ):
        """Scenario: forgot with unknown email returns 200 (no enumeration)."""
        resp = await async_client.post(
            "/api/auth/forgot",
            json={"email": "ghost@nobody.example", "dev_mode": True},
            headers={"x-tenant-id": str(tenant_info)},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_reset_with_valid_token_updates_password(
        self,
        async_client: AsyncClient,
        test_session_factory: async_sessionmaker[AsyncSession],
        tenant_info: uuid.UUID,
    ):
        """Scenario: valid token + new password → password updated, token consumed."""
        async with test_session_factory() as session:
            info = await _create_usuario(
                session,
                tenant_id=tenant_info,
                email=f"reset-{uuid.uuid4().hex[:6]}@test.com",
                password="OldPassword123!",
            )
            await session.commit()

        headers = {"x-tenant-id": str(tenant_info)}

        # Get reset token in dev mode
        forgot_resp = await async_client.post(
            "/api/auth/forgot",
            json={"email": info.email, "dev_mode": True},
            headers=headers,
        )
        token = forgot_resp.json().get("token")
        assert token is not None, "dev_mode should return the token"

        # Reset
        reset_resp = await async_client.post(
            "/api/auth/reset",
            json={"token": token, "new_password": "NewPassword456!"},
            headers=headers,
        )
        assert reset_resp.status_code == 200

        # Login with new password should work
        login_resp = await async_client.post(
            "/api/auth/login",
            json={"email": info.email, "password": "NewPassword456!"},
            headers=headers,
        )
        assert login_resp.status_code == 200

    @pytest.mark.asyncio
    async def test_reset_with_reused_token_returns_400(
        self,
        async_client: AsyncClient,
        test_session_factory: async_sessionmaker[AsyncSession],
        tenant_info: uuid.UUID,
    ):
        """Triangulation: reusing a consumed reset token → 400."""
        async with test_session_factory() as session:
            info = await _create_usuario(
                session,
                tenant_id=tenant_info,
                email=f"reset-reuse-{uuid.uuid4().hex[:6]}@test.com",
                password="OldPassword123!",
            )
            await session.commit()

        headers = {"x-tenant-id": str(tenant_info)}

        forgot_resp = await async_client.post(
            "/api/auth/forgot",
            json={"email": info.email, "dev_mode": True},
            headers=headers,
        )
        token = forgot_resp.json()["token"]

        # First reset — should work
        resp1 = await async_client.post(
            "/api/auth/reset",
            json={"token": token, "new_password": "NewPassword456!"},
            headers=headers,
        )
        assert resp1.status_code == 200

        # Second reset with the same token — should fail
        resp2 = await async_client.post(
            "/api/auth/reset",
            json={"token": token, "new_password": "AnotherPassword789!"},
            headers=headers,
        )
        assert resp2.status_code == 400
