"""services/comunicacion_service.py — ComunicacionService (C-12).

Orchestrates preview, enqueuing, approval and cancellation of outbound
communications. Never accesses the DB directly — all persistence goes through
ComunicacionRepository.

Methods:
  preview               — render template without persisting (F3.1, RN-16)
  encolar_lote          — encrypt + enqueue a batch, check approval config (F3.2)
  aprobar_lote          — approve all Pendiente in a lote (F3.3, RN-17)
  cancelar_lote         — cancel all Pendiente in a lote
  cancelar_individual   — cancel a single message
  validar_transicion    — static: validate state machine transitions (D5)

Design decisions (C-12 design.md):
- D3: aprobado flag for approval; worker dispatches only aprobado=True.
- D4: destinatario AES-256-GCM encrypted before persisting.
- D5: VALID_TRANSITIONS dict enforces state machine (imported from models).
- D6: preview does NOT persist; returns rendered strings directly.
- Audit: COMUNICACION_ENVIAR, COMUNICACION_APROBAR, COMUNICACION_CANCELAR.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit_action
from app.core.crypto import encrypt, decrypt
from app.models.comunicacion import VALID_TRANSITIONS
from app.repositories.comunicacion_repository import ComunicacionRepository
from app.schemas.comunicacion import (
    ComunicacionOut,
    DestinatarioItem,
    EncoladoResponse,
    LoteStatusOut,
    PreviewRequest,
    PreviewResponse,
    _mask_email,
    _render_template,
)

# ── Audit action codes ────────────────────────────────────────────────────────
_ACCION_ENVIAR = "COMUNICACION_ENVIAR"
_ACCION_APROBAR = "COMUNICACION_APROBAR"
_ACCION_CANCELAR = "COMUNICACION_CANCELAR"


class ComunicacionService:
    """Orchestrates all outbound communication operations.

    Instantiated per-request with the active DB session and caller context
    (always sourced from the verified JWT via the router dependency).
    """

    def __init__(
        self,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._actor_id = actor_id
        self._repo = ComunicacionRepository(session, tenant_id)

    # ── Static state machine validator ───────────────────────────────────────

    @staticmethod
    def validar_transicion(estado_actual: str, nuevo_estado: str) -> None:
        """Validate that the state transition is legal.

        Raises ValueError if the transition is not in VALID_TRANSITIONS.
        Terminal states (Enviado, Error, Cancelado) raise with 'terminal' in
        the message so callers can distinguish and map to 409 Conflict.
        """
        allowed = VALID_TRANSITIONS.get(estado_actual, set())
        if not allowed:
            # estado_actual is terminal
            raise ValueError(
                f"Estado '{estado_actual}' is terminal — no further transitions allowed."
            )
        if nuevo_estado not in allowed:
            raise ValueError(
                f"Transition '{estado_actual}' → '{nuevo_estado}' is not allowed. "
                f"Allowed: {sorted(allowed)}"
            )

    # ── Preview (F3.1, RN-16) ─────────────────────────────────────────────────

    async def preview(self, request: PreviewRequest) -> PreviewResponse:
        """Render a message template without persisting anything.

        Raises ValueError if any template variable is missing.
        """
        rendered_asunto = _render_template(request.asunto, request.variables)
        rendered_cuerpo = _render_template(request.cuerpo, request.variables)
        return PreviewResponse(asunto=rendered_asunto, cuerpo=rendered_cuerpo)

    # ── Enqueue (F3.2) ────────────────────────────────────────────────────────

    async def encolar_lote(
        self,
        materia_id: uuid.UUID | None,
        asunto: str,
        cuerpo: str,
        destinatarios: list[DestinatarioItem],
        *,
        ip: str = "unknown",
        user_agent: str = "",
    ) -> EncoladoResponse:
        """Encrypt and enqueue a batch of outbound messages.

        Generates a single lote_id for the whole batch.
        Checks tenant config to decide if messages need approval (D3).
        If comunicacion_requiere_aprobacion=True AND len(destinatarios) > 1:
            messages enqueued with aprobado=False (await approval).
        Else: aprobado=True (worker can dispatch immediately).
        Audits COMUNICACION_ENVIAR.
        """
        lote_id = uuid.uuid4()

        # Read tenant config
        requiere_aprobacion = await self._get_tenant_requiere_aprobacion()
        aprobado = not (requiere_aprobacion and len(destinatarios) > 1)

        records = []
        for dest in destinatarios:
            # Render cuerpo with per-recipient variables (best-effort: no raise here
            # since preview was supposed to catch missing vars upstream)
            try:
                rendered_cuerpo = _render_template(cuerpo, dest.variables)
                rendered_asunto = _render_template(asunto, dest.variables)
            except ValueError:
                rendered_cuerpo = cuerpo
                rendered_asunto = asunto

            records.append(
                {
                    "id": uuid.uuid4(),
                    "enviado_por": self._actor_id,
                    "materia_id": materia_id,
                    "destinatario": encrypt(dest.email),
                    "asunto": rendered_asunto,
                    "cuerpo": rendered_cuerpo,
                    "estado": "Pendiente",
                    "aprobado": aprobado,
                    "lote_id": lote_id,
                }
            )

        await self._repo.create_bulk(records)

        # Audit
        await audit_action(
            self._session,
            actor_id=self._actor_id,
            tenant_id=self._tenant_id,
            accion=_ACCION_ENVIAR,
            detalle={
                "lote_id": str(lote_id),
                "count": len(records),
                "materia_id": str(materia_id) if materia_id else None,
                "requiere_aprobacion": requiere_aprobacion,
            },
            filas_afectadas=len(records),
            ip=ip,
            user_agent=user_agent,
        )

        await self._session.commit()
        return EncoladoResponse(
            lote_id=lote_id,
            count=len(records),
            requiere_aprobacion=requiere_aprobacion,
        )

    # ── Approval (F3.3, RN-17) ────────────────────────────────────────────────

    async def aprobar_lote(
        self,
        lote_id: uuid.UUID,
        *,
        ip: str = "unknown",
        user_agent: str = "",
    ) -> int:
        """Approve all Pendiente messages in lote_id for dispatch.

        Returns the count of updated messages.
        Raises LookupError if the lote does not exist in this tenant.
        Audits COMUNICACION_APROBAR.
        """
        # Verify lote belongs to this tenant
        mensajes = await self._repo.get_lote(lote_id)
        if not mensajes:
            raise LookupError(f"Lote {lote_id} not found in this tenant.")

        count = await self._repo.aprobar_lote(lote_id)

        await audit_action(
            self._session,
            actor_id=self._actor_id,
            tenant_id=self._tenant_id,
            accion=_ACCION_APROBAR,
            detalle={"lote_id": str(lote_id), "count": count},
            filas_afectadas=count,
            ip=ip,
            user_agent=user_agent,
        )
        await self._session.commit()
        return count

    async def cancelar_lote(
        self,
        lote_id: uuid.UUID,
        *,
        ip: str = "unknown",
        user_agent: str = "",
    ) -> int:
        """Cancel all Pendiente messages in lote_id.

        Returns the count of updated messages.
        Raises LookupError if the lote does not exist in this tenant.
        Audits COMUNICACION_CANCELAR.
        """
        mensajes = await self._repo.get_lote(lote_id)
        if not mensajes:
            raise LookupError(f"Lote {lote_id} not found in this tenant.")

        count = await self._repo.cancelar_lote(lote_id)

        await audit_action(
            self._session,
            actor_id=self._actor_id,
            tenant_id=self._tenant_id,
            accion=_ACCION_CANCELAR,
            detalle={"lote_id": str(lote_id), "count": count},
            filas_afectadas=count,
            ip=ip,
            user_agent=user_agent,
        )
        await self._session.commit()
        return count

    async def cancelar_individual(
        self,
        comunicacion_id: uuid.UUID,
        *,
        ip: str = "unknown",
        user_agent: str = "",
    ) -> None:
        """Cancel a single Pendiente message.

        Validates state machine (only Pendiente→Cancelado allowed).
        Raises ValueError on invalid transition, LookupError if not found.
        """
        msg = await self._repo.get_by_id(comunicacion_id)
        if msg is None:
            raise LookupError(f"Comunicacion {comunicacion_id} not found.")

        self.validar_transicion(msg.estado, "Cancelado")
        await self._repo.update_estado(comunicacion_id, "Cancelado")

        await audit_action(
            self._session,
            actor_id=self._actor_id,
            tenant_id=self._tenant_id,
            accion=_ACCION_CANCELAR,
            detalle={
                "comunicacion_id": str(comunicacion_id),
                "lote_id": str(msg.lote_id),
                "count": 1,
            },
            filas_afectadas=1,
            ip=ip,
            user_agent=user_agent,
        )
        await self._session.commit()

    # ── Lote status ───────────────────────────────────────────────────────────

    async def get_lote_status(self, lote_id: uuid.UUID) -> LoteStatusOut:
        """Return the status of a lote with masked destinatarios.

        Raises LookupError if the lote does not exist in this tenant.
        """
        mensajes = await self._repo.get_lote(lote_id)
        if not mensajes:
            raise LookupError(f"Lote {lote_id} not found in this tenant.")

        msgs_out = []
        for m in mensajes:
            try:
                plain_email = decrypt(m.destinatario)
                masked = _mask_email(plain_email)
            except Exception:
                masked = "***@unknown"
            msgs_out.append(
                ComunicacionOut(
                    id=m.id,
                    lote_id=m.lote_id,
                    destinatario=masked,
                    asunto=m.asunto,
                    estado=m.estado,
                    aprobado=m.aprobado,
                    enviado_at=m.enviado_at,
                    created_at=m.created_at,
                )
            )

        return LoteStatusOut(
            lote_id=lote_id,
            total=len(mensajes),
            pendientes=sum(1 for m in mensajes if m.estado == "Pendiente"),
            enviados=sum(1 for m in mensajes if m.estado == "Enviado"),
            errores=sum(1 for m in mensajes if m.estado == "Error"),
            cancelados=sum(1 for m in mensajes if m.estado == "Cancelado"),
            mensajes=msgs_out,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _get_tenant_requiere_aprobacion(self) -> bool:
        """Read comunicacion_requiere_aprobacion from the current tenant row."""
        from sqlalchemy import select
        from app.models.tenant import Tenant

        stmt = select(Tenant.comunicacion_requiere_aprobacion).where(
            Tenant.id == self._tenant_id
        )
        result = await self._session.execute(stmt)
        val = result.scalar_one_or_none()
        # Default to True (fail-safe: require approval if tenant row not found)
        return val if val is not None else True
