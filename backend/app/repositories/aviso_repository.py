"""repositories/aviso_repository.py — AvisoRepository (C-15: avisos-y-acknowledgment).

All queries are scoped to tenant_id. Never emits DELETE statements.

Methods:
  create_aviso      — persist a new Aviso
  list_vigentes     — return active notices within the visibility window, filtered by scope
  get_aviso         — fetch a single Aviso by id (tenant-scoped)
  patch_aviso       — update mutable fields (activo, titulo, cuerpo, etc.)
  create_ack        — create or ignore duplicate AvisoAck (idempotent)
  list_acks         — return all AvisoAck records for a given Aviso
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.aviso import Aviso, AvisoScope
from app.models.aviso_ack import AvisoAck


class AvisoRepository:
    """Tenant-scoped repository for Aviso and AvisoAck records."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    # ── Aviso writes ──────────────────────────────────────────────────────────

    async def create_aviso(
        self,
        publicado_por: uuid.UUID,
        data: dict[str, Any],
    ) -> Aviso:
        """Persist a new Aviso.

        tenant_id and publicado_por are always sourced from the repository
        instance / JWT — never from the data dict.
        """
        payload = {
            **data,
            "tenant_id": self._tenant_id,
            "publicado_por": publicado_por,
        }
        aviso = Aviso(**payload)
        self._session.add(aviso)
        await self._session.flush()
        await self._session.refresh(aviso)
        return aviso

    async def patch_aviso(
        self, aviso_id: uuid.UUID, data: dict[str, Any]
    ) -> Aviso | None:
        """Update mutable fields on an existing Aviso.

        Returns the updated Aviso, or None if not found in this tenant.
        Immutable fields (id, tenant_id, publicado_por) are silently ignored.
        """
        aviso = await self.get_aviso(aviso_id)
        if aviso is None:
            return None

        data.pop("id", None)
        data.pop("tenant_id", None)
        data.pop("publicado_por", None)

        for key, value in data.items():
            setattr(aviso, key, value)

        aviso.updated_at = datetime.now(tz=timezone.utc)
        self._session.add(aviso)
        await self._session.flush()
        await self._session.refresh(aviso)
        return aviso

    # ── Aviso reads ───────────────────────────────────────────────────────────

    async def get_aviso(self, aviso_id: uuid.UUID) -> Aviso | None:
        """Return a single Aviso by PK, scoped to tenant. None if not found."""
        stmt = select(Aviso).where(
            Aviso.id == aviso_id,
            Aviso.tenant_id == self._tenant_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_vigentes(
        self,
        usuario_id: uuid.UUID,
        roles: list[str],
        now: datetime | None = None,
    ) -> list[Aviso]:
        """Return active Avisos within their visibility window for this user.

        Filters applied:
          1. tenant_id = self._tenant_id
          2. activo = True
          3. vig_desde <= now <= vig_hasta
          4. scope audience matches (TODOS, ROL matching user roles, USUARIO matching user)

        Args:
            usuario_id: UUID of the requesting user.
            roles:      List of role codes held by the requesting user.
            now:        Reference datetime (defaults to utcnow). Injected in tests.
        """
        if now is None:
            now = datetime.now(tz=timezone.utc)

        scope_filter = or_(
            Aviso.scope == AvisoScope.TODOS.value,
            and_(
                Aviso.scope == AvisoScope.ROL.value,
                Aviso.scope_valor.in_(roles) if roles else Aviso.scope_valor.is_(None),
            ),
            and_(
                Aviso.scope == AvisoScope.USUARIO.value,
                Aviso.scope_valor == str(usuario_id),
            ),
        )

        stmt = (
            select(Aviso)
            .where(
                Aviso.tenant_id == self._tenant_id,
                Aviso.activo.is_(True),
                Aviso.vig_desde <= now,
                Aviso.vig_hasta >= now,
                scope_filter,
            )
            .order_by(Aviso.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ── AvisoAck writes ───────────────────────────────────────────────────────

    async def create_ack(
        self, aviso_id: uuid.UUID, usuario_id: uuid.UUID
    ) -> AvisoAck:
        """Create an acknowledgment, ignoring duplicates (idempotent).

        Uses INSERT … ON CONFLICT DO NOTHING to avoid race conditions.
        Always returns the existing or newly created AvisoAck row.
        """
        new_id = uuid.uuid4()
        now = datetime.now(tz=timezone.utc)

        stmt = (
            pg_insert(AvisoAck)
            .values(
                id=new_id,
                tenant_id=self._tenant_id,
                aviso_id=aviso_id,
                usuario_id=usuario_id,
                leido_en=now,
            )
            .on_conflict_do_nothing(
                constraint="uq_aviso_ack_aviso_usuario",
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()

        # Fetch the canonical row (either the one just inserted or the preexisting one)
        fetch_stmt = select(AvisoAck).where(
            AvisoAck.aviso_id == aviso_id,
            AvisoAck.usuario_id == usuario_id,
            AvisoAck.tenant_id == self._tenant_id,
        )
        result = await self._session.execute(fetch_stmt)
        ack = result.scalar_one()
        return ack

    # ── AvisoAck reads ────────────────────────────────────────────────────────

    async def list_acks(self, aviso_id: uuid.UUID) -> list[AvisoAck]:
        """Return all acknowledgments for a given Aviso in this tenant."""
        stmt = select(AvisoAck).where(
            AvisoAck.aviso_id == aviso_id,
            AvisoAck.tenant_id == self._tenant_id,
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
