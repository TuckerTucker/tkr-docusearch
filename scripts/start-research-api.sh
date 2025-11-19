#!/bin/bash
# Start the Research API server

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

VENV_DIR=".venv-native"
PID_FILE=".research-api.pid"
LOG_FILE="logs/research-api.log"

echo -e "${BLUE}Starting Research API...${NC}"

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}✗ Virtual environment not found at $VENV_DIR${NC}"
    echo -e "${YELLOW}  Run: ./scripts/run-worker-native.sh setup${NC}"
    exit 1
fi

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠ Research API already running (PID: $OLD_PID)${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠ Removing stale PID file${NC}"
        rm -f "$PID_FILE"
    fi
fi

# Create logs directory
mkdir -p logs

# Check environment variables
if [ -z "$LLM_PROVIDER" ] && [ -z "$(grep -E '^LLM_PROVIDER=' .env 2>/dev/null)" ]; then
    echo -e "${YELLOW}⚠ Warning: LLM_PROVIDER not set in .env${NC}"
    echo -e "${YELLOW}  Defaulting to 'openai'${NC}"
fi

# Load environment
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Verify API key is set
PROVIDER="${LLM_PROVIDER:-openai}"
case "$PROVIDER" in
    openai)
        if [ -z "$OPENAI_API_KEY" ]; then
            echo -e "${RED}✗ OPENAI_API_KEY not set in .env${NC}"
            exit 1
        fi
        ;;
    anthropic)
        if [ -z "$ANTHROPIC_API_KEY" ]; then
            echo -e "${RED}✗ ANTHROPIC_API_KEY not set in .env${NC}"
            exit 1
        fi
        ;;
    google)
        if [ -z "$GOOGLE_API_KEY" ]; then
            echo -e "${RED}✗ GOOGLE_API_KEY not set in .env${NC}"
            exit 1
        fi
        ;;
esac

# Start the research API
echo -e "${BLUE}→ Starting Research API on port 8004...${NC}"
source "$VENV_DIR/bin/activate"

nohup uvicorn tkr_docusearch.api.research:app \
    --host 0.0.0.0 \
    --port 8004 \
    --log-level info \
    > "$LOG_FILE" 2>&1 &

RESEARCH_PID=$!
echo $RESEARCH_PID > "$PID_FILE"

# Wait a moment and verify it started
sleep 2

if ps -p $RESEARCH_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Research API started successfully${NC}"
    echo -e "${BLUE}  → PID:  $RESEARCH_PID${NC}"
    echo -e "${BLUE}  → URL:  http://localhost:8004${NC}"
    echo -e "${BLUE}  → Logs: $LOG_FILE${NC}"
    echo ""
    echo -e "${BLUE}Test the API:${NC}"
    echo -e "  curl http://localhost:8004/api/research/health"
else
    echo -e "${RED}✗ Research API failed to start${NC}"
    echo -e "${YELLOW}Check logs: tail -f $LOG_FILE${NC}"
    rm -f "$PID_FILE"
    exit 1
fi
