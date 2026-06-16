"""services/equipos.py — EquiposService (C-08: equipos-docentes).

Business logic for Asignacion management: CRUD, bulk assignment, team cloning,
bulk vigencia update, and CSV export. Delegates all DB access to
AsignacionRepository. Never touches DB directly.

Design decisions (C-08 design.md):
  D2 — mis_asignaciones uses get_vigentes_by_usuario; identity from JWT only.
  D4 — clone_team iterates + bulk_creates (not raw SQL) for audit and validation.
  D5 — exportar_csv builds CSV in-memory via io.StringIO; no tmp files.
  D7 — bulk operations return (creadas, omitidos) for transparency.
"""

import csv
import io
import uuid
from datetime import date
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit_action
from app.core.exceptions import NotFoundError
from app.models.asignacion import Asignacion
from app.repositories.asignacion import AsignacionRepository
from app.schemas.asignacion import (
    AsignacionCreate,
    AsignacionFilter,
    AsignacionMasivaCreate,
    AsignacionMasivaOut,
    AsignacionOut,
    AsignacionUpdate,
    ClonarEquipoRequest,
    VigenciaMasivaOut,
    VigenciaMasivaRequest,
)

# Audit action codes
_ASIGNACION_CREAR = "ASIGNACION_CREAR"
_ASIGNACION_MODIFICAR = "ASIGNACION_MODIFICAR"
_ASIGNACION_ELIMINAR = "ASIGNACION_ELIMINAR"

# CSV column headers for exportación
_CSV_HEADERS = [
    "id",
    "usuario_id",
    "rol",
    "materia_id",
    "carrera_id",
    "cohorte_id",
    "comisiones",
    "responsable_id",
    "desde",
    "hasta",
    "created_at",
    "updated_at",
]


