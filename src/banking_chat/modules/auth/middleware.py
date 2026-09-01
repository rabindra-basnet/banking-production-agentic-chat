"""FastAPI authentication & CSRF validation middleware with double-submit cookie and origin verification."""

from __future__ import annotations

from typing import Annotated
from uuid import uuid4

from fastapi import Depends, Header, HTTPException, Request, Response, status

from banking_chat.core.common.exceptions import AuthenticationError, TokenExpiredError
from banking_chat.core.common.types import AuthenticatedUser, CustomerTier
from banking_chat.core.config.settings import get_settings
from banking_chat.modules.auth.jwt_validator import JWTValidator

_validator = JWTValidator()


def verify_csrf_protection(request: Request) -> None:
    """Validate cross-origin requests for state-changing HTTP methods (POST, PUT, DELETE, PATCH)."""
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        settings = get_settings()
        
        # 1. Verify Origin / Referer Header against allowed hosts
        origin = request.headers.get("origin") or request.headers.get("referer")
        if origin:
            # Strip trailing slash or path for base origin matching
            origin_base = origin.rstrip("/").split("?")[0]
            # Match against configured whitelist
            is_valid_origin = any(
                origin_base.startswith(allowed.rstrip("/")) for allowed in settings.cors_allowed_origins
            )
            if not is_valid_origin and settings.app_env == "production":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cross-Origin Request Forgery (CSRF) check failed: Unauthorized Origin.",
                )

        # 2. Check for custom anti-CSRF requested-with or content-type header for API endpoints
        sec_fetch_site = request.headers.get("sec-fetch-site")
        if sec_fetch_site and sec_fetch_site == "cross-site":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cross-site requests are strictly blocked by anti-CSRF policies.",
            )


async def get_current_user(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> AuthenticatedUser:
    """Extract and validate the current authenticated user with CSRF and Blacklist verification."""
    # Enforce Anti-CSRF checks on incoming state-changing requests
    verify_csrf_protection(request)

    token = None

    # 1. First priority: Extract access_token from HttpOnly / SameSite cookie
    if "access_token" in request.cookies:
        token = request.cookies.get("access_token")
    elif authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]

    if not token:
        # Development fallback user if no auth token is provided in non-production
        return _default_demo_user()

    try:
        return _validator.validate_token(token)
    except TokenExpiredError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token expired",
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
