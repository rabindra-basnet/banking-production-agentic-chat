"""Application-wide constants."""

from __future__ import annotations

# API Versioning
API_V1_PREFIX = "/api/v1"

# Agent Names
COORDINATOR_AGENT = "coordinator_agent"
ACCOUNTS_AGENT = "accounts_agent"
TRANSACTION_AGENT = "transaction_agent"
SERVICE_AGENT = "service_agent"

# MCP Server Names
ACCOUNTS_MCP = "banking-accounts-mcp"
TRANSACTIONS_MCP = "banking-transactions-mcp"
SERVICES_MCP = "banking-services-mcp"

# Session
DEFAULT_SESSION_TTL = 1800  # 30 minutes
MAX_CONVERSATION_HISTORY = 50  # Max messages to retain
CHECKPOINT_INTERVAL = 5  # Checkpoint every N messages

# PII
PII_TOKEN_PREFIX = "{{PII_"
PII_TOKEN_SUFFIX = "}}"

# NLP Model Paths (presidio AnalyzerEngine / spaCy)
NLP_MODELS_DIR = "models"
SPACY_MODEL_LG = "en_core_web_lg"
SPACY_MODEL_SM = "en_core_web_sm"

# Cost
DEFAULT_COST_WARNING_THRESHOLD = 0.10
DEFAULT_COST_HARD_LIMIT = 0.50

# Rate Limiting
RATE_LIMIT_BURST_ALLOWANCE = 5
RATE_LIMIT_LOCKOUT_SECONDS = 300
