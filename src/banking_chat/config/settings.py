"""Application settings using Pydantic Settings for environment-based configuration."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="banking-agentic-chat", description="Application name")
    app_env: str = Field(default="development", description="Environment: development|staging|production")
    app_port: int = Field(default=8000, description="Application port")
    app_log_level: str = Field(default="INFO", description="Logging level")
    app_secret_key: str = Field(default="change-me-in-production", description="Secret key for signing")

    # Authentication
    auth_idp_issuer: str = Field(default="https://idp.bank.com/realms/banking", description="IdP issuer URL")
    auth_idp_jwks_url: str = Field(default="https://idp.bank.com/realms/banking/protocol/openid-connect/certs", description="JWKS URL")
    auth_idp_client_id: str = Field(default="banking-chat-app", description="OAuth2 client ID")
    auth_jwt_algorithm: str = Field(default="RS256", description="JWT algorithm")
    auth_token_expiry_minutes: int = Field(default=30, description="Token expiry in minutes")

    # LLM: Self-Hosted
    llm_self_hosted_base_url: str = Field(default="http://localhost:11434/v1", description="Self-hosted LLM base URL")
    llm_self_hosted_model: str = Field(default="llama3.1:8b", description="Self-hosted model name")
    llm_self_hosted_max_tokens: int = Field(default=2048, description="Max tokens for self-hosted LLM")
    llm_self_hosted_temperature: float = Field(default=0.1, description="Temperature for self-hosted LLM")

    # LLM: Third-Party
    llm_openai_api_key: str = Field(default="", description="OpenAI API key")
    llm_openai_model: str = Field(default="gpt-4o", description="OpenAI model")
    llm_openai_max_tokens: int = Field(default=2048, description="Max tokens for OpenAI")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    redis_session_ttl_seconds: int = Field(default=1800, description="Session TTL (30 min)")

    # PostgreSQL
    database_url: str = Field(default="postgresql+asyncpg://postgres:postgres@localhost:5432/banking_chat", description="Database URL")

    # MCP Servers
    mcp_accounts_url: str = Field(default="http://localhost:9001", description="Accounts MCP server URL")
    mcp_transactions_url: str = Field(default="http://localhost:9002", description="Transactions MCP server URL")
    mcp_services_url: str = Field(default="http://localhost:9003", description="Services MCP server URL")

    # Observability
    otel_exporter_endpoint: str = Field(default="http://localhost:4317", description="OTLP exporter endpoint")
    otel_service_name: str = Field(default="banking-agentic-chat", description="OTEL service name")
    langfuse_public_key: str = Field(default="", description="Langfuse public key")
    langfuse_secret_key: str = Field(default="", description="Langfuse secret key")
    langfuse_host: str = Field(default="https://cloud.langfuse.com", description="Langfuse host")

    # Cost Tracking
    cost_daily_budget_usd: float = Field(default=500.0, description="Daily LLM budget")
    cost_monthly_budget_usd: float = Field(default=10000.0, description="Monthly LLM budget")
    cost_per_interaction_warn_usd: float = Field(default=0.10, description="Per-interaction warning threshold")
    cost_per_interaction_limit_usd: float = Field(default=0.50, description="Per-interaction hard limit")

    # Rate Limiting
    rate_limit_standard_rpm: int = Field(default=20, description="Standard tier rate limit")
    rate_limit_premium_rpm: int = Field(default=40, description="Premium tier rate limit")
    rate_limit_privileged_rpm: int = Field(default=60, description="Privileged tier rate limit")


def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
