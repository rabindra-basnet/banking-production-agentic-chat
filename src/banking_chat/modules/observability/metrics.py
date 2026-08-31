"""Prometheus metrics collectors for banking chat application."""

from __future__ import annotations

from prometheus_client import Counter, Histogram

# Request & Error Metrics
CHAT_REQUEST_COUNT = Counter(
    "banking_chat_requests_total",
    "Total chat requests received",
    ["status", "tier"],
)

ROUTING_DECISIONS_COUNT = Counter(
    "banking_routing_decisions_total",
    "Total routing decisions made by coordinator",
    ["target_agent"],
)

TOOL_CALLS_COUNT = Counter(
    "banking_mcp_tool_calls_total",
    "Total MCP tool calls executed",
    ["server", "tool_name", "status"],
)

PII_DETECTIONS_COUNT = Counter(
    "banking_pii_detections_total",
    "Total PII entities detected",
    ["entity_type"],
)

# Latency Histograms
CHAT_LATENCY_SECONDS = Histogram(
    "banking_chat_latency_seconds",
    "Latency of chat request handling in seconds",
    ["target_agent"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

LLM_INFERENCE_LATENCY_SECONDS = Histogram(
    "banking_llm_inference_latency_seconds",
    "Latency of LLM inference calls in seconds",
    ["provider", "model"],
    buckets=[0.2, 0.5, 1.0, 2.0, 5.0, 15.0],
)
