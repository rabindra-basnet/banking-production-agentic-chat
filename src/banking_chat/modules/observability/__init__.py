"""Observability, Telemetry, and Monitoring Feature Slice module."""

from __future__ import annotations

from banking_chat.modules.observability.ai_logger import AIAuditLogger
from banking_chat.modules.observability.cost_monitor import CostMonitor
from banking_chat.modules.observability.metrics import (
    CHAT_LATENCY_SECONDS,
    CHAT_REQUEST_COUNT,
    LLM_INFERENCE_LATENCY_SECONDS,
    PII_DETECTIONS_COUNT,
    ROUTING_DECISIONS_COUNT,
    TOOL_CALLS_COUNT,
)
from banking_chat.modules.observability.tracing import create_agent_span, get_tracer, setup_tracing

__all__ = [
    "CHAT_LATENCY_SECONDS",
    "CHAT_REQUEST_COUNT",
    "LLM_INFERENCE_LATENCY_SECONDS",
    "PII_DETECTIONS_COUNT",
    "ROUTING_DECISIONS_COUNT",
    "TOOL_CALLS_COUNT",
    "AIAuditLogger",
    "CostMonitor",
    "create_agent_span",
    "get_tracer",
    "setup_tracing",
]
