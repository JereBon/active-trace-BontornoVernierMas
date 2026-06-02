"""workers/main.py — Background worker entrypoint (placeholder).

C-01: no-op loop. The actual queue technology (asyncio / Celery / ARQ)
is defined in ADR-003 and implemented in the communications change.

To run: python -m app.workers.main
"""

import asyncio
import logging
import signal
import sys

from app.core.logging import configure_logging

logger = logging.getLogger(__name__)

_shutdown = asyncio.Event()


def _handle_signal(signum: int, frame) -> None:  # noqa: ANN001
    logger.info("Worker received shutdown signal", extra={"signal": signum})
    _shutdown.set()


async def run_worker() -> None:
    """Main worker loop — no-op placeholder.

    Replace the loop body with real task processing in the communications
    change once ADR-003 selects the queue technology.
    """
    configure_logging()
    logger.info("activia-trace worker started (no-op placeholder)")

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    while not _shutdown.is_set():
        # PLACEHOLDER: poll queue or wait for tasks here
        await asyncio.sleep(5)

    logger.info("activia-trace worker stopped cleanly")


if __name__ == "__main__":
    asyncio.run(run_worker())
