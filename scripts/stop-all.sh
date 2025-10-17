#!/bin/bash
# ============================================================================
# DocuSearch - Stop All Services (macOS)
# ============================================================================
# Stops all DocuSearch services:
# - Native worker (if running)
# - Docker containers (ChromaDB, Copyparty, Worker)
# - Cleans up PID files
#
# Usage:
#   ./scripts/stop-all.sh [--force]
#
# Options:
#   --force  Force stop (kill -9) if graceful shutdown fails
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

FORCE_MODE="${1:-}"
WORKER_PID_FILE="${PROJECT_ROOT}/.worker.pid"
RESEARCH_PID_FILE="${PROJECT_ROOT}/.research-api.pid"
COMPOSE_DIR="${PROJECT_ROOT}/docker"

# ============================================================================
# Functions
# ============================================================================

print_header() {
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  ${CYAN}DocuSearch - Stopping All Services${NC}                   ${BLUE}║${NC}"
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

stop_native_worker() {
    echo -e "${CYAN}Stopping native worker...${NC}\n"

    # Check PID file
    if [ -f "$WORKER_PID_FILE" ]; then
        local worker_pid=$(cat "$WORKER_PID_FILE")

        if ps -p "$worker_pid" > /dev/null 2>&1; then
            print_status "Worker PID" "info" "Found: $worker_pid"

            if [ "$FORCE_MODE" = "--force" ]; then
                print_status "Worker" "warn" "Force killing (SIGKILL)"
                kill -9 "$worker_pid" 2>/dev/null || true
            else
                print_status "Worker" "info" "Gracefully stopping (SIGTERM)"
                kill "$worker_pid" 2>/dev/null || true

                # Wait up to 10 seconds for graceful shutdown
                local count=0
                while ps -p "$worker_pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
                    sleep 1
                    count=$((count + 1))
                done

                # Force kill if still running
                if ps -p "$worker_pid" > /dev/null 2>&1; then
                    print_status "Worker" "warn" "Graceful shutdown timed out, force killing"
                    kill -9 "$worker_pid" 2>/dev/null || true
                fi
            fi

            # Verify stopped
            if ps -p "$worker_pid" > /dev/null 2>&1; then
                print_status "Worker" "error" "Failed to stop (PID: $worker_pid)"
            else
                print_status "Worker" "ok" "Stopped"
            fi
        else
            print_status "Worker" "info" "Not running (stale PID file)"
        fi

        rm -f "$WORKER_PID_FILE"
        print_status "PID file" "ok" "Cleaned up"
    else
        print_status "Worker" "info" "No PID file found (may not be running)"
    fi

    # Check for orphaned worker processes
    local orphaned_pids=$(pgrep -f "worker_webhook.py" || true)
    if [ -n "$orphaned_pids" ]; then
        print_status "Orphaned workers" "warn" "Found: $orphaned_pids"

        if [ "$FORCE_MODE" = "--force" ]; then
            pkill -9 -f "worker_webhook.py" || true
            print_status "Orphaned workers" "ok" "Killed"
        else
            echo -e "\n  ${YELLOW}Run with --force to kill orphaned workers${NC}"
        fi
    fi
}

stop_research_api() {
    echo -e "\n${CYAN}Stopping research API...${NC}\n"

    # Check PID file
    if [ -f "$RESEARCH_PID_FILE" ]; then
        local research_pid=$(cat "$RESEARCH_PID_FILE")

        if ps -p "$research_pid" > /dev/null 2>&1; then
            print_status "Research API PID" "info" "Found: $research_pid"

            if [ "$FORCE_MODE" = "--force" ]; then
                print_status "Research API" "warn" "Force killing (SIGKILL)"
                kill -9 "$research_pid" 2>/dev/null || true
            else
                print_status "Research API" "info" "Gracefully stopping (SIGTERM)"
                kill "$research_pid" 2>/dev/null || true

                # Wait up to 10 seconds for graceful shutdown
                local count=0
                while ps -p "$research_pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
                    sleep 1
                    count=$((count + 1))
                done

                # Force kill if still running
                if ps -p "$research_pid" > /dev/null 2>&1; then
                    print_status "Research API" "warn" "Graceful shutdown timed out, force killing"
                    kill -9 "$research_pid" 2>/dev/null || true
                fi
            fi

            # Verify stopped
            if ps -p "$research_pid" > /dev/null 2>&1; then
                print_status "Research API" "error" "Failed to stop (PID: $research_pid)"
            else
                print_status "Research API" "ok" "Stopped"
            fi
        else
            print_status "Research API" "info" "Not running (stale PID file)"
        fi

        rm -f "$RESEARCH_PID_FILE"
        print_status "Research PID file" "ok" "Cleaned up"
    else
        print_status "Research API" "info" "No PID file found (may not be running)"
    fi

    # Check for orphaned research API processes
    local orphaned_pids=$(pgrep -f "src/api/research.py" || true)
    if [ -n "$orphaned_pids" ]; then
        print_status "Orphaned research APIs" "warn" "Found: $orphaned_pids"

        if [ "$FORCE_MODE" = "--force" ]; then
            pkill -9 -f "src/api/research.py" || true
            print_status "Orphaned research APIs" "ok" "Killed"
        else
            echo -e "\n  ${YELLOW}Run with --force to kill orphaned research APIs${NC}"
        fi
    fi
}

stop_docker_services() {
    echo -e "\n${CYAN}Stopping Docker services...${NC}\n"

    cd "$COMPOSE_DIR"

    # Try to stop with both compose files
    local stopped=false

    # First try with native worker override
    if docker-compose -f docker-compose.yml -f docker-compose.native-worker.yml ps -q 2>/dev/null | grep -q .; then
        print_status "Docker Compose" "info" "Using native worker configuration"
        docker-compose -f docker-compose.yml -f docker-compose.native-worker.yml down
        stopped=true
    fi

    # Then try standard compose
    if ! $stopped && docker-compose ps -q 2>/dev/null | grep -q .; then
        print_status "Docker Compose" "info" "Using standard configuration"
        docker-compose down
        stopped=true
    fi

    if ! $stopped; then
        print_status "Docker services" "info" "No running containers found"
    else
        print_status "Docker services" "ok" "Stopped"
    fi

    cd "$PROJECT_ROOT"

    # Verify containers are stopped
    echo ""
    local running_containers=$(docker ps --filter "name=docusearch" --format "{{.Names}}" || true)

    if [ -n "$running_containers" ]; then
        print_status "Containers" "warn" "Some containers still running:"
        echo "$running_containers" | while read -r container; do
            echo -e "    ${YELLOW}→${NC} $container"
        done

        if [ "$FORCE_MODE" = "--force" ]; then
            echo -e "\n  ${YELLOW}Force stopping containers...${NC}"
            docker stop $(docker ps --filter "name=docusearch" -q) 2>/dev/null || true
            docker rm $(docker ps --filter "name=docusearch" -aq) 2>/dev/null || true
            print_status "Containers" "ok" "Force stopped"
        fi
    else
        print_status "Containers" "ok" "All stopped"
    fi
}

check_ports() {
    echo -e "\n${CYAN}Checking ports...${NC}\n"

    local ports=("8000" "8001" "8002" "8004")
    local port_names=("Copyparty" "ChromaDB" "Worker" "Research API")
    local ports_in_use=false

    for i in "${!ports[@]}"; do
        local port="${ports[$i]}"
        local name="${port_names[$i]}"

        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            local pid=$(lsof -Pi :$port -sTCP:LISTEN -t)
            local process=$(ps -p $pid -o comm= || echo "unknown")
            print_status "Port $port" "warn" "$name port still in use by $process (PID: $pid)"
            ports_in_use=true
        else
            print_status "Port $port" "ok" "$name port is free"
        fi
    done

    if $ports_in_use && [ "$FORCE_MODE" = "--force" ]; then
        echo -e "\n  ${YELLOW}Use lsof/kill to manually free ports if needed${NC}"
    fi
}

cleanup_logs() {
    echo -e "\n${CYAN}Log files:${NC}\n"

    if [ -f "logs/worker-native.log" ]; then
        local log_size=$(du -h logs/worker-native.log | cut -f1)
        print_status "Worker log" "info" "Saved (${log_size}): logs/worker-native.log"
    fi

    if [ -f "logs/research-api.log" ]; then
        local log_size=$(du -h logs/research-api.log | cut -f1)
        print_status "Research API log" "info" "Saved (${log_size}): logs/research-api.log"
    fi

    # Show recent Docker logs
    cd "$COMPOSE_DIR"
    local compose_logs=$(docker-compose logs --tail=0 2>/dev/null || echo "")
    cd "$PROJECT_ROOT"

    if [ -n "$compose_logs" ]; then
        print_status "Docker logs" "info" "Available via: docker-compose -f docker/docker-compose.yml logs"
    fi
}

show_summary() {
    echo -e "\n${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  ${GREEN}All Services Stopped${NC}                                 ${BLUE}║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"

    echo -e "\n${CYAN}To restart services:${NC}"
    echo -e "  ${GREEN}→${NC} With GPU:  ${YELLOW}./scripts/start-all.sh${NC}"
    echo -e "  ${GREEN}→${NC} CPU only:  ${YELLOW}./scripts/start-all.sh --cpu${NC}"

    if [ "$FORCE_MODE" != "--force" ]; then
        echo -e "\n${CYAN}Troubleshooting:${NC}"
        echo -e "  ${GREEN}→${NC} Force stop: ${YELLOW}./scripts/stop-all.sh --force${NC}"
        echo -e "  ${GREEN}→${NC} Check ports: ${YELLOW}lsof -i :8000,8001,8002,8004${NC}"
    fi

    echo ""
}

show_help() {
    cat << EOF
${BLUE}DocuSearch - Stop All Services${NC}

${YELLOW}Usage:${NC}
  ./scripts/stop-all.sh [option]

${YELLOW}Options:${NC}
  --force  Force stop (SIGKILL) if graceful shutdown fails
  --help   Show this help message

${YELLOW}What gets stopped:${NC}
  1. Native worker process (if running)
  2. Research API process (if running)
  3. Docker containers:
     - docusearch-copyparty (Copyparty upload server)
     - docusearch-chromadb (ChromaDB vector database)
     - docusearch-worker (Worker, if in Docker mode)
  4. Cleanup:
     - PID files
     - Orphaned processes

${YELLOW}Examples:${NC}
  # Normal stop (graceful shutdown)
  ./scripts/stop-all.sh

  # Force stop (if processes don't respond)
  ./scripts/stop-all.sh --force

${YELLOW}Troubleshooting:${NC}
  # Check what's running on DocuSearch ports
  lsof -i :8000,8001,8002,8004

  # Manually kill worker
  pkill -f worker_webhook.py

  # Manually kill research API
  pkill -f src/api/research.py

  # Force remove Docker containers
  docker rm -f \$(docker ps -aq --filter "name=docusearch")

${YELLOW}See Also:${NC}
  - Start services: ./scripts/start-all.sh
  - View logs:      tail -f logs/worker-native.log
EOF
}

# ============================================================================
# Main
# ============================================================================

# Parse arguments
case "$FORCE_MODE" in
    --help|-h|help)
        show_help
        exit 0
        ;;
    --force|-f)
        FORCE_MODE="--force"
        ;;
    "")
        FORCE_MODE=""
        ;;
    *)
        echo -e "${RED}Error: Unknown option '$FORCE_MODE'${NC}\n"
        show_help
        exit 1
        ;;
esac

# Stop services
print_header

if [ "$FORCE_MODE" = "--force" ]; then
    echo -e "${YELLOW}Mode: Force stop (SIGKILL)${NC}\n"
else
    echo -e "${CYAN}Mode: Graceful stop (SIGTERM)${NC}\n"
fi

stop_native_worker
stop_research_api
stop_docker_services
check_ports
cleanup_logs
show_summary

echo -e "${GREEN}👋 DocuSearch stopped successfully${NC}\n"
