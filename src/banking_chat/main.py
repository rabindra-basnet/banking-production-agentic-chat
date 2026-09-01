"""FastAPI Application Factory for Banking Production Agentic Chat with Global Exception Handlers."""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any, cast

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from banking_chat import __version__
from banking_chat.core.common.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BankingChatError,
    TokenExpiredError,
)
from banking_chat.core.config.constants import API_V1_PREFIX
from banking_chat.core.config.logging_config import setup_logging
from banking_chat.core.config.settings import get_settings
from banking_chat.core.db.session import close_db_engine, get_engine
from banking_chat.modules.chat.router import router as chat_router
from banking_chat.modules.observability.tracing import setup_tracing

logger = logging.getLogger("banking_chat.app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle management for database, cache, and telemetry."""
    settings = get_settings()
    setup_logging(log_level=settings.app_log_level, json_output=settings.app_env == "production")
    setup_tracing()
    get_engine()

    yield

    await close_db_engine()


def create_app() -> FastAPI:
    """Instantiate and configure the FastAPI application with global exception handling."""
    app = FastAPI(
        title="Banking Production Agentic Chat",
        description="Production-grade AI-powered retail banking assistant with Vertical Slicing.",
        version=__version__,
        lifespan=lifespan,
    )

    settings = get_settings()

    # CORS configuration - Strict origin validation preventing cross-site request forgery
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    access_logger = logging.getLogger("banking_chat.access")

    # ─── HTTP Access Logging Middleware ───
    @app.middleware("http")
    async def access_log_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start_time = time.perf_counter()
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path

        response: Response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000

        access_logger.info(
            f"{client_ip} - \"{method} {path}\" {response.status_code} ({duration_ms:.2f}ms)"
        )
        return response

    # ─── Global Exception Handlers ───

    @app.exception_handler(TokenExpiredError)
    async def token_expired_handler(request: Request, exc: TokenExpiredError) -> JSONResponse:
        logger.warning(f"Token expired: path={request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "TokenExpiredError", "message": "Access token expired. Please refresh session.", "code": "TOKEN_EXPIRED"},
        )

    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
        logger.warning(f"Authentication failure: path={request.url.path} msg={str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "AuthenticationError", "message": exc.message, "code": exc.code},
        )

    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
        logger.warning(f"Authorization forbidden: path={request.url.path} msg={str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": "AuthorizationError", "message": exc.message, "code": exc.code},
        )

    @app.exception_handler(BankingChatError)
    async def banking_chat_error_handler(request: Request, exc: BankingChatError) -> JSONResponse:
        logger.error(f"Banking application domain error: path={request.url.path} error={exc.message}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": exc.__class__.__name__, "message": exc.message, "code": exc.code},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning(f"Request validation failure on {request.url.path}: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "ValidationError", "message": "Invalid request payload", "details": exc.errors()},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        # 1. Always log full diagnostic detail in backend server logs
        logger.warning(
            f"HTTP exception on {request.method} {request.url.path}: status={exc.status_code} detail={exc.detail}"
        )

        # 2. In development, provide exact detail; in production, sanitize client response
        if settings.app_env == "development":
            client_msg = exc.detail
        else:
            # Clean standard production status descriptions
            status_messages = {
                400: "Bad Request",
                401: "Authentication required or session expired",
                403: "Access forbidden",
                404: "Requested resource not found",
                405: "Method not allowed",
                422: "Unprocessable request payload",
                429: "Too many requests. Please try again later.",
            }
            client_msg = status_messages.get(exc.status_code, "A client request error occurred")

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": exc.status_code,
                "message": client_msg,
                "code": f"HTTP_{exc.status_code}",
            },
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(f"Unhandled server exception on {request.url.path}: {str(exc)}")
        # In development, attach debug error info; in production, keep sanitized
        error_detail = str(exc) if settings.app_env == "development" else "An unexpected server error occurred. Please try again later."
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "InternalServerError", "message": error_detail, "code": "INTERNAL_SERVER_ERROR"},
        )

    # Mount Vertical Slice API Routers
    app.include_router(chat_router, prefix=API_V1_PREFIX)
    app.include_router(chat_router)  # Mount at root for /health and direct access

    return app


app = create_app()


def start() -> None:
    """Entry point for running the API server in development mode."""
    import uvicorn

    settings = get_settings()
    uvicorn.run("banking_chat.main:app", host="0.0.0.0", port=settings.app_port, reload=True)


if __name__ == "__main__":
    start()
