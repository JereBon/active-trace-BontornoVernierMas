"""alembic/env.py — Alembic migration environment (async, SQLAlchemy 2.0).

Configured for async engine (asyncpg driver).
C-01: no domain migrations. Migration 001 (Tenant + base models) is C-02.

Usage:
  alembic revision --autogenerate -m "description"
  alembic upgrade head
"""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ── Alembic config object ────────────────────────────────────────────────────
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Metadata ─────────────────────────────────────────────────────────────────
# Import Base so Alembic can detect model changes via autogenerate.
# Models must be imported BEFORE accessing target_metadata.
from app.models.base import Base  # noqa: E402

# All model modules imported here so their tables register on Base.metadata.
import app.models  # noqa: F401, E402  — registers Tenant and all future models

target_metadata = Base.metadata

# ── URL override from env ─────────────────────────────────────────────────────


def get_url() -> str:
    """Prefer DATABASE_URL from the environment over alembic.ini."""
    return os.environ.get(
        "DATABASE_URL",
        config.get_main_option("sqlalchemy.url", ""),
    )


# ── Offline migration ─────────────────────────────────────────────────────────


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generates SQL without a live DB)."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online migration (async) ──────────────────────────────────────────────────


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations online using the async engine."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


# ── Entry point ───────────────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
