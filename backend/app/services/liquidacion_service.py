"""services/liquidacion_service.py — LiquidacionService (C-18).

Orchestrates salary calculation, closing, historical queries and period view.
Never accesses the DB directly — all persistence via repositories.

Methods:
  calcular(cohorte_id, periodo)       — compute and persist Liquidacion records
  cerrar(cohorte_id, periodo, ...)    — close a period (audit + immutability check)
  vista_periodo(cohorte_id, periodo)  — segmented view with KPIs
  historial(...)                      — closed records filtered by cohorte/period

Design decisions (C-18 design.md):
  D1: facturador flag from Usuario → excluido_por_factura in Liquidacion.
  D3: pure calculation in _calcular_montos / liquidacion_calc; I/O in repos.
  D4: period normalization via parse_periodo (liquidacion_utils).
  D5: cerrar raises ConflictError if any Cerrada record already exists.
  D6: KPI aggregates computed in memory, not persisted.
"""

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit_action
from app.core.exceptions import ConflictError
from app.models.liquidacion import EstadoLiquidacion
from app.repositories.liquidacion import LiquidacionRepository
from app.repositories.salario_base import SalarioBaseRepository
from app.repositories.salario_plus import SalarioPlusRepository
from app.services.liquidacion_calc import _calcular_montos
from app.services.liquidacion_utils import parse_periodo

_ACCION_CERRAR = "LIQUIDACION_CERRAR"


