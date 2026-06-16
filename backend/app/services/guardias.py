"""services/guardias.py — GuardiasService (C-13).

Business logic for Guardia management: creation, listing, CSV export.
Delegates all DB access to GuardiaRepository.

Design decisions (C-13 design.md):
  D5 — CSV export uses io.StringIO + csv.DictWriter; no tmp files.
  D8 — No business logic in routers; all logic here.
"""

import csv
import io
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit_action
from app.models.guardia import Guardia
from app.repositories.guardia import GuardiaRepository
from app.schemas.guardia import GuardiaCreate, GuardiaFilter, GuardiaOut

# Audit action codes
_GUARDIA_CREAR = "GUARDIA_CREAR"

# CSV column headers
_CSV_HEADERS = [
    "id",
    "tenant_id",
    "asignacion_id",
    "materia_id",
    "carrera_id",
    "cohorte_id",
    "dia",
    "horario",
    "estado",
    "comentarios",
    "creada_at",
    "created_at",
]


class GuardiasService:
    """Service layer for Guardia operations.

    Instantiated per-request with the active DB session and tenant context
    (sourced from the verified JWT via the router dependency).
    """

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._repo = GuardiaRepository(session, tenant_id)

    # ── F6.6 — Register guardia ───────────────────────────────────────────────

    async def crear_guardia(
        self,
        data: GuardiaCreate,
        actor_id: uuid.UUID,
    ) -> Guardia:
        """Create a new Guardia record and record audit log."""
        guardia = await self._repo.create(
            {
                "asignacion_id": data.asignacion_id,
                "materia_id": data.materia_id,
                "carrera_id": data.carrera_id,
                "cohorte_id": data.cohorte_id,
                "dia": data.dia,
                "horario": data.horario,
                "estado": data.estado,
                "comentarios": data.comentarios,
            }
        )
        await audit_action(
            self._session,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            accion=_GUARDIA_CREAR,
            detalle={
                "guardia_id": str(guardia.id),
                "asignacion_id": str(data.asignacion_id),
                "dia": data.dia,
            },
            filas_afectadas=1,
        )
        return guardia

    # ── F6.6 — List guardias ──────────────────────────────────────────────────

    async def list_guardias(self, filters: GuardiaFilter) -> list[Guardia]:
        """Return guardias for the current tenant with optional filters."""
        return await self._repo.list_with_filters(filters)

    # ── F6.6 — Export CSV ─────────────────────────────────────────────────────

    async def exportar_csv(self, filters: GuardiaFilter) -> str:
        """Return CSV string with guardias matching the given filters.

        Headers are always present; data rows follow.
        Built in-memory (no tmp files). Returns empty CSV (headers only) if no records match.
        """
        guardias = await self._repo.list_with_filters(filters)

        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=_CSV_HEADERS, lineterminator="\n")
        writer.writeheader()

        for g in guardias:
            writer.writerow(
                {
                    "id": str(g.id),
                    "tenant_id": str(g.tenant_id),
                    "asignacion_id": str(g.asignacion_id),
                    "materia_id": str(g.materia_id),
                    "carrera_id": str(g.carrera_id),
                    "cohorte_id": str(g.cohorte_id),
                    "dia": g.dia,
                    "horario": g.horario,
                    "estado": g.estado,
                    "comentarios": g.comentarios or "",
                    "creada_at": g.creada_at.isoformat(),
                    "created_at": g.created_at.isoformat(),
                }
            )

        return buf.getvalue()