class EquiposService:
    """Service layer for Equipos Docentes operations.

    Instantiated per-request with the active DB session and tenant context
    (sourced from the verified JWT via the router dependency).
    """

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._repo = AsignacionRepository(session, tenant_id)

    # ── F4.2 — Vista propia del docente ───────────────────────────────────────

    async def mis_asignaciones(self, usuario_id: uuid.UUID) -> list[Asignacion]:
        """Return active assignments for the authenticated user.

        Identity comes exclusively from the JWT (usuario_id passed by router).
        """
        return await self._repo.get_vigentes_by_usuario(usuario_id)

    # ── F4.3 — Listado global con filtros ────────────────────────────────────

    async def list_asignaciones(self, filters: AsignacionFilter) -> list[Asignacion]:
        """Return assignments for the current tenant with optional filters."""
        return await self._repo.list_with_filters(filters)

    # ── CRUD individual ───────────────────────────────────────────────────────

    async def create_asignacion(
        self,
        data: AsignacionCreate,
        actor_id: uuid.UUID,
    ) -> Asignacion:
        """Create a single Asignacion and record audit log."""
        created = await self._repo.create(
            {
                "usuario_id": data.usuario_id,
                "rol": data.rol,
                "materia_id": data.materia_id,
                "carrera_id": data.carrera_id,
                "cohorte_id": data.cohorte_id,
                "comisiones": data.comisiones,
                "responsable_id": data.responsable_id,
                "desde": data.desde,
                "hasta": data.hasta,
            }
        )
        await audit_action(
            self._session,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            accion=_ASIGNACION_CREAR,
            detalle={
                "asignacion_id": str(created.id),
                "usuario_id": str(data.usuario_id),
                "rol": data.rol,
            },
            filas_afectadas=1,
        )
        return created

    async def update_asignacion(
        self,
        asignacion_id: uuid.UUID,
        data: AsignacionUpdate,
        actor_id: uuid.UUID,
    ) -> Asignacion:
        """Update an existing Asignacion.

        Raises:
            NotFoundError: if not found or belongs to another tenant.
        """
        update_dict: dict[str, Any] = {}
        if data.rol is not None:
            update_dict["rol"] = data.rol
        if data.materia_id is not None:
            update_dict["materia_id"] = data.materia_id
        if data.carrera_id is not None:
            update_dict["carrera_id"] = data.carrera_id
        if data.cohorte_id is not None:
            update_dict["cohorte_id"] = data.cohorte_id
        if data.comisiones is not None:
            update_dict["comisiones"] = data.comisiones
        if data.responsable_id is not None:
            update_dict["responsable_id"] = data.responsable_id
        if data.desde is not None:
            update_dict["desde"] = data.desde
        # hasta can be explicitly set to None (open-ended) — check presence
        if "hasta" in data.model_fields_set:
            update_dict["hasta"] = data.hasta

        updated = await self._repo.update(asignacion_id, update_dict)
        if updated is None:
            raise NotFoundError(f"Asignacion {asignacion_id} no encontrada")

        await audit_action(
            self._session,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            accion=_ASIGNACION_MODIFICAR,
            detalle={"asignacion_id": str(asignacion_id), **{k: str(v) for k, v in update_dict.items()}},
            filas_afectadas=1,
        )
        return updated

    async def delete_asignacion(
        self,
        asignacion_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> None:
        """Soft-delete an Asignacion.

        Raises:
            NotFoundError: if not found or belongs to another tenant.
        """
        deleted = await self._repo.soft_delete(asignacion_id)
        if not deleted:
            raise NotFoundError(f"Asignacion {asignacion_id} no encontrada")

        await audit_action(
            self._session,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            accion=_ASIGNACION_ELIMINAR,
            detalle={"asignacion_id": str(asignacion_id)},
            filas_afectadas=1,
        )

    # ── F4.4 — Asignación masiva ──────────────────────────────────────────────

    async def asignacion_masiva(
        self,
        data: AsignacionMasivaCreate,
        actor_id: uuid.UUID,
    ) -> AsignacionMasivaOut:
        """Assign multiple users to a single context+rol in bulk.

        Idempotent: existing duplicates are skipped, not errored.
        """
        items = [
            {
                "usuario_id": uid,
                "rol": data.rol,
                "materia_id": data.materia_id,
                "carrera_id": data.carrera_id,
                "cohorte_id": data.cohorte_id,
                "comisiones": data.comisiones,
                "responsable_id": data.responsable_id,
                "desde": data.desde,
                "hasta": data.hasta,
            }
            for uid in data.usuario_ids
        ]
        creadas, omitidos = await self._repo.bulk_create(items)

        if creadas:
            await audit_action(
                self._session,
                actor_id=actor_id,
                tenant_id=self._tenant_id,
                accion=_ASIGNACION_CREAR,
                detalle={
                    "operacion": "asignacion_masiva",
                    "rol": data.rol,
                    "creadas": len(creadas),
                    "omitidos": len(omitidos),
                },
                filas_afectadas=len(creadas),
            )

        return AsignacionMasivaOut(
            creadas=[AsignacionOut.model_validate(a) for a in creadas],
            omitidos=omitidos,
        )

    # ── F4.5 — Clonar equipo ──────────────────────────────────────────────────

    async def clonar_equipo(
        self,
        data: ClonarEquipoRequest,
        actor_id: uuid.UUID,
    ) -> AsignacionMasivaOut:
        """Clone all vigente assignments from origin to destination cohorte."""
        creadas, omitidos = await self._repo.clone_team(
            origen_cohorte_id=data.origen_cohorte_id,
            destino_cohorte_id=data.destino_cohorte_id,
            materia_id=data.materia_id,
            carrera_id=data.carrera_id,
            desde=data.desde,
            hasta=data.hasta,
        )

        if creadas:
            await audit_action(
                self._session,
                actor_id=actor_id,
                tenant_id=self._tenant_id,
                accion=_ASIGNACION_CREAR,
                detalle={
                    "operacion": "clonar_equipo",
                    "origen_cohorte_id": str(data.origen_cohorte_id),
                    "destino_cohorte_id": str(data.destino_cohorte_id),
                    "creadas": len(creadas),
                    "omitidos": len(omitidos),
                },
                filas_afectadas=len(creadas),
            )

        return AsignacionMasivaOut(
            creadas=[AsignacionOut.model_validate(a) for a in creadas],
            omitidos=omitidos,
        )

    # ── F4.6 — Vigencia masiva ────────────────────────────────────────────────

    async def vigencia_masiva(
        self,
        data: VigenciaMasivaRequest,
        actor_id: uuid.UUID,
    ) -> VigenciaMasivaOut:
        """Update desde/hasta for all assignments of a team atomically."""
        count = await self._repo.bulk_update_vigencia(
            materia_id=data.materia_id,
            carrera_id=data.carrera_id,
            cohorte_id=data.cohorte_id,
            desde=data.desde,
            hasta=data.hasta,
        )

        await audit_action(
            self._session,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            accion=_ASIGNACION_MODIFICAR,
            detalle={
                "operacion": "vigencia_masiva",
                "materia_id": str(data.materia_id),
                "carrera_id": str(data.carrera_id),
                "cohorte_id": str(data.cohorte_id),
                "desde": str(data.desde),
                "hasta": str(data.hasta) if data.hasta else None,
            },
            filas_afectadas=count,
        )

        return VigenciaMasivaOut(filas_afectadas=count)

    # ── F4.7 — Exportar CSV ───────────────────────────────────────────────────

    async def exportar_csv(self, filters: AsignacionFilter) -> str:
        """Return CSV string with team assignments matching the given filters.

        Headers are always present; data rows follow. Built in-memory (no tmp
        files). Returns empty CSV (headers only) if no records match.
        """
        asignaciones = await self._repo.list_with_filters(filters)

        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=_CSV_HEADERS, lineterminator="\n")
        writer.writeheader()

        for a in asignaciones:
            writer.writerow(
                {
                    "id": str(a.id),
                    "usuario_id": str(a.usuario_id),
                    "rol": a.rol,
                    "materia_id": str(a.materia_id) if a.materia_id else "",
                    "carrera_id": str(a.carrera_id) if a.carrera_id else "",
                    "cohorte_id": str(a.cohorte_id) if a.cohorte_id else "",
                    "comisiones": "|".join(a.comisiones) if a.comisiones else "",
                    "responsable_id": str(a.responsable_id) if a.responsable_id else "",
                    "desde": str(a.desde),
                    "hasta": str(a.hasta) if a.hasta else "",
                    "created_at": a.created_at.isoformat(),
                    "updated_at": a.updated_at.isoformat(),
                }
            )

        return buf.getvalue()
