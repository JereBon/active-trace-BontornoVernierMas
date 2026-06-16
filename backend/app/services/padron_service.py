"""services/padron_service.py — PadronService (C-09: padron-ingesta-moodle).

Orchestrates padrón import, versioning, and Moodle WS sync. Never accesses
the DB directly — all persistence goes through PadronRepository.

Methods:
  preview_desde_archivo    — parse file, return preview without persisting
  confirmar_importacion    — persist versioned padrón + audit log
  sync_desde_moodle        — sync from Moodle WS + confirmar_importacion
  vaciar_padron            — soft-delete all versions for a materia + audit log
  listar_versiones         — list all versions for a materia (history)

Design decisions (C-09 design.md D3, D6, D7):
- Email in EntradaPadron is AES-256 encrypted via app.core.crypto.
- Audit log action 'PADRON_CARGAR' for all loads; 'PADRON_VACIAR' for clears.
- MoodleWSClient is injected or instantiated from tenant config.
- preview_desde_archivo returns EntradaPadronRaw (no DB write) — the two-step
  flow allows the UI to confirm before committing.
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit_action
from app.core.crypto import encrypt
from app.core.exceptions import NotFoundError
from app.models.version_padron import VersionPadron
from app.repositories.padron_repository import PadronRepository
from app.services.padron_parser import EntradaPadronRaw, PadronParseError, PadronParser  # noqa: F401

# Re-export PadronParseError so callers import from one place
__all__ = ["PadronService", "PadronParseError"]

# Audit action codes
_ACCION_CARGAR = "PADRON_CARGAR"
_ACCION_VACIAR = "PADRON_VACIAR"


class PadronService:
    """Orchestrates padrón import, versioning, and Moodle WS sync.

    Instantiated per-request with the active DB session and tenant context
    (always sourced from the verified JWT via the router dependency).
    """

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._repo = PadronRepository(session, tenant_id)
        self._parser = PadronParser()

    # ── Preview (no DB writes) ────────────────────────────────────────────────

    def preview_desde_archivo(
        self,
        file_bytes: bytes,
        content_type: str,
    ) -> list[EntradaPadronRaw]:
        """Parse a .xlsx or .csv file and return a preview without persisting.

        Args:
            file_bytes:   Raw bytes of the uploaded file.
            content_type: MIME type string (e.g. 'text/csv',
                          'application/vnd.openxmlformats-officedocument.
                          spreadsheetml.sheet').

        Returns:
            List of EntradaPadronRaw — preview data.

        Raises:
            PadronParseError: If required columns are missing or file is malformed.
            ValueError: If the content_type is not supported.
        """
        ct = content_type.lower()
        if "spreadsheetml" in ct or "xlsx" in ct or "excel" in ct:
            return self._parser.parse_xlsx(file_bytes)
        elif "csv" in ct or "text/plain" in ct:
            return self._parser.parse_csv(file_bytes)
        else:
            # Try xlsx first, then csv as fallback
            try:
                return self._parser.parse_xlsx(file_bytes)
            except Exception:  # noqa: BLE001
                return self._parser.parse_csv(file_bytes)

    # ── Confirmation (DB writes) ──────────────────────────────────────────────

    async def confirmar_importacion(
        self,
        materia_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        entradas: list[EntradaPadronRaw],
        usuario_id: uuid.UUID,
        ip: str = "unknown",
        user_agent: str = "",
    ) -> VersionPadron:
        """Persist a new versioned padrón and emit audit log.

        Creates a new VersionPadron (deactivating the previous one) and
        bulk-inserts the EntradaPadron rows with encrypted email.

        Args:
            materia_id:  UUID of the materia.
            cohorte_id:  UUID of the cohorte.
            entradas:    Parsed student entries.
            usuario_id:  UUID of the user performing the upload (from JWT).
            ip:          Client IP (for audit).
            user_agent:  Client user-agent (for audit).

        Returns:
            The newly created VersionPadron (activa=True).
        """
        # Create new version (deactivates previous atomically)
        version = await self._repo.crear_version(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            cargado_por=usuario_id,
        )

        # Encrypt PII and build entrada dicts
        entrada_dicts: list[dict[str, Any]] = [
            {
                "nombre": e.nombre,
                "apellidos": e.apellidos,
                "email_cifrado": encrypt(e.email),
                "comision": e.comision,
                "regional": e.regional,
                "usuario_id": None,  # not linked yet
            }
            for e in entradas
        ]

        await self._repo.bulk_insert_entradas(version.id, entrada_dicts)

        # Audit log (best-effort)
        await audit_action(
            session=self._session,
            actor_id=usuario_id,
            tenant_id=self._tenant_id,
            accion=_ACCION_CARGAR,
            detalle={
                "materia_id": str(materia_id),
                "cohorte_id": str(cohorte_id),
                "version_id": str(version.id),
                "filas": len(entradas),
            },
            filas_afectadas=len(entradas),
            ip=ip,
            user_agent=user_agent,
        )

        return version

    # ── Moodle WS sync ────────────────────────────────────────────────────────

    async def sync_desde_moodle(
        self,
        materia_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        course_id: int,
        usuario_id: uuid.UUID,
        moodle_url: str,
        moodle_token: str,
        ip: str = "unknown",
        user_agent: str = "",
    ) -> VersionPadron:
        """Sync padrón from Moodle WS and create a new version.

        Args:
            materia_id:    UUID of the materia.
            cohorte_id:    UUID of the cohorte.
            course_id:     Moodle course ID to sync from.
            usuario_id:    UUID of the user performing the sync (from JWT).
            moodle_url:    Moodle base URL (plaintext, from tenant config).
            moodle_token:  Moodle WS token (plaintext, from tenant config).
            ip:            Client IP (for audit).
            user_agent:    Client user-agent (for audit).

        Returns:
            The newly created VersionPadron.

        Raises:
            MoodleWSError: If Moodle WS is unavailable (caller maps to 502).
        """
        from app.integrations.moodle_ws import MoodleWSClient  # noqa: PLC0415

        client = MoodleWSClient(moodle_url=moodle_url, token=moodle_token)
        moodle_users = await client.get_enrolled_users(course_id)

        # Convert Moodle users to EntradaPadronRaw
        entradas = [
            EntradaPadronRaw(
                nombre=u.firstname,
                apellidos=u.lastname,
                email=u.email,
                comision=None,
                regional=None,
            )
            for u in moodle_users
        ]

        return await self.confirmar_importacion(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            entradas=entradas,
            usuario_id=usuario_id,
            ip=ip,
            user_agent=user_agent,
        )

    # ── Vaciar ────────────────────────────────────────────────────────────────

    async def vaciar_padron(
        self,
        materia_id: uuid.UUID,
        usuario_id: uuid.UUID,
        ip: str = "unknown",
        user_agent: str = "",
    ) -> int:
        """Soft-delete all versions and entries for a materia.

        Scope-isolated (RN-04): deletes versions for this tenant's materia.
        All versions and their entries are soft-deleted.

        Args:
            materia_id:  UUID of the materia to clear.
            usuario_id:  UUID of the user performing the clear (from JWT).
            ip:          Client IP (for audit).
            user_agent:  Client user-agent (for audit).

        Returns:
            Total number of rows soft-deleted.
        """
        total = await self._repo.soft_delete_by_materia(materia_id)

        await audit_action(
            session=self._session,
            actor_id=usuario_id,
            tenant_id=self._tenant_id,
            accion=_ACCION_VACIAR,
            detalle={
                "materia_id": str(materia_id),
                "filas_afectadas": total,
            },
            filas_afectadas=total,
            ip=ip,
            user_agent=user_agent,
        )

        return total

    # ── Query ─────────────────────────────────────────────────────────────────

    async def listar_versiones(
        self,
        materia_id: uuid.UUID,
    ) -> list[VersionPadron]:
        """List all versions (active + historical) for a materia in this tenant.

        Returns:
            List of VersionPadron ordered by cargado_at descending.

        Raises:
            NotFoundError: if materia_id not found (checked by the router via
                           the materias service; not validated here to avoid
                           coupling).
        """
        return await self._repo.get_versiones(materia_id)
