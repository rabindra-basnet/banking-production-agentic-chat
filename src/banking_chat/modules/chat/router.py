"""FastAPI router endpoints for chat interactions, authentication, history, and health checks."""

from __future__ import annotations

import asyncio
import hmac
import json
import logging
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from hashlib import sha256
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse

from banking_chat.core.common.exceptions import AuthenticationError, TokenExpiredError
from banking_chat.core.common.idempotency import IdempotencyManager
from banking_chat.core.config.settings import get_settings
from banking_chat.modules.auth.jwt_validator import JWTValidator
from banking_chat.modules.auth.middleware import CurrentUser
from banking_chat.modules.auth.models import (
    LoginRequest,
    RefreshResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserProfileResponse,
    UserRepository,
)
from banking_chat.modules.chat.dependencies import (
    get_chat_pipeline,
    get_idempotency_manager,
    get_jwt_validator,
    get_memory_manager,
)
from banking_chat.modules.chat.graph import ChatPipeline
from banking_chat.modules.chat.schemas import (
    AppConfigResponse,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatSessionItem,
    ChatSessionListResponse,
    ConversationHistoryResponse,
    HealthResponse,
)
from banking_chat.modules.session_memory.conversation import ConversationMemoryManager

router = APIRouter(tags=["Chat & Authentication"])

auth_logger = logging.getLogger("banking_chat.modules.auth")
chat_logger = logging.getLogger("banking_chat.modules.chat")

settings = get_settings()


@router.get(
    "/config",
    response_model=AppConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch dynamic SaaS institution branding, agent names, and compliance notices",
)
async def get_app_config() -> AppConfigResponse:
    """Return backend-driven brand configuration to enable multi-tenant SaaS banking deployments."""
    settings = get_settings()
    return AppConfigResponse(
        bank_name=settings.bank_name,
        bank_tagline=settings.bank_tagline,
        bank_badge=settings.bank_badge,
        assistant_name=settings.assistant_name,
        compliance_notice=settings.compliance_notice,
        supported_services=settings.supported_services,
    )


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate customer via SSO / Banking Credentials and set HttpOnly Cookies",
)
async def login_endpoint(
    payload: LoginRequest,
    response: Response,
    validator: JWTValidator = Depends(get_jwt_validator),
) -> TokenResponse:
    """Real system SSO / Banking Login handler. Sets secure access & refresh tokens in HttpOnly cookies."""
    username = payload.username.strip()
    plain_password = payload.password

    # Query customer from PostgreSQL / SQLite Users Database Table
    matched_customer = await UserRepository.get_by_identifier_or_email(username)

    if not matched_customer and username.lower() == "admin":
        matched_customer = await UserRepository.get_by_customer_id("CIF908999")

    # Verify the presented password against the stored credential hash.
    # Constant-time comparison to reduce timing side-channels.
    password_valid = False
    if matched_customer is not None and matched_customer.password:
        stored_hash = matched_customer.password.encode("utf-8")
        presented_hash = sha256(plain_password.encode("utf-8")).hexdigest().encode("utf-8")
        password_valid = hmac.compare_digest(presented_hash, stored_hash)

    if not matched_customer or not password_valid:
        auth_logger.warning(
            "Login failed for identifier='%s': %s",
            username,
            "user not found" if not matched_customer else "invalid password",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )

    pair = validator.create_token_pair(
        customer_id=matched_customer.customer_id,
        name=matched_customer.name,
        email=matched_customer.email,
        tier=matched_customer.tier,
        accounts=[acc.split(" ")[0] for acc in matched_customer.accounts],
    )

    _is_secure = settings.app_env == "production"

    # Set refresh token in Secure SameSite Cookie (Isolated to auth refresh path)
    response.set_cookie(
        key="refresh_token",
        value=pair["refresh_token"],
        httponly=True,
        samesite="lax",
        secure=_is_secure,
        max_age=7 * 86400,
        path="/api/v1/auth",
    )

    auth_logger.info(
        "Customer login successful: customer_id=%s name='%s' tier=%s",
        matched_customer.customer_id, matched_customer.name, matched_customer.tier,
    )

    # Return access_token directly in response body for in-memory JS client storage
    return TokenResponse(
        access_token=pair["access_token"],
        csrf_token=pair["access_token"][:16],
        customer_id=matched_customer.customer_id,
        name=matched_customer.name,
        email=matched_customer.email,
        role=str(matched_customer.role),
        tier=str(matched_customer.tier),
        accounts=matched_customer.accounts,
    )


@router.get(
    "/auth/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user session profile from Bearer token",
)
async def get_current_user_profile(
    current_user: CurrentUser,
) -> UserProfileResponse:
    """Validate current session from in-memory token and return customer profile directly from Users database table."""
    user_info = await UserRepository.get_by_customer_id(current_user.customer_id)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found in database.",
        )
    return UserProfileResponse(
        customer_id=current_user.customer_id,
        name=current_user.name,
        email=current_user.email,
        role=str(user_info.role),
        tier=str(current_user.tier),
        accounts=user_info.accounts,
    )


