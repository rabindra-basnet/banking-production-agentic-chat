"""Production-ready structured logging with JSON formatter and correlation IDs."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    """Formats log records as structured JSON lines for enterprise SIEM ingestion."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "func_name": record.funcName,
            "line_no": record.lineno,
            "process": record.process,
            "thread": record.threadName,
        }

        # Include custom context fields if attached
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if hasattr(record, "session_id"):
            log_obj["session_id"] = record.session_id
        if hasattr(record, "customer_id"):
            log_obj["customer_id"] = record.customer_id
        if hasattr(record, "agent"):
            log_obj["agent"] = record.agent

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def setup_logging(log_level: str = "INFO", json_output: bool = True) -> None:
    """Configure comprehensive structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        json_output: If True, output logs as structured JSON lines (for production).
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    if json_output:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%SZ",
            )
        )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]

    # Suppress noisy third-party loggers while keeping application and MCP logs detailed
    for logger_name in ("httpx", "httpcore", "urllib3", "asyncio"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    logging.getLogger("banking_chat").setLevel(level)
    logging.getLogger("mcp").setLevel(level)
