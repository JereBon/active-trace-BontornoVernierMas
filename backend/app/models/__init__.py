"""models/__init__.py — Import all models so Alembic autogenerate can detect them.

Every model module MUST be imported here. The import registers the model's
table metadata on Base.metadata, enabling Alembic to detect schema changes.
"""

from app.models.base import Base, EstadoEntidad, TenantScopedMixin  # noqa: F401
from app.models.tenant import Tenant  # noqa: F401
from app.models.usuario import Usuario  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.password_reset_token import PasswordResetToken  # noqa: F401
from app.models.rol import Rol  # noqa: F401
from app.models.permiso import Permiso  # noqa: F401
from app.models.rol_permiso import RolPermiso  # noqa: F401
from app.models.usuario_rol import UsuarioRol  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.carrera import Carrera  # noqa: F401
from app.models.cohorte import Cohorte  # noqa: F401
from app.models.materia import Materia  # noqa: F401
from app.models.aviso import Aviso  # noqa: F401
from app.models.aviso_ack import AvisoAck  # noqa: F401
from app.models.programa_materia import ProgramaMateria  # noqa: F401
from app.models.fecha_academica import FechaAcademica, TipoEvaluacion  # noqa: F401
from app.models.asignacion import Asignacion  # noqa: F401
from app.models.version_padron import VersionPadron  # noqa: F401
from app.models.entrada_padron import EntradaPadron  # noqa: F401
from app.models.encuentro import SlotEncuentro, InstanciaEncuentro  # noqa: F401
from app.models.guardia import Guardia  # noqa: F401
from app.models.calificacion import Calificacion  # noqa: F401
from app.models.umbral_materia import UmbralMateria  # noqa: F401
from app.models.comunicacion import Comunicacion, EstadoComunicacion  # noqa: F401
from app.models.tarea import Tarea, ComentarioTarea  # noqa: F401

__all__ = [
    "Base",
    "EstadoEntidad",
    "TenantScopedMixin",
    "Tenant",
    "Usuario",
    "RefreshToken",
    "PasswordResetToken",
    "Rol",
    "Permiso",
    "RolPermiso",
    "UsuarioRol",
    "AuditLog",
    "Carrera",
    "Cohorte",
    "Materia",
    "Aviso",
    "AvisoAck",
    "ProgramaMateria",
    "FechaAcademica",
    "TipoEvaluacion",
    "Asignacion",
    "VersionPadron",
    "EntradaPadron",
    "SlotEncuentro",
    "InstanciaEncuentro",
    "Guardia",
    "Calificacion",
    "UmbralMateria",
    "Comunicacion",
    "EstadoComunicacion",
    "Tarea",
    "ComentarioTarea",
]
