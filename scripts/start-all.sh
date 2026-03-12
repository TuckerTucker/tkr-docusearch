#!/bin/bash
# ============================================================================
# DocuSearch - Start All Services (macOS)
# ============================================================================
# Starts the complete DocuSearch stack natively (no Docker):
# - Processing Worker - Document processing with Metal GPU + Koji DB
# - Research API - LLM-powered document Q&A
# - Frontend - React 19 SPA
# - Ngrok - Tunnel for vision mode (optional)
#
# Usage:
#   ./scripts/start-all.sh [--no-vision]
#
# Options:
#   --no-vision    Disable vision mode (skip ngrok tunnel)
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

FRONTEND_PORT=${VITE_FRONTEND_PORT:-3333}
ACTUAL_DEVICE=""  # Will be set to 'mps' or 'cpu' during worker startup
WORKER_PID_FILE="${PROJECT_ROOT}/.worker.pid"
FRONTEND_PID_FILE="${PROJECT_ROOT}/.frontend.pid"
NGROK_PID_FILE="${PROJECT_ROOT}/.ngrok.pid"
SHIKOMI_PID_FILE="${PROJECT_ROOT}/.shikomi.pid"
SHIKOMI_BINARY="${PROJECT_ROOT}/bin/shikomi-worker"
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

check_infrastructure() {
    echo -e "${CYAN}Infrastructure:${NC}\n"

    # Koji database
    local koji_path="${KOJI_DB_PATH:-data/koji.db}"
    if [ -e "$koji_path" ]; then
        print_status "Koji DB" "ok" "Found at $koji_path"
    else
        print_status "Koji DB" "info" "Will be created at $koji_path on first use"
    fi

    # Shikomi embedding service
    local shikomi_target="${SHIKOMI_GRPC_TARGET:-localhost:50051}"
    local shikomi_host="${shikomi_target%%:*}"
    local shikomi_port="${shikomi_target##*:}"

    if python3 -c "
import socket; s = socket.socket(); s.settimeout(2)
s.connect(('$shikomi_host', $shikomi_port)); s.close()
" 2>/dev/null; then
        print_status "Shikomi" "ok" "Embedding service reachable at $shikomi_target"
    else
        print_status "Shikomi" "warn" "Not reachable at $shikomi_target (embeddings will fail)"
        echo -e "    ${BLUE}→${NC} Start Shikomi or set SHIKOMI_GRPC_TARGET in .env"
    fi

    echo ""
}

check_ports() {
    local ports=("8002" "8004" "$FRONTEND_PORT")
    local port_names=("Worker" "Research API" "Frontend")

    for i in "${!ports[@]}"; do
        local port="${ports[$i]}"
        local name="${port_names[$i]}"

        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            local pid=$(lsof -Pi :$port -sTCP:LISTEN -t)
            print_status "$name port $port" "warn" "Already in use by PID $pid"
        fi
    done
}

