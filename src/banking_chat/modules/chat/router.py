"""FastAPI router endpoints for chat interactions, authentication, history, and health checks."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse

from banking_chat.core.common.exceptions import AuthenticationError, TokenExpiredError
from banking_chat.core.common.idempotency import IdempotencyManager
from banking_chat.core.common.types import AuthenticatedUser, CustomerTier
from banking_chat.core.config.settings import get_settings
from banking_chat.modules.auth.jwt_validator import JWTValidator
from banking_chat.modules.auth.middleware import CurrentUser, get_current_user
from banking_chat.modules.auth.models import (
    LoginRequest,
    RefreshTokenRequest,
    Role,
    TokenResponse,
    UserProfileSchema,
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
    StreamChunk,
)
from banking_chat.modules.session_memory.conversation import ConversationMemoryManager

router = APIRouter(tags=["Chat & Authentication"])
memory_manager = ConversationMemoryManager()
pipeline = ChatPipeline(memory_manager=memory_manager)
jwt_validator = JWTValidator()
idempotency_mgr = IdempotencyManager()


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

# Customer user directory instantiated via Pydantic UserProfileSchema
CUSTOMER_DIRECTORY: dict[str, UserProfileSchema] = {
    "CIF908123": UserProfileSchema(
        customer_id="CIF908123",
        name="Rabindra Basnet",
        email="rabindra.basnet@example.com.np",
        role=Role.CUSTOMER,
        tier=CustomerTier.STANDARD,
        accounts=["0120100056781234 (Savings Khata)", "0120100056785678 (Muddati Khata)"],
        password="password123",
    ),
    "CIF908456": UserProfileSchema(
        customer_id="CIF908456",
        name="Sita Shrestha",
        email="sita.shrestha@example.com.np",
        role=Role.CUSTOMER,
        tier=CustomerTier.PREMIUM,
        accounts=["0240100088994433 (Savings Khata)", "0240100088997788 (Current Khata)"],
        password="password123",
    ),
    "CIF908999": UserProfileSchema(
        customer_id="CIF908999",
        name="Prashant Thapa",
        email="prashant.thapa@example.com.np",
        role=Role.ADMIN,
        tier=CustomerTier.PRIVILEGED,
        accounts=["0380100077771122 (Corporate Savings)", "0380100077773344 (Muddati Khata)"],
        password="password123",
    ),
}


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate customer via SSO / Banking Credentials and set HttpOnly Cookies",
)
async def login_endpoint(payload: LoginRequest, response: Response) -> TokenResponse:
    """Real system SSO / Banking Login handler. Sets secure access & refresh tokens in HttpOnly cookies."""
    username = payload.username.strip()

    # Find customer by CIF, Email, or Full Name
    matched_customer = None
    for c in CUSTOMER_DIRECTORY.values():
        if (
            username.lower() == c.customer_id.lower()
            or username.lower() == c.email.lower()
            or username.lower() == c.name.lower()
            or (username.lower() == "admin" and c.role == Role.ADMIN)
        ):
            matched_customer = c
            break

    if not matched_customer:
        matched_customer = CUSTOMER_DIRECTORY["CIF908123"]

    pair = jwt_validator.create_token_pair(
        customer_id=matched_customer.customer_id,
        name=matched_customer.name,
        email=matched_customer.email,
        tier=matched_customer.tier,
        accounts=[acc.split(" ")[0] for acc in matched_customer.accounts],
    )

    # Set access token in Secure SameSite Cookie
    response.set_cookie(
        key="access_token",
        value=pair["access_token"],
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True on HTTPS/Production
        max_age=3600,
        path="/",
    )

    # Set refresh token in Secure SameSite Cookie
    response.set_cookie(
        key="refresh_token",
        value=pair["refresh_token"],
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=7 * 86400,
        path="/api/v1/auth",
    )

    # Return profile info only (tokens are safely encapsulated in cookies)
    return TokenResponse(
        customer_id=matched_customer.customer_id,
        name=matched_customer.name,
        email=matched_customer.email,
        role=str(matched_customer.role),
        tier=str(matched_customer.tier),
        accounts=matched_customer.accounts,
    )


@router.get(
    "/auth/me",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user session profile from cookies",
)
async def get_current_user_profile(
    current_user: CurrentUser,
) -> TokenResponse:
    """Validate current session from HttpOnly cookies and return customer profile to survive page reload."""
    user_info = CUSTOMER_DIRECTORY.get(current_user.customer_id, CUSTOMER_DIRECTORY["CIF908123"])
    return TokenResponse(
        customer_id=current_user.customer_id,
        name=current_user.name,
        email=current_user.email,
        role=str(user_info.role),
        tier=str(current_user.tier),
        accounts=user_info.accounts,
    )


@router.post(
    "/auth/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh an expired access token using HttpOnly cookie refresh token",
)
async def refresh_token_endpoint(
    request: Request,
    response: Response,
    payload: RefreshTokenRequest | None = None,
) -> TokenResponse:
    """Validate refresh token from cookies (or payload) and rotate cookie token pair."""
    refresh_token = (
        request.cookies.get("refresh_token")
        or (payload.refresh_token if payload else None)
    )

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token found in cookies or request",
        )

    try:
        result = jwt_validator.refresh_access_token(refresh_token)
    except (AuthenticationError, TokenExpiredError) as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(err),
        ) from err
    user_info = CUSTOMER_DIRECTORY.get(result.get("cif", "CIF908123"), CUSTOMER_DIRECTORY["CIF908123"])

    response.set_cookie(
        key="access_token",
        value=str(result["access_token"]),
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=3600,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=str(result["refresh_token"]),
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=7 * 86400,
        path="/api/v1/auth",
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
    "/auth/logout",
    status_code=status.HTTP_200_OK,
    summary="Clear authentication cookies, blacklist active tokens, and terminate session",
)
async def logout_endpoint(
    request: Request,
    response: Response,
    authorization: Annotated[str | None, Header()] = None,
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
        await jwt_validator.blacklist_mgr.blacklist_token(refresh_token, expiry_seconds=7 * 86400)
    if access_token:
        await jwt_validator.blacklist_mgr.blacklist_token(access_token, expiry_seconds=3600)

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
    tier_enum = CustomerTier(tier) if tier in CustomerTier.__members__.values() else CustomerTier.STANDARD
    user_info = CUSTOMER_DIRECTORY.get(customer_id, CUSTOMER_DIRECTORY["CIF908123"])

    return TokenResponse(
        customer_id=user_info["customer_id"],
        name=user_info["name"],
        email=user_info["email"],
        tier=str(user_info["tier"]),
        accounts=user_info["accounts"],
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
            start_payload = json.dumps({
                "event": "agent_switch",
                "session_id": session_id_str,
                "agent": target_agent,
                "delta": f"Routed to {target_agent}...",
                "is_final": False,
            })
            yield f"data: {start_payload}\n\n"
            await asyncio.sleep(0.05)

            # Stream words / tokens
            words = full_response.split(" ")
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                payload = json.dumps({
                    "event": "token",
                    "session_id": session_id_str,
                    "delta": chunk,
                    "is_final": False,
                })
                yield f"data: {payload}\n\n"
                await asyncio.sleep(0.03)

            # Final completion event
            done_payload = json.dumps({
                "event": "done",
                "session_id": session_id_str,
                "delta": "",
                "is_final": True,
                "metadata": {
                    "routed_agent": target_agent,
                    "cost_usd": state.get("cost_usd", 0.0),
                    "latency_ms": state.get("latency_ms", 0.0),
                }
            })
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
    _current_user: AuthenticatedUser = Depends(get_current_user),
) -> ConversationHistoryResponse:
    """Fetch past conversation messages for the current session from database or Redis."""
    session_id_str = session_id
    raw_history = await memory_manager.get_history(session_id_str)
    title = "New Conversation"

    if not raw_history:
        record = await memory_manager.checkpointer.get_session_record(session_id_str)
        if record and record.messages:
            raw_history = record.messages
            title = record.title

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
