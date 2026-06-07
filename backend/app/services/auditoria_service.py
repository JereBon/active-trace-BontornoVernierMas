"""services/auditoria_service.py — AuditoriaService (C-19: panel-auditoria-metricas).

Design decisions (C-19 design.md):
  D2 — Scope (propio) logic lives HERE, not in the repository.
       COORDINADOR → actor_id = current_user.user_id (only own actions)
       ADMIN       → actor_id = None (all actions in tenant)
  The repository receives a concrete actor_id (or None) — it has no knowledge
  of roles.

All methods are async and read-only.  No mutations occur in this service.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import UsuarioAutenticado
from app.repositories.auditoria_repository import AuditoriaRepository
from app.schemas.auditoria import (
    AccionPorDia,
    ComunicacionDocenteOut,
    InteraccionDocente,
    InteraccionMateria,
    LogPaginadoOut,
    PanelMetricasOut,
)

# Role constant — matches the seed value in 0003_rbac.py
_ROL_COORDINADOR = "COORDINADOR"


def _is_coordinador(current_user: UsuarioAutenticado) -> bool:
    """Return True if the user has the COORDINADOR role (and not ADMIN).

    ADMIN always sees all tenant data.  COORDINADOR is scoped to own actions.
    If both roles are present, ADMIN wins (broader scope).
    """
    roles = set(current_user.roles)
    return _ROL_COORDINADOR in roles and "ADMIN" not in roles


class AuditoriaService:
    """Read-only service for the audit panel endpoints.

    Constructor args:
        session      — open AsyncSession for the current unit-of-work.
        tenant_id    — UUID of the current tenant (from verified JWT).
    """

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._repo = AuditoriaRepository(session, tenant_id)

    # ── get_panel ─────────────────────────────────────────────────────────────

    async def get_panel(self, current_user: UsuarioAutenticado) -> PanelMetricasOut:
        """Return aggregate metrics for the audit panel.

        Scope:
          COORDINADOR → only their own actions (actor_id = current_user.user_id)
          ADMIN       → all actions in the tenant (actor_id = None)
        """
        actor_id = current_user.user_id if _is_coordinador(current_user) else None

        por_dia_raw = await self._repo.acciones_por_dia(actor_id=actor_id)
        por_docente_raw = await self._repo.interacciones_por_docente(actor_id=actor_id)
        por_materia_raw = await self._repo.interacciones_por_materia(actor_id=actor_id)

        return PanelMetricasOut(
            acciones_por_dia=[AccionPorDia(**r) for r in por_dia_raw],
            por_docente=[InteraccionDocente(**r) for r in por_docente_raw],
            por_materia=[InteraccionMateria(**r) for r in por_materia_raw],
        )

    # ── get_log ───────────────────────────────────────────────────────────────

    async def get_log(
        self,
        current_user: UsuarioAutenticado,
        *,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        usuario_id: uuid.UUID | None = None,
        accion: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> LogPaginadoOut:
        """Return paginated, filtered audit log entries.

        Scope:
          COORDINADOR → actor_id is forced to current_user.user_id; the
                        usuario_id query param is silently ignored.
          ADMIN       → actor_id uses the usuario_id param (if provided).

        Args:
            current_user: Authenticated user from JWT.
            fecha_desde:  Filter start date (inclusive).
            fecha_hasta:  Filter end date (inclusive).
            usuario_id:   Filter by actor (ADMIN only; ignored for COORDINADOR).
            accion:       Filter by exact action code.
            limit:        Max entries (default 200).
            offset:       Pagination offset.
        """
        if _is_coordinador(current_user):
            actor_id: uuid.UUID | None = current_user.user_id
        else:
            actor_id = usuario_id  # may be None → no filter

        items, total = await self._repo.log_paginado(
            actor_id=actor_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            accion=accion,
            limit=limit,
            offset=offset,
        )

        return LogPaginadoOut(
            items=items,  # type: ignore[arg-type]  # AuditLog → AuditLogOut via from_attributes
            total=total,
        )

    # ── get_comunicaciones ────────────────────────────────────────────────────

    async def get_comunicaciones(
        self, current_user: UsuarioAutenticado
    ) -> list[ComunicacionDocenteOut]:
        """Return communication counts per docente grouped by estado.

        Scope:
          COORDINADOR → only their own sent communications
                        (docente_id = current_user.user_id)
          ADMIN       → all docentes in the tenant
        """
        docente_id = current_user.user_id if _is_coordinador(current_user) else None

        raw = await self._repo.comunicaciones_por_docente(docente_id=docente_id)
        return [ComunicacionDocenteOut(**r) for r in raw]
