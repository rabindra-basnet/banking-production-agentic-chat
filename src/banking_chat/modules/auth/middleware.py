"""FastAPI authentication middleware enforcing strict production Bearer token validation."""

from __future__ import annotations

from typing import Annotated
from uuid import uuid4

from fastapi import Depends, Header, HTTPException, Request, Response, status

from banking_chat.core.common.exceptions import AuthenticationError, TokenExpiredError
from banking_chat.core.common.types import AuthenticatedUser, CustomerTier
from banking_chat.core.config.settings import get_settings
from banking_chat.modules.auth.jwt_validator import JWTValidator


def get_jwt_validator() -> JWTValidator:
    """Dependency injector for JWTValidator ensuring fresh runtime settings."""
    return JWTValidator()


async def get_current_user(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    validator: Annotated[JWTValidator, Depends(get_jwt_validator)] = None,
) -> AuthenticatedUser:
    """Extract and validate JWT access token strictly from in-memory Authorization Bearer header (or cookie fallback)."""
    settings = get_settings()
    token = None

    # 1. Primary: Extract access_token from Authorization: Bearer <token> header (In-Memory JS client state)
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]

    # 2. Secondary fallback for SSR / cookie clients
    if not token and "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    # 3. Production Protection: Reject requests without token strictly with 401
    if not token:
        if settings.app_env == "production":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. No active session token found.",
            )
        # Development-only fallback user
        return _default_demo_user()

    jwt_val = validator or JWTValidator()
    try:
        return jwt_val.validate_token(token)
    except TokenExpiredError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token expired. Please refresh session.",
        ) from err
    except AuthenticationError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(err),
        ) from err


# Type alias for current authenticated user dependency
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]


def _default_demo_user() -> AuthenticatedUser:
    """Fallback user for local development without active token."""
    from datetime import UTC, datetime, timedelta

    return AuthenticatedUser(
        user_id=uuid4(),
        customer_id="CIF908123",
        name="Rabindra Basnet",
        email="rabindra.basnet@example.com.np",
        tier=CustomerTier.STANDARD,
        accounts=["0120100056781234", "0120100056785678"],
        session_id=uuid4(),
        token_expiry=datetime.now(UTC) + timedelta(hours=1),
    )
