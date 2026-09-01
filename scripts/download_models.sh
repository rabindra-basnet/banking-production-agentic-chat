#!/usr/bin/env bash
set -euo pipefail

# Downloads the spaCy NLP models required by presidio-based PII detection.
# Models are placed in ./models (gitignored) and loaded at runtime via
# src/banking_chat/core/config/constants.py -> NLP_MODELS_DIR / SPACY_MODEL_LG.
#
# Usage: ./scripts/download_models.sh

command -v uv >/dev/null 2>&1 || { echo "uv is required. Install: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }

MODEL="${1:-en_core_web_lg}"
TARGET="models"

echo "Downloading spaCy model '$MODEL' into ./$TARGET ..."
uv run python -m spacy download "$MODEL" --target "$TARGET"

echo "✅ Model '$MODEL' ready in ./$TARGET"
echo "   To use: SPACY run the app; PII detection loads it from $TARGET."
