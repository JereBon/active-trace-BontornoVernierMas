# ─────────────────────────────────────────────────────────────────────────────
# activia-trace API — Multi-stage Dockerfile (Easypanel convention)
#
# Stage 1 (builder): install Python dependencies using uv for fast, deterministic builds
# Stage 2 (runtime): minimal Python 3.13-slim image; no build toolchain
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.13-slim AS builder

WORKDIR /build

# Install uv (fast Python package installer)
RUN pip install --no-cache-dir uv==0.4.30

# Copy dependency manifest first (cache layer)
COPY pyproject.toml .

# Install all dependencies (including asyncpg C extension) into /build/.venv
RUN uv venv /build/.venv \
    && uv pip install --python /build/.venv/bin/python \
       --no-cache ".[dev]"

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.13-slim AS runtime

# Security: run as non-root user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Copy the virtual environment from builder (no pip, no build tools)
COPY --from=builder /build/.venv /app/.venv

# Copy application source
COPY app/ ./app/

# Activate venv by prepending to PATH
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Expose API port
EXPOSE 8000

# Runtime user (non-root)
USER appuser

# Start the FastAPI application via uvicorn
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
