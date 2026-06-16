"""workers/main.py — Background worker entrypoint.

Runs ComunicacionWorker as a standalone process (used by docker-compose
`worker` service). The same worker also runs embedded in the FastAPI lifespan
when running with uvicorn — both paths are supported.

To run: python -m app.workers.main
"""

import asyncio
import logging
import os
import signal

from app.core.logging import configure_logging

logger = logging.getLogger(__name__)

_shutdown = asyncio.Event()


def _handle_signal(signum: int, frame) -> None:  # noqa: ANN001
    logger.info("Worker received shutdown signal", extra={"signal": signum})
    _shutdown.set()


async def run_worker() -> None:
    configure_logging()
    logger.info("activia-trace worker starting")

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    from app.core.config import get_settings
    from app.core.database import create_engine_and_session

    settings = get_settings()
    create_engine_and_session(settings.DATABASE_URL)

    # Bridge pydantic-settings → os.environ so crypto.py finds ENCRYPTION_KEY.
    os.environ.setdefault("ENCRYPTION_KEY", settings.ENCRYPTION_KEY)
    from app.core.crypto import validate_key
    validate_key()

    from app.core.database import async_session_factory
    from workers.comunicacion_worker import ComunicacionWorker

    if async_session_factory is None:
        logger.error("DB session factory not initialised — aborting worker")
        return

    worker = ComunicacionWorker(async_session_factory)
    logger.info("ComunicacionWorker started")

    # Run until shutdown signal
    worker_task = asyncio.create_task(worker.run_forever())
    shutdown_task = asyncio.create_task(_shutdown.wait())
    done, pending = await asyncio.wait(
        [worker_task, shutdown_task], return_when=asyncio.FIRST_COMPLETED
    )
    for t in pending:
        t.cancel()
        try:
            await t
        except (asyncio.CancelledError, Exception):
            pass

    logger.info("activia-trace worker stopped cleanly")


if __name__ == "__main__":
    asyncio.run(run_worker())