start_shikomi() {
    echo -e "\n${CYAN}Starting Shikomi embedding service...${NC}\n"

    local shikomi_target="${SHIKOMI_GRPC_TARGET:-localhost:50051}"
    local shikomi_host="${shikomi_target%%:*}"
    local shikomi_port="${shikomi_target##*:}"

    # Check if already running
    if python3 -c "import socket; s = socket.socket(); s.settimeout(1); s.connect(('$shikomi_host', $shikomi_port)); s.close()" 2>/dev/null; then
        print_status "Shikomi" "ok" "Already running at $shikomi_target"
        return
    fi

    # Check if binary exists
    if [ ! -x "$SHIKOMI_BINARY" ]; then
        print_status "Shikomi" "warn" "Binary not found at $SHIKOMI_BINARY"
        echo -e "    ${BLUE}→${NC} Build: cd tkr-koji && cargo build --release --features server -p shikomi"
        echo -e "    ${BLUE}→${NC} Copy:  cp target/release/shikomi-worker ${SHIKOMI_BINARY}"
        return
    fi

    # Check for stale PID
    if [ -f "$SHIKOMI_PID_FILE" ]; then
        local old_pid=$(cat "$SHIKOMI_PID_FILE")
        if ps -p "$old_pid" > /dev/null 2>&1; then
            print_status "Shikomi" "warn" "Already running (PID: $old_pid)"
            return
        else
            rm -f "$SHIKOMI_PID_FILE"
        fi
    fi

    # Determine mode: use --mock unless SHIKOMI_USE_MOCK=false
    local mock_flag="--mock"
    if [ "${SHIKOMI_USE_MOCK:-true}" = "false" ]; then
        mock_flag=""
    fi

    # Start shikomi
    # shikomi-worker expects IP address, not hostname
    local listen_addr="$shikomi_host"
    if [ "$listen_addr" = "localhost" ]; then
        listen_addr="127.0.0.1"
    fi
    nohup "$SHIKOMI_BINARY" --listen "$listen_addr:$shikomi_port" $mock_flag > logs/shikomi.log 2>&1 &
    local shikomi_pid=$!
    echo $shikomi_pid > "$SHIKOMI_PID_FILE"

    # Wait for it to be reachable
    local count=0
    local max_wait=5
    while [ $count -lt $max_wait ]; do
        if python3 -c "import socket; s = socket.socket(); s.settimeout(1); s.connect(('$shikomi_host', $shikomi_port)); s.close()" 2>/dev/null; then
            if [ -n "$mock_flag" ]; then
                print_status "Shikomi" "ok" "Running in mock mode at $shikomi_target (PID: $shikomi_pid)"
            else
                print_status "Shikomi" "ok" "Running at $shikomi_target (PID: $shikomi_pid)"
            fi
            return
        fi
        sleep 1
        count=$((count + 1))
    done

    if ps -p "$shikomi_pid" > /dev/null 2>&1; then
        print_status "Shikomi" "warn" "Started but not yet reachable (check logs/shikomi.log)"
    else
        print_status "Shikomi" "error" "Failed to start (check logs/shikomi.log)"
        rm -f "$SHIKOMI_PID_FILE"
    fi
}

