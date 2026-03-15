#!/usr/bin/env bash
# ============================================================================
# DocuSearch MVP - Setup Script
# ============================================================================
# Initializes project environment, validates requirements, and prepares system
# for document processing and semantic search
#
# Usage:
#   ./scripts/setup.sh [--skip-model-download]
#
# Requirements:
#   - Docker and Docker Compose
#   - 20GB+ free disk space (model cache + data)
#   - 16GB+ RAM (recommended for FP16)
#   - M1/M2 Mac OR NVIDIA GPU OR CPU fallback
# ============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKIP_MODEL_DOWNLOAD=false

# Parse command line arguments
for arg in "$@"; do
  case $arg in
    --skip-model-download)
      SKIP_MODEL_DOWNLOAD=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [--skip-model-download]"
      echo ""
      echo "Options:"
      echo "  --skip-model-download  Skip pre-downloading the ColNomic 7B model"
      echo "  --help, -h             Show this help message"
      exit 0
      ;;
  esac
done

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
  if command -v "$1" &> /dev/null; then
    log_success "$1 is installed"
    return 0
  else
    log_error "$1 is not installed"
    return 1
  fi
}

check_disk_space() {
  local required_gb=$1
  local available_gb=$(df -BG "$PROJECT_ROOT" | tail -1 | awk '{print $4}' | sed 's/G//')

  if [ "$available_gb" -lt "$required_gb" ]; then
    log_error "Insufficient disk space: ${available_gb}GB available, ${required_gb}GB required"
    return 1
  else
    log_success "Sufficient disk space: ${available_gb}GB available"
    return 0
  fi
}

# ============================================================================
# Pre-flight Checks
# ============================================================================

log_info "Starting DocuSearch MVP setup..."
echo ""

log_info "Checking system requirements..."

# Check Docker
if ! check_command docker; then
  log_error "Please install Docker: https://docs.docker.com/get-docker/"
  exit 1
fi

# Check Docker Compose
if ! check_command docker-compose && ! docker compose version &> /dev/null; then
  log_error "Please install Docker Compose"
  exit 1
fi

# Check disk space
if ! check_disk_space 20; then
  log_warning "Low disk space may cause issues during model download"
fi

# Check Docker daemon
if ! docker info &> /dev/null; then
  log_error "Docker daemon is not running. Please start Docker."
  exit 1
fi

log_success "All system requirements met"
echo ""

# ============================================================================
# Create Directory Structure
# ============================================================================

log_info "Creating directory structure..."

mkdir -p \
  "$PROJECT_ROOT/data/uploads" \
  "$PROJECT_ROOT/data/models" \
  "$PROJECT_ROOT/data/koji" \
  "$PROJECT_ROOT/data/logs" \
  "$PROJECT_ROOT/src/storage" \
  "$PROJECT_ROOT/src/embeddings" \
  "$PROJECT_ROOT/src/processing" \
  "$PROJECT_ROOT/src/search" \
  "$PROJECT_ROOT/src/config"

# Set permissions
chmod 755 "$PROJECT_ROOT/data"
chmod 777 "$PROJECT_ROOT/data/uploads"  # Writable by worker
chmod 777 "$PROJECT_ROOT/data/models"   # Writable by worker
chmod 777 "$PROJECT_ROOT/data/koji"     # Writable by Koji Lance DB
chmod 777 "$PROJECT_ROOT/data/logs"     # Writable by worker

log_success "Directory structure created"
echo ""

# ============================================================================
# Environment Configuration
# ============================================================================

log_info "Setting up environment configuration..."

if [ ! -f "$PROJECT_ROOT/docker/.env" ]; then
  if [ -f "$PROJECT_ROOT/docker/.env.template" ]; then
    cp "$PROJECT_ROOT/docker/.env.template" "$PROJECT_ROOT/docker/.env"
    log_success "Created .env from template"
  else
    log_error ".env.template not found"
    exit 1
  fi
else
  log_info ".env already exists, skipping"
fi

echo ""

# ============================================================================
# Build Docker Images
# ============================================================================

log_info "Building Docker images..."
cd "$PROJECT_ROOT/docker"

if docker-compose build; then
  log_success "Docker images built successfully"
else
  log_error "Docker build failed"
  exit 1
fi

echo ""

# ============================================================================
# Pre-download Model (Optional)
# ============================================================================

if [ "$SKIP_MODEL_DOWNLOAD" = false ]; then
  log_info "Pre-downloading ColNomic 7B model (14GB, this may take a while)..."
  log_warning "Press Ctrl+C to skip model download (will download on first run instead)"

  sleep 3

  docker-compose run --rm processing-worker python3 -c "
from transformers import AutoModel
import os

model_name = os.getenv('MODEL_NAME', 'vidore/colqwen2-v0.1')
print(f'Downloading model: {model_name}')
print('This will take several minutes...')

try:
    model = AutoModel.from_pretrained(
        model_name,
        cache_dir='/models',
        trust_remote_code=True
    )
    print('Model downloaded successfully!')
except Exception as e:
    print(f'Model download failed: {e}')
    print('Model will be downloaded on first processing run')
" || log_warning "Model download failed, will retry on first run"

  echo ""
else
  log_info "Skipping model download (will download on first run)"
  echo ""
fi

# ============================================================================
# Validate MPS Support (M1 Mac)
# ============================================================================

log_info "Validating PyTorch MPS support..."

if docker-compose run --rm processing-worker python3 -c "
import torch
import sys

mps_available = torch.backends.mps.is_available()
mps_built = torch.backends.mps.is_built()

print(f'PyTorch version: {torch.__version__}')
print(f'MPS available: {mps_available}')
print(f'MPS built: {mps_built}')

if mps_available:
    print('✓ MPS acceleration enabled (M1/M2 Mac GPU)')
    sys.exit(0)
elif torch.cuda.is_available():
    print('✓ CUDA acceleration available (NVIDIA GPU)')
    sys.exit(0)
else:
    print('⚠ CPU fallback mode (slower performance)')
    sys.exit(0)
"; then
  log_success "Device acceleration validated"
else
  log_warning "Acceleration validation failed, will use CPU"
fi

echo ""

log_success "Koji database directory created at data/koji"
echo ""

# ============================================================================
# Summary
# ============================================================================

log_success "=========================================="
log_success "DocuSearch MVP Setup Complete!"
log_success "=========================================="
echo ""
log_info "Next steps:"
echo "  1. Start services:     cd docker && docker-compose up"
echo "  2. Access UI:          http://localhost:8000"
echo "  3. Upload documents:   Use the web interface"
echo "  4. View logs:          docker-compose logs -f processing-worker"
echo ""
log_info "Wave 1 Status:"
echo "  ✓ Integration contracts defined"
echo "  ✓ Docker infrastructure created"
echo "  ✓ Directory structure initialized"
echo "  ✓ Environment configured"
if [ "$SKIP_MODEL_DOWNLOAD" = false ]; then
  echo "  ✓ Model pre-downloaded (or will download on first run)"
else
  echo "  ⚠ Model will download on first processing run"
fi
echo ""
log_info "Ready for Wave 2: Component Implementation"
echo ""
