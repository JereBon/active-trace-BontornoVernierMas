"""app/main.py — FastAPI application bootstrap.

Responsibilities:
  1. Configure structured JSON logging.
  2. Initialize the async DB engine via lifespan.
  3. Initialize OpenTelemetry instrumentation (if enabled).
  4. Apply middleware (CORS, etc. — currently minimal).
  5. Register API routers.

Design decisions:
  D1 — this file wires everything together; business logic lives in services.
  D3 — DB engine is created once at startup and disposed at shutdown.
  D5 — no secrets logged; logging configured before engine init.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application-level resources (startup / shutdown)."""
    # ── Startup ──────────────────────────────────────────────────────────────
    configure_logging()
    logger.info("activia-trace API starting up")

    # Initialize DB engine
    from app.core.config import get_settings
    from app.core.database import create_engine_and_session

    _settings = get_settings()
    create_engine_and_session(_settings.DATABASE_URL)
    logger.info("Database engine initialized")

    # Validate ENCRYPTION_KEY fail-fast before serving requests (C-02)
    from app.core.crypto import validate_key
    validate_key()
    logger.info("Encryption key validated")

    yield  # application runs here

    # ── Shutdown ─────────────────────────────────────────────────────────────
    from app.core.database import dispose_engine

    await dispose_engine()
    logger.info("activia-trace API shut down cleanly")


def create_application() -> FastAPI:
    """Factory that builds and configures the FastAPI application.

    Importing this function (not calling it) does NOT initialize the DB or
    logging — that happens in the lifespan context manager, called by ASGI.
    """
    application = FastAPI(
        title="activia-trace API",
        description="Plataforma de gestión académica multi-tenant",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── Middleware ────────────────────────────────────────────────────────────
    # CORS — permissive in development; tighten in production via config.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    from app.api.v1.routers.health import router as health_router
    from app.api.v1.routers.auth import router as auth_router
    from app.api.v1.routers.carreras import router as carreras_router
    from app.api.v1.routers.cohortes import router as cohortes_router
    from app.api.v1.routers.materias import router as materias_router
    from app.api.v1.routers.avisos import router as avisos_router
    from app.api.v1.routers.programas import router as programas_router
    from app.api.v1.routers.fechas_academicas import router as fechas_academicas_router
    from app.api.v1.routers.usuarios import router as usuarios_router

    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(carreras_router)
    application.include_router(cohortes_router)
    application.include_router(materias_router)
    application.include_router(avisos_router)
    application.include_router(programas_router)
    application.include_router(fechas_academicas_router)
    application.include_router(usuarios_router)

    # ── Exception handlers ────────────────────────────────────────────────────
    from app.core.exceptions import register_exception_handlers

    register_exception_handlers(application)

    # ── OpenTelemetry ─────────────────────────────────────────────────────────
    # Must be called AFTER routers are included (instruments existing routes).
    from app.core.observability import configure_otel

    configure_otel(application)

    return application


# Module-level app instance consumed by uvicorn / ASGI servers.
app = create_application()
