.PHONY: help install lint format type-check test test-unit test-integration security-scan run clean

# Default target
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ─── Setup ───

install: ## Install all dependencies
	uv sync --all-extras
	uv run pre-commit install

install-prod: ## Install production dependencies only
	uv sync

# ─── Code Quality ───

lint: ## Run ruff linter
	uv run ruff check src/ tests/

format: ## Format code with ruff
	uv run ruff format src/ tests/

format-check: ## Check code formatting without modifying
	uv run ruff format --check src/ tests/

type-check: ## Run mypy type checking
	uv run mypy src/

quality: lint format-check type-check ## Run all quality checks

# ─── Testing ───

test: ## Run all tests
	uv run pytest

test-unit: ## Run unit tests only
	uv run pytest tests/unit/ -v

test-integration: ## Run integration tests
	uv run pytest tests/integration/ -v -m integration

test-e2e: ## Run end-to-end tests
	uv run pytest tests/e2e/ -v -m e2e

test-security: ## Run security tests
	uv run pytest tests/security/ -v -m security

test-evaluation: ## Run AI evaluation suite
	uv run pytest tests/evaluation/ -v -m evaluation

test-cov: ## Run tests with coverage report
	uv run pytest --cov=src/banking_chat --cov-report=html --cov-report=term-missing

# ─── Security ───

security-scan: ## Run all security scans
	uv run bandit -r src/ -c pyproject.toml
	uv run pip-audit
	@echo "Security scan complete."

pre-commit-all: ## Run all pre-commit hooks
	uv run pre-commit run --all-files

# ─── Database Migrations (Alembic) ───

migrate: ## Run pending database migrations
	uv run alembic upgrade head

migration-generate: ## Generate a new Alembic migration (e.g. make migration-generate m="add accounts table")
	uv run alembic revision --autogenerate -m "$(m)"

migrate-down: ## Rollback last migration
	uv run alembic downgrade -1

migrate-history: ## View migration history
	uv run alembic history

# ─── Application & MCP Servers ───

run: ## Run the chat application (development)
	uv run uvicorn banking_chat.main:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Run the chat application (production)
	uv run uvicorn banking_chat.main:app --host 0.0.0.0 --port 8000 --workers 4

run-mcp-accounts: ## Run Accounts FastMCP standalone server (port 9001)
	uv run python src/banking_chat/mcp/accounts_server/main.py

run-mcp-transactions: ## Run Transactions FastMCP standalone server (port 9002)
	uv run python src/banking_chat/mcp/transactions_server/main.py

run-mcp-services: ## Run Services FastMCP standalone server (port 9003)
	uv run python src/banking_chat/mcp/services_server/main.py

# ─── Docker ───

docker-build: ## Build Docker image
	docker build -f deploy/docker/Dockerfile -t banking-agentic-chat .

docker-up: ## Start all services with Docker Compose
	docker compose -f deploy/docker/docker-compose.yml up -d

docker-down: ## Stop all services
	docker compose -f deploy/docker/docker-compose.yml down

# ─── Cleanup ───

clean: ## Clean build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name *.egg-info -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ .coverage
