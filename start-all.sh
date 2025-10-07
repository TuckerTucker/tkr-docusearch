#!/bin/bash
# DocuSearch MVP - Complete System Startup
#
# Starts all components: ChromaDB, Copyparty UI, API Server, Processing Worker

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "==================================================="
echo "🚀 DocuSearch MVP - Complete System Startup"
echo "==================================================="
echo ""

# Parse arguments
AUTO_OPEN=true
START_WORKER=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-open)
            AUTO_OPEN=false
            shift
            ;;
        --no-worker)
            START_WORKER=false
            shift
            ;;
        *)
            echo "Usage: $0 [--no-open] [--no-worker]"
            echo ""
            echo "Options:"
            echo "  --no-open     Don't automatically open browser"
            echo "  --no-worker   Don't start processing worker"
            exit 1
            ;;
    esac
done

# Check Python environment
echo -e "${BLUE}[1/5] Checking Python environment...${NC}"
if [ ! -f "start_env" ]; then
    echo -e "${RED}❌ start_env not found. Run ./quick-start.sh first.${NC}"
    exit 1
fi
source start_env
echo "✓ Python environment activated"
echo ""

# Check Docker
echo -e "${BLUE}[2/5] Checking Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker Desktop.${NC}"
    exit 1
fi
echo "✓ Docker available"
echo ""

# Start Docker services
echo -e "${BLUE}[3/5] Starting Docker services...${NC}"
cd docker

if [ "$START_WORKER" = true ]; then
    echo "  Starting all services (ChromaDB + Copyparty + Worker)..."
    docker-compose up -d
else
    echo "  Starting core services (ChromaDB + Copyparty)..."
    docker-compose up -d chromadb copyparty
fi

echo ""
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
echo ""

# Wait for ChromaDB
echo -n "  ChromaDB (localhost:8001): "
for i in {1..30}; do
    if curl -s http://localhost:8001/api/v2/heartbeat > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}⚠️  Timeout (still starting)${NC}"
    fi
    sleep 1
done

# Wait for Copyparty
echo -n "  Copyparty UI (localhost:8000): "
for i in {1..30}; do
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}⚠️  Timeout (still starting)${NC}"
    fi
    sleep 1
done

# Check worker if enabled
if [ "$START_WORKER" = true ]; then
    echo -n "  Processing Worker: "
    sleep 3  # Give worker time to start
    if docker ps | grep -q docusearch-worker; then
        echo -e "${GREEN}✓ Running${NC}"
    else
        echo -e "${YELLOW}⚠️  Not running${NC}"
    fi
fi

cd ..

# Start API server in background
echo ""
echo -e "${BLUE}[4/5] Starting API server...${NC}"

# Kill existing API server if running
pkill -f "uvicorn src.api.server:app" 2>/dev/null || true

# Start API server in background
nohup python -m uvicorn src.api.server:app \
    --host 0.0.0.0 \
    --port 8002 \
    > data/logs/api.log 2>&1 &

API_PID=$!
echo "  API server started (PID: $API_PID)"

# Wait for API to be ready
echo -n "  API Server (localhost:8002): "
for i in {1..30}; do
    if curl -s http://localhost:8002/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}⚠️  Timeout (still starting)${NC}"
    fi
    sleep 1
done

# System ready
echo ""
echo -e "${GREEN}==================================================="
echo "✅ DocuSearch MVP is fully operational!"
echo "===================================================${NC}"
echo ""

# Show service status
echo "📊 Service Status:"
echo ""
docker ps --filter "name=docusearch" --format "  {{.Names}}: {{.Status}}" | grep -E "docusearch"
echo "  API Server: Running (PID: $API_PID)"
echo ""

echo "🌐 Access Points:"
echo ""
echo "  📤 File Upload:"
echo "     http://localhost:8000"
echo "     (Drag & drop PDF/DOCX/PPTX files)"
echo ""
echo "  🔍 Search Interface:"
echo "     http://localhost:8000/search.html"
echo "     (Search uploaded documents)"
echo ""
echo "  📈 Status Dashboard:"
echo "     http://localhost:8000/status_dashboard.html"
echo "     (View system status and metrics)"
echo ""
echo "  🔌 API Documentation:"
echo "     http://localhost:8002/docs"
echo "     (Swagger UI - REST API documentation)"
echo ""
echo "  📚 API Alternative Docs:"
echo "     http://localhost:8002/redoc"
echo "     (ReDoc - Alternative API documentation)"
echo ""

echo "⚙️  System Features:"
echo ""
if [ "$START_WORKER" = true ]; then
    echo "  ✓ Auto-processing enabled (upload triggers processing)"
    echo "  ✓ Background worker monitors uploads directory"
else
    echo "  ⚠️  Manual processing mode (worker not running)"
    echo "  → Process docs via API: POST http://localhost:8002/upload"
fi
echo "  ✓ Real-time semantic search (visual + text)"
echo "  ✓ ColPali embeddings with MPS acceleration"
echo "  ✓ Two-stage search (HNSW + MaxSim re-ranking)"
echo "  ✓ REST API with full documentation"
echo ""

echo "📝 Quick Guide:"
echo ""
echo "  1. Upload Documents:"
echo "     → Open http://localhost:8000"
echo "     → Drag and drop files or browse"
echo ""
if [ "$START_WORKER" = true ]; then
    echo "  2. Automatic Processing:"
    echo "     → Worker processes uploads automatically"
    echo "     → Monitor progress in status dashboard"
else
    echo "  2. Manual Processing:"
    echo "     → Use API endpoint: POST /upload"
    echo "     → Or start worker: ./start-all.sh"
fi
echo ""
echo "  3. Search Documents:"
echo "     → Open http://localhost:8000/search.html"
echo "     → Enter natural language query"
echo "     → View ranked results with scores"
echo ""

echo "🛠️  Management:"
echo ""
echo "  View logs:"
echo "    • ChromaDB:    docker logs docusearch-chromadb"
echo "    • Copyparty:   docker logs docusearch-copyparty"
if [ "$START_WORKER" = true ]; then
    echo "    • Worker:      docker logs docusearch-worker"
fi
echo "    • API Server:  tail -f data/logs/api.log"
echo ""
echo "  Stop all services:"
echo "    • Full shutdown:  ./stop-all.sh"
echo "    • Docker only:    cd docker && docker-compose down"
echo "    • API only:       kill $API_PID"
echo ""

# Save PID for stop script
echo $API_PID > data/logs/api.pid

# Auto-open browser
if [ "$AUTO_OPEN" = true ]; then
    echo -e "${BLUE}🌐 Opening browser...${NC}"
    echo ""
    sleep 2

    if command -v open &> /dev/null; then
        open http://localhost:8000
        echo "  ✓ Opened http://localhost:8000 in browser"
    elif command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8000
        echo "  ✓ Opened http://localhost:8000 in browser"
    else
        echo "  → Visit http://localhost:8000 in your browser"
    fi
fi

echo ""
echo -e "${GREEN}🎉 DocuSearch MVP ready to use!${NC}"
echo ""
echo "Press Ctrl+C to stop (or run ./stop-all.sh)"
echo ""

# Keep script running
tail -f data/logs/api.log
