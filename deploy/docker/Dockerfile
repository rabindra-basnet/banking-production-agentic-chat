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

# Copy source code and deployment config
COPY src/ src/
COPY deploy/docker/gunicorn.yaml ./gunicorn.yaml

# Stage 2: Model builder - downloads the spaCy NLP model (presidio PII detection)
FROM python:3.12-slim AS models

# Install the spaCy model into a venv-matching location that presidio can load by name
RUN pip install --no-cache-dir en_core_web_lg==3.8.0

# Stage 3: Runtime
FROM python:3.12-slim AS runtime

# Security: run as non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy installed packages and source
COPY --from=builder /app /app

# Install model into runtime site-packages so spacy.load('en_core_web_lg') works
RUN pip install --no-cache-dir en_core_web_lg==3.8.0

# Switch to non-root user
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uv", "run", "gunicorn", "banking_chat.main:app", "-c", "python:banking_chat.gunicorn_conf"]
