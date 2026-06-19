"""core/email.py — Async email sender with SMTP backend.

Usage:
    from app.core.email import send_email
    await send_email("to@example.com", "Subject", "<html>...</html>")
"""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import get_settings


async def send_email(
    to: str,
    subject: str,
    html_body: str,
    *,
    _settings = None,
) -> bool:
    """Send an HTML email via SMTP.

    Args:
        to:        Recipient email address (plaintext, already decrypted).
        subject:   Email subject line.
        html_body: HTML body content.

    Returns:
        True on success, False on failure (logs the error).
    """
    import logging
    logger = logging.getLogger(__name__)

    settings = _settings or get_settings()

    msg = MIMEMultipart("alternative")
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER or None,
            password=settings.SMTP_PASSWORD or None,
            use_tls=settings.SMTP_TLS,
        )
        logger.info("Email sent to %s — subject=%r", to, subject[:50])
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to, exc, exc_info=True)
        return False
