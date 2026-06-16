"""Tests for core/config.py — Settings (Pydantic v2 / pydantic-settings).

TDD cycle:
  RED  (2.1) — this file, written BEFORE core/config.py exists
  GREEN (2.2) — implement Settings to make these pass
  TRIANGULATE (2.3) — add missing-var and invalid-type cases

Strategy: instantiate Settings() directly (not via module reload) to avoid
the module-level `settings` singleton interfering with test isolation.
pydantic-settings reads from os.environ; monkeypatch sets the right env.
"""

import pytest
from pydantic import ValidationError


def make_settings(**overrides):
    """Helper: instantiate Settings with test env, optionally overriding fields."""
    import os
    from app.core.config import Settings
    return Settings(**overrides)


class TestSettingsValid:
    """Settings instantiates successfully with valid environment."""

    def test_settings_instancia_con_env_valido(self, monkeypatch):
        """Scenario: Carga valida desde el entorno — Settings se instancia con campos tipados."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 64)
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")

        from app.core.config import Settings

        s = Settings()
        assert s.DATABASE_URL == "postgresql+asyncpg://u:p@localhost:5432/db"
        assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 30

    def test_access_token_default_15(self, monkeypatch):
        """Scenario: Default del tiempo de expiracion — 15 minutos cuando no se provee."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 64)
        monkeypatch.delenv("ACCESS_TOKEN_EXPIRE_MINUTES", raising=False)

        from app.core.config import Settings

        s = Settings()
        assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 15


class TestSettingsInvalid:
    """Settings fails fast with invalid or missing configuration."""

    def test_falla_si_falta_database_url(self, monkeypatch):
        """Scenario: Configuracion incompleta — DATABASE_URL ausente causa ValidationError."""
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 64)

        from app.core.config import Settings

        with pytest.raises(ValidationError) as exc_info:
            Settings()
        assert "DATABASE_URL" in str(exc_info.value)

    def test_falla_si_falta_secret_key(self, monkeypatch):
        """Settings falla si SECRET_KEY esta ausente."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
        monkeypatch.delenv("SECRET_KEY", raising=False)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 64)

        from app.core.config import Settings

        with pytest.raises(ValidationError):
            Settings()

    def test_falla_si_secret_key_muy_corta(self, monkeypatch):
        """Settings falla si SECRET_KEY tiene menos de 32 caracteres."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "short")
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 64)

        from app.core.config import Settings

        with pytest.raises(ValidationError) as exc_info:
            Settings()
        assert "SECRET_KEY" in str(exc_info.value)

    def test_falla_si_encryption_key_no_es_64_hex_chars(self, monkeypatch):
        """Settings falla si ENCRYPTION_KEY no tiene exactamente 64 caracteres hex (32 bytes)."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "tooshort")

        from app.core.config import Settings

        with pytest.raises(ValidationError) as exc_info:
            Settings()
        assert "ENCRYPTION_KEY" in str(exc_info.value)

    def test_falla_si_access_token_expire_no_es_entero(self, monkeypatch):
        """Scenario: Valor con tipo invalido — ACCESS_TOKEN_EXPIRE_MINUTES no numerico."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 64)
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "not-a-number")

        from app.core.config import Settings

        with pytest.raises(ValidationError):
            Settings()


class TestCorsAllowedOrigins:
    """CORS_ALLOWED_ORIGINS parses correctly from env and defaults safely."""

    def _base_env(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 64)

    def test_default_incluye_localhost_vite(self, monkeypatch):
        """Sin env var, el default incluye el puerto de Vite (5173)."""
        self._base_env(monkeypatch)
        monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)

        from app.core.config import Settings

        s = Settings()
        assert "http://localhost:5173" in s.CORS_ALLOWED_ORIGINS

    def test_parsea_string_separado_por_comas(self, monkeypatch):
        """Un string CSV se divide en lista de origenes."""
        self._base_env(monkeypatch)
        monkeypatch.setenv(
            "CORS_ALLOWED_ORIGINS",
            "https://app.example.com,https://admin.example.com",
        )

        from app.core.config import Settings

        s = Settings()
        assert s.CORS_ALLOWED_ORIGINS == [
            "https://app.example.com",
            "https://admin.example.com",
        ]

    def test_parsea_json_array(self, monkeypatch):
        """Un JSON array en string se parsea correctamente."""
        self._base_env(monkeypatch)
        monkeypatch.setenv(
            "CORS_ALLOWED_ORIGINS",
            '["https://app.example.com","https://admin.example.com"]',
        )

        from app.core.config import Settings

        s = Settings()
        assert "https://app.example.com" in s.CORS_ALLOWED_ORIGINS
        assert "https://admin.example.com" in s.CORS_ALLOWED_ORIGINS

    def test_no_incluye_wildcard_en_default(self, monkeypatch):
        """El default NO contiene '*' — wildcard con credentials=True es invalido per CORS spec."""
        self._base_env(monkeypatch)
        monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)

        from app.core.config import Settings

        s = Settings()
        assert "*" not in s.CORS_ALLOWED_ORIGINS
