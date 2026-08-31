"""Health check endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from banking_chat import __version__

router = APIRouter()

_START_TIME = datetime.now(timezone.utc)


@router.get("/health")
async def health_check() -> dict:
    """Basic health check."""
    return {
        "status": "healthy",
        "version": __version__,
        "uptime_seconds": (datetime.now(timezone.utc) - _START_TIME).total_seconds(),
    }


@router.get("/health/ready")
async def readiness_check() -> dict:
    """Readiness check — verifies all dependencies are available."""
    # TODO: Check Redis, PostgreSQL, MCP servers
    return {
        "ready": True,
        "checks": {
            "redis": "not_configured",
            "database": "not_configured",
            "mcp_servers": "not_configured",
        },
    }
