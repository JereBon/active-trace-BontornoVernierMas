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
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")

        from app.core.config import Settings

        s = Settings()
        assert s.DATABASE_URL == "postgresql+asyncpg://u:p@localhost:5432/db"
        assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 30

    def test_access_token_default_15(self, monkeypatch):
        """Scenario: Default del tiempo de expiracion — 15 minutos cuando no se provee."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)
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
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)

        from app.core.config import Settings

        with pytest.raises(ValidationError) as exc_info:
            Settings()
        assert "DATABASE_URL" in str(exc_info.value)

    def test_falla_si_falta_secret_key(self, monkeypatch):
        """Settings falla si SECRET_KEY esta ausente."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
        monkeypatch.delenv("SECRET_KEY", raising=False)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)

        from app.core.config import Settings

        with pytest.raises(ValidationError):
            Settings()

    def test_falla_si_secret_key_muy_corta(self, monkeypatch):
        """Settings falla si SECRET_KEY tiene menos de 32 caracteres."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
        monkeypatch.setenv("SECRET_KEY", "short")
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)

        from app.core.config import Settings

        with pytest.raises(ValidationError) as exc_info:
            Settings()
        assert "SECRET_KEY" in str(exc_info.value)

    def test_falla_si_encryption_key_no_es_32_chars(self, monkeypatch):
        """Settings falla si ENCRYPTION_KEY no tiene exactamente 32 caracteres."""
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
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "not-a-number")

        from app.core.config import Settings

        with pytest.raises(ValidationError):
            Settings()
