"""repositories/asignacion.py — AsignacionRepository (C-07 / C-08).

All queries are scoped to tenant_id and exclude soft-deleted records.

Methods (C-07):
  create               — persist a new Asignacion
  list_by_usuario      — all (including expired) for a user in this tenant
  get_vigentes_by_usuario — only active assignments (hasta IS NULL OR hasta >= today)

Methods added in C-08:
  get(id)              — get by id, scoped to tenant (inherited from BaseRepository)
  update(id, data)     — update scoped to tenant (inherited from BaseRepository)
  list_with_filters    — list with optional filters + solo_vigentes flag
  bulk_create          — idempotent multi-create
  clone_team           — duplicate vigentes between cohortes
  bulk_update_vigencia — update desde/hasta for an entire team
"""

import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import and_, or_, select, update

from app.models.asignacion import Asignacion
from app.repositories.base import BaseRepository

if TYPE_CHECKING:
    from app.schemas.asignacion import AsignacionFilter


class AsignacionRepository(BaseRepository[Asignacion]):
    """Tenant-scoped repository for Asignacion records."""

    def __init__(self, session, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, Asignacion)

    # ── C-07 methods ──────────────────────────────────────────────────────────

    async def list_by_usuario(self, usuario_id: uuid.UUID) -> list[Asignacion]:
        """Return all (including expired) assignments for a user in this tenant.

        Excludes soft-deleted records.
        """
        stmt = select(Asignacion).where(
            Asignacion.tenant_id == self._tenant_id,
            Asignacion.usuario_id == usuario_id,
            Asignacion.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_vigentes_by_usuario(
        self,
        usuario_id: uuid.UUID,
        reference_date: date | None = None,
    ) -> list[Asignacion]:
        """Return only active (vigentes) assignments for a user in this tenant.

        An assignment is vigente when: hasta IS NULL OR hasta >= reference_date.
        Excludes soft-deleted records.

        Args:
            usuario_id:      UUID of the user.
            reference_date:  Date to check vigencia against (default: today).
        """
        if reference_date is None:
            reference_date = date.today()

        stmt = select(Asignacion).where(
            Asignacion.tenant_id == self._tenant_id,
            Asignacion.usuario_id == usuario_id,
            Asignacion.deleted_at.is_(None),
            Asignacion.desde <= reference_date,
            or_(
                Asignacion.hasta.is_(None),
                Asignacion.hasta >= reference_date,
            ),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ── C-08 methods ──────────────────────────────────────────────────────────

    async def list_with_filters(self, filters: "AsignacionFilter") -> list[Asignacion]:
        """Return assignments for the current tenant with optional filters.

        Args:
            filters: AsignacionFilter with optional materia_id, carrera_id,
                     cohorte_id, usuario_id, rol, solo_vigentes.
        """
        today = date.today()
        conditions = [
            Asignacion.tenant_id == self._tenant_id,
            Asignacion.deleted_at.is_(None),
        ]

        if filters.materia_id is not None:
            conditions.append(Asignacion.materia_id == filters.materia_id)
        if filters.carrera_id is not None:
            conditions.append(Asignacion.carrera_id == filters.carrera_id)
        if filters.cohorte_id is not None:
            conditions.append(Asignacion.cohorte_id == filters.cohorte_id)
        if filters.usuario_id is not None:
            conditions.append(Asignacion.usuario_id == filters.usuario_id)
        if filters.rol is not None:
            conditions.append(Asignacion.rol == filters.rol)
        if filters.solo_vigentes:
            conditions.append(Asignacion.desde <= today)
            conditions.append(
                or_(
                    Asignacion.hasta.is_(None),
                    Asignacion.hasta >= today,
                )
            )

        stmt = select(Asignacion).where(and_(*conditions))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def bulk_create(
        self,
        items: list[dict],
    ) -> tuple[list[Asignacion], list[uuid.UUID]]:
        """Create multiple Asignacion records, skipping duplicates.

        An assignment is considered a duplicate if an active (non-deleted)
        record already exists with the same
        (tenant_id, usuario_id, rol, materia_id, carrera_id, cohorte_id).

        Returns:
            A tuple (creadas, omitidos) where:
              creadas  — list of newly created Asignacion objects
              omitidos — list of usuario_ids that were skipped
        """
        creadas: list[Asignacion] = []
        omitidos: list[uuid.UUID] = []

        for item in items:
            usuario_id = item["usuario_id"]
            duplicate = await self._find_duplicate(
                usuario_id=usuario_id,
                rol=item.get("rol"),
                materia_id=item.get("materia_id"),
                carrera_id=item.get("carrera_id"),
                cohorte_id=item.get("cohorte_id"),
            )
            if duplicate is not None:
                omitidos.append(usuario_id)
                continue

            created = await self.create(item)
            creadas.append(created)

        return creadas, omitidos

    async def clone_team(
        self,
        origen_cohorte_id: uuid.UUID,
        destino_cohorte_id: uuid.UUID,
        materia_id: uuid.UUID,
        carrera_id: uuid.UUID,
        desde: date,
        hasta: date | None,
    ) -> tuple[list[Asignacion], list[uuid.UUID]]:
        """Clone all vigente assignments from origen to destino cohorte.

        Rules:
          - Only vigentes (active) assignments from the origin are cloned.
          - The clone uses the new cohorte_id, desde, hasta.
          - All other fields (usuario_id, rol, comisiones, responsable_id) are
            preserved from the origin.
          - If a duplicate already exists in the destination, it is omitted.

        Returns:
            (creadas, omitidos) — created records and skipped usuario_ids.
        """
        today = date.today()
        stmt = select(Asignacion).where(
            Asignacion.tenant_id == self._tenant_id,
            Asignacion.materia_id == materia_id,
            Asignacion.carrera_id == carrera_id,
            Asignacion.cohorte_id == origen_cohorte_id,
            Asignacion.deleted_at.is_(None),
            Asignacion.desde <= today,
            or_(
                Asignacion.hasta.is_(None),
                Asignacion.hasta >= today,
            ),
        )
        result = await self._session.execute(stmt)
        origen_asignaciones = list(result.scalars().all())

        items = [
            {
                "usuario_id": a.usuario_id,
                "rol": a.rol,
                "materia_id": materia_id,
                "carrera_id": carrera_id,
                "cohorte_id": destino_cohorte_id,
                "comisiones": list(a.comisiones),
                "responsable_id": a.responsable_id,
                "desde": desde,
                "hasta": hasta,
            }
            for a in origen_asignaciones
        ]

        return await self.bulk_create(items)

    async def bulk_update_vigencia(
        self,
        materia_id: uuid.UUID,
        carrera_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        desde: date,
        hasta: date | None,
    ) -> int:
        """Update desde/hasta for all active assignments of a team.

        A team is identified by (tenant_id, materia_id, carrera_id, cohorte_id).
        Only non-deleted records are updated.

        Returns:
            Number of rows updated.
        """
        stmt = (
            update(Asignacion)
            .where(
                Asignacion.tenant_id == self._tenant_id,
                Asignacion.materia_id == materia_id,
                Asignacion.carrera_id == carrera_id,
                Asignacion.cohorte_id == cohorte_id,
                Asignacion.deleted_at.is_(None),
            )
            .values(
                desde=desde,
                hasta=hasta,
                updated_at=datetime.now(tz=timezone.utc),
            )
            .execution_options(synchronize_session="fetch")
        )
        result = await self._session.execute(stmt)
        return result.rowcount  # type: ignore[return-value]

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _find_duplicate(
        self,
        usuario_id: uuid.UUID,
        rol: str | None,
        materia_id: uuid.UUID | None,
        carrera_id: uuid.UUID | None,
        cohorte_id: uuid.UUID | None,
    ) -> Asignacion | None:
        """Find an existing non-deleted assignment with the same key tuple."""
        conditions = [
            Asignacion.tenant_id == self._tenant_id,
            Asignacion.usuario_id == usuario_id,
            Asignacion.deleted_at.is_(None),
        ]
        if rol is not None:
            conditions.append(Asignacion.rol == rol)

        # Nullable FK comparisons: NULL == NULL must match
        if materia_id is None:
            conditions.append(Asignacion.materia_id.is_(None))
        else:
            conditions.append(Asignacion.materia_id == materia_id)

        if carrera_id is None:
            conditions.append(Asignacion.carrera_id.is_(None))
        else:
            conditions.append(Asignacion.carrera_id == carrera_id)

        if cohorte_id is None:
            conditions.append(Asignacion.cohorte_id.is_(None))
        else:
            conditions.append(Asignacion.cohorte_id == cohorte_id)

        stmt = select(Asignacion).where(and_(*conditions)).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
