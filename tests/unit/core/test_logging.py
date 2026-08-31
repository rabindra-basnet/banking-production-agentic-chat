"""Unit tests for structured JSON logging and context normalization."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from uuid import uuid4

from banking_chat.core.config.logging_config import JSONFormatter, setup_logging


def test_json_formatter_normalization() -> None:
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test_file.py",
        lineno=42,
        msg="Transaction processed",
        args=(),
        exc_info=None,
    )

    req_id = uuid4()
    sess_id = uuid4()
    now = datetime.now(UTC)

    # Attach complex non-primitive context objects
    record.request_id = req_id  # type: ignore[attr-defined]
    record.session_id = sess_id  # type: ignore[attr-defined]
    record.customer_id = "CIF999888"  # type: ignore[attr-defined]
    record.agent = "coordinator_agent"  # type: ignore[attr-defined]
    record.created_at = now  # type: ignore[attr-defined]

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert parsed["message"] == "Transaction processed"
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test_logger"
    assert parsed["request_id"] == str(req_id)
    assert parsed["session_id"] == str(sess_id)
    assert parsed["customer_id"] == "CIF999888"
    assert parsed["agent"] == "coordinator_agent"


def test_setup_logging_initialization() -> None:
    setup_logging(log_level="DEBUG", json_output=True)
    logger = logging.getLogger("banking_chat")
    assert logger.level == logging.DEBUG
