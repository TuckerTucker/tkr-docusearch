#!/bin/bash
# ============================================================================
# DocuSearch - Start All Services (macOS)
# ============================================================================
# Starts the complete DocuSearch stack with native Metal GPU support:
# - ChromaDB (Docker) - Vector database
# - Copyparty (Docker) - File upload server
# - Processing Worker (Native) - Document processing with Metal GPU
#
# Usage:
#   ./scripts/start-all.sh [--cpu|--gpu|--docker-only]
#
# Options:
#   --cpu          Run worker in Docker (CPU only, no setup needed)
#   --gpu          Run worker natively with Metal GPU (default, requires setup)
#   --docker-only  Start only Docker services (no worker)
# ============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Load environment variables
if [ -f "${PROJECT_ROOT}/.env" ]; then
    set -a
    source "${PROJECT_ROOT}/.env"
    set +a
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ============================================================================
# Configuration
# ============================================================================

MODE="${1:-gpu}"  # Default to GPU mode
FRONTEND_PORT=${VITE_FRONTEND_PORT:-42007}
ACTUAL_DEVICE=""  # Will be set to 'mps' or 'cpu' during worker startup
WORKER_PID_FILE="${PROJECT_ROOT}/.worker.pid"
FRONTEND_PID_FILE="${PROJECT_ROOT}/.frontend.pid"
NGROK_PID_FILE="${PROJECT_ROOT}/.ngrok.pid"
COMPOSE_DIR="${PROJECT_ROOT}/docker"
VISION_ENABLED=true  # Vision mode enabled by default

# ============================================================================
# Functions
# ============================================================================

