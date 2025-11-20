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

OUTPUT_FORMAT="${1:-text}"
FRONTEND_PORT=${VITE_FRONTEND_PORT:-42007}
WORKER_PID_FILE="${PROJECT_ROOT}/.worker.pid"
FRONTEND_PID_FILE="${PROJECT_ROOT}/.frontend.pid"
NGROK_PID_FILE="${PROJECT_ROOT}/.ngrok.pid"

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

    # Research API
    echo -e "\n${CYAN}Research API:${NC}"

    local research_api_status=$(check_service "http://localhost:8004/api/research/health")
    if [ "$research_api_status" = "running" ]; then
        echo -e "  ${GREEN}✓${NC} Research:  Running on http://localhost:8004"
        if [ -f ".research-api.pid" ]; then
            echo -e "    ${BLUE}→${NC} PID:     $(cat .research-api.pid)"
        fi
        echo -e "    ${BLUE}→${NC} Logs:    logs/research-api.log"
    else
        echo -e "  ${RED}✗${NC} Research:  Stopped"
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

    # Ngrok (Vision Mode)
    echo -e "\n${CYAN}Vision Mode (Ngrok):${NC}"

    # Check ngrok PID
    local ngrok_running=false
    if [ -f "$NGROK_PID_FILE" ]; then
        local ngrok_pid=$(cat "$NGROK_PID_FILE")
        if ps -p "$ngrok_pid" > /dev/null 2>&1; then
            ngrok_running=true
        fi
    fi

    # Check ngrok API
    local ngrok_url=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | jq -r '.tunnels[0].public_url' 2>/dev/null || echo "")

    if [ $ngrok_running = true ] && [ -n "$ngrok_url" ] && [ "$ngrok_url" != "null" ]; then
        echo -e "  ${GREEN}✓${NC} Ngrok:     Running (Vision enabled)"
        echo -e "    ${BLUE}→${NC} PID:     $(cat $NGROK_PID_FILE)"
        echo -e "    ${BLUE}→${NC} URL:     $ngrok_url"
        echo -e "    ${BLUE}→${NC} Tunnel:  Port 8002 (Worker API) → Internet"
        echo -e "    ${BLUE}→${NC} Logs:    logs/ngrok.log"

        # Check if .env is up to date
        if [ -f ".env" ]; then
            local env_ngrok_url=$(grep "^NGROK_URL=" .env 2>/dev/null | cut -d'=' -f2-)
            if [ "$env_ngrok_url" != "$ngrok_url" ]; then
                echo -e "    ${YELLOW}⚠${NC} Warning: .env has outdated URL"
                echo -e "    ${YELLOW}→${NC} Run: ${YELLOW}./scripts/start-all.sh${NC} to update"
            fi
        fi
    elif [ $ngrok_running = true ]; then
        echo -e "  ${YELLOW}⚠${NC} Ngrok:     Process running but tunnel not ready"
        echo -e "    ${BLUE}→${NC} PID:     $(cat $NGROK_PID_FILE)"
        echo -e "    ${BLUE}→${NC} Check:   logs/ngrok.log"
    else
        echo -e "  ${BLUE}○${NC} Ngrok:     Stopped (vision mode disabled)"
        echo -e "    ${BLUE}→${NC} To enable: ${YELLOW}./scripts/start-all.sh${NC} (auto-starts ngrok)"
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

    # Preprocessing configuration
    echo -e "\n${CYAN}Local LLM Preprocessing:${NC}"
    if [ -f "$PROJECT_ROOT/.env" ]; then
        local preprocess_enabled=$(grep -E "^LOCAL_PREPROCESS_ENABLED=" "$PROJECT_ROOT/.env" | cut -d'=' -f2)
        local preprocess_strategy=$(grep -E "^LOCAL_PREPROCESS_STRATEGY=" "$PROJECT_ROOT/.env" | cut -d'=' -f2)

        if [ "$preprocess_enabled" = "true" ]; then
            echo -e "  ${GREEN}✓${NC} Enabled (strategy: ${preprocess_strategy:-compress})"
            echo -e "    ${YELLOW}→ Reduces costs ~50% but adds 70-90s latency${NC}"
        else
            echo -e "  ${BLUE}○${NC} Disabled (default - fast responses)"
            echo -e "    ${BLUE}→ Set LOCAL_PREPROCESS_ENABLED=true to enable${NC}"
        fi
    else
        echo -e "  ${BLUE}○${NC} Disabled (no .env file)"
    fi

    # Overall status
    echo -e "\n${CYAN}System Status:${NC}"

    local all_running=true
    local core_running=true
    [ "$chromadb_status" != "running" ] && all_running=false && core_running=false
    [ "$copyparty_status" != "running" ] && all_running=false && core_running=false
    [ "$worker_status" != "running" ] && all_running=false && core_running=false
    [ "$frontend_status" != "running" ] && all_running=false
    [ "$research_api_status" != "running" ] && all_running=false

    # Ngrok is optional, don't fail overall status
    if [ $ngrok_running != true ]; then
        echo -e "  ${BLUE}ℹ${NC} Vision mode disabled (ngrok not running)"
    fi

    if $all_running; then
        echo -e "  ${GREEN}✓ All services running${NC}"
    elif $core_running; then
        echo -e "  ${YELLOW}⚠ Core services running, some optional services stopped${NC}"
        echo -e "\n  ${CYAN}To start all services:${NC}"
        echo -e "    ${YELLOW}./scripts/start-all.sh${NC}"
    else
        echo -e "  ${RED}✗ Core services not running${NC}"
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
    local research_api_status=$(check_service "http://localhost:8004/api/research/health")
    local frontend_status=$(check_service "http://localhost:3000")

    local native_worker=false
    local worker_pid=""
    local research_pid=""
    local frontend_pid=""
    local ngrok_pid=""
    local ngrok_url=""
    local ngrok_status="stopped"

    if [ -f "$WORKER_PID_FILE" ]; then
        worker_pid=$(cat "$WORKER_PID_FILE")
        if ps -p "$worker_pid" > /dev/null 2>&1; then
            native_worker=true
        fi
    fi

    if [ -f ".research-api.pid" ]; then
        research_pid=$(cat ".research-api.pid")
    fi

    if [ -f "$FRONTEND_PID_FILE" ]; then
        frontend_pid=$(cat "$FRONTEND_PID_FILE")
    fi

    if [ -f "$NGROK_PID_FILE" ]; then
        ngrok_pid=$(cat "$NGROK_PID_FILE")
        if ps -p "$ngrok_pid" > /dev/null 2>&1; then
            ngrok_url=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | jq -r '.tunnels[0].public_url' 2>/dev/null || echo "")
            if [ -n "$ngrok_url" ] && [ "$ngrok_url" != "null" ]; then
                ngrok_status="running"
            fi
        fi
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
    },
    "research_api": {
      "status": "$research_api_status",
      "url": "http://localhost:8004",
      "pid": "$research_pid"
    },
    "ngrok": {
      "status": "$ngrok_status",
      "url": "$ngrok_url",
      "pid": "$ngrok_pid",
      "vision_enabled": $([ "$ngrok_status" = "running" ] && echo 'true' || echo 'false')
    }
  },
  "all_running": $([ "$chromadb_status" = "running" ] && [ "$copyparty_status" = "running" ] && [ "$worker_status" = "running" ] && [ "$frontend_status" = "running" ] && [ "$research_api_status" = "running" ] && echo 'true' || echo 'false')
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
