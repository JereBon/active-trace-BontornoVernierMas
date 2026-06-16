"""repositories/calificacion_repository.py — CalificacionRepository + UmbralMateriaRepository (C-10).

Tenant-scoped repositories for calificacion and umbral_materia records.
All queries filter by tenant_id and exclude soft-deleted records.

CalificacionRepository methods:
  upsert_bulk              — upsert multiple Calificacion rows (ON CONFLICT DO UPDATE)
  list_by_materia          — list all active calificaciones for a materia in this tenant
  list_by_entrada_padron   — list calificaciones for a specific student entry
  delete_by_asignacion_materia — soft-delete calificaciones for asignacion×materia (RN-04)

UmbralMateriaRepository methods:
  get_by_asignacion_materia — get umbral for a specific asignacion×materia pair
  upsert                    — create or update umbral for a specific asignacion×materia pair

Design decisions (C-10 design.md D3, D4):
- upsert_bulk uses INSERT ... ON CONFLICT DO UPDATE to handle re-imports cleanly.
- UmbralMateriaRepository.upsert: SELECT then INSERT or UPDATE within one session.
- Tenant isolation enforced on every query.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calificacion import Calificacion
from app.models.umbral_materia import UmbralMateria
from app.repositories.base import BaseRepository


class CalificacionRepository(BaseRepository[Calificacion]):
    """Tenant-scoped repository for Calificacion records."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, Calificacion)

    async def upsert_bulk(
        self,
        calificaciones: list[dict[str, Any]],
    ) -> list[Calificacion]:
        """Insert or update multiple Calificacion rows.

        Uses PostgreSQL INSERT ... ON CONFLICT DO UPDATE to handle re-imports.
        Unique conflict key: (tenant_id, entrada_padron_id, actividad).

        Each dict must contain:
          entrada_padron_id, materia_id, actividad, nota_numerica (or None),
          nota_textual (or None), aprobado, origen.

        Returns:
            List of upserted Calificacion instances.
        """
        if not calificaciones:
            return []

        now = datetime.now(tz=timezone.utc)
        created: list[Calificacion] = []

        for data in calificaciones:
            # Build the INSERT statement with ON CONFLICT
            stmt = (
                pg_insert(Calificacion)
                .values(
                    id=uuid.uuid4(),
                    tenant_id=self._tenant_id,
                    entrada_padron_id=data["entrada_padron_id"],
                    materia_id=data["materia_id"],
                    actividad=data["actividad"],
                    nota_numerica=data.get("nota_numerica"),
                    nota_textual=data.get("nota_textual"),
                    aprobado=data["aprobado"],
                    origen=data.get("origen", "Importado"),
                    importado_at=now,
                    created_at=now,
                    updated_at=now,
                    deleted_at=None,
                )
                .on_conflict_do_update(
                    constraint="uq_calificacion_entrada_actividad",
                    set_={
                        "nota_numerica": data.get("nota_numerica"),
                        "nota_textual": data.get("nota_textual"),
                        "aprobado": data["aprobado"],
                        "origen": data.get("origen", "Importado"),
                        "importado_at": now,
                        "updated_at": now,
                        "deleted_at": None,
                    },
                )
                .returning(Calificacion)
            )
            result = await self._session.execute(stmt)
            row = result.scalar_one()
            created.append(row)

        await self._session.flush()
        return created

    async def list_by_materia(
        self,
        materia_id: uuid.UUID,
    ) -> list[Calificacion]:
        """Return all active calificaciones for a materia in this tenant."""
        stmt = select(Calificacion).where(
            Calificacion.tenant_id == self._tenant_id,
            Calificacion.materia_id == materia_id,
            Calificacion.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_entrada_padron(
        self,
        entrada_padron_id: uuid.UUID,
    ) -> list[Calificacion]:
        """Return all active calificaciones for a specific student entry in this tenant."""
        stmt = select(Calificacion).where(
            Calificacion.tenant_id == self._tenant_id,
            Calificacion.entrada_padron_id == entrada_padron_id,
            Calificacion.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_aprobado_batch(
        self,
        materia_id: uuid.UUID,
        entrada_padron_ids: list[uuid.UUID],
        umbral_pct: int,
        valores_aprobatorios: list[str],
    ) -> int:
        """Recalculate and update `aprobado` for a batch of calificaciones.

        Used when the umbral changes. Returns the number of rows updated.
        """
        if not entrada_padron_ids:
            return 0

        now = datetime.now(tz=timezone.utc)

        # Fetch all relevant calificaciones
        stmt = select(Calificacion).where(
            Calificacion.tenant_id == self._tenant_id,
            Calificacion.materia_id == materia_id,
            Calificacion.entrada_padron_id.in_(entrada_padron_ids),
            Calificacion.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        cals = list(result.scalars().all())

        from app.services.calificacion_service import calcular_aprobado  # avoid circular

        updated_count = 0
        for cal in cals:
            new_aprobado = calcular_aprobado(
                nota_numerica=float(cal.nota_numerica) if cal.nota_numerica is not None else None,
                nota_textual=cal.nota_textual,
                umbral_pct=umbral_pct,
                valores_aprobatorios=valores_aprobatorios,
            )
            if cal.aprobado != new_aprobado:
                cal.aprobado = new_aprobado
                cal.updated_at = now
                self._session.add(cal)
                updated_count += 1

        if updated_count:
            await self._session.flush()

        return len(cals)  # return total processed, not just updated

    async def delete_by_asignacion_materia(
        self,
        materia_id: uuid.UUID,
    ) -> int:
        """Soft-delete all calificaciones for a materia in this tenant (RN-04).

        Scope-isolated: only affects the current tenant's calificaciones
        for the given materia.

        Returns:
            Number of rows soft-deleted.
        """
        now = datetime.now(tz=timezone.utc)
        stmt = (
            update(Calificacion)
            .where(
                and_(
                    Calificacion.tenant_id == self._tenant_id,
                    Calificacion.materia_id == materia_id,
                    Calificacion.deleted_at.is_(None),
                )
            )
            .values(deleted_at=now, updated_at=now)
            .execution_options(synchronize_session="fetch")
        )
        result = await self._session.execute(stmt)
        return result.rowcount


class UmbralMateriaRepository(BaseRepository[UmbralMateria]):
    """Tenant-scoped repository for UmbralMateria records."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, UmbralMateria)

    async def get_by_asignacion_materia(
        self,
        asignacion_id: uuid.UUID,
        materia_id: uuid.UUID,
    ) -> UmbralMateria | None:
        """Return the umbral for a specific (asignacion, materia) pair, or None."""
        stmt = select(UmbralMateria).where(
            UmbralMateria.tenant_id == self._tenant_id,
            UmbralMateria.asignacion_id == asignacion_id,
            UmbralMateria.materia_id == materia_id,
            UmbralMateria.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(
        self,
        asignacion_id: uuid.UUID,
        materia_id: uuid.UUID,
        umbral_pct: int,
        valores_aprobatorios: list[str],
    ) -> UmbralMateria:
        """Create or update the umbral for an (asignacion, materia) pair.

        Uses PostgreSQL INSERT ... ON CONFLICT DO UPDATE for atomicity.

        Returns:
            The created or updated UmbralMateria.
        """
        now = datetime.now(tz=timezone.utc)
        stmt = (
            pg_insert(UmbralMateria)
            .values(
                id=uuid.uuid4(),
                tenant_id=self._tenant_id,
                asignacion_id=asignacion_id,
                materia_id=materia_id,
                umbral_pct=umbral_pct,
                valores_aprobatorios=valores_aprobatorios,
                created_at=now,
                updated_at=now,
                deleted_at=None,
            )
            .on_conflict_do_update(
                constraint="uq_umbral_materia_asignacion",
                set_={
                    "umbral_pct": umbral_pct,
                    "valores_aprobatorios": valores_aprobatorios,
                    "updated_at": now,
                    "deleted_at": None,
                },
            )
            .returning(UmbralMateria)
        )
        result = await self._session.execute(stmt)
        umbral = result.scalar_one()
        await self._session.flush()
        return umbral
