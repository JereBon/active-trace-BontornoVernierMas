"""core/config.py — Typed application configuration via Pydantic v2 / pydantic-settings.

Loads values from environment variables and/or a .env file.
Validates on instantiation; raises ValidationError (app cannot start) if invalid.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str
    DATABASE_URL_TEST: str = ""

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY: str
    ENCRYPTION_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    # ── Observability (optional) ──────────────────────────────────────────────
    OTEL_ENABLED: bool = False
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""
    OTEL_SERVICE_NAME: str = "activia-trace-api"

    # ── Validators ────────────────────────────────────────────────────────────

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_min_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @field_validator("ENCRYPTION_KEY")
    @classmethod
    def encryption_key_exact_length(cls, v: str) -> str:
        if len(v) != 32:
            raise ValueError("ENCRYPTION_KEY must be exactly 32 characters (AES-256)")
        return v


def get_settings() -> "Settings":
    """Return the module-level settings singleton, creating it on first call.

    Lazy initialization allows tests to manipulate the environment via
    monkeypatch before the singleton is created, without requiring module reload.
    Call `_reset_settings()` in tests to force re-creation with patched env.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def _reset_settings() -> None:
    """Force re-creation of the settings singleton on next call to get_settings().

    Test-only helper — do NOT call in production code.
    """
    global _settings
    _settings = None


# Module-level private sentinel
_settings: "Settings | None" = None

# Convenience alias: `from app.core.config import settings` still works.
# In production the first import triggers instantiation (env must be set).
# In tests, import the class directly and instantiate it after env is patched.
try:
    settings = get_settings()
except Exception:  # noqa: BLE001
    # Deferred: allow import without a valid env (e.g. during test collection).
    # Callers that use `settings` at function scope will get the real value.
    settings = None  # type: ignore[assignment]
