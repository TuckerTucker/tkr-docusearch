#!/bin/bash
# DocuSearch MVP - API Server Startup Script
#
# Starts the FastAPI REST API server

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "=================================================="
echo "🚀 DocuSearch API - Starting REST API Server"
echo "=================================================="
echo ""

# Parse arguments
PORT=${1:-8002}
RELOAD=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --reload)
            RELOAD="--reload"
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Check Python environment
echo -e "${BLUE}[1/4] Checking Python environment...${NC}"
if [ ! -f "start_env" ]; then
    echo -e "${RED}❌ start_env not found. Run ./quick-start.sh first.${NC}"
    exit 1
fi
source start_env
echo "✓ Python environment activated"
echo ""

# Check dependencies
echo -e "${BLUE}[2/4] Checking API dependencies...${NC}"
if ! python -c "import fastapi, uvicorn" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  FastAPI not installed. Installing...${NC}"
    pip install fastapi uvicorn[standard] python-multipart
fi
echo "✓ API dependencies available"
echo ""

# Check ChromaDB
echo -e "${BLUE}[3/4] Checking ChromaDB connection...${NC}"
if ! curl -s http://localhost:8001/api/v2/heartbeat > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  ChromaDB not responding. Starting ChromaDB...${NC}"
    cd docker && docker-compose up -d chromadb && cd ..
    echo "  Waiting for ChromaDB..."
    for i in {1..30}; do
        if curl -s http://localhost:8001/api/v2/heartbeat > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done
fi
echo "✓ ChromaDB connected (localhost:8001)"
echo ""

# Start API server
echo -e "${BLUE}[4/4] Starting API server...${NC}"
echo ""
echo -e "${GREEN}API server starting on http://localhost:${PORT}${NC}"
echo ""
echo "📚 Documentation:"
echo "  • Swagger UI: http://localhost:${PORT}/docs"
echo "  • ReDoc:      http://localhost:${PORT}/redoc"
echo ""
echo "🔌 Endpoints:"
echo "  • GET  /health          - Health check"
echo "  • GET  /status          - System status"
echo "  • POST /search          - Search documents"
echo "  • GET  /search?q=...    - Search via GET"
echo "  • POST /upload          - Upload document"
echo "  • GET  /stats/search    - Search statistics"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run with uvicorn
python -m uvicorn src.api.server:app \
    --host 0.0.0.0 \
    --port ${PORT} \
    ${RELOAD}
