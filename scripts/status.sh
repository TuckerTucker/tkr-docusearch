#!/bin/bash
# ============================================================================
# DocuSearch - System Status
# ============================================================================
# Shows the current status of all DocuSearch services
#
# Usage:
#   ./scripts/status.sh [--json]
#
# Options:
#   --json  Output status in JSON format
# ============================================================================

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

OUTPUT_FORMAT="${1:-text}"
WORKER_PID_FILE="${PROJECT_ROOT}/.worker.pid"
FRONTEND_PID_FILE="${PROJECT_ROOT}/.frontend.pid"

# ============================================================================
# Functions
# ============================================================================

check_service() {
    local url=$1
    local timeout=${2:-2}

    if curl -s --max-time $timeout "$url" > /dev/null 2>&1; then
        echo "running"
    else
        echo "stopped"
    fi
}

get_service_info() {
    local service=$1
    local status=$2

    case "$service" in
        copyparty)
            if [ "$status" = "running" ]; then
                echo "http://localhost:8000"
            fi
            ;;
        chromadb)
            if [ "$status" = "running" ]; then
                local response=$(curl -s http://localhost:8001/api/v2/heartbeat 2>/dev/null)
                if [ -n "$response" ]; then
                    echo "http://localhost:8001"
                fi
            fi
            ;;
        worker)
            if [ "$status" = "running" ]; then
                local response=$(curl -s http://localhost:8002/status 2>/dev/null)
                if [ -n "$response" ]; then
                    echo "$response"
                fi
            fi
            ;;
    esac
}

