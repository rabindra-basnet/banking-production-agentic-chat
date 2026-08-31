"""Production Gunicorn Configuration for Banking Production Agentic Chat."""

import multiprocessing
import os

# Server socket
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")
backlog = int(os.getenv("GUNICORN_BACKLOG", "2048"))

# Worker processes (Vertical scaling: auto-calculated from CPU cores or env override)
workers = int(os.getenv("WEB_CONCURRENCY", str(max(2, multiprocessing.cpu_count() * 2))))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = int(os.getenv("GUNICORN_WORKER_CONNECTIONS", "1000"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
capture_output = True

# Process naming
proc_name = "banking_chat_api"
