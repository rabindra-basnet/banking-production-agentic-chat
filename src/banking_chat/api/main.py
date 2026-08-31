"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from banking_chat.api.routes import chat, health
from banking_chat.config.constants import API_V1_PREFIX
from banking_chat.config.logging_config import setup_logging
from banking_chat.config.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown events."""
    settings = get_settings()
    setup_logging(log_level=settings.app_log_level)
    # TODO: Initialize Redis, PostgreSQL, MCP clients
    yield
    # TODO: Cleanup connections


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Banking Agentic Chat API",
        description="Production-grade AI-powered banking customer support chatbot",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.app_env == "development" else None,
        redoc_url="/redoc" if settings.app_env == "development" else None,
    )

    # Register routes
    app.include_router(health.router, tags=["Health"])
    app.include_router(chat.router, prefix=API_V1_PREFIX, tags=["Chat"])

    return app


# Application instance
app = create_app()
