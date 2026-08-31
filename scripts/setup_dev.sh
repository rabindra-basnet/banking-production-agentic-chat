#!/usr/bin/env bash
set -euo pipefail

echo "🏦 Setting up Banking Agentic Chat development environment..."

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required"; exit 1; }
command -v uv >/dev/null 2>&1 || { echo "uv is required. Install: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }

# Install dependencies
echo "📦 Installing dependencies..."
uv sync --all-extras

# Install pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
uv run pre-commit install

# Copy env file if not exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
fi

echo "✅ Development environment ready!"
echo "   Run: make run"
