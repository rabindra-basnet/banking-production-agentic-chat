"""OpenTelemetry distributed tracing configuration and span utilities."""

from __future__ import annotations

from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider

from banking_chat.core.config.settings import get_settings


def setup_tracing() -> None:
    """Initialize OpenTelemetry tracer provider."""
    settings = get_settings()
    resource = Resource(attributes={SERVICE_NAME: settings.otel_service_name})
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)


def get_tracer(name: str = "banking_chat") -> trace.Tracer:
    """Get named tracer instance."""
    return trace.get_tracer(name)


def create_agent_span(agent_name: str, **attributes: Any) -> Any:
    """Context manager for tracing agent execution steps."""
    tracer = get_tracer("banking_chat.agents")
    return tracer.start_as_current_span(f"agent.{agent_name}", attributes=attributes)
