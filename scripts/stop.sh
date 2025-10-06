#!/usr/bin/env bash
# ============================================================================
# DocuSearch MVP - Stop Script
# ============================================================================
# Gracefully stops all Docker services
#
# Usage:
#   ./scripts/stop.sh [--remove-volumes]
# ============================================================================

set -euo pipefail

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOVE_VOLUMES=false

# Parse arguments
for arg in "$@"; do
  case $arg in
    --remove-volumes)
      REMOVE_VOLUMES=true
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

log_warning() {
  echo -e "${RED}[WARNING]${NC} $1"
}

log_info "Stopping DocuSearch MVP services..."

cd "$PROJECT_ROOT/docker"

if [ "$REMOVE_VOLUMES" = true ]; then
  log_warning "Removing volumes (all data will be lost)..."
  docker-compose down -v
  log_success "Services stopped and volumes removed"
else
  docker-compose down
  log_success "Services stopped (data preserved)"
fi
