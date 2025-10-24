#!/usr/bin/env bash
# ============================================================================
# Model Download Status Monitor
# ============================================================================
# Monitors HuggingFace model downloads for:
# - gpt-oss-20b-MLX-4bit (~11GB) - Local preprocessing
# - ColPali models (~2-3GB) - Document embeddings
#
# Usage:
#   ./scripts/model-download-status.sh           # One-time check
#   ./scripts/model-download-status.sh --watch   # Continuous monitoring
# ============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Load environment variables if .env exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

# Model paths
MODELS_DIR="${HF_HOME:-$PROJECT_ROOT/data/models}"
MLX_MODEL_PATH="${MLX_MODEL_PATH:-$MODELS_DIR/gpt-oss-20b-MLX-4bit}"
COLPALI_MODEL="vidore/colpali-v1.2"

# Expected sizes (in GB)
MLX_MODEL_SIZE=11
COLPALI_MODEL_SIZE=2.5

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "\n${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${CYAN}  $1${NC}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_section() {
    echo -e "${BOLD}${CYAN}▶ $1${NC}"
}

print_status() {
    local status=$1
    local message=$2

    case $status in
        "complete")
            echo -e "  ${GREEN}✓${NC} $message"
            ;;
        "downloading")
            echo -e "  ${YELLOW}⬇${NC} $message"
            ;;
        "missing")
            echo -e "  ${RED}✗${NC} $message"
            ;;
        "info")
            echo -e "  ${BLUE}ℹ${NC} $message"
            ;;
    esac
}

format_size() {
    local size=$1
    if [ -z "$size" ]; then
        echo "0B"
    else
        echo "$size"
    fi
}

get_dir_size_gb() {
    local dir=$1
    if [ -d "$dir" ]; then
        # macOS compatible - get size in GB
        local size_kb=$(du -sk "$dir" 2>/dev/null | cut -f1)
        if [ -n "$size_kb" ]; then
            echo "scale=2; $size_kb / 1024 / 1024" | bc
        else
            echo "0"
        fi
    else
        echo "0"
    fi
}

check_file() {
    local file=$1
    local name=$2

    if [ -f "$file" ]; then
        local size=$(ls -lh "$file" 2>/dev/null | awk '{print $5}')
        print_status "complete" "$name ($(format_size $size))"
        return 0
    else
        print_status "missing" "$name"
        return 1
    fi
}

check_model_weights() {
    local model_dir=$1

    # Check for single file
    if [ -f "$model_dir/model.safetensors" ]; then
        local size=$(ls -lh "$model_dir/model.safetensors" 2>/dev/null | awk '{print $5}')
        print_status "complete" "Model weights: model.safetensors ($(format_size $size))"
        return 0
    fi

    # Check for sharded files
    local shard_files=("$model_dir"/model-*-of-*.safetensors)
    if [ -e "${shard_files[0]}" ]; then
        local shard_count=$(ls "$model_dir"/model-*-of-*.safetensors 2>/dev/null | wc -l | tr -d ' ')
        local total_size=$(du -sh "$model_dir"/model-*.safetensors 2>/dev/null | tail -1 | awk '{print $1}')
        print_status "complete" "Model weights: $shard_count shards ($(format_size $total_size))"
        return 0
    fi

    print_status "missing" "Model weights (no .safetensors files found)"
    return 1
}

calculate_progress() {
    local current=$1
    local expected=$2

    if [ "$expected" = "0" ]; then
        echo "0"
    else
        echo "scale=0; $current * 100 / $expected" | bc
    fi
}

# ============================================================================
# Model Status Checks
# ============================================================================

