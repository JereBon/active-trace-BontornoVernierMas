"""tests/test_tenancy.py — Tests for multi-tenant isolation via BaseRepository.

TDD cycles:
  5.1 Fixture setup: two tenants in a real test DB
  5.2 RED→GREEN: repo scoped to tenant A cannot see records of tenant B
  5.3 RED→GREEN: soft_delete marks deleted_at; record excluded from list/get
  5.4 RED→GREEN: created_at/updated_at auto-set on create; updated_at changes on update
  5.5 Triangulation: multiple records from different tenants → list returns only own

Uses a real PostgreSQL test DB (DATABASE_URL_TEST). No DB mocking.

Note on fixture scoping: all async fixtures use scope="module" so they share
the same event loop. Function-scoped tests create sessions inline using the
module-scoped factory to avoid asyncio event loop cross-scope issues.
"""

import uuid
from dataclasses import dataclass, field

import pytest
import pytest_asyncio
from sqlalchemy import String, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import mapped_column

from app.models.base import Base, TenantScopedMixin
from app.repositories.base import BaseRepository


# ── Test-only model ───────────────────────────────────────────────────────────


class SampleEntity(Base, TenantScopedMixin):
    """Minimal tenant-scoped entity used only in tests.

    Exists so we can test BaseRepository behaviour without depending on domain
    models that will be created in later changes (C-06 onwards).
    """

    __tablename__ = "test_sample_entities"

    name = mapped_column(String(255), nullable=False)


# ── Module-scoped fixtures ────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def db_tables(test_session_factory: async_sessionmaker[AsyncSession]):
    """Create test tables (SampleEntity, Tenant) at module start; drop at end."""
    from app.core import database as db_module

    engine = db_module.engine
    assert engine is not None, "Engine must be initialized before tests run"

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@dataclass
class TenantInfo:
    """Holds tenant ID and slug (detached from DB session)."""

    id: uuid.UUID
    slug: str
    nombre: str


@pytest_asyncio.fixture(scope="module")
async def two_tenants(
    test_session_factory: async_sessionmaker[AsyncSession],
    db_tables,
) -> tuple[TenantInfo, TenantInfo]:
    """Create and persist two distinct Tenant rows for isolation tests."""
    from app.models.tenant import Tenant

    async with test_session_factory() as session:
        tenant_a = Tenant(
            id=uuid.uuid4(),
            slug=f"tenant-a-{uuid.uuid4().hex[:8]}",
            nombre="Tenant A",
        )
        tenant_b = Tenant(
            id=uuid.uuid4(),
            slug=f"tenant-b-{uuid.uuid4().hex[:8]}",
            nombre="Tenant B",
        )
        session.add(tenant_a)
        session.add(tenant_b)
        await session.commit()
        # Capture before session closes (objects become detached)
        info_a = TenantInfo(tenant_a.id, tenant_a.slug, tenant_a.nombre)
        info_b = TenantInfo(tenant_b.id, tenant_b.slug, tenant_b.nombre)

    return info_a, info_b


# ── 5.2 Tenant isolation ──────────────────────────────────────────────────────


class TestTenantIsolation:
    """BaseRepository scoped to tenant A must never return tenant B records."""

    @pytest.mark.asyncio
    async def test_get_returns_none_for_other_tenant(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        two_tenants: tuple[TenantInfo, TenantInfo],
    ):
        """Scenario: Records from another tenant are never returned (get → None)."""
        tenant_a, tenant_b = two_tenants

        async with test_session_factory() as session:
            # Create a record belonging to tenant_b
            repo_b = BaseRepository(session, tenant_b.id, SampleEntity)
            record = await repo_b.create({"name": "secret record of B"})
            await session.commit()
            record_id = record.id

        async with test_session_factory() as session:
            # Repo scoped to tenant_a must NOT find tenant_b's record
            repo_a = BaseRepository(session, tenant_a.id, SampleEntity)
            result = await repo_a.get(record_id)
            assert result is None

    @pytest.mark.asyncio
    async def test_list_returns_no_other_tenant_records(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        two_tenants: tuple[TenantInfo, TenantInfo],
    ):
        """Scenario: Records from another tenant are never returned (list items)."""
        tenant_a, tenant_b = two_tenants

        async with test_session_factory() as session:
            repo_b = BaseRepository(session, tenant_b.id, SampleEntity)
            await repo_b.create({"name": "b-exclusive-1"})
            await repo_b.create({"name": "b-exclusive-2"})
            await session.commit()

        async with test_session_factory() as session:
            repo_a = BaseRepository(session, tenant_a.id, SampleEntity)
            results = await repo_a.list()

            # verify none of tenant_a's results belong to tenant_b
            for item in results:
                assert item.tenant_id == tenant_a.id


# ── 5.3 Soft delete ───────────────────────────────────────────────────────────


