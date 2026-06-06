"""services/tarea_service.py — TareaService (C-16).

Business logic for internal task management:
  - Creating and assigning tasks (F8.1)
  - Changing task estado with valid-transition enforcement (F8.2)
  - Adding and reading comment threads (F8.2)
  - Delegating (reassigning) tasks preserving asignado_por (F8.3)

Delegates all DB access to TareaRepository and ComentarioTareaRepository.

Business rules:
  - Valid transitions: Pendiente → En_progreso | Cancelada
                       En_progreso → Resuelta | Cancelada
                       Resuelta / Cancelada → (terminal, no transitions allowed)
  - asignado_por is set once on creation and never overwritten by delegation.
  - All estado changes are audit-logged with TAREA_ESTADO_CAMBIAR action.
  - Delegation is audit-logged with TAREA_DELEGAR action.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit_action
from app.models.tarea import ComentarioTarea, Tarea
from app.repositories.tarea_repository import ComentarioTareaRepository, TareaRepository
from app.schemas.tarea import (
    ComentarioCreate,
    TareaCreate,
    TareaFilter,
    TRANSICIONES_VALIDAS,
)

# Audit action codes
_TAREA_CREAR = "TAREA_CREAR"
_TAREA_ESTADO_CAMBIAR = "TAREA_ESTADO_CAMBIAR"
_TAREA_COMENTAR = "TAREA_COMENTAR"
_TAREA_DELEGAR = "TAREA_DELEGAR"


class TareaService:
    """Service layer for Tarea operations.

    Instantiated per-request with the active DB session and tenant context
    (sourced from the verified JWT via the router dependency).
    """

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._repo = TareaRepository(session, tenant_id)
        self._comentario_repo = ComentarioTareaRepository(session, tenant_id)

    # ── F8.1 — Create and assign task ────────────────────────────────────────

    async def crear_tarea(
        self,
        data: TareaCreate,
        actor_id: uuid.UUID,
    ) -> Tarea:
        """Create a new Tarea and assign it to the target user.

        asignado_por is always set to actor_id (the JWT identity).
        asignado_a is the target user from the request body.

        Args:
            data: TareaCreate schema with task details.
            actor_id: UUID of the authenticated user (from JWT).

        Returns:
            Persisted Tarea ORM instance.
        """
        tarea = await self._repo.create(
            {
                "titulo": data.titulo,
                "descripcion": data.descripcion,
                "asignado_a": data.asignado_a,
                "asignado_por": actor_id,
                "estado": "Pendiente",
                "materia_id": data.materia_id,
                "contexto_id": data.contexto_id,
            }
        )
        await audit_action(
            self._session,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            accion=_TAREA_CREAR,
            detalle={
                "tarea_id": str(tarea.id),
                "asignado_a": str(data.asignado_a),
                "titulo": data.titulo,
            },
            filas_afectadas=1,
        )
        return tarea

    # ── F8.1 — List my tasks ─────────────────────────────────────────────────

    async def list_mis_tareas(
        self,
        current_user_id: uuid.UUID,
        filters: TareaFilter,
    ) -> list[Tarea]:
        """Return tasks assigned to the current user with optional filters.

        Args:
            current_user_id: UUID of the authenticated user (from JWT).
            filters: Optional TareaFilter (estado, materia_id).
        """
        return await self._repo.list_mis_tareas(
            asignado_a=current_user_id,
            filters=filters,
        )

    # ── Admin — List all tasks ────────────────────────────────────────────────

    async def list_todas_las_tareas(self, filters: TareaFilter) -> list[Tarea]:
        """Return all tasks for the tenant. Admin-only view.

        Args:
            filters: Optional TareaFilter (estado, asignado_a, materia_id).
        """
        return await self._repo.list_todas(filters)

    # ── F8.2 — Change estado ──────────────────────────────────────────────────

    async def cambiar_estado(
        self,
        tarea_id: uuid.UUID,
        nuevo_estado: str,
        actor_id: uuid.UUID,
    ) -> Tarea:
        """Change the estado of a Tarea with valid-transition enforcement.

        Args:
            tarea_id: UUID of the tarea to update.
            nuevo_estado: Target estado string.
            actor_id: UUID of the authenticated user (from JWT).

        Returns:
            Updated Tarea ORM instance.

        Raises:
            HTTPException 404: Tarea not found or not in current tenant.
            HTTPException 422: Invalid state transition.
        """
        tarea = await self._repo.get(tarea_id)
        if tarea is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea not found.",
            )

        estado_actual = tarea.estado
        transiciones_permitidas = TRANSICIONES_VALIDAS.get(estado_actual, frozenset())
        if nuevo_estado not in transiciones_permitidas:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Invalid transition: {estado_actual!r} → {nuevo_estado!r}. "
                    f"Allowed: {sorted(transiciones_permitidas) or 'none (terminal state)'}."
                ),
            )

        updated = await self._repo.update(tarea_id, {"estado": nuevo_estado})
        await audit_action(
            self._session,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            accion=_TAREA_ESTADO_CAMBIAR,
            detalle={
                "tarea_id": str(tarea_id),
                "estado_anterior": estado_actual,
                "estado_nuevo": nuevo_estado,
            },
            filas_afectadas=1,
        )
        return updated  # type: ignore[return-value]

    # ── F8.2 — Add comment ────────────────────────────────────────────────────

    async def agregar_comentario(
        self,
        tarea_id: uuid.UUID,
        data: ComentarioCreate,
        actor_id: uuid.UUID,
    ) -> ComentarioTarea:
        """Add a comment to a Tarea's thread.

        Args:
            tarea_id: UUID of the tarea to comment on.
            data: ComentarioCreate with the comment text.
            actor_id: UUID of the authenticated user (from JWT).

        Returns:
            Persisted ComentarioTarea ORM instance.

        Raises:
            HTTPException 404: Tarea not found or not in current tenant.
        """
        tarea = await self._repo.get(tarea_id)
        if tarea is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea not found.",
            )

        comentario = await self._comentario_repo.create(
            {
                "tarea_id": tarea_id,
                "autor_id": actor_id,
                "contenido": data.contenido,
            }
        )
        await audit_action(
            self._session,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            accion=_TAREA_COMENTAR,
            detalle={
                "tarea_id": str(tarea_id),
                "comentario_id": str(comentario.id),
            },
            filas_afectadas=1,
        )
        return comentario

    # ── F8.2 — Get comment thread ─────────────────────────────────────────────

    async def get_comentarios(
        self,
        tarea_id: uuid.UUID,
    ) -> list[ComentarioTarea]:
        """Return the chronological comment thread for a Tarea.

        Args:
            tarea_id: UUID of the tarea whose comments to fetch.

        Returns:
            List of ComentarioTarea ordered by created_at ASC.

        Raises:
            HTTPException 404: Tarea not found or not in current tenant.
        """
        tarea = await self._repo.get(tarea_id)
        if tarea is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea not found.",
            )
        return await self._comentario_repo.list_for_tarea(tarea_id)

    # ── F8.3 — Delegate task ──────────────────────────────────────────────────

    async def delegar_tarea(
        self,
        tarea_id: uuid.UUID,
        nuevo_asignado_a: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> Tarea:
        """Reassign a Tarea to a different user, preserving original asignado_por.

        The original asignado_por is NEVER changed — it records who originally
        created and assigned the task. Only asignado_a is updated.

        Args:
            tarea_id: UUID of the tarea to delegate.
            nuevo_asignado_a: UUID of the new assignee.
            actor_id: UUID of the authenticated user (from JWT).

        Returns:
            Updated Tarea ORM instance.

        Raises:
            HTTPException 404: Tarea not found or not in current tenant.
        """
        tarea = await self._repo.get(tarea_id)
        if tarea is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea not found.",
            )

        asignado_a_anterior = tarea.asignado_a
        # Only update asignado_a — asignado_por is immutable after creation
        updated = await self._repo.update(tarea_id, {"asignado_a": nuevo_asignado_a})
        await audit_action(
            self._session,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            accion=_TAREA_DELEGAR,
            detalle={
                "tarea_id": str(tarea_id),
                "asignado_a_anterior": str(asignado_a_anterior),
                "asignado_a_nuevo": str(nuevo_asignado_a),
                "asignado_por_original": str(tarea.asignado_por),
            },
            filas_afectadas=1,
        )
        return updated  # type: ignore[return-value]
