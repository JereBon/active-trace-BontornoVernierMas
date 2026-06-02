"""core/observability.py — OpenTelemetry instrumentation for FastAPI.

Spec (observability-base):
- Instruments the FastAPI app so each HTTP request generates a trace span.
- Configurable via environment (OTEL_ENABLED, OTEL_EXPORTER_OTLP_ENDPOINT,
  OTEL_SERVICE_NAME).
- NO mandatory exporter: the app starts normally even without an OTLP backend.
- D6 decision: telemetry destination is deployment config, not code.

Usage:
    from app.core.observability import configure_otel
    configure_otel(app)  # called once in app startup
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def configure_otel(fastapi_app, *, service_name: str = "activia-trace-api") -> None:
    """Instrument a FastAPI application with OpenTelemetry tracing.

    The instrumentation is a no-op when:
      - OTEL_ENABLED env var is not set or falsy, or
      - the opentelemetry packages are not installed.

    Never raises: any OTel setup failure is logged and swallowed so the app
    can start without a telemetry backend.
    """
    import os

    enabled = os.environ.get("OTEL_ENABLED", "").lower() in {"1", "true", "yes"}
    if not enabled:
        logger.info("OpenTelemetry disabled (OTEL_ENABLED not set); skipping init.")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)

        # Optional OTLP exporter — only attached if endpoint is configured
        otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
        if otlp_endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                    OTLPSpanExporter,
                )
                from opentelemetry.sdk.trace.export import BatchSpanProcessor

                exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
                provider.add_span_processor(BatchSpanProcessor(exporter))
                logger.info(
                    "OpenTelemetry OTLP exporter configured",
                    extra={"otlp_endpoint": otlp_endpoint},
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to configure OTLP exporter; traces will not be exported",
                    extra={"error": str(exc)},
                )

        trace.set_tracer_provider(provider)

        FastAPIInstrumentor.instrument_app(fastapi_app)
        logger.info(
            "OpenTelemetry FastAPI instrumentation active",
            extra={"service_name": service_name},
        )

    except Exception as exc:  # noqa: BLE001
        # Never block startup on OTel failure
        logger.warning(
            "OpenTelemetry initialization failed; continuing without tracing",
            extra={"error": str(exc)},
        )