class TestSoftDelete:
    """soft_delete must set deleted_at; record persists in DB but is invisible."""

    @pytest.mark.asyncio
    async def test_soft_delete_sets_deleted_at(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        two_tenants: tuple[TenantInfo, TenantInfo],
    ):
        """Scenario: Soft-deleted record remains in database with deleted_at set."""
        tenant_a, _ = two_tenants

        async with test_session_factory() as session:
            repo = BaseRepository(session, tenant_a.id, SampleEntity)
            record = await repo.create({"name": "to-be-deleted"})
            await session.commit()
            record_id = record.id

        async with test_session_factory() as session:
            repo = BaseRepository(session, tenant_a.id, SampleEntity)
            deleted = await repo.soft_delete(record_id)
            await session.commit()

        assert deleted is True

        async with test_session_factory() as session:
            repo = BaseRepository(session, tenant_a.id, SampleEntity)
            # Must not appear in list or get
            assert await repo.get(record_id) is None
            items = await repo.list()
            assert all(item.id != record_id for item in items)

            # Must still exist in DB (physical row present)
            stmt = select(SampleEntity).where(SampleEntity.id == record_id)
            result = await session.execute(stmt)
            raw = result.scalar_one_or_none()
            assert raw is not None
            assert raw.deleted_at is not None

    @pytest.mark.asyncio
    async def test_soft_delete_returns_false_for_nonexistent(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        two_tenants: tuple[TenantInfo, TenantInfo],
    ):
        """soft_delete on an unknown id returns False (no error)."""
        tenant_a, _ = two_tenants

        async with test_session_factory() as session:
            repo = BaseRepository(session, tenant_a.id, SampleEntity)
            result = await repo.soft_delete(uuid.uuid4())

        assert result is False


# ── 5.4 Timestamps ────────────────────────────────────────────────────────────


class TestTimestamps:
    """created_at/updated_at are auto-set; updated_at changes on update."""

    @pytest.mark.asyncio
    async def test_timestamps_set_on_create(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        two_tenants: tuple[TenantInfo, TenantInfo],
    ):
        """Scenario: created_at and updated_at non-null after create."""
        tenant_a, _ = two_tenants

        async with test_session_factory() as session:
            repo = BaseRepository(session, tenant_a.id, SampleEntity)
            record = await repo.create({"name": "ts-test"})
            await session.commit()

            assert record.created_at is not None
            assert record.updated_at is not None

    @pytest.mark.asyncio
    async def test_updated_at_changes_on_update(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        two_tenants: tuple[TenantInfo, TenantInfo],
    ):
        """Scenario: updated_at is greater after update."""
        import asyncio

        tenant_a, _ = two_tenants

        async with test_session_factory() as session:
            repo = BaseRepository(session, tenant_a.id, SampleEntity)
            record = await repo.create({"name": "update-ts-test"})
            await session.commit()
            record_id = record.id
            original_updated_at = record.updated_at

        # Small sleep to guarantee a different timestamp
        await asyncio.sleep(0.05)

        async with test_session_factory() as session:
            repo = BaseRepository(session, tenant_a.id, SampleEntity)
            updated = await repo.update(record_id, {"name": "updated-name"})
            await session.commit()

        assert updated is not None
        assert updated.updated_at > original_updated_at


# ── 5.5 Triangulation: multiple tenants mixed ─────────────────────────────────


class TestTenantIsolationTriangulation:
    """list() returns only records belonging to the correct tenant."""

    @pytest.mark.asyncio
    async def test_list_returns_only_own_tenant_records(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        two_tenants: tuple[TenantInfo, TenantInfo],
    ):
        """Scenario: Multiple records from different tenants; list isolates correctly."""
        tenant_a, tenant_b = two_tenants
        names_a = {"tri-a-1", "tri-a-2", "tri-a-3"}
        names_b = {"tri-b-1", "tri-b-2"}

        async with test_session_factory() as session:
            repo_a = BaseRepository(session, tenant_a.id, SampleEntity)
            repo_b = BaseRepository(session, tenant_b.id, SampleEntity)

            for name in names_a:
                await repo_a.create({"name": name})
            for name in names_b:
                await repo_b.create({"name": name})
            await session.commit()

        async with test_session_factory() as session:
            repo_a = BaseRepository(session, tenant_a.id, SampleEntity)
            repo_b = BaseRepository(session, tenant_b.id, SampleEntity)

            results_a = await repo_a.list()
            results_b = await repo_b.list()

        # All records in results_a must belong to tenant_a
        for item in results_a:
            assert item.tenant_id == tenant_a.id

        # All records in results_b must belong to tenant_b
        for item in results_b:
            assert item.tenant_id == tenant_b.id

        # The tri-a-* names must appear in a's list
        names_in_a = {item.name for item in results_a}
        assert names_a.issubset(names_in_a)

        # The tri-b-* names must appear in b's list
        names_in_b = {item.name for item in results_b}
        assert names_b.issubset(names_in_b)
