"""core/exceptions.py — Domain exception base classes and FastAPI handlers (C-02+).

Hierarchy:
  AppError (base)
    ConfigurationError  — missing/invalid environment configuration
    NotFoundError       — resource not found (→ 404)
    ConflictError       — uniqueness constraint violation (→ 409)
    AuthError           — authentication / authorization failure (→ 401/403)

FastAPI exception handlers are registered in main.py via register_exception_handlers().
"""

from fastapi import Request
from fastapi.responses import JSONResponse


# ── Base ──────────────────────────────────────────────────────────────────────


class AppError(Exception):
    """Base class for all application domain errors.

    Attributes:
        message: Human-readable error description.
        code: Machine-readable error code (snake_case).
    """

    http_status: int = 500

    def __init__(self, message: str, code: str = "internal_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


# ── Concrete errors ───────────────────────────────────────────────────────────


class ConfigurationError(AppError):
    """Raised when required configuration (env vars, keys) is absent or invalid.

    The application should fail fast and not serve requests when this is raised.
    """

    http_status = 500

    def __init__(self, message: str) -> None:
        super().__init__(message, code="configuration_error")


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    http_status = 404

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, code="not_found")


class ConflictError(AppError):
    """Raised when an operation would violate a uniqueness constraint."""

    http_status = 409

    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(message, code="conflict")


class AuthError(AppError):
    """Raised for authentication and authorization failures."""

    http_status = 403

    def __init__(self, message: str = "Access denied", code: str = "forbidden") -> None:
        super().__init__(message, code=code)


# ── FastAPI handlers ──────────────────────────────────────────────────────────


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Convert AppError subclasses to structured JSON responses."""
    return JSONResponse(
        status_code=exc.http_status,
        content={"error": exc.code, "message": exc.message},
    )


def register_exception_handlers(app) -> None:
    """Register all domain exception handlers on the FastAPI application.

    Call this from create_application() after router registration.
    """
    app.add_exception_handler(AppError, app_error_handler)
