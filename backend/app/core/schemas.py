"""core/schemas.py — Shared application-level schemas (C-04: RBAC).

UsuarioAutenticado is the object returned by get_current_user after C-04.
It carries the authenticated identity plus the effective permissions resolved
from DB for the current request.

Design (design.md D-04):
  - permisos_efectivos is computed per-request via UsuarioRolRepository.
  - It is NEVER stored in the JWT — always fresh from DB.
  - Pydantic v2 with extra='forbid' to reject unexpected fields.
"""

import uuid

from pydantic import BaseModel, ConfigDict


class UsuarioAutenticado(BaseModel):
    """Authenticated user context, enriched with effective RBAC permissions.

    Returned by get_current_user after C-04 extends it to resolve permisos.

    Fields:
        user_id            — UUID of the authenticated user.
        tenant_id          — UUID of the user's tenant (from JWT claim).
        roles              — List of role codes active for this user (e.g. ['PROFESOR']).
        permisos_efectivos — Union of all permissions from all active roles.

    Compatibility:
        The `id` property is an alias for `user_id` to allow existing router
        code (written against the old `Usuario` ORM object) to work without
        changes during the C-04 migration cycle.  New code should use `user_id`.
    """

    model_config = ConfigDict(extra="forbid")

    user_id: uuid.UUID
    tenant_id: uuid.UUID
    roles: list[str]
    permisos_efectivos: set[str]

    @property
    def id(self) -> uuid.UUID:
        """Alias for user_id — compatibility with pre-C04 router code."""
        return self.user_id
