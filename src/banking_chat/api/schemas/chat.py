"""Chat request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from banking_chat.common.utils import utc_now


class ChatMessage(BaseModel):
    """A single message in the conversation."""

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] | None = None


class ChatRequest(BaseModel):
    """Incoming chat request from the UI."""

    message: str = Field(min_length=1, max_length=2000, description="User's message")
    session_id: UUID = Field(description="Chat session identifier")
    stream: bool = Field(default=True, description="Whether to stream the response via SSE")


class ChatResponse(BaseModel):
    """Chat response (non-streaming)."""

    session_id: UUID
    message: str
    agent_used: str = Field(description="Which agent handled this query")
    tools_called: list[str] = Field(default_factory=list, description="Tools invoked")
    latency_ms: int = Field(description="Response latency in milliseconds")
    cost_usd: float = Field(description="Estimated cost of this interaction")


class StreamChunk(BaseModel):
    """SSE streaming chunk."""

    event: Literal["token", "tool_call", "agent_switch", "done", "error"]
    data: str
    metadata: dict[str, Any] | None = None


class ChatFeedback(BaseModel):
    """User feedback on a chat response."""

    session_id: UUID
    message_id: str
    rating: int = Field(ge=1, le=5, description="Rating from 1-5")
    comment: str | None = Field(default=None, max_length=500)
