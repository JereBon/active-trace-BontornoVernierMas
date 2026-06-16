"""core/rbac.py — RBAC guard for FastAPI endpoints (C-04: RBAC).

Usage in a router:
    from fastapi import Depends
    from app.core.rbac import require_permission
    from app.core.permisos import CALIFICACIONES_IMPORTAR

    @router.get(
        "/calificaciones",
        dependencies=[Depends(require_permission(CALIFICACIONES_IMPORTAR))],
    )
    async def importar_calificaciones(...): ...

Design (design.md D-05):
  - require_permission(permiso) is a factory that returns a FastAPI dependency.
  - The returned callable depends on get_current_user, which already carries
    permisos_efectivos after C-04 extends it.
  - Fail-closed: any missing or absent permission → HTTP 403.
"""

from collections.abc import Callable
from typing import Annotated, TYPE_CHECKING

from fastapi import Depends, HTTPException, status

if TYPE_CHECKING:
    from app.core.schemas import UsuarioAutenticado


def require_permission(permiso: str) -> Callable:
    """Return a FastAPI dependency that enforces the given permission.

    The returned dependency raises:
      HTTP 401 — if the user is not authenticated (raised by get_current_user)
      HTTP 403 — if the authenticated user lacks *permiso*

    Args:
        permiso: Permission code in 'modulo:accion' format.

    Returns:
        An async FastAPI-compatible dependency callable.
    """
    # Import here (not at module level) to avoid import cycles:
    # rbac ← dependencies ← rbac would cause a cycle if imported at module
    # level.  FastAPI resolves dependencies lazily, so this is safe.
    from app.core.dependencies import get_current_user  # noqa: PLC0415

    async def _guard(
        current_user: Annotated["UsuarioAutenticado", Depends(get_current_user)],
    ) -> None:
        if permiso not in current_user.permisos_efectivos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden",
            )

    return _guard