class LiquidacionService:
    """Orchestrate liquidacion calculation, closing and reporting."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._liq_repo = LiquidacionRepository(session, tenant_id)
        self._base_repo = SalarioBaseRepository(session, tenant_id)
        self._plus_repo = SalarioPlusRepository(session, tenant_id)

    # ── calcular ───────────────────────────────────────────────────────────────

    async def calcular(
        self,
        cohorte_id: uuid.UUID,
        periodo: str,
    ) -> list[Any]:
        """Compute and persist Liquidacion records for (cohorte, periodo).

        Steps:
        1. Normalise period to (ini_mes, fin_mes).
        2. Reject if any Cerrada record already exists for this period (D5).
        3. Fetch vigente asignaciones (grouped by docente via repo helper).
        4. For each docente: resolve Base + Plus vigentes, compute montos.
        5. Persist Liquidacion records (replace existing Abierta via soft-delete).

        Returns the list of Liquidacion ORM instances created.
        """
        ini_mes, fin_mes = parse_periodo(periodo)

        # Immutability gate: refuse recalculation if period already closed
        if await self._liq_repo.tiene_cerradas(cohorte_id, periodo):
            raise ConflictError(
                f"Period {periodo} already has closed records; recalculation rejected.",
            )

        # Soft-delete any existing Abierta records for this period (idempotent recalc)
        existing = await self._liq_repo.listar_por_periodo(cohorte_id, periodo)
        for liq in existing:
            await self._liq_repo.soft_delete(liq.id)

        # Fetch asignaciones vigentes
        asignaciones = await self._liq_repo.get_asignaciones_vigentes(
            cohorte_id, ini_mes, fin_mes
        )

        # Group by (usuario_id, rol) — aggregate comisiones and claves
        from collections import defaultdict
        docentes: dict[tuple[uuid.UUID, str], dict] = defaultdict(lambda: {
            "comisiones": [],
            "claves_count": defaultdict(int),  # clave → count
            "facturador": False,
        })

        for asig in asignaciones:
            key = (asig["usuario_id"], asig["rol"])
            docentes[key]["comisiones"].extend(asig["comisiones"])
            docentes[key]["facturador"] = asig["facturador"]
            clave = asig["categoria_clave"]
            # Count commissions per clave (per asignacion, not per comision code)
            # Each asignacion contributes len(comisiones) commissions of its clave
            docentes[key]["claves_count"][clave] += len(asig["comisiones"])

        # Resolve salary grids (cache per rol and (grupo, rol))
        base_cache: dict[str, Decimal] = {}
        plus_cache: dict[tuple[str, str], Decimal] = {}

        # Pre-collect distinct roles and claves to resolve vigentes
        all_roles = {rol for (_, rol) in docentes.keys()}
        all_claves = set()
        for data in docentes.values():
            for clave in data["claves_count"]:
                if clave is not None:
                    all_claves.add(clave)

        for rol in all_roles:
            base = await self._base_repo.get_vigente(rol, ini_mes, fin_mes)
            base_cache[rol] = base.monto if base else Decimal("0")

        for (uid, rol), data in docentes.items():
            for clave in data["claves_count"]:
                if clave is None:
                    continue
                if (clave, rol) not in plus_cache:
                    plus = await self._plus_repo.get_vigente(clave, rol, ini_mes, fin_mes)
                    plus_cache[(clave, rol)] = plus.monto if plus else Decimal("0")

        # Build and persist Liquidacion records
        created = []
        for (usuario_id, rol), data in docentes.items():
            # Build plus_por_clave dict for this (rol)
            plus_por_clave: dict[str, Decimal] = {
                clave: plus_cache.get((clave, rol), Decimal("0"))
                for clave in data["claves_count"]
                if clave is not None
            }

            monto_base, monto_plus, total = _calcular_montos(
                asignaciones_por_clave=dict(data["claves_count"]),
                base_rol=base_cache.get(rol, Decimal("0")),
                plus_por_clave=plus_por_clave,
            )

            liq = await self._liq_repo.crear({
                "cohorte_id": cohorte_id,
                "periodo": periodo,
                "usuario_id": usuario_id,
                "rol": rol,
                "comisiones": data["comisiones"],
                "monto_base": monto_base,
                "monto_plus": monto_plus,
                "total": total,
                "es_nexo": rol == "NEXO",
                "excluido_por_factura": data["facturador"],
                "estado": EstadoLiquidacion.Abierta.value,
            })
            created.append(liq)

        await self._session.commit()
        return created

    # ── cerrar ────────────────────────────────────────────────────────────────

    async def cerrar(
        self,
        cohorte_id: uuid.UUID,
        periodo: str,
        actor_id: uuid.UUID,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> int:
        """Close all Abierta Liquidacion records for (cohorte, periodo).

        Raises ConflictError (→ 409) if the period is already closed (D5).
        Emits audit_action("LIQUIDACION_CERRAR").

        Returns the number of records closed.
        """
        if await self._liq_repo.tiene_cerradas(cohorte_id, periodo):
            raise ConflictError(
                f"Period {periodo} is already closed; no further mutations allowed.",
            )

        count = await self._liq_repo.cerrar_periodo(cohorte_id, periodo)

        await audit_action(
            session=self._session,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            accion=_ACCION_CERRAR,
            detalle={
                "cohorte_id": str(cohorte_id),
                "periodo": periodo,
                "registros_cerrados": count,
            },
            ip=ip,
            user_agent=user_agent,
        )

        await self._session.commit()
        return count

    # ── vista_periodo ─────────────────────────────────────────────────────────

    async def vista_periodo(
        self,
        cohorte_id: uuid.UUID,
        periodo: str,
    ) -> dict[str, Any]:
        """Return segmented view with KPIs for (cohorte, periodo).

        Segments:
          - general: Abierta or Cerrada, non-facturante, non-nexo
          - nexo:    es_nexo=True
          - facturantes: excluido_por_factura=True

        KPIs:
          - total_sin_factura: Σ total where excluido_por_factura=False
          - total_con_factura: Σ total where excluido_por_factura=True
        """
        records = await self._liq_repo.listar_por_periodo(cohorte_id, periodo)

        general = []
        nexo = []
        facturantes = []
        total_sin_factura = Decimal("0")
        total_con_factura = Decimal("0")

        for r in records:
            row = {
                "id": r.id,
                "usuario_id": r.usuario_id,
                "rol": r.rol,
                "comisiones": r.comisiones,
                "monto_base": r.monto_base,
                "monto_plus": r.monto_plus,
                "total": r.total,
                "es_nexo": r.es_nexo,
                "excluido_por_factura": r.excluido_por_factura,
                "estado": r.estado,
            }
            if r.excluido_por_factura:
                facturantes.append(row)
                total_con_factura += r.total
            elif r.es_nexo:
                nexo.append(row)
                total_sin_factura += r.total
            else:
                general.append(row)
                total_sin_factura += r.total

        return {
            "general": general,
            "nexo": nexo,
            "facturantes": facturantes,
            "total_sin_factura": total_sin_factura,
            "total_con_factura": total_con_factura,
            "periodo": periodo,
            "cohorte_id": cohorte_id,
        }

    # ── historial ─────────────────────────────────────────────────────────────

    async def historial(
        self,
        cohorte_id: uuid.UUID | None = None,
        periodo: str | None = None,
    ) -> list[Any]:
        """Return closed (Cerrada) Liquidacion records, optionally filtered."""
        return await self._liq_repo.listar_historial(
            cohorte_id=cohorte_id,
            periodo=periodo,
        )
