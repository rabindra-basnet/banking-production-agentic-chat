"""Authentication middleware for JWT validation."""

from __future__ import annotations

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Validates JWT tokens from the bank's identity provider."""

    # Paths that don't require authentication
    PUBLIC_PATHS = {"/health", "/health/ready", "/openapi.json"}  # noqa: RUF012

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Validate JWT token for protected routes."""
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        # TODO: Implement JWT validation (Phase 3 - Step 6)
        # 1. Extract Bearer token from Authorization header
        # 2. Validate JWT signature against bank's JWKS
        # 3. Check token expiry
        # 4. Extract user claims and create AuthenticatedUser
        # 5. Attach user to request.state

        return await call_next(request)