@router.post(
    "/auth/refresh",
    response_model=RefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh an expired access token using HttpOnly cookie refresh token",
)
async def refresh_token_endpoint(
    request: Request,
    response: Response,
    payload: RefreshTokenRequest | None = None,
    validator: JWTValidator = Depends(get_jwt_validator),
) -> RefreshResponse:
    """Validate refresh token from cookies (or payload) and issue new in-memory access token strictly without PII."""
    refresh_token = request.cookies.get("refresh_token") or (payload.refresh_token if payload else None)

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token found in cookies or request",
        )

    try:
        result = await validator.refresh_access_token_async(refresh_token)
    except (AuthenticationError, TokenExpiredError) as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(err),
        ) from err

    _is_secure = settings.app_env == "production"

    response.set_cookie(
        key="refresh_token",
        value=str(result["refresh_token"]),
        httponly=True,
        samesite="lax",
        secure=_is_secure,
        max_age=7 * 86400,
        path="/api/v1/auth",
    )

    return RefreshResponse(
        access_token=str(result["access_token"]),
        token_type="Bearer",  # noqa: S106
        expires_in=int(result.get("expires_in", 900)),
    )


@router.post(
    "/auth/logout",
    status_code=status.HTTP_200_OK,
    summary="Clear authentication cookies, blacklist active tokens, and terminate session",
)
async def logout_endpoint(
    request: Request,
    response: Response,
    authorization: Annotated[str | None, Header()] = None,
    validator: JWTValidator = Depends(get_jwt_validator),
) -> dict[str, str]:
    """Blacklist refresh token and access token, and clear client cookies."""
    # 1. Retrieve tokens from cookies or headers
    refresh_token = request.cookies.get("refresh_token")
    access_token = request.cookies.get("access_token")

    if not access_token and authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            access_token = parts[1]

    # 2. Blacklist tokens in server memory/redis store
    if refresh_token:
        await validator.blacklist_mgr.blacklist_token(refresh_token, expiry_seconds=7 * 86400)
    if access_token:
        await validator.blacklist_mgr.blacklist_token(access_token, expiry_seconds=3600)

    # 3. Clear cookies on the client side
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/api/v1/auth")
    return {"status": "logged_out", "message": "Tokens revoked and authentication cookies cleared"}


