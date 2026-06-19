"""workers/main.py — Async background worker for outbound communications.

Polls for approved (aprobado=True) communications and sends them via SMTP.
Runs as: python -m app.workers.main
"""

import asyncio
import logging
import os
import smtplib
import uuid
from email.message import EmailMessage

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text as sql_text

logger = logging.getLogger("worker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")

POLL_INTERVAL = 5  # seconds
SMTP_HOST = os.environ.get("SMTP_HOST", "mailhog")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "1025"))
DB_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://activia:changeme@postgres:5432/activia_trace")


def _send_email(to: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = "trace@activia.edu"
    msg["To"] = to
    msg.set_content(body)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as s:
        s.send_message(msg)


async def process_queue(engine) -> None:
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        rows = await session.execute(
            sql_text("""
                SELECT id, destinatario, asunto, cuerpo
                FROM comunicaciones
                WHERE estado = 'Pendiente'
                  AND aprobado = true
                LIMIT 20
            """)
        )
        messages = rows.fetchall()

        if not messages:
            return

        for msg_id, destinatario, asunto, cuerpo in messages:
            try:
                _send_email(destinatario, asunto, cuerpo)
                await session.execute(
                    sql_text("UPDATE comunicaciones SET estado = 'Enviado', enviado_at = NOW() WHERE id = :id"),
                    {"id": msg_id},
                )
                logger.info("Sent %s -> %s", str(msg_id)[:8], destinatario)
            except Exception as e:
                logger.error("Failed %s: %s", str(msg_id)[:8], e)
                await session.execute(
                    sql_text("UPDATE comunicaciones SET estado = 'Error' WHERE id = :id"),
                    {"id": msg_id},
                )

        await session.commit()


async def main() -> None:
    logger.info("Worker starting — polling every %ss", POLL_INTERVAL)
    engine = create_async_engine(DB_URL, pool_size=2)
    while True:
        try:
            await process_queue(engine)
        except Exception as e:
            logger.error("Poll error: %s", e)
        await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
