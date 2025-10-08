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
WORKER_PID_FILE="${PROJECT_ROOT}/.worker.pid"
COMPOSE_DIR="${PROJECT_ROOT}/docker"

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

    if ! docker info &> /dev/null; then
        echo -e "${RED}Error: Docker daemon not running${NC}"
        echo "Please start Docker Desktop"
        exit 1
    fi
}

check_ports() {
    local ports=("8000" "8001" "8002")
    local port_names=("Copyparty" "ChromaDB" "Worker")

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
    echo -e "\n${CYAN}Starting native worker with Metal GPU...${NC}\n"

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

    # Start worker in background
    nohup ./scripts/run-worker-native.sh run > logs/worker-native.log 2>&1 &
    local worker_pid=$!
    echo $worker_pid > "$WORKER_PID_FILE"

    # Wait for worker to start
    sleep 3

    # Check if worker is running
    if ps -p "$worker_pid" > /dev/null 2>&1; then
        if curl -s http://localhost:8002/health > /dev/null 2>&1; then
            print_status "Worker (Native)" "ok" "Running on http://localhost:8002 (Metal GPU)"
            print_status "Worker PID" "info" "$worker_pid (saved to .worker.pid)"
        else
            print_status "Worker (Native)" "warn" "Starting... (check logs/worker-native.log)"
        fi
    else
        print_status "Worker (Native)" "error" "Failed to start (check logs/worker-native.log)"
        rm -f "$WORKER_PID_FILE"
    fi
}

show_summary() {
    echo -e "\n${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  ${GREEN}Services Started Successfully${NC}                        ${BLUE}║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo -e "\n${CYAN}Available Services:${NC}"
    echo -e "  ${GREEN}→${NC} Upload UI:     ${BLUE}http://localhost:8002/ui/${NC}"
    echo -e "  ${GREEN}→${NC} ChromaDB:      ${BLUE}http://localhost:8001${NC}"
    echo -e "  ${GREEN}→${NC} Copyparty:     ${BLUE}http://localhost:8000${NC}"
    echo -e "  ${GREEN}→${NC} Worker API:    ${BLUE}http://localhost:8002${NC}"
    echo -e "  ${GREEN}→${NC} Worker Status: ${BLUE}http://localhost:8002/status${NC}"

    if [ "$MODE" = "gpu" ]; then
        echo -e "\n${CYAN}Worker Mode:${NC} ${GREEN}Native with Metal GPU${NC}"
        echo -e "  ${BLUE}ℹ${NC} Logs: ${YELLOW}logs/worker-native.log${NC}"
        echo -e "  ${BLUE}ℹ${NC} PID file: ${YELLOW}.worker.pid${NC}"
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
  ./scripts/start-all.sh [option]

${YELLOW}Options:${NC}
  --gpu          Run worker natively with Metal GPU (default, 10-20x faster)
  --cpu          Run worker in Docker with CPU (simpler, slower)
  --docker-only  Start only Docker services (no worker)
  --help         Show this help message

${YELLOW}Examples:${NC}
  # Start with Metal GPU (recommended for M1/M2/M3 Mac)
  ./scripts/start-all.sh
  ./scripts/start-all.sh --gpu

  # Start with CPU (no GPU setup required)
  ./scripts/start-all.sh --cpu

  # Start only ChromaDB and Copyparty
  ./scripts/start-all.sh --docker-only

${YELLOW}Services:${NC}
  - ChromaDB:  Vector database (http://localhost:8001)
  - Copyparty:  File upload server (http://localhost:8000)
  - Worker:     Document processing (http://localhost:8002)

${YELLOW}Requirements:${NC}
  - Docker Desktop running
  - For --gpu mode: Run './scripts/run-worker-native.sh setup' first

${YELLOW}See Also:${NC}
  - Setup GPU worker: ./scripts/run-worker-native.sh setup
  - Stop services:    ./scripts/stop-all.sh
  - Documentation:    docs/NATIVE_WORKER_SETUP.md
EOF
}

# ============================================================================
# Main
# ============================================================================

# Parse arguments
case "$MODE" in
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
    *)
        if [ -n "$MODE" ]; then
            echo -e "${RED}Error: Unknown option '$MODE'${NC}\n"
            show_help
            exit 1
        fi
        MODE="gpu"  # Default
        ;;
esac

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
elif [ "$MODE" = "docker-only" ]; then
    print_status "Worker" "info" "Skipped (--docker-only mode)"
fi

# Show summary
show_summary

# Final message
if [ "$MODE" = "gpu" ]; then
    echo -e "${GREEN}🚀 DocuSearch is running with Metal GPU acceleration!${NC}\n"
else
    echo -e "${GREEN}🚀 DocuSearch is running!${NC}\n"
fi
