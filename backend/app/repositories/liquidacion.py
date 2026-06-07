"""repositories/liquidacion.py — LiquidacionRepository (C-18).

All queries are scoped to tenant_id. Key methods:
  - crear / get / listar_por_periodo / listar_historial / cerrar_periodo
  - get_asignaciones_vigentes: helper to fetch Asignacion+Materia data for
    the calculation engine (task 2.5).

Design decisions (C-18 design.md):
- D5: cerrar_periodo bulk-updates all Abierta records for (cohorte, periodo).
      The service validates immutability before calling this.
- D3: all DB I/O in this file; calculation logic stays in LiquidacionService.
- Multi-tenancy: every query includes tenant_id = self._tenant_id.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.models.liquidacion import EstadoLiquidacion, Liquidacion
from app.models.materia import Materia
from app.models.usuario import Usuario
from app.repositories.base import BaseRepository


class LiquidacionRepository(BaseRepository[Liquidacion]):
    """Tenant-scoped repository for Liquidacion records."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id, Liquidacion)

    # ── Reads ─────────────────────────────────────────────────────────────────

    async def listar_por_periodo(
        self,
        cohorte_id: uuid.UUID,
        periodo: str,
    ) -> list[Liquidacion]:
        """Return all active Liquidacion records for (cohorte, periodo)."""
        stmt = (
            select(Liquidacion)
            .where(
                Liquidacion.tenant_id == self._tenant_id,
                Liquidacion.deleted_at.is_(None),
                Liquidacion.cohorte_id == cohorte_id,
                Liquidacion.periodo == periodo,
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def listar_historial(
        self,
        cohorte_id: uuid.UUID | None = None,
        periodo: str | None = None,
    ) -> list[Liquidacion]:
        """Return closed (Cerrada) Liquidacion records, optionally filtered."""
        stmt = (
            select(Liquidacion)
            .where(
                Liquidacion.tenant_id == self._tenant_id,
                Liquidacion.deleted_at.is_(None),
                Liquidacion.estado == EstadoLiquidacion.Cerrada.value,
            )
        )
        if cohorte_id is not None:
            stmt = stmt.where(Liquidacion.cohorte_id == cohorte_id)
        if periodo is not None:
            stmt = stmt.where(Liquidacion.periodo == periodo)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def tiene_cerradas(self, cohorte_id: uuid.UUID, periodo: str) -> bool:
        """Return True if any Cerrada records exist for (cohorte, periodo)."""
        stmt = (
            select(Liquidacion.id)
            .where(
                Liquidacion.tenant_id == self._tenant_id,
                Liquidacion.deleted_at.is_(None),
                Liquidacion.cohorte_id == cohorte_id,
                Liquidacion.periodo == periodo,
                Liquidacion.estado == EstadoLiquidacion.Cerrada.value,
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    # ── Writes ────────────────────────────────────────────────────────────────

    async def crear(self, data: dict[str, Any]) -> Liquidacion:
        """Persist a new Liquidacion record with tenant scope."""
        return await self.create(data)

    async def cerrar_periodo(
        self,
        cohorte_id: uuid.UUID,
        periodo: str,
    ) -> int:
        """Bulk-set estado=Cerrada for all Abierta records of (cohorte, periodo).

        Returns the number of rows updated. The caller (service) must have
        already verified that no Cerrada records exist (immutability gate).
        """
        now = datetime.now(tz=timezone.utc)
        stmt = (
            update(Liquidacion)
            .where(
                Liquidacion.tenant_id == self._tenant_id,
                Liquidacion.deleted_at.is_(None),
                Liquidacion.cohorte_id == cohorte_id,
                Liquidacion.periodo == periodo,
                Liquidacion.estado == EstadoLiquidacion.Abierta.value,
            )
            .values(
                estado=EstadoLiquidacion.Cerrada.value,
                updated_at=now,
            )
        )
        result = await self._session.execute(stmt)
        return result.rowcount  # type: ignore[return-value]

    # ── Calculation helper (task 2.5) ─────────────────────────────────────────

    async def get_asignaciones_vigentes(
        self,
        cohorte_id: uuid.UUID,
        ini_mes: Any,  # date
        fin_mes: Any,  # date
    ) -> list[dict[str, Any]]:
        """Return docente assignment data for the calculation engine.

        Fetches Asignacion rows vigentes for the given cohorte and period,
        joined with Materia.categoria_clave and Usuario.facturador.

        Vigencia predicate: desde <= fin_mes AND (hasta IS NULL OR hasta >= ini_mes).

        Returns a list of dicts with keys:
          usuario_id, rol, comisiones, categoria_clave (nullable), facturador (bool)
        """
        stmt = (
            select(
                Asignacion.usuario_id,
                Asignacion.rol,
                Asignacion.comisiones,
                Materia.categoria_clave,
                Usuario.facturador,
            )
            .outerjoin(Materia, Asignacion.materia_id == Materia.id)
            .join(Usuario, Asignacion.usuario_id == Usuario.id)
            .where(
                Asignacion.tenant_id == self._tenant_id,
                Asignacion.deleted_at.is_(None),
                Asignacion.cohorte_id == cohorte_id,
                Asignacion.desde <= fin_mes,
                (Asignacion.hasta.is_(None)) | (Asignacion.hasta >= ini_mes),
                # Only roles that participate in liquidaciones
                Asignacion.rol.in_(["PROFESOR", "TUTOR", "NEXO", "COORDINADOR"]),
            )
        )
        result = await self._session.execute(stmt)
        rows = result.all()
        return [
            {
                "usuario_id": r.usuario_id,
                "rol": r.rol,
                "comisiones": r.comisiones or [],
                "categoria_clave": r.categoria_clave,
                "facturador": bool(r.facturador),
            }
            for r in rows
        ]