print_header() {
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  ${CYAN}DocuSearch - Starting All Services${NC}                   ${BLUE}║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_status() {
    local service=$1
    local status=$2
    local message=$3

    if [ "$status" = "ok" ]; then
        echo -e "  ${GREEN}✓${NC} ${service}: ${message}"
    elif [ "$status" = "info" ]; then
        echo -e "  ${BLUE}ℹ${NC} ${service}: ${message}"
    elif [ "$status" = "warn" ]; then
        echo -e "  ${YELLOW}⚠${NC} ${service}: ${message}"
    else
        echo -e "  ${RED}✗${NC} ${service}: ${message}"
    fi
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker not found${NC}"
        echo "Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
        exit 1
    fi

    if ! docker info &> /dev/null 2>&1; then
        # Check if auto-start is enabled (default: true)
        local auto_start="${AUTO_START_DOCKER:-true}"

        if [ "$auto_start" = "true" ]; then
            echo -e "${YELLOW}Docker not running. Starting Docker Desktop...${NC}"

            # Start Docker Desktop (OS-specific)
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                open -a Docker
            elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
                # Linux
                echo -e "${YELLOW}Attempting to start Docker service...${NC}"
                if command -v systemctl &> /dev/null; then
                    sudo systemctl start docker
                else
                    echo -e "${RED}Error: Cannot auto-start Docker on this system${NC}"
                    echo "Please start Docker manually"
                    exit 1
                fi
            else
                echo -e "${RED}Error: Unsupported OS for auto-start${NC}"
                echo "Please start Docker Desktop manually"
                exit 1
            fi

            # Wait for Docker daemon to be ready
            echo -n "  Waiting for Docker daemon"
            local max_wait=60
            local waited=0

            while ! docker info &> /dev/null 2>&1; do
                if [ $waited -ge $max_wait ]; then
                    echo ""
                    echo -e "${RED}Error: Docker failed to start after ${max_wait}s${NC}"
                    echo "Please check Docker Desktop and try again"
                    echo ""
                    echo "Troubleshooting:"
                    echo "  1. Check if Docker Desktop is installed"
                    echo "  2. Try starting Docker Desktop manually"
                    echo "  3. Check system resources (CPU, memory)"
                    echo "  4. Set AUTO_START_DOCKER=false to disable auto-start"
                    exit 1
                fi

                echo -n "."
                sleep 2
                waited=$((waited + 2))
            done

            echo ""
            echo -e "${GREEN}✓ Docker started successfully (${waited}s)${NC}"

            # Give Docker a moment to stabilize
            sleep 3
        else
            echo -e "${RED}Error: Docker daemon not running${NC}"
            echo "Please start Docker Desktop or set AUTO_START_DOCKER=true in .env"
            exit 1
        fi
    fi
}

check_ports() {
    local ports=("8000" "8001" "8002" "8004" "$FRONTEND_PORT")
    local port_names=("Copyparty" "ChromaDB" "Worker" "Research API" "Frontend")

    for i in "${!ports[@]}"; do
        local port="${ports[$i]}"
        local name="${port_names[$i]}"

        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            local pid=$(lsof -Pi :$port -sTCP:LISTEN -t)
            print_status "$name port $port" "warn" "Already in use by PID $pid"
        fi
    done
}

start_docker_services() {
    echo -e "\n${CYAN}Starting Docker services...${NC}\n"

    cd "$COMPOSE_DIR"

    if [ "$MODE" = "gpu" ]; then
        # Use native worker override
        docker-compose -f docker-compose.yml -f docker-compose.native-worker.yml up -d
    else
        # Standard Docker setup (CPU worker)
        docker-compose up -d
    fi

    cd "$PROJECT_ROOT"

    # Wait for services to be ready
    echo -e "\n${CYAN}Waiting for services to be ready...${NC}\n"
    sleep 3

    # Check ChromaDB
    if curl -s http://localhost:8001/api/v2/heartbeat > /dev/null 2>&1; then
        print_status "ChromaDB" "ok" "Running on http://localhost:8001"
    else
        print_status "ChromaDB" "error" "Not responding"
    fi

    # Check Copyparty
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        print_status "Copyparty" "ok" "Running on http://localhost:8000"
    else
        print_status "Copyparty" "error" "Not responding"
    fi

    # Check worker (if in Docker mode)
    if [ "$MODE" = "cpu" ]; then
        if curl -s http://localhost:8002/health > /dev/null 2>&1; then
            print_status "Worker (Docker)" "ok" "Running on http://localhost:8002 (CPU)"
        else
            print_status "Worker (Docker)" "warn" "Starting..."
        fi
    fi
}

start_native_worker() {
    # Check Metal availability first
    echo -e "\n${CYAN}Checking Metal/MPS availability...${NC}\n"

    # Use the check from run-worker-native.sh
    if ./scripts/run-worker-native.sh check > /dev/null 2>&1; then
        ACTUAL_DEVICE="mps"
        echo -e "${GREEN}✓ Metal/MPS available - using GPU acceleration${NC}\n"
        echo -e "\n${CYAN}Starting native worker with Metal GPU...${NC}\n"
    else
        ACTUAL_DEVICE="cpu"
        echo -e "${YELLOW}⚠ Metal/MPS not available - falling back to CPU${NC}"
        echo -e "${YELLOW}Note: Worker will run in CPU mode (slower)${NC}\n"
        echo -e "\n${CYAN}Starting native worker (CPU mode)...${NC}\n"
    fi

    # Check if virtual environment exists
    if [ ! -d ".venv-native" ]; then
        echo -e "${YELLOW}Virtual environment not found. Running setup...${NC}\n"
        ./scripts/run-worker-native.sh setup
        echo ""
    fi

    # Check if worker is already running
    if [ -f "$WORKER_PID_FILE" ]; then
        local old_pid=$(cat "$WORKER_PID_FILE")
        if ps -p "$old_pid" > /dev/null 2>&1; then
            print_status "Worker" "warn" "Already running (PID: $old_pid)"
            return
        else
            rm -f "$WORKER_PID_FILE"
        fi
    fi

    # Check ChromaDB is running first
    if ! curl -s http://localhost:8001/api/v2/heartbeat > /dev/null 2>&1; then
        print_status "Worker (Native)" "error" "ChromaDB not running (required for worker)"
        return
    fi

    # Start worker in background using bash script
    # The script will handle venv activation and all environment setup
    nohup bash -c "cd '${PROJECT_ROOT}' && ./scripts/run-worker-native.sh run" > logs/worker-native.log 2>&1 &
    local worker_pid=$!
    echo $worker_pid > "$WORKER_PID_FILE"

    print_status "Worker" "info" "Starting... (PID: $worker_pid)"

    # Wait for worker to start (up to 15 seconds)
    local count=0
    local max_wait=15
    while [ $count -lt $max_wait ]; do
        if curl -s http://localhost:8002/health > /dev/null 2>&1; then
            if [ "$ACTUAL_DEVICE" = "mps" ]; then
                print_status "Worker (Native)" "ok" "Running on http://localhost:8002 (Metal GPU)"
            else
                print_status "Worker (Native)" "ok" "Running on http://localhost:8002 (CPU)"
            fi
            print_status "Worker PID" "info" "$worker_pid (saved to .worker.pid)"
            return
        fi
        sleep 1
        count=$((count + 1))
    done

    # Check if process is still running
    if ps -p "$worker_pid" > /dev/null 2>&1; then
        print_status "Worker (Native)" "warn" "Still starting... (check logs/worker-native.log)"
    else
        print_status "Worker (Native)" "error" "Failed to start (check logs/worker-native.log)"
        rm -f "$WORKER_PID_FILE"
    fi
}

start_ngrok() {
    echo -e "\n${CYAN}Starting ngrok tunnel (for vision mode)...${NC}\n"

    # Check if vision mode is disabled
    if [ "$VISION_ENABLED" = false ]; then
        print_status "Ngrok" "info" "Skipped (vision mode disabled)"
        return
    fi

    # Check if ngrok is installed
    if ! command -v ngrok &> /dev/null; then
        print_status "Ngrok" "warn" "Not installed (vision mode will be disabled)"
        echo -e "  ${YELLOW}ℹ${NC} Install: ${YELLOW}brew install ngrok${NC}"
        echo -e "  ${YELLOW}ℹ${NC} Docs: ${YELLOW}docs/RESEARCH_BOT_VISION_SETUP.md${NC}"
        return
    fi

    # Check if ngrok is already running
    if [ -f "$NGROK_PID_FILE" ]; then
        local old_pid=$(cat "$NGROK_PID_FILE")
        if ps -p "$old_pid" > /dev/null 2>&1; then
            # Verify it's actually tunneling the right port
            if pgrep -f "ngrok http 8002" > /dev/null 2>&1; then
                print_status "Ngrok" "warn" "Already running (PID: $old_pid)"

                # Get current URL
                local ngrok_url=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | jq -r '.tunnels[0].public_url' 2>/dev/null || echo "")
                if [ -n "$ngrok_url" ] && [ "$ngrok_url" != "null" ]; then
                    print_status "Ngrok URL" "ok" "$ngrok_url"

                    # Update .env with current URL
                    update_ngrok_url "$ngrok_url"
                fi
                return
            else
                # Stale PID file
                rm -f "$NGROK_PID_FILE"
            fi
        else
            rm -f "$NGROK_PID_FILE"
        fi
    fi

    # Check if Worker API is running (ngrok needs it for images)
    if ! curl -s http://localhost:8002/health > /dev/null 2>&1; then
        print_status "Ngrok" "error" "Worker API not running (required for ngrok)"
        return
    fi

    # Load NGROK_AUTHTOKEN from .env if present
    if [ -f .env ]; then
        local ngrok_token=$(grep "^NGROK_AUTHTOKEN=" .env 2>/dev/null | cut -d'=' -f2-)
        if [ -n "$ngrok_token" ] && [ "$ngrok_token" != "your-ngrok-authtoken-here" ]; then
            export NGROK_AUTHTOKEN="$ngrok_token"
        fi
    fi

    # Verify ngrok is configured (has authtoken)
    if ! ngrok config check &> /dev/null; then
        print_status "Ngrok" "warn" "Not configured (no authtoken)"
        echo -e "  ${YELLOW}ℹ${NC} Get token: ${BLUE}https://dashboard.ngrok.com/get-started/your-authtoken${NC}"
        echo -e "  ${YELLOW}ℹ${NC} Configure: ${YELLOW}ngrok config add-authtoken YOUR_TOKEN${NC}"
        echo -e "  ${YELLOW}ℹ${NC} Or add to .env: ${YELLOW}NGROK_AUTHTOKEN=your_token${NC}"
        return
    fi

    # Start ngrok tunnel to Worker API (port 8002) for image access
    print_status "Ngrok" "info" "Starting tunnel to port 8002..."
    nohup ngrok http 8002 > logs/ngrok.log 2>&1 &
    local ngrok_pid=$!
    echo $ngrok_pid > "$NGROK_PID_FILE"

    # Wait for ngrok to start (up to 10 seconds)
    local count=0
    local max_wait=10
    local ngrok_url=""

    while [ $count -lt $max_wait ]; do
        ngrok_url=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | jq -r '.tunnels[0].public_url' 2>/dev/null || echo "")

        if [ -n "$ngrok_url" ] && [ "$ngrok_url" != "null" ]; then
            print_status "Ngrok" "ok" "Running (PID: $ngrok_pid)"
            print_status "Ngrok URL" "ok" "$ngrok_url"

            # Update .env with new URL
            update_ngrok_url "$ngrok_url"

            print_status "Vision Mode" "ok" "Enabled (images accessible via ngrok)"
            return
        fi

        sleep 1
        count=$((count + 1))
    done

    # Failed to get URL
    if ps -p "$ngrok_pid" > /dev/null 2>&1; then
        print_status "Ngrok" "warn" "Started but URL not available yet (check logs/ngrok.log)"
    else
        print_status "Ngrok" "error" "Failed to start (check logs/ngrok.log)"
        rm -f "$NGROK_PID_FILE"
    fi
}

