#!/bin/bash
# Query ChromaDB helper script
# Activates virtual environment and runs the Python query script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Check if virtual environment exists
if [ -d "$PROJECT_ROOT/.venv-native" ]; then
    source "$PROJECT_ROOT/.venv-native/bin/activate"
    python3 "$SCRIPT_DIR/query-chromadb.py" "$@"
else
    echo "❌ Virtual environment not found at $PROJECT_ROOT/.venv-native"
    echo "Run: python3 -m venv .venv-native && source .venv-native/bin/activate && pip install -r requirements.txt"
    exit 1
fi
