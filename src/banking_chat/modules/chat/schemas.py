"""Pydantic schemas for the Chat Orchestration API, Sessions, and SaaS App Config."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from banking_chat.core.common.types import StrictBaseModel


class AppConfigResponse(StrictBaseModel):
    """Dynamically configurable SaaS branding, institution names, and greeting metadata."""

    bank_name: str = Field(description="Institution Name (e.g. NepalBank AI, Global IME, Nabil Bank)")
    bank_tagline: str = Field(description="Institution Tagline")
    bank_badge: str = Field(description="Regulatory / Country Badge (e.g. NRB, MAS, RBI)")
    assistant_name: str = Field(description="Assistant Label (e.g. NepalBank Assistant)")
    compliance_notice: str = Field(description="Regulatory Compliance text")
    supported_services: str = Field(description="Supported services overview")


class ChatMessage(StrictBaseModel):
    """An individual message in a chat thread."""

    role: str = Field(description="Message role (user, assistant, system, tool)")
    content: str = Field(description="Message text content")
    timestamp: datetime | None = Field(default=None, description="Message timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional context/metadata")


class ChatSessionItem(StrictBaseModel):
    """Chat session metadata for user sidebar list."""

    id: str = Field(description="Session UUID string")
    title: str = Field(description="User-friendly auto-generated session title")
    created_at: datetime = Field(description="Session creation timestamp")
    updated_at: datetime = Field(description="Last message update timestamp")
    message_count: int = Field(default=0, description="Total messages in session")


class ChatSessionListResponse(StrictBaseModel):
    """List of chat sessions owned by the authenticated customer."""

    sessions: list[ChatSessionItem] = Field(default_factory=list, description="Customer chat sessions")


class ChatRequest(StrictBaseModel):
    """Incoming user chat request payload."""

    message: str = Field(min_length=1, max_length=2000, description="User's query")
    session_id: UUID | None = Field(default=None, description="Optional existing session ID")
    stream: bool = Field(default=False, description="Whether to stream the response via SSE")
    idempotency_key: str | None = Field(
        default=None,
        description="Unique request key to guarantee idempotent execution for sensitive banking requests",
    )


class ChatResponse(StrictBaseModel):
    """Outgoing chat response payload."""

    session_id: UUID = Field(description="Chat session ID")
    message: str = Field(description="Assistant's response text")
    routed_agent: str = Field(description="The specialist agent that handled the query")
    cost_usd: float = Field(default=0.0, description="Estimated interaction cost in USD")
    latency_ms: float = Field(default=0.0, description="Processing latency in milliseconds")
    idempotency_key: str | None = Field(default=None, description="Echoed idempotency key if provided")


class StreamChunk(StrictBaseModel):
    """Chunk delivered during streaming chat responses."""

    session_id: UUID = Field(description="Chat session ID")
    delta: str = Field(description="Incremental text token or chunk")
    is_final: bool = Field(default=False, description="Whether this is the last chunk in stream")


class ConversationHistoryResponse(StrictBaseModel):
    """Historical messages for a given session."""

    session_id: str = Field(description="Chat session ID string")
    title: str = Field(default="New Conversation", description="Session title")
    messages: list[ChatMessage] = Field(default_factory=list, description="List of past messages")


class HealthResponse(StrictBaseModel):
    """Health check payload."""

    status: str = Field(description="Service status")
    version: str = Field(description="Application version")
    timestamp: datetime = Field(description="Current server time")
