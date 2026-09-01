"""FastAPI Dependency Injection providers for Chat Pipeline, Memory Managers, and Validators."""

from __future__ import annotations

from functools import lru_cache

from banking_chat.core.common.idempotency import IdempotencyManager
from banking_chat.modules.auth.jwt_validator import JWTValidator
from banking_chat.modules.chat.graph import ChatPipeline
from banking_chat.modules.session_memory.conversation import ConversationMemoryManager


@lru_cache(maxsize=1)
def get_memory_manager() -> ConversationMemoryManager:
    """Dependency injector for ConversationMemoryManager (Thread-safe singleton)."""
    return ConversationMemoryManager()


@lru_cache(maxsize=1)
def get_chat_pipeline() -> ChatPipeline:
    """Dependency injector for ChatPipeline."""
    return ChatPipeline(memory_manager=get_memory_manager())


@lru_cache(maxsize=1)
def get_jwt_validator() -> JWTValidator:
    """Dependency injector for JWTValidator."""
    return JWTValidator()


@lru_cache(maxsize=1)
def get_idempotency_manager() -> IdempotencyManager:
    """Dependency injector for IdempotencyManager."""
    return IdempotencyManager()