update_ngrok_url() {
    local ngrok_url="$1"

    if [ -z "$ngrok_url" ]; then
        return
    fi

    # Update or add NGROK_URL in .env
    if grep -q "^NGROK_URL=" .env 2>/dev/null; then
        # Update existing line (macOS compatible)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|^NGROK_URL=.*|NGROK_URL=$ngrok_url|" .env
        else
            sed -i "s|^NGROK_URL=.*|NGROK_URL=$ngrok_url|" .env
        fi
    else
        # Add new line
        echo "" >> .env
        echo "# Ngrok tunnel URL (auto-updated by start-all.sh)" >> .env
        echo "NGROK_URL=$ngrok_url" >> .env
    fi

    # Ensure RESEARCH_VISION_ENABLED is set to true
    if grep -q "^RESEARCH_VISION_ENABLED=" .env 2>/dev/null; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|^RESEARCH_VISION_ENABLED=.*|RESEARCH_VISION_ENABLED=true|" .env
        else
            sed -i "s|^RESEARCH_VISION_ENABLED=.*|RESEARCH_VISION_ENABLED=true|" .env
        fi
    else
        echo "RESEARCH_VISION_ENABLED=true" >> .env
    fi
}

start_research_api() {
    echo -e "\n${CYAN}Starting Research API...${NC}\n"

    if [ ! -d ".venv-native" ]; then
        echo -e "${YELLOW}Virtual environment not found. Skipping Research API.${NC}"
        return
    fi

    # Start research API
    ./scripts/start-research-api.sh

    # Check if started
    if [ -f ".research-api.pid" ]; then
        local api_pid=$(cat ".research-api.pid")
        print_status "Research API" "ok" "Running on http://localhost:8004 (PID: $api_pid)"
    else
        print_status "Research API" "warn" "Failed to start (check logs/research-api.log)"
    fi
}

