#!/usr/bin/env bash
# ============================================================================
# DocuSearch MVP - Start Script
# ============================================================================
# Starts all Docker services and validates health
#
# Usage:
#   ./scripts/start.sh [--detach|-d]
# ============================================================================

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DETACH=false

# Parse arguments
for arg in "$@"; do
  case $arg in
    --detach|-d)
      DETACH=true
      shift
      ;;
  esac
done

log_info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_info "Starting DocuSearch MVP services..."

cd "$PROJECT_ROOT/docker"

if [ "$DETACH" = true ]; then
  docker-compose up -d
  log_success "Services started in detached mode"

  echo ""
  log_info "Waiting for health checks..."
  sleep 10

  docker-compose ps

  echo ""
  log_info "Service URLs:"
  echo "  Copyparty UI:    http://localhost:8000"
  echo "  ChromaDB API:    http://localhost:8001"
  echo ""
  log_info "View logs: docker-compose logs -f"
else
  docker-compose up
fi
