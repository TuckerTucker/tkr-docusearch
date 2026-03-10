#!/bin/bash
# ============================================================================
# Run Processing Worker Natively (with Metal/MPS support)
# ============================================================================
# This script runs the processing worker directly on macOS to access Metal GPU.
#
# Usage:
#   ./scripts/run-worker-native.sh [setup|run|check]
#
# Commands:
#   setup - Install Python dependencies natively
#   run   - Run the worker with Metal/MPS
#   check - Check Metal availability
# ============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Configuration
# ============================================================================

PYTHON="${PYTHON:-python3}"
VENV_DIR="${VENV_DIR:-.venv-native}"

# Environment variables for worker
export DEVICE="mps"
export MODEL_NAME="${MODEL_NAME:-default}"
export MODEL_PRECISION="${MODEL_PRECISION:-fp16}"
export BATCH_SIZE_VISUAL="${BATCH_SIZE_VISUAL:-4}"
export BATCH_SIZE_TEXT="${BATCH_SIZE_TEXT:-8}"

# File paths
export UPLOADS_DIR="${UPLOADS_DIR:-${PROJECT_ROOT}/data/uploads}"

# Load SUPPORTED_FORMATS from docker/.env if available
if [ -f "${PROJECT_ROOT}/docker/.env" ]; then
    # Extract SUPPORTED_FORMATS from .env file
    SUPPORTED_FORMATS_FROM_ENV=$(grep "^SUPPORTED_FORMATS=" "${PROJECT_ROOT}/docker/.env" | cut -d '=' -f2)
    export SUPPORTED_FORMATS="${SUPPORTED_FORMATS:-${SUPPORTED_FORMATS_FROM_ENV}}"
else
    # Fallback to comprehensive list
    export SUPPORTED_FORMATS="${SUPPORTED_FORMATS:-pdf,docx,pptx,xlsx,md,html,htm,xhtml,asciidoc,csv,png,jpg,jpeg,tiff,bmp,webp,vtt,wav,mp3,xml,json}"
fi
export MAX_FILE_SIZE_MB="${MAX_FILE_SIZE_MB:-100}"

# ASR (Whisper) configuration for audio transcription
export ASR_ENABLED="${ASR_ENABLED:-true}"
export ASR_MODEL="${ASR_MODEL:-turbo}"
export ASR_LANGUAGE="${ASR_LANGUAGE:-en}"
export ASR_DEVICE="${ASR_DEVICE:-mps}"
export ASR_WORD_TIMESTAMPS="${ASR_WORD_TIMESTAMPS:-true}"
export ASR_TEMPERATURE="${ASR_TEMPERATURE:-0.0}"
export ASR_MAX_TIME_CHUNK="${ASR_MAX_TIME_CHUNK:-30.0}"

# Legacy Office Converter configuration (PPTX rendering + DOC conversion)
export LEGACY_OFFICE_HOST="${LEGACY_OFFICE_HOST:-localhost}"
export LEGACY_OFFICE_PORT="${LEGACY_OFFICE_PORT:-8003}"
# Backward compatibility: Allow old SLIDE_RENDERER_* variables
export SLIDE_RENDERER_HOST="${SLIDE_RENDERER_HOST:-${LEGACY_OFFICE_HOST}}"
export SLIDE_RENDERER_PORT="${SLIDE_RENDERER_PORT:-${LEGACY_OFFICE_PORT}}"

# Logging
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export PYTHONUNBUFFERED=1


# ============================================================================
# Functions
# ============================================================================

