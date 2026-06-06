"""workers/comunicacion_worker.py — Async communication queue worker (C-12).

Consumes Pendiente+aprobado=True messages from the comunicaciones table,
dispatches them via a configurable email backend stub, and transitions them to
Enviado or Error.

Design decisions (C-12 design.md D1):
- Uses SELECT FOR UPDATE SKIP LOCKED via direct SQLAlchemy so concurrent
  workers never pick up the same message.
- The dispatch function is a stub that reads EMAIL_BACKEND env var:
    stub  → log only (default; safe for dev/test)
    smtp  → (future) real SMTP send
- The worker runs in a loop with configurable poll_interval_secs.
- Integrates as a background asyncio.Task in the FastAPI lifespan (OQ-1).
- run_once() is provided for testing: processes one batch without looping.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)

# ── Email backend stub ────────────────────────────────────────────────────────


async def _dispatch_email(destinatario_cifrado: str, asunto: str, cuerpo: str) -> bool:
    """Dispatch a single email. Returns True on success, False on failure.

    The actual backend is selected via EMAIL_BACKEND env var:
      stub (default) — log and return True (no real email sent)
      smtp           — (not implemented yet; reserved for future)
    """
    backend = os.environ.get("EMAIL_BACKEND", "stub").lower()
    if backend == "stub":
        logger.info(
            "comunicacion_worker [stub] dispatching email asunto=%r",
            asunto[:50],
        )
        return True
    logger.warning("Unknown EMAIL_BACKEND=%r — treating as stub", backend)
    return True


# ── Worker class ─────────────────────────────────────────────────────────────


class ComunicacionWorker:
    """Async worker that polls and dispatches queued communications.

    Usage (one-shot for tests):
        worker = ComunicacionWorker(session_factory)
        await worker.run_once()

    Usage (long-running background task):
        worker = ComunicacionWorker(session_factory)
        await worker.run_forever()   # runs until stop() is called
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        poll_interval_secs: float = 5.0,
        batch_size: int = 10,
    ) -> None:
        self._session_factory = session_factory
        self._poll_interval = poll_interval_secs
        self._batch_size = batch_size
        self._running = False

    async def run_once(self) -> int:
        """Process one batch of Pendiente+aprobado messages.

        Returns the number of messages processed (Enviado + Error combined).
        Opens its own DB session for the batch (SELECT FOR UPDATE SKIP LOCKED).
        """
        from app.models.comunicacion import Comunicacion

        processed = 0

        # ── Phase 1: Lock and transition to Enviando ──────────────────────────
        msg_ids: list = []
        async with self._session_factory() as session:
            async with session.begin():
                stmt = (
                    select(Comunicacion)
                    .where(
                        Comunicacion.estado == "Pendiente",
                        Comunicacion.aprobado.is_(True),
                        Comunicacion.deleted_at.is_(None),
                    )
                    .limit(self._batch_size)
                    .with_for_update(skip_locked=True)
                )
                result = await session.execute(stmt)
                mensajes = list(result.scalars().all())

                for msg in mensajes:
                    msg.estado = "Enviando"
                    msg.updated_at = datetime.now(tz=timezone.utc)
                    session.add(msg)
                    msg_ids.append(
                        (msg.id, msg.destinatario, msg.asunto, msg.cuerpo)
                    )
                # session.begin() auto-commits on context exit

        # ── Phase 2: Dispatch and update final state ──────────────────────────
        for msg_id, destinatario, asunto, cuerpo in msg_ids:
            try:
                success = await _dispatch_email(destinatario, asunto, cuerpo)
                nuevo_estado = "Enviado" if success else "Error"
                enviado_at = datetime.now(tz=timezone.utc) if success else None
            except Exception as exc:
                logger.error(
                    "Worker dispatch error for msg %s: %s", msg_id, exc, exc_info=True
                )
                nuevo_estado = "Error"
                enviado_at = None

            async with self._session_factory() as upd_session:
                async with upd_session.begin():
                    values: dict = {
                        "estado": nuevo_estado,
                        "updated_at": datetime.now(tz=timezone.utc),
                    }
                    if enviado_at is not None:
                        values["enviado_at"] = enviado_at

                    await upd_session.execute(
                        update(Comunicacion)
                        .where(Comunicacion.id == msg_id)
                        .values(**values)
                    )
            processed += 1

        return processed

    async def run_forever(self) -> None:
        """Run the dispatch loop until stop() is called or the task is cancelled."""
        self._running = True
        logger.info("ComunicacionWorker starting (poll_interval=%ss)", self._poll_interval)
        while self._running:
            try:
                count = await self.run_once()
                if count:
                    logger.info("ComunicacionWorker dispatched %d messages", count)
            except Exception as exc:
                logger.error("ComunicacionWorker loop error: %s", exc, exc_info=True)
            await asyncio.sleep(self._poll_interval)

    def stop(self) -> None:
        """Signal the worker to stop after the current batch completes."""
        self._running = False
        logger.info("ComunicacionWorker stopping")
