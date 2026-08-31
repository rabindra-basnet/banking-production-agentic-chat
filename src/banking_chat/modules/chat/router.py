"""FastAPI router endpoints for chat interactions, authentication, history, and health checks."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, status

from banking_chat.core.common.types import AuthenticatedUser
from banking_chat.modules.auth.jwt_validator import JWTValidator
from banking_chat.modules.auth.middleware import CurrentUser, get_current_user
from banking_chat.modules.auth.models import RefreshTokenRequest, TokenResponse
from banking_chat.modules.chat.graph import ChatPipeline
from banking_chat.modules.chat.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ConversationHistoryResponse,
    HealthResponse,
)
from banking_chat.modules.session_memory.conversation import ConversationMemoryManager

router = APIRouter(tags=["Chat & Authentication"])
memory_manager = ConversationMemoryManager()
pipeline = ChatPipeline(memory_manager=memory_manager)
jwt_validator = JWTValidator()


@router.post(
    "/auth/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh an expired access token using a valid refresh token",
)
async def refresh_token_endpoint(
    payload: RefreshTokenRequest,
) -> TokenResponse:
    """Validate refresh token and issue a new access token and rotated refresh token."""
    result = jwt_validator.refresh_access_token(payload.refresh_token)
    return TokenResponse.model_validate(result)


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a chat message to the banking assistant",
)
async def chat_endpoint(
    request: ChatRequest,
    current_user: CurrentUser,
) -> ChatResponse:
    """Process incoming chat query through PII filter, Coordinator, and Domain Agents."""
    session_uuid = request.session_id or uuid4()
    session_id_str = str(session_uuid)

    state = await pipeline.execute(
        session_id=session_id_str,
        user_message=request.message,
        user=current_user,
    )

    return ChatResponse(
        session_id=session_uuid,
        message=state.get("final_response", ""),
        routed_agent=state.get("target_agent", "accounts_agent"),
        cost_usd=state.get("cost_usd", 0.0),
        latency_ms=state.get("latency_ms", 0.0),
    )


@router.get(
    "/history/{session_id}",
    response_model=ConversationHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve session message history",
)
async def get_chat_history(
    session_id: UUID,
    _current_user: AuthenticatedUser = Depends(get_current_user),
) -> ConversationHistoryResponse:
    """Fetch past conversation messages for the current session."""
    raw_history = await memory_manager.get_history(str(session_id))
    messages = [
        ChatMessage(
            role=m.get("role", "user"),
            content=m.get("content", ""),
            metadata={k: v for k, v in m.items() if k not in ("role", "content")},
        )
        for m in raw_history
    ]
    return ConversationHistoryResponse(session_id=session_id, messages=messages)


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