check_mlx_model() {
    print_section "MLX Model (gpt-oss-20b-MLX-4bit)"

    if [ ! -d "$MLX_MODEL_PATH" ]; then
        print_status "missing" "Model directory not found"
        print_status "info" "Run: ./scripts/setup-mlx-model.sh"
        echo ""
        return 1
    fi

    local current_size=$(get_dir_size_gb "$MLX_MODEL_PATH")
    local progress=$(calculate_progress ${current_size%.*} $MLX_MODEL_SIZE)

    print_status "info" "Location: $MLX_MODEL_PATH"
    print_status "info" "Size: ${current_size}GB / ${MLX_MODEL_SIZE}GB (${progress}%)"

    # Check required files
    local all_present=true

    check_file "$MLX_MODEL_PATH/config.json" "config.json" || all_present=false
    check_file "$MLX_MODEL_PATH/tokenizer.json" "tokenizer.json" || all_present=false
    check_file "$MLX_MODEL_PATH/tokenizer_config.json" "tokenizer_config.json" || all_present=false
    check_model_weights "$MLX_MODEL_PATH" || all_present=false

    echo ""

    if [ "$all_present" = true ]; then
        if [ "${current_size%.*}" -ge "$MLX_MODEL_SIZE" ]; then
            print_status "complete" "${BOLD}MLX model is complete and ready${NC}"
        else
            print_status "downloading" "${BOLD}MLX model is downloading (${progress}%)${NC}"
        fi
        return 0
    else
        print_status "missing" "${BOLD}MLX model is incomplete${NC}"
        print_status "info" "Run: ./scripts/setup-mlx-model.sh"
        return 1
    fi
}

check_colpali_model() {
    print_section "ColPali Model (vidore/colpali-v1.2)"

    # ColPali models are stored in HuggingFace hub cache
    local hub_dir="$MODELS_DIR/hub"

    if [ ! -d "$hub_dir" ]; then
        print_status "missing" "HuggingFace cache directory not found"
        print_status "info" "Model will download on first worker startup"
        echo ""
        return 1
    fi

    # Look for ColPali model in snapshots
    local colpali_found=false
    local colpali_size="0"

    # Search for model files (they have specific patterns)
    if find "$hub_dir" -name "*.safetensors" -o -name "config.json" 2>/dev/null | grep -q "models--vidore--colpali"; then
        colpali_found=true
        local model_dir=$(find "$hub_dir" -type d -name "*vidore*colpali*" 2>/dev/null | head -1)
        if [ -n "$model_dir" ]; then
            colpali_size=$(get_dir_size_gb "$model_dir")
        fi
    fi

    if [ "$colpali_found" = true ]; then
        local progress=$(calculate_progress ${colpali_size%.*} ${COLPALI_MODEL_SIZE%.*})
        print_status "info" "Cache location: $hub_dir"
        print_status "info" "Size: ${colpali_size}GB / ${COLPALI_MODEL_SIZE}GB (${progress}%)"

        if [ "${colpali_size%.*}" -ge "${COLPALI_MODEL_SIZE%.*}" ]; then
            print_status "complete" "${BOLD}ColPali model is complete and ready${NC}"
        else
            print_status "downloading" "${BOLD}ColPali model is downloading (${progress}%)${NC}"
        fi
        echo ""
        return 0
    else
        print_status "missing" "ColPali model not found in cache"
        print_status "info" "Model will download on first worker startup"
        echo ""
        return 1
    fi
}

check_download_processes() {
    print_section "Active Download Processes"

    local processes_found=false

    # Check for huggingface-cli
    if pgrep -f "huggingface-cli download" > /dev/null; then
        print_status "downloading" "huggingface-cli download (MLX model)"
        processes_found=true
    fi

    # Check for Python processes that might be downloading
    if pgrep -f "python.*from_pretrained" > /dev/null; then
        print_status "downloading" "Python model download (likely ColPali)"
        processes_found=true
    fi

    # Check for general HuggingFace downloads
    if lsof -i -n 2>/dev/null | grep -q "huggingface.co"; then
        print_status "downloading" "Active connection to huggingface.co"
        processes_found=true
    fi

    if [ "$processes_found" = false ]; then
        print_status "info" "No active downloads detected"
    fi

    echo ""
}

