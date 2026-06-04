"""repositories/__init__.py — Public exports for the repositories package."""

from app.repositories.base import BaseRepository  # noqa: F401
from app.repositories.audit_log import AuditLogRepository  # noqa: F401
from app.repositories.carrera import CarreraRepository  # noqa: F401
from app.repositories.cohorte import CohorteRepository  # noqa: F401
from app.repositories.materia import MateriaRepository  # noqa: F401

__all__ = [
    "BaseRepository",
    "AuditLogRepository",
    "CarreraRepository",
    "CohorteRepository",
    "MateriaRepository",
]
