"""repositories/__init__.py — Public exports for the repositories package."""

from app.repositories.base import BaseRepository  # noqa: F401
from app.repositories.audit_log import AuditLogRepository  # noqa: F401
from app.repositories.carrera import CarreraRepository  # noqa: F401
from app.repositories.cohorte import CohorteRepository  # noqa: F401
from app.repositories.materia import MateriaRepository  # noqa: F401
from app.repositories.aviso_repository import AvisoRepository  # noqa: F401
from app.repositories.programa_materia import ProgramaMateriaRepository  # noqa: F401
from app.repositories.fecha_academica import FechaAcademicaRepository  # noqa: F401
from app.repositories.usuario import UsuarioRepository  # noqa: F401
from app.repositories.asignacion import AsignacionRepository  # noqa: F401

__all__ = [
    "BaseRepository",
    "AuditLogRepository",
    "CarreraRepository",
    "CohorteRepository",
    "MateriaRepository",
    "AvisoRepository",
    "ProgramaMateriaRepository",
    "FechaAcademicaRepository",
    "UsuarioRepository",
    "AsignacionRepository",
]
