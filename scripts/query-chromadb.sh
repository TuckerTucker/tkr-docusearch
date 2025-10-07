#!/bin/bash
# Query ChromaDB helper script
# Activates virtual environment and runs the Python query script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Check if virtual environment exists
if [ -d "$PROJECT_ROOT/tkr_env/project_env" ]; then
    source "$PROJECT_ROOT/tkr_env/project_env/bin/activate"
    python3 "$SCRIPT_DIR/query-chromadb.py" "$@"
else
    echo "❌ Virtual environment not found at $PROJECT_ROOT/tkr_env/project_env"
    echo "Run: ./scripts/run-worker-native.sh setup"
    exit 1
fi
