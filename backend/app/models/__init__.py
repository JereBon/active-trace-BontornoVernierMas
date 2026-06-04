"""models/__init__.py — Import all models so Alembic autogenerate can detect them.

Every model module MUST be imported here. The import registers the model's
table metadata on Base.metadata, enabling Alembic to detect schema changes.
"""

from app.models.base import Base, TenantScopedMixin  # noqa: F401
from app.models.tenant import Tenant  # noqa: F401

__all__ = ["Base", "TenantScopedMixin", "Tenant"]