start_frontend() {
    echo -e "\n${CYAN}Starting React Frontend...${NC}\n"

    # Check if frontend is already running
    if [ -f "$FRONTEND_PID_FILE" ]; then
        local old_pid=$(cat "$FRONTEND_PID_FILE")
        if ps -p "$old_pid" > /dev/null 2>&1; then
            print_status "Frontend" "warn" "Already running (PID: $old_pid)"
            return
        else
            rm -f "$FRONTEND_PID_FILE"
        fi
    fi

    # Wait for worker to be ready before starting frontend
    # Frontend proxy needs worker API to be available
    local max_wait=30
    local wait_count=0
    echo -e "${YELLOW}Waiting for worker API to be ready...${NC}"

    while [ $wait_count -lt $max_wait ]; do
        if curl -s http://localhost:8002/health > /dev/null 2>&1; then
            print_status "Worker API" "ok" "Ready"
            break
        fi
        sleep 1
        wait_count=$((wait_count + 1))
    done

    if [ $wait_count -ge $max_wait ]; then
        print_status "Worker API" "warn" "Not ready after ${max_wait}s, starting frontend anyway"
    fi

    # Check if node_modules exists
    if [ ! -d "frontend/node_modules" ]; then
        echo -e "${YELLOW}Installing frontend dependencies...${NC}"
        cd frontend
        npm install
        cd "$PROJECT_ROOT"
    fi

    # Start frontend dev server in background
    cd frontend
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    local frontend_pid=$!
    echo $frontend_pid > "$FRONTEND_PID_FILE"
    cd "$PROJECT_ROOT"

    # Wait for frontend to start
    sleep 3

    # Check if frontend is running
    if ps -p "$frontend_pid" > /dev/null 2>&1; then
        if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
            print_status "Frontend" "ok" "Running on http://localhost:$FRONTEND_PORT (React 19)"
            print_status "Frontend PID" "info" "$frontend_pid (saved to .frontend.pid)"
        else
            print_status "Frontend" "warn" "Starting... (check logs/frontend.log)"
        fi
    else
        print_status "Frontend" "error" "Failed to start (check logs/frontend.log)"
        rm -f "$FRONTEND_PID_FILE"
    fi
}

