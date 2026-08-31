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

## Project Structure
```
src/banking_chat/
├── api/              # FastAPI application and routes
├── agents/           # AI agents (coordinator, accounts, transactions, services)
├── mcp_servers/      # MCP servers wrapping bank APIs
├── security/         # Authentication, authorization, PII redaction
├── llm/              # LLM integration (self-hosted + third-party)
├── session/          # Session and state management
├── observability/    # Metrics, tracing, AI logging
├── config/           # Configuration management
└── common/           # Shared types, exceptions, utilities
```

## Documentation
- [Architecture Overview](docs/architecture/overview.md)
- [Step-by-Step Evolution](docs/architecture/step-by-step-evolution.md)
- [Security Policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)
- [Learning Guides](docs/learning/)

## License
MIT License — see [LICENSE](LICENSE) for details.
