"""Tests for PII leakage prevention."""

from __future__ import annotations

import pytest

from banking_chat.core.common.types import AuthenticatedUser
from banking_chat.modules.llm_gateway.router import LLMRouter
from banking_chat.modules.pii_guard.detector import PIIDetector


@pytest.mark.asyncio
async def test_pii_leakage_block(standard_user: AuthenticatedUser) -> None:
    router = LLMRouter()
    messages = [{"role": "user", "content": "My PAN is ABCDE1234F"}]
    # Should use self-hosted and NOT raise PIILeakageError
    content, _cost = await router.route_and_generate(messages, standard_user, prefer_cloud=False)
    assert len(content) > 0


def test_pii_leakage_exception() -> None:
    detector = PIIDetector()
    res = detector.detect("Aadhaar: 2345 6789 0123")
    assert res.has_pii is True
    assert "IN_AADHAAR" in res.entity_counts
