"""Chat endpoints — main conversation interface."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException

from banking_chat.api.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
) -> ChatResponse:
    """Process a chat message and return agent response.

    This endpoint handles the full pipeline:
    1. Authenticate user (via middleware)
    2. Redact PII from input
    3. Route to coordinator agent
    4. Return response with de-tokenized PII
    """
    # TODO: Implement full pipeline (Phase 1)
    raise HTTPException(status_code=501, detail="Chat endpoint not yet implemented")


@router.get("/chat/history/{session_id}")
async def get_chat_history(
    session_id: UUID,
) -> dict[str, Any]:
    """Retrieve conversation history for a session."""
    # TODO: Implement (Phase 4)
    raise HTTPException(status_code=501, detail="Not yet implemented")


@router.delete("/chat/session/{session_id}", status_code=204)
async def delete_session(
    session_id: UUID,
) -> None:
    """Delete a chat session and its history."""
    # TODO: Implement (Phase 4)
    raise HTTPException(status_code=501, detail="Not yet implemented")
