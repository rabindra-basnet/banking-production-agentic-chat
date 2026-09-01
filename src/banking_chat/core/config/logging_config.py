"""Production-ready modular file logging with clean, readable single-line format per module."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, date, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any
from uuid import UUID

# Clean, human-readable single-line format
LOG_LINE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

MODULE_LOG_MAP = {
    "access": ["banking_chat.access"],
    "auth": ["banking_chat.modules.auth", "banking_chat.security"],
    "chat": ["banking_chat.modules.chat", "banking_chat.modules.session_memory"],
    "accounts": ["banking_chat.modules.accounts", "banking_chat.mcp.accounts"],
    "transactions": ["banking_chat.modules.transactions", "banking_chat.mcp.transactions"],
    "services": ["banking_chat.modules.services", "banking_chat.mcp.services"],
    "db": ["sqlalchemy.engine", "banking_chat.core.db"],
    "llm": [
        "banking_chat.modules.llm_gateway",
        "banking_chat.modules.pii_guard",
        "banking_chat.modules.session_memory.redis",
    ],
}


class JSONFormatter(logging.Formatter):
    """Formats log records as structured JSON lines for SIEM/audit ingestion when requested."""

    @staticmethod
    def _normalize_value(val: Any) -> Any:
        if isinstance(val, (datetime, date)):
            return val.isoformat()
        if isinstance(val, UUID):
            return str(val)
        if isinstance(val, (int, float, bool, str)) or val is None:
            return val
        if isinstance(val, (list, tuple, set)):
            return [JSONFormatter._normalize_value(x) for x in val]
        if isinstance(val, dict):
            return {str(k): JSONFormatter._normalize_value(v) for k, v in val.items()}
        return str(val)

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
        for field in ("request_id", "session_id", "customer_id", "agent", "idempotency_key", "tier"):
            if hasattr(record, field):
                log_obj[field] = self._normalize_value(getattr(record, field))
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logging(
    log_level: str = "INFO",
    json_output: bool = False,
    log_dir: str = "logs",
) -> None:
    """Configure comprehensive clean modular line logging separated by module files.

    Files generated in logs/:
      - logs/app.log (All application logs in clean single line format)
      - logs/error.log (Errors and stack traces)
      - logs/auth.log (Authentication & Token Blacklist operations)
      - logs/chat.log (Chat pipelines & SSE Streaming)
      - logs/accounts.log (Accounts queries & MCP calls)
      - logs/transactions.log (Fonepay, ConnectIPS, transfer events)
      - logs/services.log (Cheque book, card protection, disputes)
      - logs/db.log (Database engine & session queries)
      - logs/llm.log (LLM Gateway routing & PII guard events)
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Standard clean human-readable single-line formatter
    line_formatter = logging.Formatter(LOG_LINE_FORMAT, datefmt=DATE_FORMAT)

    # 1. Console Stream Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(line_formatter)

    # 2. Main App Log (Unified clean single line)
    app_handler = RotatingFileHandler(
        log_path / "app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    app_handler.setFormatter(line_formatter)

    # 3. Error Log File
    error_handler = RotatingFileHandler(
        log_path / "error.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(line_formatter)

    # Exclude verbose DB query engine logs from app.log (diverted strictly to logs/db.log if needed)
    app_handler.addFilter(lambda record: not record.name.startswith("sqlalchemy.engine"))

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [console_handler, app_handler, error_handler]

    # 4. Attach Dedicated Modular Loggers: logs/{module}.log
    for module_name, logger_prefixes in MODULE_LOG_MAP.items():
        module_file_handler = RotatingFileHandler(
            log_path / f"{module_name}.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        module_file_handler.setFormatter(line_formatter)
        module_file_handler.setLevel(level)

        for prefix in logger_prefixes:
            target_logger = logging.getLogger(prefix)
            target_logger.addHandler(module_file_handler)

    # Suppress raw uvicorn.access, noisy SQL queries, and low-level transport engine logs
    for logger_name in (
        "uvicorn.access",
        "sqlalchemy.engine",
        "sqlalchemy.pool",
        "sqlalchemy.dialects",
        "httpx",
        "httpcore",
        "urllib3",
        "asyncio",
        "aiosqlite",
    ):
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    # Disable uvicorn raw access logger to prevent log pollution and duplicate logs
    logging.getLogger("uvicorn.access").disabled = True

    logging.getLogger("banking_chat").setLevel(level)
