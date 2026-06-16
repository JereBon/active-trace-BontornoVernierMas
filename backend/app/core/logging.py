"""core/logging.py — Structured JSON logging configuration.

Spec (observability-base):
- One JSON line per event with fields: timestamp, level, message.
- Applied to the root logger at app startup.
- MUST NOT emit secrets or PII in plain text.

Usage:
    from app.core.logging import configure_logging
    configure_logging()  # called once in app startup
"""

import json
import logging
import sys
from datetime import UTC, datetime


class _JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON objects.

    Output fields per record:
      timestamp  — ISO-8601 UTC timestamp
      level      — log level name (INFO, ERROR, …)
      message    — the formatted log message
      name       — logger name
      extra fields passed via the `extra=` kwarg of logging calls
    """

    def format(self, record: logging.LogRecord) -> str:
        # Build the base payload
        payload: dict = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }

        # Include exception info if present
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        # Include any extra fields attached to the record, but skip private attrs
        _reserved = {
            "args", "asctime", "created", "exc_info", "exc_text", "filename",
            "funcName", "levelname", "levelno", "lineno", "message", "module",
            "msecs", "msg", "name", "pathname", "process", "processName",
            "relativeCreated", "stack_info", "thread", "threadName", "taskName",
        }
        for key, value in record.__dict__.items():
            if key not in _reserved and not key.startswith("_"):
                payload[key] = value

        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    """Install the JSON formatter on the root logger.

    Safe to call multiple times (idempotent — only adds handler once
    if the root logger has no handlers yet).
    """
    root = logging.getLogger()
    root.setLevel(level)

    # Only attach if not already configured (prevents duplicate output)
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_JsonFormatter())
        root.addHandler(handler)
    else:
        # Replace formatters on existing handlers with JSON formatter
        formatter = _JsonFormatter()
        for handler in root.handlers:
            handler.setFormatter(formatter)
