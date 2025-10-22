#!/usr/bin/env bash
# ============================================================================
# MLX Model Setup Script
# ============================================================================
# Downloads and validates gpt-oss-20B MLX model for local preprocessing
#
# Usage:
#   ./scripts/setup-mlx-model.sh
#
# Requirements:
#   - huggingface-cli (pip install huggingface-hub)
#   - 16GB+ disk space (model is ~11GB)
#   - Python environment with MLX-LM
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

# Load environment variables if .env exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    # Export variables from .env
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

# Get model path from environment or use default
MLX_MODEL_PATH="${MLX_MODEL_PATH:-$PROJECT_ROOT/data/models/gpt-oss-20b-MLX-4bit}"
HF_REPO="InferenceIllusionist/gpt-oss-20b-MLX-4bit"

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

check_disk_space() {
    local required_gb=$1
    # macOS compatible disk space check
    local available_gb=$(df -h "$PROJECT_ROOT" | tail -1 | awk '{print $4}' | sed 's/Gi\?//')

    # Convert to integer if fractional
    available_gb=${available_gb%.*}

    if [ -z "$available_gb" ] || [ "$available_gb" = "" ]; then
        log_warning "Could not determine available disk space"
        return 0  # Continue anyway
    elif [ "$available_gb" -lt "$required_gb" ]; then
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

log_info "Starting MLX model setup for local preprocessing..."
echo ""

# Check if model already exists
if [ -d "$MLX_MODEL_PATH" ] && [ -f "$MLX_MODEL_PATH/config.json" ]; then
    log_warning "Model already exists at: $MLX_MODEL_PATH"
    read -p "Do you want to re-download? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Skipping download. Validating existing model..."
        # Skip to validation
    else
        log_info "Removing existing model..."
        rm -rf "$MLX_MODEL_PATH"
    fi
fi

# Check disk space (model is ~11GB)
if ! check_disk_space 16; then
    log_error "Insufficient disk space for model download"
    exit 1
fi

# Check if huggingface-cli is installed
if ! command -v huggingface-cli &> /dev/null; then
    log_error "huggingface-cli not found"
    log_info "Install with: pip install huggingface-hub"
    exit 1
fi

log_success "Pre-flight checks passed"
echo ""

# ============================================================================
# Download Model
# ============================================================================

if [ ! -f "$MLX_MODEL_PATH/config.json" ]; then
    log_info "Downloading gpt-oss-20B MLX model (~11GB, 4-bit quantized)..."
    log_info "Repository: $HF_REPO"
    log_info "Destination: $MLX_MODEL_PATH"
    echo ""

    # Create parent directory
    mkdir -p "$(dirname "$MLX_MODEL_PATH")"

    # Download model
    if huggingface-cli download "$HF_REPO" \
        --local-dir "$MLX_MODEL_PATH" \
        --local-dir-use-symlinks False; then
        log_success "Model downloaded successfully"
    else
        log_error "Model download failed"
        exit 1
    fi
    echo ""
fi

# ============================================================================
# Validate Model
# ============================================================================

log_info "Validating model files..."

# Required files
required_files=(
    "config.json"
    "tokenizer_config.json"
    "tokenizer.json"
)

all_files_present=true
for file in "${required_files[@]}"; do
    if [ -f "$MLX_MODEL_PATH/$file" ]; then
        log_success "✓ $file"
    else
        log_error "✗ $file (missing)"
        all_files_present=false
    fi
done

# Check for model weights (either single file or sharded)
if [ -f "$MLX_MODEL_PATH/model.safetensors" ]; then
    log_success "✓ model.safetensors"
elif ls "$MLX_MODEL_PATH"/model-*-of-*.safetensors 1> /dev/null 2>&1; then
    shard_count=$(ls "$MLX_MODEL_PATH"/model-*-of-*.safetensors | wc -l | tr -d ' ')
    log_success "✓ model weights (${shard_count} shards)"
else
    log_error "✗ model weights (missing)"
    all_files_present=false
fi

if [ "$all_files_present" = false ]; then
    log_error "Model validation failed - missing required files"
    exit 1
fi

echo ""
log_success "Model validation passed"
echo ""

# ============================================================================
# Test Model Loading (Optional)
# ============================================================================

log_info "Testing model loading..."
echo ""

# Check if Python is available
if command -v python &> /dev/null; then
    python - <<EOFPYTHON
import sys
import os

try:
    # Test MLX-LM import
    from mlx_lm import load
    print("✓ MLX-LM installed")

    # Test model loading
    model_path = "$MLX_MODEL_PATH"
    print(f"Loading model from: {model_path}")

    model, tokenizer = load(model_path)
    print("✓ Model loaded successfully")

    # Test basic inference
    print("Testing inference...")
    from mlx_lm import generate
    prompt = "The capital of France is"
    response = generate(model, tokenizer, prompt=prompt, max_tokens=5, verbose=False)
    print(f"✓ Inference test passed: '{prompt}' -> '{response}'")

    print("\n✅ All tests passed - model is ready!")
    sys.exit(0)

except ImportError as e:
    print(f"⚠ MLX-LM not installed: {e}")
    print("Install with: pip install mlx-lm>=0.19.3")
    sys.exit(1)

except Exception as e:
    print(f"❌ Model loading failed: {e}")
    sys.exit(1)
EOFPYTHON

    test_result=$?
    echo ""

    if [ $test_result -eq 0 ]; then
        log_success "Model loading test passed"
    else
        log_warning "Model loading test failed (but model files are present)"
        log_info "This may be due to missing dependencies (mlx-lm)"
    fi
else
    log_warning "Python not found in PATH - skipping model loading test"
fi

echo ""

# ============================================================================
# Update .env Configuration
# ============================================================================

log_info "Checking .env configuration..."

if [ -f "$PROJECT_ROOT/.env" ]; then
    # Check if MLX_MODEL_PATH is set correctly
    if grep -q "^MLX_MODEL_PATH=" "$PROJECT_ROOT/.env"; then
        current_path=$(grep "^MLX_MODEL_PATH=" "$PROJECT_ROOT/.env" | cut -d'=' -f2-)
        if [ "$current_path" = "$MLX_MODEL_PATH" ]; then
            log_success "MLX_MODEL_PATH already configured correctly"
        else
            log_warning "MLX_MODEL_PATH in .env differs from downloaded location"
            log_info "  .env:       $current_path"
            log_info "  Downloaded: $MLX_MODEL_PATH"
        fi
    else
        log_warning "MLX_MODEL_PATH not found in .env"
        log_info "Add this line to .env:"
        echo "  MLX_MODEL_PATH=$MLX_MODEL_PATH"
    fi

    # Check if preprocessing is enabled
    if grep -q "^LOCAL_PREPROCESS_ENABLED=true" "$PROJECT_ROOT/.env"; then
        log_success "Local preprocessing is enabled"
    else
        log_info "Local preprocessing is disabled"
        log_info "To enable, set in .env:"
        echo "  LOCAL_PREPROCESS_ENABLED=true"
    fi
else
    log_warning ".env file not found"
    log_info "Create .env from .env.example and configure preprocessing"
fi

echo ""

# ============================================================================
# Summary
# ============================================================================

log_success "=========================================="
log_success "MLX Model Setup Complete!"
log_success "=========================================="
echo ""
log_info "Model location:"
echo "  $MLX_MODEL_PATH"
echo ""
log_info "Model details:"
echo "  Repository: $HF_REPO"
echo "  Size: ~11GB (4-bit quantized)"
echo "  Context: 32K tokens"
echo "  Performance: ~15-30 tokens/sec (M1 Mac)"
echo ""
log_info "Next steps:"
echo "  1. Ensure .env has correct MLX_MODEL_PATH"
echo "  2. Enable preprocessing: LOCAL_PREPROCESS_ENABLED=true"
echo "  3. Restart research API: ./scripts/stop-all.sh && ./scripts/start-all.sh"
echo "  4. Test with a query to verify preprocessing works"
echo ""
log_info "Verification:"
echo "  Check research API logs for: 'MLX client initialized'"
echo "  Query metadata should show 'preprocessing_enabled: true'"
echo ""