@router.post(
    "/auth/demo-token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate demo token for testing",
)
async def demo_token_endpoint(
    customer_id: str = "CIF908123",
    tier: str = "standard",
) -> TokenResponse:
    """Generate mock demo credentials for testing."""
    user_info = await UserRepository.get_by_customer_id(customer_id)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo user not found in database.",
        )

    return TokenResponse(
        customer_id=user_info.customer_id,
        name=user_info.name,
        email=user_info.email,
        role=str(user_info.role),
        tier=str(user_info.tier),
        accounts=user_info.accounts,
    )


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a chat message to the banking assistant (supports Idempotency)",
)
async def chat_endpoint(
    request: ChatRequest,
    current_user: CurrentUser,
    idempotency_key_header: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    pipeline: ChatPipeline = Depends(get_chat_pipeline),
    idempotency_mgr: IdempotencyManager = Depends(get_idempotency_manager),
) -> ChatResponse | StreamingResponse:
    """Process incoming chat query through PII filter, Coordinator, and Domain Agents with idempotency protection."""
    session_uuid = request.session_id or uuid4()
    session_id_str = str(session_uuid)
    idem_key = request.idempotency_key or idempotency_key_header

    # Check for idempotent cached response
    if idem_key:
        cached_resp = await idempotency_mgr.get_response(idem_key, current_user.customer_id)
        if cached_resp:
            if request.stream:

                async def cached_stream() -> AsyncGenerator[str, None]:
                    yield f"data: {json.dumps({'event': 'token', 'session_id': session_id_str, 'delta': cached_resp['message'], 'is_final': False})}\n\n"
                    yield f"data: {json.dumps({'event': 'done', 'session_id': session_id_str, 'delta': '', 'is_final': True, 'metadata': {'routed_agent': cached_resp['routed_agent'], 'cost_usd': cached_resp.get('cost_usd', 0.0), 'latency_ms': 0.0}})}\n\n"

                return StreamingResponse(cached_stream(), media_type="text/event-stream")
            return ChatResponse(
                session_id=session_uuid,
                message=cached_resp["message"],
                routed_agent=cached_resp.get("routed_agent", "accounts_agent"),
                cost_usd=cached_resp.get("cost_usd", 0.0),
                latency_ms=0.0,
                idempotency_key=idem_key,
            )

    if request.stream:

        async def event_generator() -> AsyncGenerator[str, None]:
            state = await pipeline.execute(
                session_id=session_id_str,
                user_message=request.message,
                user=current_user,
            )
            full_response = state.get("final_response", "")
            target_agent = state.get("target_agent", "accounts_agent")

            chat_logger.info(
                f"Chat executed: session_id={session_id_str} customer_id={current_user.customer_id} agent={target_agent} latency_ms={state.get('latency_ms', 0):.2f}"
            )

            if idem_key:
                await idempotency_mgr.save_response(
                    idem_key,
                    current_user.customer_id,
                    {
                        "message": full_response,
                        "routed_agent": target_agent,
                        "cost_usd": state.get("cost_usd", 0.0),
                    },
                )

            # Send start / routing event
            start_payload = json.dumps(
                {
                    "event": "agent_switch",
                    "session_id": session_id_str,
                    "agent": target_agent,
                    "delta": f"Routed to {target_agent}...",
                    "is_final": False,
                }
            )
            yield f"data: {start_payload}\n\n"
            await asyncio.sleep(0.05)

            # Stream words / tokens
            words = full_response.split(" ")
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                payload = json.dumps(
                    {
                        "event": "token",
                        "session_id": session_id_str,
                        "delta": chunk,
                        "is_final": False,
                    }
                )
                yield f"data: {payload}\n\n"
                await asyncio.sleep(0.03)

            # Final completion event
            done_payload = json.dumps(
                {
                    "event": "done",
                    "session_id": session_id_str,
                    "delta": "",
                    "is_final": True,
                    "metadata": {
                        "routed_agent": target_agent,
                        "cost_usd": state.get("cost_usd", 0.0),
                        "latency_ms": state.get("latency_ms", 0.0),
                    },
                }
            )
            yield f"data: {done_payload}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    state = await pipeline.execute(
        session_id=session_id_str,
        user_message=request.message,
        user=current_user,
    )

    final_resp_text = state.get("final_response", "")
    target_agent_str = state.get("target_agent", "accounts_agent")
    cost = state.get("cost_usd", 0.0)

    if idem_key:
        await idempotency_mgr.save_response(
            idem_key,
            current_user.customer_id,
            {
                "message": final_resp_text,
                "routed_agent": target_agent_str,
                "cost_usd": cost,
            },
        )

    return ChatResponse(
        session_id=session_uuid,
        message=final_resp_text,
        routed_agent=target_agent_str,
        cost_usd=cost,
        latency_ms=state.get("latency_ms", 0.0),
        idempotency_key=idem_key,
    )


@router.get(
    "/sessions",
    response_model=ChatSessionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all persistent chat sessions for the authenticated customer",
)
async def list_chat_sessions(
    current_user: CurrentUser,
    memory_manager: ConversationMemoryManager = Depends(get_memory_manager),
) -> ChatSessionListResponse:
    """Retrieve all chat sessions owned by the authenticated customer from PostgreSQL / SQLite."""
    records = await memory_manager.checkpointer.list_customer_sessions(current_user.customer_id)
    items = [
        ChatSessionItem(
            id=rec.session_id,
            title=rec.title,
            created_at=rec.created_at,
            updated_at=rec.updated_at,
            message_count=len(rec.messages) if rec.messages else 0,
        )
        for rec in records
    ]
    return ChatSessionListResponse(sessions=items)


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a persistent chat session",
)
async def delete_chat_session(
    session_id: str,
    current_user: CurrentUser,
    memory_manager: ConversationMemoryManager = Depends(get_memory_manager),
) -> dict[str, str]:
    """Delete a chat session owned by the authenticated customer."""
    deleted = await memory_manager.checkpointer.delete_session(session_id, current_user.customer_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    return {"status": "deleted", "session_id": session_id}


@router.get(
    "/history/{session_id}",
    response_model=ConversationHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve session message history",
)
async def get_chat_history(
    session_id: str,
    current_user: CurrentUser,
    memory_manager: ConversationMemoryManager = Depends(get_memory_manager),
) -> ConversationHistoryResponse:
    """Fetch past conversation messages for a session owned by the authenticated customer."""
    session_id_str = session_id

    # Enforce session ownership: a customer may only read their own sessions.
    record = await memory_manager.checkpointer.get_session_record_by_owner(
        session_id_str, current_user.customer_id
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )

    raw_history = await memory_manager.get_history(session_id_str)
    title = record.title
    if not raw_history:
        raw_history = record.messages

    messages = [
        ChatMessage(
            role=m.get("role", "user"),
            content=m.get("content", ""),
            timestamp=datetime.now(UTC),
            metadata={k: v for k, v in m.items() if k not in ("role", "content")},
        )
        for m in raw_history
    ]
    return ConversationHistoryResponse(session_id=session_id, title=title, messages=messages)


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Service health check",
)
async def health_check() -> HealthResponse:
    """Check health and status of the banking chat API service."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        timestamp=datetime.now(UTC),
    )
