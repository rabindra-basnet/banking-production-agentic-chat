"""CORS configuration middleware."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app: FastAPI, allowed_origins: list[str] | None = None) -> None:
    """Configure CORS middleware.

    Args:
        app: FastAPI application instance.
        allowed_origins: List of allowed origins. Defaults to localhost for development.
    """
    origins = allowed_origins or ["http://localhost:3000", "http://localhost:5173"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        max_age=3600,
    )
