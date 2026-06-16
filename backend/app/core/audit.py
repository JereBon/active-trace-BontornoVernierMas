"""core/audit.py — Audit helper for recording significant actions (C-05).

Usage in any service:
    from app.core.audit import audit_action

    await audit_action(
        session=session,
        actor_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        accion="CALIFICACIONES_IMPORTAR",
        detalle={"materia_id": str(materia_id)},
        filas_afectadas=42,
        ip=ip,
        user_agent=user_agent,
        # actor_impersonado_id=current_user.impersonando_id,  # if impersonating
    )

Design decisions (design.md):
  D2: function (not decorator) so the caller controls what data to pass and
      the I/O contract is explicit.
  D3: best-effort — if the write fails, log the error and continue.  The
      primary business operation must NOT be aborted because an audit log
      write failed.
  D5: actor_impersonado_id must be passed explicitly by the caller when the
      action occurs under an impersonation session.  The caller knows this
      because get_current_user exposes impersonando_id on UsuarioAutenticado.
"""

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def audit_action(
    session: AsyncSession,
    *,
    actor_id: uuid.UUID,
    tenant_id: uuid.UUID,
    accion: str,
    detalle: dict[str, Any] | None = None,
    filas_afectadas: int = 0,
    ip: str = "unknown",
    user_agent: str = "",
    actor_impersonado_id: uuid.UUID | None = None,
) -> None:
    """Record a significant action in the audit log.

    This function is best-effort: if the write fails (e.g. transient DB error),
    the error is logged and the function returns normally without raising.
    The calling service must NOT depend on this function raising exceptions.

    Args:
        session:               Open AsyncSession for the current unit-of-work.
        actor_id:              UUID of the user who performed the action
                               (always the REAL actor, never the impersonated one).
        tenant_id:             UUID of the tenant in which the action occurred.
        accion:                Action code string (e.g. "CALIFICACIONES_IMPORTAR").
                               Use constants from app.core.acciones_auditoria.
        detalle:               Optional JSONB dict with action-specific context.
        filas_afectadas:       Number of DB records affected (0 if not applicable).
        ip:                    Client IP address.
        user_agent:            HTTP User-Agent string.
        actor_impersonado_id:  UUID of the impersonated user, or None.
    """
    from app.repositories.audit_log import AuditLogRepository  # avoid cycle

    try:
        repo = AuditLogRepository(session, tenant_id)
        await repo.create(
            {
                "actor_id": actor_id,
                "actor_impersonado_id": actor_impersonado_id,
                "accion": accion,
                "detalle": detalle or {},
                "filas_afectadas": filas_afectadas,
                "ip": ip,
                "user_agent": user_agent,
            }
        )
    except Exception:  # noqa: BLE001
        logger.error(
            "audit_action failed — accion=%s actor_id=%s tenant_id=%s",
            accion,
            actor_id,
            tenant_id,
            exc_info=True,
        )