show_summary() {
    echo -e "\n${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  ${GREEN}Services Started Successfully${NC}                        ${BLUE}║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo -e "\n${CYAN}Available Services:${NC}"
    echo -e "  ${GREEN}→${NC} React Frontend:   ${BLUE}http://localhost:$FRONTEND_PORT${NC} (React 19)"
    echo -e "  ${GREEN}→${NC} Copyparty:        ${BLUE}http://localhost:8000${NC} (File upload)"
    echo -e "  ${GREEN}→${NC} ChromaDB:         ${BLUE}http://localhost:8001${NC}"
    echo -e "  ${GREEN}→${NC} Worker API:       ${BLUE}http://localhost:8002${NC}"
    echo -e "  ${GREEN}→${NC} Worker Status:    ${BLUE}http://localhost:8002/status${NC}"
    echo -e "  ${GREEN}→${NC} Research API:     ${BLUE}http://localhost:8004${NC}"

    if [ "$MODE" = "gpu" ]; then
        if [ "$ACTUAL_DEVICE" = "mps" ]; then
            echo -e "\n${CYAN}Worker Mode:${NC} ${GREEN}Native with Metal GPU (MPS)${NC}"
        elif [ "$ACTUAL_DEVICE" = "cpu" ]; then
            echo -e "\n${CYAN}Worker Mode:${NC} ${YELLOW}Native (CPU fallback - MPS unavailable)${NC}"
        else
            echo -e "\n${CYAN}Worker Mode:${NC} ${GREEN}Native${NC}"
        fi
        echo -e "  ${BLUE}ℹ${NC} Logs: ${YELLOW}logs/worker-native.log${NC}"
        echo -e "  ${BLUE}ℹ${NC} PID file: ${YELLOW}.worker.pid${NC}"
        echo -e "  ${BLUE}ℹ${NC} Frontend waits for worker to be ready (model loading ~10s)"
    else
        echo -e "\n${CYAN}Worker Mode:${NC} ${YELLOW}Docker (CPU only)${NC}"
        echo -e "  ${BLUE}ℹ${NC} For GPU: ${YELLOW}./scripts/start-all.sh --gpu${NC}"
    fi

    echo -e "\n${CYAN}Management:${NC}"
    echo -e "  ${GREEN}→${NC} Stop all:      ${YELLOW}./scripts/stop-all.sh${NC}"
    echo -e "  ${GREEN}→${NC} View logs:     ${YELLOW}docker-compose -f docker/docker-compose.yml logs -f${NC}"

    if [ "$MODE" = "gpu" ]; then
        echo -e "  ${GREEN}→${NC} Worker logs:   ${YELLOW}tail -f logs/worker-native.log${NC}"
    fi

    echo ""
}

show_help() {
    cat << EOF
${BLUE}DocuSearch - Start All Services${NC}

${YELLOW}Usage:${NC}
  ./scripts/start-all.sh [options]

${YELLOW}Options:${NC}
  --gpu          Run worker natively with Metal GPU (default, 10-20x faster)
  --cpu          Run worker in Docker with CPU (simpler, slower)
  --docker-only  Start only Docker services (no worker)
  --no-vision    Disable vision mode (skip ngrok tunnel)
  --help         Show this help message

${YELLOW}Examples:${NC}
  # Start with Metal GPU and vision mode (default)
  ./scripts/start-all.sh
  ./scripts/start-all.sh --gpu

  # Start with CPU (no GPU setup required)
  ./scripts/start-all.sh --cpu

  # Start without vision mode (no ngrok)
  ./scripts/start-all.sh --no-vision

  # Combine options
  ./scripts/start-all.sh --gpu --no-vision

  # Start only ChromaDB and Copyparty
  ./scripts/start-all.sh --docker-only

${YELLOW}Services:${NC}
  - ChromaDB:    Vector database (http://localhost:8001)
  - Copyparty:   File upload server (http://localhost:8000)
  - Worker:      Document processing (http://localhost:8002)
  - Ngrok:       Tunnel for vision mode (auto-managed)
  - Research:    AI research API (http://localhost:8004)
  - Frontend:    React UI (http://localhost:$FRONTEND_PORT)

${YELLOW}Vision Mode:${NC}
  - Enabled by default (multimodal LLM with images)
  - Requires ngrok (auto-started, free account needed)
  - Use --no-vision to disable and skip ngrok

${YELLOW}Requirements:${NC}
  - Docker Desktop running
  - For --gpu mode: Run './scripts/run-worker-native.sh setup' first
  - For vision mode: ngrok installed and configured (optional)

${YELLOW}See Also:${NC}
  - Setup GPU worker:     ./scripts/run-worker-native.sh setup
  - Stop services:        ./scripts/stop-all.sh
  - Check status:         ./scripts/status.sh
  - Vision mode docs:     docs/RESEARCH_BOT_VISION_SETUP.md
  - Worker documentation: docs/NATIVE_WORKER_SETUP.md
EOF
}

# ============================================================================
# Main
# ============================================================================

# Parse arguments
for arg in "$@"; do
    case "$arg" in
        --help|-h|help)
            show_help
            exit 0
            ;;
        --gpu|gpu)
            MODE="gpu"
            ;;
        --cpu|cpu)
            MODE="cpu"
            ;;
        --docker-only)
            MODE="docker-only"
            ;;
        --no-vision)
            VISION_ENABLED=false
            ;;
        *)
            if [ -n "$arg" ] && [[ ! "$arg" =~ ^-- ]]; then
                echo -e "${RED}Error: Unknown option '$arg'${NC}\n"
                show_help
                exit 1
            fi
            ;;
    esac
