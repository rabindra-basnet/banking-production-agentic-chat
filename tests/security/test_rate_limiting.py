"""Tests for rate limiting exceptions."""

from __future__ import annotations

from banking_chat.core.common.exceptions import RateLimitExceededError


def test_rate_limit_exception() -> None:
    err = RateLimitExceededError(retry_after_seconds=60)
    assert err.retry_after_seconds == 60
    assert err.code == "RATE_LIMITED"