# Text output
show_status_text() {
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  ${CYAN}DocuSearch - System Status${NC}                           ${BLUE}║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Check Docker
    echo -e "${CYAN}Docker Services:${NC}"

    # ChromaDB
    local chromadb_status=$(check_service "http://localhost:8001/api/v2/heartbeat")
    if [ "$chromadb_status" = "running" ]; then
        echo -e "  ${GREEN}✓${NC} ChromaDB:  Running on http://localhost:8001"
    else
        echo -e "  ${RED}✗${NC} ChromaDB:  Stopped"
    fi

    # Copyparty
    local copyparty_status=$(check_service "http://localhost:8000/")
    if [ "$copyparty_status" = "running" ]; then
        echo -e "  ${GREEN}✓${NC} Copyparty: Running on http://localhost:8000"
    else
        echo -e "  ${RED}✗${NC} Copyparty: Stopped"
    fi

    # Worker
    echo -e "\n${CYAN}Processing Worker:${NC}"

    # Check native worker PID
    local native_worker_running=false
    if [ -f "$WORKER_PID_FILE" ]; then
        local worker_pid=$(cat "$WORKER_PID_FILE")
        if ps -p "$worker_pid" > /dev/null 2>&1; then
            native_worker_running=true
        fi
    fi

    # Check worker endpoint
    local worker_status=$(check_service "http://localhost:8002/health")

    if [ "$worker_status" = "running" ]; then
        local worker_info=$(curl -s http://localhost:8002/status 2>/dev/null)

        if [ $native_worker_running = true ]; then
            echo -e "  ${GREEN}✓${NC} Worker:    Running (Native with Metal GPU)"
            echo -e "    ${BLUE}→${NC} PID:     $(cat $WORKER_PID_FILE)"
            echo -e "    ${BLUE}→${NC} Logs:    logs/worker-native.log"
        else
            echo -e "  ${GREEN}✓${NC} Worker:    Running (Docker - CPU only)"
        fi

        echo -e "    ${BLUE}→${NC} URL:     http://localhost:8002"

        # Parse worker stats if available
        if [ -n "$worker_info" ]; then
            local docs=$(echo "$worker_info" | grep -o '"total_documents":[0-9]*' | cut -d: -f2 || echo "0")
            local pages=$(echo "$worker_info" | grep -o '"total_pages":[0-9]*' | cut -d: -f2 || echo "0")
            echo -e "    ${BLUE}→${NC} Stats:   $docs documents, $pages pages"
        fi
    else
        if [ $native_worker_running = true ]; then
            echo -e "  ${YELLOW}⚠${NC} Worker:    Process running but not responding"
            echo -e "    ${BLUE}→${NC} PID:     $(cat $WORKER_PID_FILE)"
        else
            echo -e "  ${RED}✗${NC} Worker:    Stopped"
        fi
    fi

    # Frontend
    echo -e "\n${CYAN}React Frontend:${NC}"

    # Check frontend PID
    local frontend_running=false
    if [ -f "$FRONTEND_PID_FILE" ]; then
        local frontend_pid=$(cat "$FRONTEND_PID_FILE")
        if ps -p "$frontend_pid" > /dev/null 2>&1; then
            frontend_running=true
        fi
    fi

    # Check frontend endpoint
    local frontend_status=$(check_service "http://localhost:3000")

    if [ "$frontend_status" = "running" ]; then
        echo -e "  ${GREEN}✓${NC} Frontend:  Running (React 19 + Vite)"
        if [ $frontend_running = true ]; then
            echo -e "    ${BLUE}→${NC} PID:     $(cat $FRONTEND_PID_FILE)"
        fi
        echo -e "    ${BLUE}→${NC} URL:     http://localhost:3000"
        echo -e "    ${BLUE}→${NC} Logs:    logs/frontend.log"
    else
        if [ $frontend_running = true ]; then
            echo -e "  ${YELLOW}⚠${NC} Frontend:  Process running but not responding"
            echo -e "    ${BLUE}→${NC} PID:     $(cat $FRONTEND_PID_FILE)"
        else
            echo -e "  ${RED}✗${NC} Frontend:  Stopped"
        fi
    fi

    # Port usage
    echo -e "\n${CYAN}Port Usage:${NC}"
    for port in 3000 8000 8001 8002 8004; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            local pid=$(lsof -Pi :$port -sTCP:LISTEN -t)
            local process=$(ps -p $pid -o comm= | tr -d '\n')
            echo -e "  ${GREEN}✓${NC} :$port → $process (PID: $pid)"
        else
            echo -e "  ${RED}○${NC} :$port → (free)"
        fi
    done

    # Overall status
    echo -e "\n${CYAN}System Status:${NC}"

    local all_running=true
    [ "$chromadb_status" != "running" ] && all_running=false
    [ "$copyparty_status" != "running" ] && all_running=false
    [ "$worker_status" != "running" ] && all_running=false
    [ "$frontend_status" != "running" ] && all_running=false

    if $all_running; then
        echo -e "  ${GREEN}✓ All services running${NC}"
    else
        echo -e "  ${YELLOW}⚠ Some services are not running${NC}"
        echo -e "\n  ${CYAN}To start all services:${NC}"
        echo -e "    ${YELLOW}./scripts/start-all.sh${NC}"
    fi

    echo ""
}

# JSON output
show_status_json() {
    local chromadb_status=$(check_service "http://localhost:8001/api/v2/heartbeat")
    local copyparty_status=$(check_service "http://localhost:8000/")
    local worker_status=$(check_service "http://localhost:8002/health")
    local frontend_status=$(check_service "http://localhost:3000")

    local native_worker=false
    local worker_pid=""
    local frontend_pid=""

    if [ -f "$WORKER_PID_FILE" ]; then
        worker_pid=$(cat "$WORKER_PID_FILE")
        if ps -p "$worker_pid" > /dev/null 2>&1; then
            native_worker=true
        fi
    fi

    if [ -f "$FRONTEND_PID_FILE" ]; then
        frontend_pid=$(cat "$FRONTEND_PID_FILE")
    fi

    cat << EOF
{
  "services": {
    "frontend": {
      "status": "$frontend_status",
      "url": "http://localhost:3000",
      "pid": "$frontend_pid"
    },
    "chromadb": {
      "status": "$chromadb_status",
      "url": "http://localhost:8001"
    },
    "copyparty": {
      "status": "$copyparty_status",
      "url": "http://localhost:8000"
    },
    "worker": {
      "status": "$worker_status",
      "url": "http://localhost:8002",
      "mode": "$([ $native_worker = true ] && echo 'native' || echo 'docker')",
      "pid": "$worker_pid"
    }
  },
  "all_running": $([ "$chromadb_status" = "running" ] && [ "$copyparty_status" = "running" ] && [ "$worker_status" = "running" ] && [ "$frontend_status" = "running" ] && echo 'true' || echo 'false')
}
EOF
}

# ============================================================================
# Main
# ============================================================================

case "$OUTPUT_FORMAT" in
    --json|-j)
        show_status_json
        ;;
    --help|-h|help)
        cat << EOF
${BLUE}DocuSearch - System Status${NC}

${YELLOW}Usage:${NC}
  ./scripts/status.sh [option]

${YELLOW}Options:${NC}
  --json, -j  Output status in JSON format
  --help, -h  Show this help message

${YELLOW}Examples:${NC}
  # Show status (human-readable)
  ./scripts/status.sh

  # Get status as JSON
  ./scripts/status.sh --json

${YELLOW}See Also:${NC}
  - Start services: ./scripts/start-all.sh
  - Stop services:  ./scripts/stop-all.sh
EOF
        ;;
    *)
        show_status_text
        ;;
esac
