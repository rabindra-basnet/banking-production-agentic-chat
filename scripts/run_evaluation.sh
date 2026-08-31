#!/usr/bin/env bash
set -euo pipefail

echo "🧪 Running AI evaluation suite..."
uv run pytest tests/evaluation/ -v -m evaluation
echo "🧪 Evaluation complete."
