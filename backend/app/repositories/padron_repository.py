"""repositories/padron_repository.py — PadronRepository (C-09).

Tenant-scoped repository for VersionPadron and EntradaPadron records.
All queries filter by tenant_id and exclude soft-deleted records.

Methods:
  get_version_activa     — get the active version for (materia, cohorte)
  get_versiones          — list all versions (active + historical) for a materia
  crear_version          — create new version, deactivating previous atomically
  bulk_insert_entradas   — insert multiple EntradaPadron for a version
  soft_delete_by_materia — soft-delete all versions + entries for a materia

Design decisions (C-09 design.md D1, D6):
- crear_version uses SELECT FOR UPDATE (via with_for_update()) to prevent
  race conditions when two requests activate simultaneously.
- soft_delete_by_materia sets deleted_at on both VersionPadron and their
  EntradaPadron rows for the current tenant and materia.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entrada_padron import EntradaPadron
from app.models.version_padron import VersionPadron
from app.repositories.base import BaseRepository


class PadronRepository(BaseRepository[VersionPadron]):
    """Tenant-scoped repository for padrón versioning and entries."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, VersionPadron)

    # ── Version queries ───────────────────────────────────────────────────────

    async def get_version_activa(
        self,
        materia_id: uuid.UUID,
        cohorte_id: uuid.UUID,
    ) -> VersionPadron | None:
        """Return the currently active version for (materia, cohorte), or None.

        Scoped to the current tenant. Excludes soft-deleted versions.
        """
        stmt = select(VersionPadron).where(
            VersionPadron.tenant_id == self._tenant_id,
            VersionPadron.materia_id == materia_id,
            VersionPadron.cohorte_id == cohorte_id,
            VersionPadron.activa.is_(True),
            VersionPadron.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_versiones(
        self,
        materia_id: uuid.UUID,
    ) -> list[VersionPadron]:
        """Return all versions (active and historical) for a materia in this tenant.

        Excludes soft-deleted versions. Ordered by cargado_at descending.
        """
        stmt = (
            select(VersionPadron)
            .where(
                VersionPadron.tenant_id == self._tenant_id,
                VersionPadron.materia_id == materia_id,
                VersionPadron.deleted_at.is_(None),
            )
            .order_by(VersionPadron.cargado_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_entradas(self, version_id: uuid.UUID) -> list[EntradaPadron]:
        """Return all active entries for a given version in this tenant."""
        stmt = select(EntradaPadron).where(
            EntradaPadron.tenant_id == self._tenant_id,
            EntradaPadron.version_id == version_id,
            EntradaPadron.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ── Version writes ────────────────────────────────────────────────────────

    async def crear_version(
        self,
        materia_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        cargado_por: uuid.UUID,
    ) -> VersionPadron:
        """Create a new VersionPadron, atomically deactivating the previous one.

        Steps (within the current transaction):
          1. Lock the existing active version for update (if any).
          2. Set activa=False on the previous version.
          3. Insert the new version with activa=True.

        The caller is responsible for committing the transaction.

        Returns:
            The newly created VersionPadron (activa=True).
        """
        # Step 1: Lock existing active version
        lock_stmt = (
            select(VersionPadron)
            .where(
                VersionPadron.tenant_id == self._tenant_id,
                VersionPadron.materia_id == materia_id,
                VersionPadron.cohorte_id == cohorte_id,
                VersionPadron.activa.is_(True),
                VersionPadron.deleted_at.is_(None),
            )
            .with_for_update()
        )
        lock_result = await self._session.execute(lock_stmt)
        prev_version = lock_result.scalar_one_or_none()

        # Step 2: Deactivate the previous version
        if prev_version is not None:
            prev_version.activa = False
            prev_version.updated_at = datetime.now(tz=timezone.utc)
            self._session.add(prev_version)
            await self._session.flush()

        # Step 3: Create new active version
        new_version = VersionPadron(
            id=uuid.uuid4(),
            tenant_id=self._tenant_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            cargado_por=cargado_por,
            activa=True,
        )
        self._session.add(new_version)
        await self._session.flush()
        await self._session.refresh(new_version)
        return new_version

    async def bulk_insert_entradas(
        self,
        version_id: uuid.UUID,
        entradas: list[dict[str, Any]],
    ) -> list[EntradaPadron]:
        """Insert multiple EntradaPadron rows for a version.

        Each dict in entradas must contain: nombre, apellidos, email_cifrado.
        Optional fields: usuario_id, comision, regional.

        Args:
            version_id: UUID of the parent VersionPadron.
            entradas:   List of dicts with entrada data.

        Returns:
            List of created EntradaPadron records.
        """
        created: list[EntradaPadron] = []
        for data in entradas:
            entrada = EntradaPadron(
                id=uuid.uuid4(),
                tenant_id=self._tenant_id,
                version_id=version_id,
                usuario_id=data.get("usuario_id"),
                nombre=data["nombre"],
                apellidos=data["apellidos"],
                email_cifrado=data["email_cifrado"],
                comision=data.get("comision"),
                regional=data.get("regional"),
            )
            self._session.add(entrada)
            created.append(entrada)

        await self._session.flush()

        # Refresh all created entries to get server-side defaults
        for entrada in created:
            await self._session.refresh(entrada)

        return created

    # ── Soft-delete ───────────────────────────────────────────────────────────

    async def soft_delete_by_materia(self, materia_id: uuid.UUID) -> int:
        """Soft-delete all versions and entries for a materia in this tenant.

        Sets deleted_at = now() on all VersionPadron and their EntradaPadron
        rows that belong to (tenant_id, materia_id).

        Returns:
            Total number of rows soft-deleted (versions + entries).
        """
        now = datetime.now(tz=timezone.utc)

        # Step 1: Find all version IDs to soft-delete
        version_stmt = select(VersionPadron.id).where(
            VersionPadron.tenant_id == self._tenant_id,
            VersionPadron.materia_id == materia_id,
            VersionPadron.deleted_at.is_(None),
        )
        version_result = await self._session.execute(version_stmt)
        version_ids = [row[0] for row in version_result.fetchall()]

        if not version_ids:
            return 0

        # Step 2: Soft-delete all entries for those versions
        entry_update = (
            update(EntradaPadron)
            .where(
                and_(
                    EntradaPadron.tenant_id == self._tenant_id,
                    EntradaPadron.version_id.in_(version_ids),
                    EntradaPadron.deleted_at.is_(None),
                )
            )
            .values(deleted_at=now, updated_at=now)
            .execution_options(synchronize_session="fetch")
        )
        entry_result = await self._session.execute(entry_update)

        # Step 3: Soft-delete the versions themselves
        version_update = (
            update(VersionPadron)
            .where(
                and_(
                    VersionPadron.tenant_id == self._tenant_id,
                    VersionPadron.id.in_(version_ids),
                    VersionPadron.deleted_at.is_(None),
                )
            )
            .values(deleted_at=now, updated_at=now, activa=False)
            .execution_options(synchronize_session="fetch")
        )
        version_result2 = await self._session.execute(version_update)

        total = entry_result.rowcount + version_result2.rowcount
        return total
