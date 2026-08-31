"""Production Gunicorn Configuration Loader for Banking Production Agentic Chat.

Supports flexible YAML config resolution across container environments (e.g. `./gunicorn.yaml`,
`deploy/docker/gunicorn.yaml`, `/app/gunicorn.yaml`, or custom via `GUNICORN_YAML_CONFIG`).
"""

from __future__ import annotations

import multiprocessing
import os
from pathlib import Path
from typing import Any

import yaml


def _resolve_yaml_config_path() -> Path | None:
    """Resolve the YAML configuration file path by inspecting common container and local candidate locations."""
    # 1. Explicit environment variable
    env_override = os.getenv("GUNICORN_YAML_CONFIG")
    if env_override:
        p = Path(env_override)
        if p.exists():
            return p

    # 2. Candidate relative and standard container locations
    cwd = Path.cwd()
    package_dir = Path(__file__).resolve().parent
    repo_root = package_dir.parent.parent

    candidate_paths = [
        cwd / "gunicorn.yaml",  # ./gunicorn.yaml (e.g. in Docker working directory /app)
        cwd / "gunicorn.yml",  # ./gunicorn.yml
        cwd / "deploy" / "docker" / "gunicorn.yaml",  # Local dev execution from repository root
        repo_root / "deploy" / "docker" / "gunicorn.yaml",  # Project root deployment path
        Path("/app/gunicorn.yaml"),  # Standard container root path
        Path("/etc/banking-chat/gunicorn.yaml"),  # Production Linux system config path
    ]

    for candidate in candidate_paths:
        if candidate.exists():
            return candidate

    return None


YAML_PATH = _resolve_yaml_config_path()

# Default configuration values
cfg: dict[str, Any] = {
    "server": {"bind": "0.0.0.0:8000", "backlog": 2048, "proc_name": "banking_chat_api"},
    "workers": {
        "count": None,
        "worker_class": "uvicorn.workers.UvicornWorker",
        "worker_connections": 1000,
        "timeout": 120,
        "keepalive": 5,
    },
    "logging": {"accesslog": "-", "errorlog": "-", "loglevel": "info", "capture_output": True},
}

# Load YAML if present
if YAML_PATH and YAML_PATH.exists():
    try:
        with open(YAML_PATH, encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
            if isinstance(loaded, dict):
                for section in ("server", "workers", "logging"):
                    if section in loaded and isinstance(loaded[section], dict):
                        cfg[section].update(loaded[section])
    except Exception:
        pass

# ─── Server Socket ───
bind = os.getenv("GUNICORN_BIND", cfg["server"].get("bind", "0.0.0.0:8000"))
backlog = int(os.getenv("GUNICORN_BACKLOG", cfg["server"].get("backlog", 2048)))
proc_name = cfg["server"].get("proc_name", "banking_chat_api")

# ─── Worker Processes (Vertical Scaling) ───
_yaml_workers = cfg["workers"].get("count")
_default_workers = max(2, multiprocessing.cpu_count() * 2) if not _yaml_workers else int(_yaml_workers)
workers = int(os.getenv("WEB_CONCURRENCY", str(_default_workers)))
worker_class = cfg["workers"].get("worker_class", "uvicorn.workers.UvicornWorker")
worker_connections = int(os.getenv("GUNICORN_WORKER_CONNECTIONS", cfg["workers"].get("worker_connections", 1000)))
timeout = int(os.getenv("GUNICORN_TIMEOUT", cfg["workers"].get("timeout", 120)))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", cfg["workers"].get("keepalive", 5)))

# ─── Logging ───
accesslog = cfg["logging"].get("accesslog", "-")
errorlog = cfg["logging"].get("errorlog", "-")
loglevel = os.getenv("GUNICORN_LOG_LEVEL", cfg["logging"].get("loglevel", "info"))
capture_output = bool(cfg["logging"].get("capture_output", True))
