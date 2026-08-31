"""FastAPI Application Factory for Banking Production Agentic Chat."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from banking_chat import __version__
from banking_chat.core.config.constants import API_V1_PREFIX
from banking_chat.core.config.logging_config import setup_logging
from banking_chat.core.config.settings import get_settings
from banking_chat.core.db.session import close_db_engine, get_engine
from banking_chat.modules.chat.router import router as chat_router
from banking_chat.modules.observability.tracing import setup_tracing


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle management for database, cache, and telemetry."""
    settings = get_settings()
    setup_logging(log_level=settings.app_log_level)
    setup_tracing()
    get_engine()

    yield

    await close_db_engine()


def create_app() -> FastAPI:
    """Instantiate and configure the FastAPI application."""
    app = FastAPI(
        title="Banking Production Agentic Chat",
        description="Production-grade AI-powered retail banking assistant with Vertical Slicing.",
        version=__version__,
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount Vertical Slice API Routers
    app.include_router(chat_router, prefix=API_V1_PREFIX)
    app.include_router(chat_router)  # Also mount at root for /health and direct access

    return app


app = create_app()


def start() -> None:
    """Entry point for running the API server in development mode."""
    import uvicorn

    settings = get_settings()
    uvicorn.run("banking_chat.main:app", host="0.0.0.0", port=settings.app_port, reload=True)


def start_prod() -> None:
    """Entry point for running the API server in production with Gunicorn + Uvicorn workers."""
    import subprocess
    import sys

    settings = get_settings()
    cmd = [
        sys.executable,
        "-m",
        "gunicorn",
        "banking_chat.main:app",
        "-w",
        "4",
        "-k",
        "uvicorn.workers.UvicornWorker",
        "-b",
        f"0.0.0.0:{settings.app_port}",
        "--access-logfile",
        "-",
        "--error-logfile",
        "-",
    ]
    subprocess.run(cmd, check=True)  # noqa: S603


if __name__ == "__main__":
    start()
