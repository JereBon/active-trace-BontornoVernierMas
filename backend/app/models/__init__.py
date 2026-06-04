"""models/__init__.py — Import all models so Alembic autogenerate can detect them.

Every model module MUST be imported here. The import registers the model's
table metadata on Base.metadata, enabling Alembic to detect schema changes.
"""

from app.models.base import Base, TenantScopedMixin  # noqa: F401
from app.models.tenant import Tenant  # noqa: F401
from app.models.usuario import Usuario  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.password_reset_token import PasswordResetToken  # noqa: F401
from app.models.rol import Rol  # noqa: F401
from app.models.permiso import Permiso  # noqa: F401
from app.models.rol_permiso import RolPermiso  # noqa: F401
from app.models.usuario_rol import UsuarioRol  # noqa: F401

__all__ = [
    "Base",
    "TenantScopedMixin",
    "Tenant",
    "Usuario",
    "RefreshToken",
    "PasswordResetToken",
    "Rol",
    "Permiso",
    "RolPermiso",
    "UsuarioRol",
]