check_metal() {
    echo -e "${BLUE}Checking Metal/MPS availability...${NC}"

    # Try venv Python first, fall back to system Python
    local VENV_PYTHON="${PROJECT_ROOT}/${VENV_DIR}/bin/python"
    local CHECK_PYTHON=""

    if [ -f "$VENV_PYTHON" ] && "$VENV_PYTHON" -c "import torch" 2>/dev/null; then
        CHECK_PYTHON="$VENV_PYTHON"
    elif python3 -c "import torch" 2>/dev/null; then
        CHECK_PYTHON="python3"
    else
        echo -e "${YELLOW}PyTorch not found. Cannot check MPS availability.${NC}"
        return 1
    fi

    # Check MPS availability
    MPS_AVAILABLE=$("$CHECK_PYTHON" -c "import torch; print(torch.backends.mps.is_available())" 2>/dev/null)
    MPS_BUILT=$("$CHECK_PYTHON" -c "import torch; print(torch.backends.mps.is_built())" 2>/dev/null)

    echo -e "  MPS Available: ${GREEN}${MPS_AVAILABLE}${NC}"
    echo -e "  MPS Built: ${GREEN}${MPS_BUILT}${NC}"

    if [ "$MPS_AVAILABLE" = "True" ]; then
        echo -e "${GREEN}✓ Metal/MPS is available!${NC}"
        return 0
    else
        echo -e "${RED}✗ Metal/MPS is not available${NC}"
        echo -e "${YELLOW}Note: MPS requires macOS 12.3+ and PyTorch 1.12+${NC}"
        return 1
    fi
}

setup_venv() {
    echo -e "${BLUE}Setting up Python virtual environment...${NC}"

    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating virtual environment: $VENV_DIR"
        $PYTHON -m venv "$VENV_DIR"
    fi

    source "$VENV_DIR/bin/activate"

    echo -e "${BLUE}Installing dependencies...${NC}"

    # Upgrade pip
    pip install --upgrade pip

    # Install all dependencies from requirements.txt
    # This includes: PyTorch, transformers, Koji, Docling, mutagen, and all other dependencies
    if [ -f "${PROJECT_ROOT}/requirements.txt" ]; then
        echo "Installing dependencies from requirements.txt..."
        pip install -r "${PROJECT_ROOT}/requirements.txt"
    else
        echo -e "${RED}Error: requirements.txt not found at ${PROJECT_ROOT}/requirements.txt${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ Dependencies installed${NC}"

    # Check Metal availability
    check_metal
}

run_worker() {
    echo -e "${BLUE}Starting worker with Metal/MPS...${NC}"

    # Note: .venv-native is not used — system Python has all deps via pip install -e .

    # Ensure Homebrew binaries (including ffmpeg) are in PATH
    export PATH="/opt/homebrew/bin:$PATH"

    # Verify uploads directory
    if [ ! -d "$UPLOADS_DIR" ]; then
        echo -e "${YELLOW}Creating uploads directory: $UPLOADS_DIR${NC}"
        mkdir -p "$UPLOADS_DIR"
    fi

    # Check Metal one more time
    check_metal || {
        echo -e "${YELLOW}Warning: Running without Metal acceleration${NC}"
        export DEVICE="cpu"
    }

    echo -e "${BLUE}Configuration:${NC}"
    echo "  Device: $DEVICE"
    echo "  Model: $MODEL_NAME"
    echo "  Precision: $MODEL_PRECISION"
    echo "  Uploads: $UPLOADS_DIR"
    echo ""

    # Run the worker
    echo -e "${GREEN}Starting worker on http://0.0.0.0:8002${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""

    cd "$PROJECT_ROOT"
    exec python3 -m tkr_docusearch.processing.worker_webhook
}

show_help() {
    cat << EOF
${BLUE}DocuSearch Native Worker Runner${NC}

Run the processing worker natively on macOS to access Metal GPU acceleration.

${YELLOW}Usage:${NC}
  ./scripts/run-worker-native.sh [command]

${YELLOW}Commands:${NC}
  setup     Install Python dependencies in virtual environment
  run       Run the worker with Metal/MPS support
  check     Check Metal/MPS availability
  help      Show this help message

${YELLOW}Examples:${NC}
  # First time setup
  ./scripts/run-worker-native.sh setup

  # Run worker
  ./scripts/run-worker-native.sh run

  # Check if Metal is available
  ./scripts/run-worker-native.sh check

${YELLOW}Environment Variables:${NC}
  DEVICE              GPU device (default: mps)
  MODEL_NAME          Model to use (default: default)

${YELLOW}Notes:${NC}
  - Requires macOS 12.3+ for Metal/MPS support
  - Worker uses Koji (embedded DB) for storage
  - Worker runs on http://0.0.0.0:8002
EOF
}

# ============================================================================
# Main
# ============================================================================

COMMAND="${1:-help}"

case "$COMMAND" in
    setup)
        setup_venv
        ;;
    run)
        run_worker
        ;;
    check)
        check_metal
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Error: Unknown command '$COMMAND'${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
