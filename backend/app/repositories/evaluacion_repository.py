"""repositories/evaluacion_repository.py — EvaluacionRepository (C-14).

All queries are scoped to tenant_id. Never emits DELETE statements.

Business rules enforced here (as the only DB access layer):
  - create_reserva: verifies cupos_disponibles > 0 before inserting; decrements cupo.
  - cancel_reserva: restores one cupo if reserva was Activa.
  - get_metricas: computes convocadas/reservas/libres aggregates.
  - All reads: tenant_id filter + deleted_at IS NULL (soft delete).

Methods:
  create_evaluacion        — create a new coloquio call
  get_evaluacion           — fetch by id (tenant-scoped)
  list_evaluaciones        — list all for tenant (optional filters)
  patch_evaluacion         — update mutable fields
  soft_delete_evaluacion   — soft delete
  create_reserva           — book a slot (checks cupos)
  get_reserva              — fetch by id (tenant-scoped)
  list_reservas_by_evaluacion — all reservas for an evaluacion
  cancel_reserva           — cancel a booking, restore cupo
  create_resultado         — register exam outcome
  get_resultado            — fetch by id (tenant-scoped)
  list_resultados_by_evaluacion — all results for an evaluacion
  get_metricas             — F7.1 aggregate metrics
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluacion import (
    EstadoEvaluacion,
    EstadoReserva,
    Evaluacion,
    ReservaEvaluacion,
    ResultadoEvaluacion,
)


class EvaluacionRepository:
    """Tenant-scoped repository for Evaluacion, Reserva, and Resultado records."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    # ── Evaluacion writes ─────────────────────────────────────────────────────

    async def create_evaluacion(self, data: dict[str, Any]) -> Evaluacion:
        """Persist a new Evaluacion. tenant_id always sourced from repo instance."""
        payload = {**data, "tenant_id": self._tenant_id}
        evaluacion = Evaluacion(**payload)
        self._session.add(evaluacion)
        await self._session.flush()
        await self._session.refresh(evaluacion)
        return evaluacion

    async def patch_evaluacion(
        self, evaluacion_id: uuid.UUID, data: dict[str, Any]
    ) -> Evaluacion | None:
        """Update mutable fields on an existing Evaluacion.

        Returns updated instance, or None if not found in this tenant.
        Immutable fields (id, tenant_id) are silently ignored.
        Only processes non-None values (partial update).
        """
        evaluacion = await self.get_evaluacion(evaluacion_id)
        if evaluacion is None:
            return None

        data.pop("id", None)
        data.pop("tenant_id", None)

        for key, value in data.items():
            if value is not None:
                setattr(evaluacion, key, value)

        evaluacion.updated_at = datetime.now(tz=timezone.utc)
        self._session.add(evaluacion)
        await self._session.flush()
        await self._session.refresh(evaluacion)
        return evaluacion

    async def soft_delete_evaluacion(self, evaluacion_id: uuid.UUID) -> bool:
        """Soft-delete an Evaluacion. Returns True if found and deleted."""
        evaluacion = await self.get_evaluacion(evaluacion_id)
        if evaluacion is None:
            return False
        evaluacion.deleted_at = datetime.now(tz=timezone.utc)
        self._session.add(evaluacion)
        await self._session.flush()
        return True

    # ── Evaluacion reads ──────────────────────────────────────────────────────

    async def get_evaluacion(self, evaluacion_id: uuid.UUID) -> Evaluacion | None:
        """Return a single active Evaluacion by PK, scoped to tenant."""
        stmt = select(Evaluacion).where(
            Evaluacion.id == evaluacion_id,
            Evaluacion.tenant_id == self._tenant_id,
            Evaluacion.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_evaluaciones(
        self,
        materia_id: uuid.UUID | None = None,
        cohorte_id: uuid.UUID | None = None,
        estado: str | None = None,
    ) -> list[Evaluacion]:
        """Return all active Evaluaciones for this tenant, optionally filtered."""
        stmt = select(Evaluacion).where(
            Evaluacion.tenant_id == self._tenant_id,
            Evaluacion.deleted_at.is_(None),
        )
        if materia_id is not None:
            stmt = stmt.where(Evaluacion.materia_id == materia_id)
        if cohorte_id is not None:
            stmt = stmt.where(Evaluacion.cohorte_id == cohorte_id)
        if estado is not None:
            stmt = stmt.where(Evaluacion.estado == estado)
        stmt = stmt.order_by(Evaluacion.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ── Reserva writes ────────────────────────────────────────────────────────

    async def create_reserva(
        self,
        evaluacion_id: uuid.UUID,
        alumno_id: uuid.UUID,
        fecha_hora: datetime,
    ) -> ReservaEvaluacion:
        """Book a slot for an alumno on an Evaluacion.

        Raises:
          ValueError: if the evaluacion is not found, not Abierta, or has no cupos.

        On success, decrements cupos_disponibles by 1 (atomically within the session).
        """
        evaluacion = await self.get_evaluacion(evaluacion_id)
        if evaluacion is None:
            raise ValueError("evaluacion_not_found")
        if evaluacion.estado != EstadoEvaluacion.Abierta.value:
            raise ValueError("evaluacion_not_open")
        if evaluacion.cupos_disponibles <= 0:
            raise ValueError("sin_cupos_disponibles")

        # Check if alumno already has an active reserva for this evaluacion
        existing_stmt = select(ReservaEvaluacion).where(
            ReservaEvaluacion.evaluacion_id == evaluacion_id,
            ReservaEvaluacion.alumno_id == alumno_id,
            ReservaEvaluacion.tenant_id == self._tenant_id,
            ReservaEvaluacion.estado == EstadoReserva.Activa.value,
            ReservaEvaluacion.deleted_at.is_(None),
        )
        existing_result = await self._session.execute(existing_stmt)
        if existing_result.scalar_one_or_none() is not None:
            raise ValueError("reserva_ya_activa")

        # Decrement cupo
        evaluacion.cupos_disponibles -= 1
        evaluacion.updated_at = datetime.now(tz=timezone.utc)
        self._session.add(evaluacion)

        # Create reserva
        reserva = ReservaEvaluacion(
            tenant_id=self._tenant_id,
            evaluacion_id=evaluacion_id,
            alumno_id=alumno_id,
            fecha_hora=fecha_hora,
            estado=EstadoReserva.Activa.value,
        )
        self._session.add(reserva)
        await self._session.flush()
        await self._session.refresh(reserva)
        return reserva

    async def cancel_reserva(self, reserva_id: uuid.UUID) -> ReservaEvaluacion | None:
        """Cancel a booking and restore one cupo to its Evaluacion.

        Returns the updated reserva, or None if not found in this tenant.
        Is a no-op (returns reserva) if already Cancelada.
        """
        reserva = await self.get_reserva(reserva_id)
        if reserva is None:
            return None

        if reserva.estado == EstadoReserva.Cancelada.value:
            return reserva  # already cancelled — idempotent

        # Restore cupo
        evaluacion = await self.get_evaluacion(reserva.evaluacion_id)
        if evaluacion is not None:
            evaluacion.cupos_disponibles += 1
            evaluacion.updated_at = datetime.now(tz=timezone.utc)
            self._session.add(evaluacion)

        reserva.estado = EstadoReserva.Cancelada.value
        reserva.updated_at = datetime.now(tz=timezone.utc)
        self._session.add(reserva)
        await self._session.flush()
        await self._session.refresh(reserva)
        return reserva

    # ── Reserva reads ─────────────────────────────────────────────────────────

    async def get_reserva(self, reserva_id: uuid.UUID) -> ReservaEvaluacion | None:
        """Return a single active ReservaEvaluacion by PK, scoped to tenant."""
        stmt = select(ReservaEvaluacion).where(
            ReservaEvaluacion.id == reserva_id,
            ReservaEvaluacion.tenant_id == self._tenant_id,
            ReservaEvaluacion.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_reservas_by_evaluacion(
        self,
        evaluacion_id: uuid.UUID,
        estado: str | None = None,
    ) -> list[ReservaEvaluacion]:
        """Return all active ReservaEvaluacion for an evaluacion in this tenant."""
        stmt = select(ReservaEvaluacion).where(
            ReservaEvaluacion.evaluacion_id == evaluacion_id,
            ReservaEvaluacion.tenant_id == self._tenant_id,
            ReservaEvaluacion.deleted_at.is_(None),
        )
        if estado is not None:
            stmt = stmt.where(ReservaEvaluacion.estado == estado)
        stmt = stmt.order_by(ReservaEvaluacion.created_at.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ── Resultado writes ──────────────────────────────────────────────────────

    async def create_resultado(
        self,
        evaluacion_id: uuid.UUID,
        alumno_id: uuid.UUID,
        aprobado: bool,
        nota_final: str | None,
        observaciones: str | None,
    ) -> ResultadoEvaluacion:
        """Register an exam outcome for an alumno.

        Raises:
          ValueError: if the evaluacion is not found in tenant.
        """
        evaluacion = await self.get_evaluacion(evaluacion_id)
        if evaluacion is None:
            raise ValueError("evaluacion_not_found")

        resultado = ResultadoEvaluacion(
            tenant_id=self._tenant_id,
            evaluacion_id=evaluacion_id,
            alumno_id=alumno_id,
            aprobado=aprobado,
            nota_final=nota_final,
            observaciones=observaciones,
        )
        self._session.add(resultado)
        await self._session.flush()
        await self._session.refresh(resultado)
        return resultado

    # ── Resultado reads ───────────────────────────────────────────────────────

    async def get_resultado(self, resultado_id: uuid.UUID) -> ResultadoEvaluacion | None:
        """Return a single ResultadoEvaluacion by PK, scoped to tenant."""
        stmt = select(ResultadoEvaluacion).where(
            ResultadoEvaluacion.id == resultado_id,
            ResultadoEvaluacion.tenant_id == self._tenant_id,
            ResultadoEvaluacion.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_resultados_by_evaluacion(
        self, evaluacion_id: uuid.UUID
    ) -> list[ResultadoEvaluacion]:
        """Return all ResultadoEvaluacion records for an evaluacion in this tenant."""
        stmt = select(ResultadoEvaluacion).where(
            ResultadoEvaluacion.evaluacion_id == evaluacion_id,
            ResultadoEvaluacion.tenant_id == self._tenant_id,
            ResultadoEvaluacion.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ── Metrics (F7.1) ────────────────────────────────────────────────────────

    async def get_metricas(self) -> dict[str, int]:
        """Return F7.1 panel metrics for the current tenant.

        Returns dict with keys:
          total_convocatorias   — active Evaluacion records with estado=Abierta
          total_reservas_activas — active ReservaEvaluacion with estado=Activa
          total_resultados       — total ResultadoEvaluacion records
          total_cupos_libres     — sum of cupos_disponibles across Abierta evaluaciones
        """
        # Count open evaluaciones
        eval_stmt = select(func.count()).select_from(Evaluacion).where(
            Evaluacion.tenant_id == self._tenant_id,
            Evaluacion.deleted_at.is_(None),
            Evaluacion.estado == EstadoEvaluacion.Abierta.value,
        )
        eval_result = await self._session.execute(eval_stmt)
        total_convocatorias = eval_result.scalar_one() or 0

        # Count active reservations
        res_stmt = select(func.count()).select_from(ReservaEvaluacion).where(
            ReservaEvaluacion.tenant_id == self._tenant_id,
            ReservaEvaluacion.deleted_at.is_(None),
            ReservaEvaluacion.estado == EstadoReserva.Activa.value,
        )
        res_result = await self._session.execute(res_stmt)
        total_reservas_activas = res_result.scalar_one() or 0

        # Count results
        resultado_stmt = select(func.count()).select_from(ResultadoEvaluacion).where(
            ResultadoEvaluacion.tenant_id == self._tenant_id,
            ResultadoEvaluacion.deleted_at.is_(None),
        )
        resultado_result = await self._session.execute(resultado_stmt)
        total_resultados = resultado_result.scalar_one() or 0

        # Sum of free slots across open evaluaciones
        cupos_stmt = select(func.coalesce(func.sum(Evaluacion.cupos_disponibles), 0)).where(
            Evaluacion.tenant_id == self._tenant_id,
            Evaluacion.deleted_at.is_(None),
            Evaluacion.estado == EstadoEvaluacion.Abierta.value,
        )
        cupos_result = await self._session.execute(cupos_stmt)
        total_cupos_libres = cupos_result.scalar_one() or 0

        return {
            "total_convocatorias": total_convocatorias,
            "total_reservas_activas": total_reservas_activas,
            "total_resultados": total_resultados,
            "total_cupos_libres": total_cupos_libres,
        }
