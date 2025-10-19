#!/bin/bash
################################################################################
# clear-caches.sh - Clear all Python and system caches
#
# Clears:
#   - Python __pycache__ directories
#   - .pyc and .pyo compiled files
#   - pytest cache
#   - Python import caches
#   - Killed Python processes to force fresh imports
#
# Usage:
#   ./scripts/clear-caches.sh           # Clear caches
#   ./scripts/clear-caches.sh --restart # Clear caches and restart services
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}🧹 Clearing Python Caches${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$PROJECT_ROOT"

# Stop services first if they're running
echo -e "${YELLOW}⏸️  Stopping services...${NC}"
if [ -f "$PROJECT_ROOT/.worker.pid" ]; then
    WORKER_PID=$(cat "$PROJECT_ROOT/.worker.pid")
    if kill -0 "$WORKER_PID" 2>/dev/null; then
        echo "  Stopping worker (PID: $WORKER_PID)"
        kill -9 "$WORKER_PID" 2>/dev/null || true
    fi
    rm -f "$PROJECT_ROOT/.worker.pid"
fi

# Kill any remaining Python processes on port 8002
if lsof -ti :8002 >/dev/null 2>&1; then
    echo "  Killing processes on port 8002"
    lsof -ti :8002 | xargs kill -9 2>/dev/null || true
fi

echo ""

# 1. Remove __pycache__ directories
echo -e "${YELLOW}📂 Removing __pycache__ directories...${NC}"
PYCACHE_COUNT=$(find . -type d -name __pycache__ 2>/dev/null | wc -l | tr -d ' ')
if [ "$PYCACHE_COUNT" -gt 0 ]; then
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    echo -e "${GREEN}  ✓ Removed $PYCACHE_COUNT __pycache__ directories${NC}"
else
    echo -e "${GREEN}  ✓ No __pycache__ directories found${NC}"
fi

# 2. Remove .pyc and .pyo files
echo -e "${YELLOW}🗑️  Removing .pyc and .pyo files...${NC}"
PYC_COUNT=$(find . -type f -name "*.pyc" -o -name "*.pyo" 2>/dev/null | wc -l | tr -d ' ')
if [ "$PYC_COUNT" -gt 0 ]; then
    find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete 2>/dev/null || true
    echo -e "${GREEN}  ✓ Removed $PYC_COUNT compiled Python files${NC}"
else
    echo -e "${GREEN}  ✓ No .pyc/.pyo files found${NC}"
fi

# 3. Remove pytest cache
echo -e "${YELLOW}🧪 Removing pytest cache...${NC}"
if [ -d ".pytest_cache" ]; then
    rm -rf .pytest_cache
    echo -e "${GREEN}  ✓ Removed .pytest_cache${NC}"
else
    echo -e "${GREEN}  ✓ No pytest cache found${NC}"
fi

# 4. Remove Python egg-info
echo -e "${YELLOW}🥚 Removing egg-info directories...${NC}"
EGG_COUNT=$(find . -type d -name "*.egg-info" 2>/dev/null | wc -l | tr -d ' ')
if [ "$EGG_COUNT" -gt 0 ]; then
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    echo -e "${GREEN}  ✓ Removed $EGG_COUNT egg-info directories${NC}"
else
    echo -e "${GREEN}  ✓ No egg-info directories found${NC}"
fi

# 5. Clear pip cache (optional, can be slow)
# Uncomment if needed:
# echo -e "${YELLOW}📦 Clearing pip cache...${NC}"
# pip cache purge 2>/dev/null || true
# echo -e "${GREEN}  ✓ Cleared pip cache${NC}"

echo ""
echo -e "${GREEN}✅ All caches cleared!${NC}"
echo ""

# Restart if requested
if [ "$1" == "--restart" ]; then
    echo -e "${BLUE}🔄 Restarting services...${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    sleep 1
    "$SCRIPT_DIR/start-all.sh"
else
    echo -e "${YELLOW}💡 Tip: Run './scripts/clear-caches.sh --restart' to clear caches and restart services${NC}"
fi
