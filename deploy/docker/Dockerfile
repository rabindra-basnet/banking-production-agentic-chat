# Multi-stage production Dockerfile
# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev --no-editable

# Copy source code
COPY src/ src/

# Stage 2: Runtime
FROM python:3.12-slim AS runtime

# Security: run as non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy installed packages and source
COPY --from=builder /app /app

# Switch to non-root user
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uv", "run", "gunicorn", "banking_chat.main:app", "-c", "python:banking_chat.gunicorn_conf"]