check_disk_space() {
    print_section "Disk Space"

    local available=$(df -h "$MODELS_DIR" 2>/dev/null | tail -1 | awk '{print $4}')
    local used=$(df -h "$MODELS_DIR" 2>/dev/null | tail -1 | awk '{print $3}')
    local capacity=$(df -h "$MODELS_DIR" 2>/dev/null | tail -1 | awk '{print $5}')

    print_status "info" "Available: $available"
    print_status "info" "Used: $used ($capacity)"

    # Check if we have enough space (20GB recommended for both models + headroom)
    local available_gb=$(echo $available | sed 's/[^0-9.]//g' | cut -d. -f1)
    if [ -n "$available_gb" ] && [ "$available_gb" != "" ] && [ "$available_gb" -lt 20 ] 2>/dev/null; then
        print_status "missing" "${YELLOW}Low disk space! Need ~20GB for all models${NC}"
    else
        print_status "complete" "Sufficient space for model downloads"
    fi

    echo ""
}

print_summary() {
    print_section "Summary & Next Steps"

    # Check overall status
    local mlx_ready=false
    local colpali_ready=false

    if [ -f "$MLX_MODEL_PATH/config.json" ]; then
        local mlx_size=$(get_dir_size_gb "$MLX_MODEL_PATH")
        if [ "${mlx_size%.*}" -ge "$MLX_MODEL_SIZE" ]; then
            mlx_ready=true
        fi
    fi

    local hub_dir="$MODELS_DIR/hub"
    if [ -d "$hub_dir" ] && find "$hub_dir" -name "*.safetensors" 2>/dev/null | grep -q "colpali"; then
        colpali_ready=true
    fi

    if [ "$mlx_ready" = true ] && [ "$colpali_ready" = true ]; then
        echo -e "${GREEN}✓ All models downloaded and ready!${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Start services: ./scripts/start-all.sh"
        echo "  2. Check status: ./scripts/status.sh"
        echo "  3. Open UI: http://localhost:3000"
    elif [ "$mlx_ready" = false ] && [ "$colpali_ready" = false ]; then
        echo -e "${YELLOW}⚠ No models downloaded yet${NC}"
        echo ""
        echo "To download models:"
        echo "  1. MLX model: ./scripts/setup-mlx-model.sh"
        echo "  2. ColPali: Will auto-download on first worker startup"
        echo "  3. Start all: ./scripts/start-all.sh"
    elif [ "$mlx_ready" = false ]; then
        echo -e "${YELLOW}⚠ MLX model not ready${NC}"
        echo ""
        echo "To download MLX model:"
        echo "  ./scripts/setup-mlx-model.sh"
    elif [ "$colpali_ready" = false ]; then
        echo -e "${YELLOW}⚠ ColPali model not ready${NC}"
        echo ""
        echo "ColPali will auto-download on first worker startup:"
        echo "  ./scripts/start-all.sh"
    fi

    echo ""
}

# ============================================================================
# Main Status Display
# ============================================================================

display_status() {
    clear

    print_header "Model Download Status"

    echo -e "Timestamp: ${CYAN}$(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo -e "Models Directory: ${CYAN}$MODELS_DIR${NC}"
    echo ""

    check_disk_space
    check_download_processes
    check_mlx_model
    check_colpali_model
    print_summary
}

# ============================================================================
# Watch Mode
# ============================================================================

watch_mode() {
    echo "Starting continuous monitoring (Ctrl+C to stop)..."
    echo "Refresh interval: 2 seconds"
    sleep 2

    while true; do
        display_status
        sleep 2
    done
}

# ============================================================================
# Main
# ============================================================================

case "${1:-}" in
    --watch|-w)
        watch_mode
        ;;
    --help|-h)
        echo "Model Download Status Monitor"
        echo ""
        echo "Usage:"
        echo "  $0           # One-time status check"
        echo "  $0 --watch   # Continuous monitoring (2s refresh)"
        echo "  $0 --help    # Show this help"
        echo ""
        echo "Models monitored:"
        echo "  - gpt-oss-20b-MLX-4bit (~11GB) - Local preprocessing"
        echo "  - vidore/colpali-v1.2 (~2.5GB) - Document embeddings"
        exit 0
        ;;
    "")
        display_status
        ;;
    *)
        echo "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac
