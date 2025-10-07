#!/bin/bash
# DocuSearch MVP - Complete System Shutdown
#
# Stops all components: API Server, Docker containers

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "==================================================="
echo "🛑 DocuSearch MVP - System Shutdown"
echo "==================================================="
echo ""

# Stop API server
echo -e "${BLUE}[1/2] Stopping API server...${NC}"
if [ -f "data/logs/api.pid" ]; then
    API_PID=$(cat data/logs/api.pid)
    if kill $API_PID 2>/dev/null; then
        echo "  ✓ API server stopped (PID: $API_PID)"
        rm data/logs/api.pid
    else
        echo "  ⚠️  API server not running"
    fi
else
    # Try to find and kill by process name
    pkill -f "uvicorn src.api.server:app" && echo "  ✓ API server stopped" || echo "  ⚠️  API server not running"
fi
echo ""

# Stop Docker containers
echo -e "${BLUE}[2/2] Stopping Docker containers...${NC}"
cd docker
docker-compose down
cd ..
echo ""

echo -e "${GREEN}==================================================="
echo "✅ All services stopped"
echo "===================================================${NC}"
echo ""
echo "To restart:"
echo "  ./start-all.sh         # Full system"
echo "  ./start-ui.sh          # UI only"
echo "  ./start-api.sh         # API only"
echo "  ./quick-start.sh       # Core components"
echo ""