start_native_worker() {
    # Check Metal availability first
    echo -e "\n${CYAN}Checking Metal/MPS availability...${NC}\n"

    if python3 -c "import torch; exit(0 if torch.backends.mps.is_available() else 1)" 2>/dev/null; then
        ACTUAL_DEVICE="mps"
        echo -e "${GREEN}✓ Metal/MPS available - using GPU acceleration${NC}\n"
        echo -e "\n${CYAN}Starting native worker with Metal GPU...${NC}\n"
    else
        ACTUAL_DEVICE="cpu"
        echo -e "${YELLOW}⚠ Metal/MPS not available - falling back to CPU${NC}"
        echo -e "${YELLOW}Note: Worker will run in CPU mode (slower)${NC}\n"
        echo -e "\n${CYAN}Starting native worker (CPU mode)...${NC}\n"
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
    # exec in run-worker-native.sh replaces bash with Python, preserving the PID
    nohup "${PROJECT_ROOT}/scripts/run-worker-native.sh" run > logs/worker-native.log 2>&1 &
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
    echo -e "\n${CYAN}Services:${NC}"
    echo -e "  ${GREEN}→${NC} Frontend:     ${BLUE}http://localhost:$FRONTEND_PORT${NC}"
    echo -e "  ${GREEN}→${NC} Worker API:   ${BLUE}http://localhost:8002${NC}"
    echo -e "  ${GREEN}→${NC} Research API: ${BLUE}http://localhost:8004${NC}"

    echo -e "\n${CYAN}Infrastructure:${NC}"
    local koji_path="${KOJI_DB_PATH:-data/koji.db}"
    if [ -e "$koji_path" ]; then
        echo -e "  ${GREEN}→${NC} Koji DB:     ${koji_path}"
    else
        echo -e "  ${YELLOW}→${NC} Koji DB:     ${koji_path} (will create on first use)"
    fi

    local shikomi_target="${SHIKOMI_GRPC_TARGET:-localhost:50051}"
    if python3 -c "
import socket; s = socket.socket(); s.settimeout(1)
s.connect(('${shikomi_target%%:*}', ${shikomi_target##*:})); s.close()
" 2>/dev/null; then
        echo -e "  ${GREEN}→${NC} Shikomi:     ${shikomi_target} (connected)"
    else
        echo -e "  ${YELLOW}→${NC} Shikomi:     ${shikomi_target} (not reachable)"
    fi

    if [ "$ACTUAL_DEVICE" = "mps" ]; then
        echo -e "\n${CYAN}Worker Mode:${NC} ${GREEN}Native with Metal GPU (MPS)${NC}"
    elif [ "$ACTUAL_DEVICE" = "cpu" ]; then
        echo -e "\n${CYAN}Worker Mode:${NC} ${YELLOW}Native (CPU fallback - MPS unavailable)${NC}"
    else
        echo -e "\n${CYAN}Worker Mode:${NC} ${GREEN}Native${NC}"
    fi
    echo -e "  ${BLUE}ℹ${NC} Logs: ${YELLOW}logs/worker-native.log${NC}"
    echo -e "  ${BLUE}ℹ${NC} PID file: ${YELLOW}.worker.pid${NC}"

    echo -e "\n${CYAN}Management:${NC}"
    echo -e "  ${GREEN}→${NC} Stop all:      ${YELLOW}./scripts/stop-all.sh${NC}"
    echo -e "  ${GREEN}→${NC} View logs:     ${YELLOW}tail -f logs/*.log${NC}"

    echo -e "  ${GREEN}→${NC} Worker logs:   ${YELLOW}tail -f logs/worker-native.log${NC}"

    echo ""
}

show_help() {
    cat << EOF
${BLUE}DocuSearch - Start All Services${NC}

${YELLOW}Usage:${NC}
  ./scripts/start-all.sh [options]

${YELLOW}Options:${NC}
  --no-vision    Disable vision mode (skip ngrok tunnel)
  --help         Show this help message

${YELLOW}Examples:${NC}
  # Start all services (default)
  ./scripts/start-all.sh

  # Start without vision mode (no ngrok)
  ./scripts/start-all.sh --no-vision

${YELLOW}Services:${NC}
  - Worker:      Document processing + Koji DB (http://localhost:8002)
  - Research:    AI research API (http://localhost:8004)
  - Ngrok:       Tunnel for vision mode (auto-managed)
  - Frontend:    React UI (http://localhost:$FRONTEND_PORT)

${YELLOW}Vision Mode:${NC}
  - Enabled by default (multimodal LLM with images)
  - Requires ngrok (auto-started, free account needed)
  - Use --no-vision to disable and skip ngrok

${YELLOW}Requirements:${NC}
  - Run './scripts/run-worker-native.sh setup' first
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
        --gpu|gpu|--cpu|cpu)
            ;; # All modes run natively now
        --docker-only)
            echo -e "${YELLOW}Docker mode removed — all services run natively now.${NC}"
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

# Create logs directory
mkdir -p logs

# Start services
print_header

echo -e "${CYAN}Mode:${NC} "
echo -e "${GREEN}Native worker with Metal GPU acceleration${NC}\n"

# Pre-flight checks
echo -e "${CYAN}Pre-flight checks...${NC}\n"
check_infrastructure
check_ports
echo ""

# Start services
start_shikomi
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

# Show summary
show_summary

# Final message
if [ "$ACTUAL_DEVICE" = "mps" ]; then
    echo -e "${GREEN}DocuSearch is running with Metal GPU acceleration!${NC}\n"
elif [ "$ACTUAL_DEVICE" = "cpu" ]; then
    echo -e "${YELLOW}DocuSearch is running (CPU mode - MPS unavailable)${NC}\n"
else
    echo -e "${GREEN}DocuSearch is running!${NC}\n"
fi
