# 🏦 Banking Production Agentic Chat

Production-grade AI-powered customer support chatbot for banking organizations.

## Architecture

This system uses a **multi-agent architecture** with domain-specific sub-agents coordinated by a central orchestrator, integrated with bank APIs via **Model Context Protocol (MCP)** servers.

### Key Features
- 🤖 Multi-agent system (Coordinator → Accounts/Transaction/Service agents)
- 🔌 MCP servers for loosely coupled bank API integration
- 🔐 Layered security: Authentication, Authorization (RBAC), PII Redaction, Edge Protection
- 🧠 Hybrid LLM routing (self-hosted for sensitive data, third-party for complex reasoning)
- 💾 Session management with Redis + PostgreSQL checkpointing
- 📊 Full observability with OpenTelemetry + Langfuse
- 💸 Per-interaction cost tracking and budget control
- 🧪 AI evaluation suite with golden datasets

### Architecture Evolution
See [architecturedesigns/](architecturedesigns/) for the step-by-step evolution from simple chatbot to production system.

## Quick Start

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Redis (for sessions)
- PostgreSQL (for checkpoints)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd banking-production-agentic-chat

# Install dependencies
make install

# Copy environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the application
make run
```

### Development
```bash
# Run quality checks
make quality

# Run tests
make test

# Run security scan
make security-scan

# Format code
make format
```

## Project Structure & Code References

| Subsystem | Source Path | Description |
|---|---|---|
| **API Layer** | [`src/banking_chat/api/`](src/banking_chat/api/) | FastAPI application factory, routes ([`chat.py`](src/banking_chat/api/routes/chat.py), [`health.py`](src/banking_chat/api/routes/health.py)), middleware |
| **Agent Core** | [`src/banking_chat/agents/`](src/banking_chat/agents/) | Coordinator ([`coordinator/`](src/banking_chat/agents/coordinator/)), Accounts ([`accounts/`](src/banking_chat/agents/accounts/)), Transactions ([`transactions/`](src/banking_chat/agents/transactions/)), Services ([`services/`](src/banking_chat/agents/services/)) |
| **MCP Servers** | [`src/banking_chat/mcp_servers/`](src/banking_chat/mcp_servers/) | Decoupled FastMCP tools for [Accounts](src/banking_chat/mcp_servers/accounts/), [Transactions](src/banking_chat/mcp_servers/transactions/), and [Services](src/banking_chat/mcp_servers/services/) |
| **Security & PII** | [`src/banking_chat/security/`](src/banking_chat/security/) | [Authentication](src/banking_chat/security/authentication/), [RBAC](src/banking_chat/security/authorization/), Presidio [PII Redaction](src/banking_chat/security/pii/), and [Edge Protection](src/banking_chat/security/edge/) |
| **LLM Routing** | [`src/banking_chat/llm/`](src/banking_chat/llm/) | Hybrid router ([`router.py`](src/banking_chat/llm/router.py)), [Self-Hosted](src/banking_chat/llm/self_hosted/), [Third-Party](src/banking_chat/llm/third_party/), and Cost Tracker ([`cost_tracker.py`](src/banking_chat/llm/cost_tracker.py)) |
| **Session & State** | [`src/banking_chat/session/`](src/banking_chat/session/) | Redis state cache ([`redis_store.py`](src/banking_chat/session/redis_store.py)), conversation history ([`conversation.py`](src/banking_chat/session/conversation.py)), shared inter-agent state |
| **Observability** | [`src/banking_chat/observability/`](src/banking_chat/observability/) | OpenTelemetry traces ([`tracing.py`](src/banking_chat/observability/tracing.py)), Prometheus metrics ([`metrics.py`](src/banking_chat/observability/metrics.py)), and AI logger |
| **Configuration** | [`src/banking_chat/config/`](src/banking_chat/config/) | Pydantic Settings ([`settings.py`](src/banking_chat/config/settings.py)), Constants ([`constants.py`](src/banking_chat/config/constants.py)) |
| **Common Schemas** | [`src/banking_chat/common/`](src/banking_chat/common/) | Domain types & models ([`types.py`](src/banking_chat/common/types.py)), exceptions ([`exceptions.py`](src/banking_chat/common/exceptions.py)), validators |

## LLM Configuration (LangChain OpenAI / Compatible)

All LLM parameters are strictly driven by environment variables via [`Settings`](src/banking_chat/config/settings.py):

- **API Key**: `LLM_OPENAI_API_KEY`
- **Base URL**: `LLM_OPENAI_BASE_URL` (supports standard OpenAI, Azure, Groq, OpenRouter, or local proxies)
- **Model**: `LLM_OPENAI_MODEL` (e.g., `gpt-4o`, `llama3.1:8b`)
- **Self-Hosted Base URL**: `LLM_SELF_HOSTED_BASE_URL` (vLLM / Ollama endpoint)
- **Self-Hosted Model**: `LLM_SELF_HOSTED_MODEL`

## Documentation
- [Architecture Overview](docs/architecture/overview.md)
- [Step-by-Step Evolution](docs/architecture/step-by-step-evolution.md)
- [Architecture Decision Records (ADRs)](docs/architecture/decisions/)
- [Security Policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)
- [Learning Guides (Step 00 to 14)](docs/learning/)

## License
MIT License — see [LICENSE](LICENSE) for details.
