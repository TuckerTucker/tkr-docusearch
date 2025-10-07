#!/bin/bash
# DocuSearch MVP - UI Startup Script
#
# This script starts the complete web UI for DocuSearch MVP
# including Copyparty file upload, search interface, and status dashboard

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "=================================================="
echo "🌐 DocuSearch MVP - Web UI Startup"
echo "=================================================="
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker Desktop.${NC}"
    exit 1
fi

# Parse options
AUTO_OPEN=true
FULL_STACK=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-open)
            AUTO_OPEN=false
            shift
            ;;
        --full)
            FULL_STACK=true
            shift
            ;;
        *)
            echo "Usage: $0 [--no-open] [--full]"
            echo ""
            echo "Options:"
            echo "  --no-open    Don't automatically open browser"
            echo "  --full       Start processing worker too"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}📋 Starting Docker services...${NC}"
echo ""

cd docker

if [ "$FULL_STACK" = true ]; then
    echo "  Starting full stack (ChromaDB + Copyparty + Worker)..."
    docker-compose up -d
else
    echo "  Starting UI services (ChromaDB + Copyparty)..."
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

# Check processing worker if full stack
if [ "$FULL_STACK" = true ]; then
    echo -n "  Processing Worker: "
    if docker ps | grep -q docusearch-worker; then
        echo -e "${GREEN}✓ Running${NC}"
    else
        echo -e "${YELLOW}⚠️  Not running${NC}"
    fi
fi

cd ..

echo ""
echo -e "${GREEN}=================================================="
echo "✅ Web UI is ready!"
echo "=================================================="
echo -e "${NC}"
echo ""

# Show service status
echo "📊 Service Status:"
docker ps --filter "name=docusearch" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "NAMES|docusearch"

echo ""
echo "🌐 Access Points:"
echo ""
echo "  📤 File Upload:"
echo "     http://localhost:8000"
echo "     (Drag & drop documents to upload)"
echo ""
echo "  🔍 Search Interface:"
echo "     http://localhost:8000/search.html"
echo "     (Search uploaded documents)"
echo ""
echo "  📈 Status Dashboard:"
echo "     http://localhost:8000/status_dashboard.html"
echo "     (View system status and metrics)"
echo ""

if [ "$FULL_STACK" = true ]; then
    echo "  ⚙️  Processing:"
    echo "     Auto-processing enabled (upload triggers processing)"
    echo ""
fi

echo "📚 Quick Guide:"
echo ""
echo "  1. Upload Documents:"
echo "     → Open http://localhost:8000"
echo "     → Drag and drop PDF/DOCX/PPTX files"
echo "     → Files are stored in data/uploads/"
echo ""

if [ "$FULL_STACK" = true ]; then
    echo "  2. Automatic Processing:"
    echo "     → Upload triggers processing worker"
    echo "     → Worker extracts text and images"
    echo "     → ColPali generates embeddings"
    echo "     → Stores in ChromaDB"
    echo ""
else
    echo "  2. Manual Processing (worker not running):"
    echo "     → Use Python API to process uploads"
    echo "     → See src/processing/processor.py"
    echo "     → Or start with: ./start-ui.sh --full"
    echo ""
fi

echo "  3. Search Documents:"
echo "     → Open http://localhost:8000/search.html"
echo "     → Enter search query"
echo "     → View ranked results with scores"
echo ""

echo "🛠️  Management:"
echo ""
echo "  View logs:"
echo "    docker logs docusearch-copyparty     # Copyparty"
echo "    docker logs docusearch-chromadb      # ChromaDB"
if [ "$FULL_STACK" = true ]; then
    echo "    docker logs docusearch-worker        # Worker"
fi
echo ""

echo "  Stop services:"
if [ "$FULL_STACK" = true ]; then
    echo "    cd docker && docker-compose down"
else
    echo "    cd docker && docker-compose down chromadb copyparty"
fi
echo ""

echo "  Restart a service:"
echo "    cd docker && docker-compose restart <service-name>"
echo ""

# Auto-open browser
if [ "$AUTO_OPEN" = true ]; then
    echo -e "${BLUE}🌐 Opening browser...${NC}"
    echo ""

    # Wait a moment for services to fully start
    sleep 2

    # Try to open browser (macOS)
    if command -v open &> /dev/null; then
        open http://localhost:8000
        echo "  ✓ Opened http://localhost:8000 in browser"
    # Linux
    elif command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8000
        echo "  ✓ Opened http://localhost:8000 in browser"
    else
        echo "  → Visit http://localhost:8000 in your browser"
    fi
fi

echo ""
echo -e "${GREEN}🎉 DocuSearch UI is ready to use!${NC}"
echo ""
