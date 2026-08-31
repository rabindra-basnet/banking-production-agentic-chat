#!/usr/bin/env bash
set -euo pipefail

echo "🔒 Running security scans..."

echo "\n--- Bandit (SAST) ---"
uv run bandit -r src/ -c pyproject.toml || true

echo "\n--- Dependency Audit ---"
uv run pip-audit || true

echo "\n🔒 Security scan complete."
