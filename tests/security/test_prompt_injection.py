"""Tests for prompt injection sanitization."""

from __future__ import annotations

from banking_chat.core.common.validators import sanitize_user_input


def test_sanitize_user_input_control_characters() -> None:
    malicious = "Hello \x00\x08World!\x0b\x0c"
    cleaned = sanitize_user_input(malicious)
    assert cleaned == "Hello World!"


def test_sanitize_user_input_length_truncation() -> None:
    long_text = "A" * 3000
    cleaned = sanitize_user_input(long_text, max_length=500)
    assert len(cleaned) == 500
