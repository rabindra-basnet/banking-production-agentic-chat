"""Structured AI audit logger for compliance and debugging."""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger("banking_chat.ai_audit")


class AIAuditLogger:
    """Logs LLM and Agent operations with security and compliance metadata."""

    @staticmethod
    def log_interaction(
        session_id: str,
        customer_id: str,
        user_prompt: str,
        agent_response: str,
        agent_name: str,
        model_name: str,
        cost_usd: float,
        latency_ms: float,
        pii_detected: bool = False,
        **extra: Any,
    ) -> None:
        """Log an AI interaction event in structured JSON format."""
        event = {
            "event_type": "ai_interaction",
            "session_id": session_id,
            "customer_id": customer_id,
            "agent_name": agent_name,
            "model_name": model_name,
            "cost_usd": cost_usd,
            "latency_ms": round(latency_ms, 2),
            "pii_detected": pii_detected,
            "prompt_length": len(user_prompt),
            "response_length": len(agent_response),
            **extra,
        }
        logger.info(json.dumps(event))
