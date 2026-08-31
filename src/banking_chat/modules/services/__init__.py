"""Customer Services Feature Slice module."""

from __future__ import annotations

from banking_chat.modules.services.agent import ServiceAgent
from banking_chat.modules.services.models import ServiceRequestModel
from banking_chat.modules.services.prompts import SERVICE_AGENT_SYSTEM_PROMPT
from banking_chat.modules.services.schemas import (
    BlockCardRequest,
    BlockCardResponse,
    CreateServiceRequestPayload,
    ServiceRequestListResponse,
)
from banking_chat.modules.services.service import CustomerServicesService
from banking_chat.modules.services.tools import ServicesTools

__all__ = [
    "SERVICE_AGENT_SYSTEM_PROMPT",
    "BlockCardRequest",
    "BlockCardResponse",
    "CreateServiceRequestPayload",
    "CustomerServicesService",
    "ServiceAgent",
    "ServiceRequestListResponse",
    "ServiceRequestModel",
    "ServicesTools",
]