done

# Set default mode if not specified
if [ -z "$MODE" ] || [ "$MODE" = "true" ]; then
    MODE="gpu"
fi

# Create logs directory
mkdir -p logs

# Start services
print_header

echo -e "${CYAN}Mode:${NC} "
case "$MODE" in
    gpu)
        echo -e "${GREEN}Native worker with Metal GPU acceleration${NC}\n"
        ;;
    cpu)
        echo -e "${YELLOW}Docker worker (CPU only)${NC}\n"
        ;;
    docker-only)
        echo -e "${BLUE}Docker services only (no worker)${NC}\n"
        ;;
esac

# Pre-flight checks
echo -e "${CYAN}Pre-flight checks...${NC}\n"
check_docker
print_status "Docker" "ok" "Running"

check_ports
echo ""

# Start services
start_docker_services

if [ "$MODE" = "gpu" ]; then
    start_native_worker

    # Wait for worker to be fully ready before starting ngrok
    if [ "$VISION_ENABLED" = true ]; then
        max_wait=20
        wait_count=0
        echo -e "\n${CYAN}Waiting for worker to be ready before starting ngrok...${NC}\n"

        while [ $wait_count -lt $max_wait ]; do
            if curl -s http://localhost:8002/health > /dev/null 2>&1; then
                break
            fi
            sleep 1
            wait_count=$((wait_count + 1))
        done
    fi

    start_ngrok  # Start ngrok after worker is ready
    start_research_api
    start_frontend
elif [ "$MODE" = "docker-only" ]; then
    print_status "Worker" "info" "Skipped (--docker-only mode)"
    print_status "Ngrok" "info" "Skipped (--docker-only mode)"
    print_status "Research API" "info" "Skipped (--docker-only mode)"
    print_status "Frontend" "info" "Skipped (--docker-only mode)"
elif [ "$MODE" = "cpu" ]; then
    # Wait for worker to be ready before starting ngrok
    if [ "$VISION_ENABLED" = true ]; then
        max_wait=20
        wait_count=0
        echo -e "\n${CYAN}Waiting for worker to be ready before starting ngrok...${NC}\n"

        while [ $wait_count -lt $max_wait ]; do
            if curl -s http://localhost:8002/health > /dev/null 2>&1; then
                break
            fi
            sleep 1
            wait_count=$((wait_count + 1))
        done
    fi

    start_ngrok  # Start ngrok in CPU mode too
    start_frontend
fi

# Show summary
show_summary

# Final message
if [ "$MODE" = "gpu" ]; then
    if [ "$ACTUAL_DEVICE" = "mps" ]; then
        echo -e "${GREEN}🚀 DocuSearch is running with Metal GPU acceleration!${NC}\n"
    elif [ "$ACTUAL_DEVICE" = "cpu" ]; then
        echo -e "${YELLOW}🚀 DocuSearch is running (CPU mode - MPS unavailable)${NC}\n"
    else
        echo -e "${GREEN}🚀 DocuSearch is running!${NC}\n"
    fi
else
    echo -e "${GREEN}🚀 DocuSearch is running!${NC}\n"
fi
