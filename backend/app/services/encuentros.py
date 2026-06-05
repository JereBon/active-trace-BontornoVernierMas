"""services/encuentros.py — EncuentrosService (C-13).

Business logic for encuentros: slot creation (recurrent + one-off), instance
editing, HTML block generation for the LMS, and admin listing.

Design decisions (C-13 design.md):
  D2 — Recurrence: generates cant_semanas instances in one transaction.
  D4 — HTML built in-memory via str concatenation; no file I/O.
  D8 — No business logic in routers; all logic here.
"""

import uuid
from datetime import date, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit_action
from app.core.exceptions import NotFoundError
from app.models.encuentro import InstanciaEncuentro, SlotEncuentro
from app.repositories.encuentro import (
    InstanciaEncuentroRepository,
    SlotEncuentroRepository,
)
from app.schemas.encuentro import (
    InstanciaOut,
    InstanciaUpdate,
    SlotCreate,
    SlotOut,
    SlotWithInstancesOut,
)

# Audit action codes
_ENCUENTRO_SLOT_CREAR = "ENCUENTRO_SLOT_CREAR"
_ENCUENTRO_INSTANCIA_EDITAR = "ENCUENTRO_INSTANCIA_EDITAR"


class EncuentrosService:
    """Service layer for Encuentros operations.

    Instantiated per-request with the active DB session and tenant context
    (sourced from the verified JWT via the router dependency).
    """

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._slot_repo = SlotEncuentroRepository(session, tenant_id)
        self._inst_repo = InstanciaEncuentroRepository(session, tenant_id)

    # ── F6.1 / F6.2 — Create slot + instances ────────────────────────────────

    async def crear_slot_recurrente(
        self,
        data: SlotCreate,
        actor_id: uuid.UUID,
    ) -> SlotWithInstancesOut:
        """Create a SlotEncuentro and generate its InstanciaEncuentro rows.

        Rules (D2 / RN-13):
          - cant_semanas > 0: generate that many weekly instances starting at fecha_inicio.
          - cant_semanas == 0: use fecha_unica; generate exactly one instance.
        Both paths run in a single transaction (flush-based).

        Returns:
            SlotWithInstancesOut with the created slot and all instances.

        Raises:
            ValueError: if cant_semanas == 0 and fecha_unica is None.
        """
        if data.cant_semanas == 0 and data.fecha_unica is None:
            raise ValueError(
                "fecha_unica is required when cant_semanas == 0 (one-off encounter)"
            )

        # Persist slot
        slot = await self._slot_repo.create(
            {
                "asignacion_id": data.asignacion_id,
                "materia_id": data.materia_id,
                "titulo": data.titulo,
                "hora": data.hora,
                "dia_semana": data.dia_semana,
                "fecha_inicio": data.fecha_inicio,
                "cant_semanas": data.cant_semanas,
                "fecha_unica": data.fecha_unica,
                "meet_url": data.meet_url,
                "vig_desde": data.vig_desde,
                "vig_hasta": data.vig_hasta,
            }
        )

        # Generate instances
        instancias: list[InstanciaEncuentro] = []
        if data.cant_semanas > 0:
            for n in range(data.cant_semanas):
                inst_date = data.fecha_inicio + timedelta(weeks=n)
                inst = await self._inst_repo.create(
                    {
                        "slot_id": slot.id,
                        "materia_id": data.materia_id,
                        "fecha": inst_date,
                        "hora": data.hora,
                        "titulo": data.titulo,
                        "estado": "Programado",
                        "meet_url": data.meet_url,
                    }
                )
                instancias.append(inst)
        else:
            # One-off
            inst = await self._inst_repo.create(
                {
                    "slot_id": slot.id,
                    "materia_id": data.materia_id,
                    "fecha": data.fecha_unica,
                    "hora": data.hora,
                    "titulo": data.titulo,
                    "estado": "Programado",
                    "meet_url": data.meet_url,
                }
            )
            instancias.append(inst)

        await audit_action(
            self._session,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            accion=_ENCUENTRO_SLOT_CREAR,
            detalle={
                "slot_id": str(slot.id),
                "cant_semanas": data.cant_semanas,
                "instancias_generadas": len(instancias),
            },
            filas_afectadas=1 + len(instancias),
        )

        return SlotWithInstancesOut(
            slot=SlotOut.model_validate(slot),
            instancias=[InstanciaOut.model_validate(i) for i in instancias],
        )

    # ── F6.3 — Edit instance ─────────────────────────────────────────────────

    async def editar_instancia(
        self,
        instancia_id: uuid.UUID,
        data: InstanciaUpdate,
        actor_id: uuid.UUID,
    ) -> InstanciaEncuentro:
        """Update an InstanciaEncuentro's mutable fields.

        Raises:
            NotFoundError: if not found or belongs to another tenant.
        """
        update_dict: dict[str, Any] = {}
        if data.estado is not None:
            update_dict["estado"] = data.estado
        if data.meet_url is not None:
            update_dict["meet_url"] = data.meet_url
        if data.video_url is not None:
            update_dict["video_url"] = data.video_url
        if data.comentario is not None:
            update_dict["comentario"] = data.comentario

        updated = await self._inst_repo.update(instancia_id, update_dict)
        if updated is None:
            raise NotFoundError(f"InstanciaEncuentro {instancia_id} no encontrada")

        await audit_action(
            self._session,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            accion=_ENCUENTRO_INSTANCIA_EDITAR,
            detalle={
                "instancia_id": str(instancia_id),
                **{k: str(v) for k, v in update_dict.items()},
            },
            filas_afectadas=1,
        )
        return updated

    # ── F6.4 — Generate HTML block ───────────────────────────────────────────

    async def generar_html(
        self,
        materia_id: uuid.UUID,
        asignacion_id: uuid.UUID | None = None,
    ) -> str:
        """Generate an HTML block of scheduled encounters for the LMS.

        Returns an HTML string with a table sorted by fecha ASC.
        Always returns a complete HTML table (empty tbody if no encounters).
        """
        instancias = await self._inst_repo.list_by_materia_slot(
            materia_id=materia_id,
            asignacion_id=asignacion_id,
        )

        rows = ""
        for inst in instancias:
            meet_link = (
                f'<a href="{inst.meet_url}" target="_blank">Ingresar</a>'
                if inst.meet_url
                else ""
            )
            video_link = (
                f'<a href="{inst.video_url}" target="_blank">Ver grabación</a>'
                if inst.video_url
                else ""
            )
            rows += (
                f"<tr>"
                f"<td>{inst.fecha}</td>"
                f"<td>{inst.hora}</td>"
                f"<td>{inst.titulo}</td>"
                f"<td>{meet_link}</td>"
                f"<td>{video_link}</td>"
                f"<td>{inst.estado}</td>"
                f"</tr>"
            )

        html = (
            "<table>"
            "<thead><tr>"
            "<th>Fecha</th><th>Hora</th><th>Título</th>"
            "<th>Sala</th><th>Grabación</th><th>Estado</th>"
            "</tr></thead>"
            f"<tbody>{rows}</tbody>"
            "</table>"
        )
        return html

    # ── F6.5 — Admin listing ──────────────────────────────────────────────────

    async def list_admin(
        self,
        materia_id: uuid.UUID | None = None,
    ) -> list[InstanciaEncuentro]:
        """Return all instances for the tenant (coordinador/admin overview).

        Args:
            materia_id: optional filter.
        """
        return await self._inst_repo.list_for_admin(materia_id=materia_id)
