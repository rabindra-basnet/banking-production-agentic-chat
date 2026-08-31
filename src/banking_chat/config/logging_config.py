"""Structured logging configuration with JSON output for production."""

from __future__ import annotations

import logging
import sys


def setup_logging(log_level: str = "INFO", json_output: bool = False) -> None:
    """Configure structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        json_output: If True, output logs as JSON (for production).
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
    ]

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=handlers,
        force=True,
    )

    # Suppress noisy third-party loggers
    for logger_name in ("httpx", "httpcore", "urllib3", "asyncio"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)
