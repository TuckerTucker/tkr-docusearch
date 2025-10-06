# Configuration Interface Contract

**Owner**: infrastructure-agent
**Consumers**: All agents
**Purpose**: Define environment variables, configuration files, and service settings

---

## Environment Variables

### Core Configuration

All services are configured via environment variables defined in `docker/.env`:

```bash
# ============================================================================
# Project Configuration
# ============================================================================
PROJECT_NAME=docusearch-mvp
PROJECT_VERSION=0.1.0
ENVIRONMENT=development  # development | staging | production

# ============================================================================
# Service Ports
# ============================================================================
COPYPARTY_PORT=8000      # Web UI and file upload
CHROMADB_PORT=8001       # Vector database HTTP API
WORKER_PORT=8002         # Processing worker API (optional, for status queries)

# ============================================================================
# Volume Mounts
# ============================================================================
UPLOAD_DIR=./data/uploads          # Copyparty upload directory
MODELS_CACHE=./data/models         # Model cache (14GB+ for ColNomic 7B)
CHROMA_DATA=./data/chroma_db       # ChromaDB persistence
LOGS_DIR=./data/logs               # Processing logs and status files

# ============================================================================
# Model Configuration
# ============================================================================
MODEL_NAME=vidore/colqwen2-v0.1    # ColPali model identifier
MODEL_PRECISION=fp16               # fp16 | int8
DEVICE=mps                         # mps | cuda | cpu (auto-detect fallback)
BATCH_SIZE_VISUAL=4                # Images per batch (memory-dependent)
BATCH_SIZE_TEXT=8                  # Text chunks per batch

# ============================================================================
# Processing Configuration
# ============================================================================
MAX_FILE_SIZE_MB=100               # Reject files larger than this
SUPPORTED_FORMATS=pdf,docx,pptx    # Comma-separated
TEXT_CHUNK_SIZE=250                # Average words per chunk
TEXT_CHUNK_OVERLAP=50              # Word overlap between chunks
PAGE_RENDER_DPI=150                # Image resolution for visual processing

# ============================================================================
# ChromaDB Configuration
# ============================================================================
CHROMA_HOST=chromadb               # Service name in docker-compose
CHROMA_PORT=8001                   # Internal container port
VISUAL_COLLECTION=visual_collection
TEXT_COLLECTION=text_collection
CHROMA_BATCH_SIZE=100              # Embeddings per batch insert

# ============================================================================
# Performance Tuning
# ============================================================================
WORKER_THREADS=1                   # Parallel processing workers (1 for MVP)
ENABLE_QUEUE=false                 # Queue system (Wave 4 feature)
CACHE_EMBEDDINGS=false             # Cache embeddings in memory (Wave 4)

# ============================================================================
# Logging
# ============================================================================
LOG_LEVEL=INFO                     # DEBUG | INFO | WARNING | ERROR
LOG_FORMAT=json                    # json | text
LOG_FILE=/data/logs/worker.log     # Worker log file path

# ============================================================================
# Security (Production)
# ============================================================================
COPYPARTY_AUTH_ENABLED=false       # Enable authentication (production)
COPYPARTY_USERNAME=admin           # Default admin user
COPYPARTY_PASSWORD=changeme        # CHANGE IN PRODUCTION
```

---

## Configuration Files

### 1. Docker Compose Configuration

**File**: `docker/docker-compose.yml`

```yaml
version: '3.8'

services:
  copyparty:
    build:
      context: .
      dockerfile: Dockerfile.copyparty
    ports:
      - "${COPYPARTY_PORT}:8000"
    volumes:
      - ${UPLOAD_DIR}:/uploads
      - ../data/copyparty/www:/www  # Custom web UI
      - ../data/copyparty/hooks:/hooks  # Event hooks
    environment:
      - CPP_PORT=8000
      - CPP_UPLOAD_DIR=/uploads
      - CPP_HOOK_ON_UPLOAD=/hooks/on_upload.py
    networks:
      - docusearch

  chromadb:
    image: chromadb/chroma:latest
    platform: linux/arm64
    ports:
      - "${CHROMADB_PORT}:8000"
    volumes:
      - ${CHROMA_DATA}:/chroma/chroma
    environment:
      - IS_PERSISTENT=TRUE
      - ANONYMIZED_TELEMETRY=FALSE
    networks:
      - docusearch

  processing-worker:
    build:
      context: .
      dockerfile: Dockerfile.processing-worker
      args:
        - BUILDPLATFORM=linux/arm64
        - TARGETPLATFORM=linux/arm64
    volumes:
      - ${UPLOAD_DIR}:/uploads:ro  # Read-only access
      - ${MODELS_CACHE}:/models    # Model cache
      - ${LOGS_DIR}:/data/logs     # Log output
      - ../src:/app/src            # Source code (development)
    environment:
      - MODEL_NAME=${MODEL_NAME}
      - MODEL_PRECISION=${MODEL_PRECISION}
      - DEVICE=${DEVICE}
      - BATCH_SIZE_VISUAL=${BATCH_SIZE_VISUAL}
      - BATCH_SIZE_TEXT=${BATCH_SIZE_TEXT}
      - CHROMA_HOST=${CHROMA_HOST}
      - CHROMA_PORT=${CHROMA_PORT}
      - LOG_LEVEL=${LOG_LEVEL}
      - LOG_FORMAT=${LOG_FORMAT}
    depends_on:
      - chromadb
    networks:
      - docusearch
    deploy:
      resources:
        limits:
          memory: 10G  # Prevent OOM for ColNomic 7B

networks:
  docusearch:
    driver: bridge
```

---

### 2. Copyparty Configuration

**File**: `data/copyparty/config.toml`

```toml
[global]
# Basic settings
listen = "0.0.0.0:8000"
data-dir = "/uploads"
www-dir = "/www"

# Upload configuration
max-upload-size = "100M"
allowed-extensions = ["pdf", "docx", "pptx"]

# Event hooks
[hooks]
on-upload = "/hooks/on_upload.py"

# UI customization
[ui]
title = "DocuSearch MVP - Document Upload"
footer = "Upload PDF, DOCX, or PPTX files for semantic search"

# Authentication (disabled for MVP, enable in production)
[auth]
enabled = false
# username = "admin"
# password-hash = "<bcrypt-hash>"
```

---

### 3. Model Configuration

**File**: `src/config/model_config.py`

```python
from dataclasses import dataclass
from typing import Literal
import os

@dataclass
class ModelConfig:
    """ColPali model configuration."""

    # Model selection
    name: str = os.getenv('MODEL_NAME', 'vidore/colqwen2-v0.1')
    precision: Literal['fp16', 'int8'] = os.getenv('MODEL_PRECISION', 'fp16')

    # Device selection
    device: Literal['mps', 'cuda', 'cpu'] = os.getenv('DEVICE', 'mps')

    # Batch sizes
    batch_size_visual: int = int(os.getenv('BATCH_SIZE_VISUAL', '4'))
    batch_size_text: int = int(os.getenv('BATCH_SIZE_TEXT', '8'))

    # Cache directory
    cache_dir: str = os.getenv('MODELS_CACHE', '/models')

    # Auto-detect device if specified device unavailable
    auto_fallback: bool = True

    def __post_init__(self):
        """Validate configuration."""
        if self.precision not in ['fp16', 'int8']:
            raise ValueError(f"Invalid precision: {self.precision}")
        if self.device not in ['mps', 'cuda', 'cpu']:
            raise ValueError(f"Invalid device: {self.device}")

        # Check device availability and fallback
        if self.auto_fallback:
            self.device = self._detect_device()

    def _detect_device(self) -> str:
        """Detect available device with fallback."""
        import torch

        if self.device == 'mps' and torch.backends.mps.is_available():
            return 'mps'
        elif self.device == 'cuda' and torch.cuda.is_available():
            return 'cuda'
        else:
            print(f"Warning: Requested device '{self.device}' not available, falling back to CPU")
            return 'cpu'

    @property
    def memory_estimate_gb(self) -> float:
        """Estimate memory usage."""
        base_model_size = 14.0  # ColNomic 7B ~14GB FP16
        if self.precision == 'int8':
            return base_model_size / 2  # ~7GB INT8
        return base_model_size
```

---

### 4. Storage Configuration

**File**: `src/config/storage_config.py`

```python
from dataclasses import dataclass
import os

@dataclass
class StorageConfig:
    """ChromaDB storage configuration."""

    # Connection
    host: str = os.getenv('CHROMA_HOST', 'chromadb')
    port: int = int(os.getenv('CHROMA_PORT', '8001'))

    # Collections
    visual_collection: str = os.getenv('VISUAL_COLLECTION', 'visual_collection')
    text_collection: str = os.getenv('TEXT_COLLECTION', 'text_collection')

    # Batch operations
    batch_size: int = int(os.getenv('CHROMA_BATCH_SIZE', '100'))

    # Persistence
    persist_directory: str = os.getenv('CHROMA_DATA', '/chroma/chroma')

    @property
    def connection_string(self) -> str:
        """Get ChromaDB connection string."""
        return f"http://{self.host}:{self.port}"
```

---

### 5. Processing Configuration

**File**: `src/config/processing_config.py`

```python
from dataclasses import dataclass
from typing import List
import os

@dataclass
class ProcessingConfig:
    """Document processing configuration."""

    # File handling
    max_file_size_mb: int = int(os.getenv('MAX_FILE_SIZE_MB', '100'))
    supported_formats: List[str] = os.getenv('SUPPORTED_FORMATS', 'pdf,docx,pptx').split(',')
    upload_dir: str = os.getenv('UPLOAD_DIR', '/uploads')

    # Text processing
    chunk_size_words: int = int(os.getenv('TEXT_CHUNK_SIZE', '250'))
    chunk_overlap_words: int = int(os.getenv('TEXT_CHUNK_OVERLAP', '50'))

    # Visual processing
    page_render_dpi: int = int(os.getenv('PAGE_RENDER_DPI', '150'))

    # Worker configuration
    worker_threads: int = int(os.getenv('WORKER_THREADS', '1'))
    enable_queue: bool = os.getenv('ENABLE_QUEUE', 'false').lower() == 'true'

    # Logging
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    log_format: str = os.getenv('LOG_FORMAT', 'json')
    log_file: str = os.getenv('LOG_FILE', '/data/logs/worker.log')

    def validate_file(self, filename: str, size_bytes: int) -> tuple[bool, str]:
        """Validate uploaded file."""
        # Check extension
        ext = filename.lower().split('.')[-1]
        if ext not in self.supported_formats:
            return False, f"Unsupported format: {ext}"

        # Check size
        size_mb = size_bytes / (1024 * 1024)
        if size_mb > self.max_file_size_mb:
            return False, f"File too large: {size_mb:.1f}MB > {self.max_file_size_mb}MB"

        return True, ""
```

---

## Configuration Management

### Loading Configuration

```python
from src.config import ModelConfig, StorageConfig, ProcessingConfig

# Load all configuration
model_config = ModelConfig()
storage_config = StorageConfig()
processing_config = ProcessingConfig()

# Access configuration values
print(f"Using device: {model_config.device}")
print(f"ChromaDB: {storage_config.connection_string}")
print(f"Max file size: {processing_config.max_file_size_mb}MB")
```

### Environment Variable Precedence

1. **Container environment variables** (highest priority)
2. **`.env` file** in docker directory
3. **Default values** in Python dataclasses

### Configuration Validation

All configuration classes validate on initialization:

```python
try:
    config = ModelConfig(precision='invalid')
except ValueError as e:
    print(f"Configuration error: {e}")
```

---

## Docker Build Arguments

### Dockerfile.processing-worker

```dockerfile
# Build arguments
ARG PYTHON_VERSION=3.10
ARG PYTORCH_VERSION=2.0.0
ARG BUILDPLATFORM=linux/arm64
ARG TARGETPLATFORM=linux/arm64

# Use build args
FROM --platform=$BUILDPLATFORM python:${PYTHON_VERSION}-slim

# Environment configuration
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
```

---

## Health Checks

### Container Health Checks

```yaml
# docker-compose.yml
services:
  chromadb:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s

  processing-worker:
    healthcheck:
      test: ["CMD", "python", "-c", "import torch; exit(0 if torch.backends.mps.is_available() else 1)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s  # Model loading takes time
```

---

## Configuration Changes Between Waves

### Wave 1-2 (Development)
- Single worker thread
- No queue system
- Debug logging
- Small batch sizes (safe defaults)

### Wave 3-4 (Integration & Production)
- Production logging (INFO level)
- Larger batch sizes (tuned for performance)
- Optional queue system (Wave 4)
- Security features enabled

---

## Testing Configuration

### Test Environment Variables

```bash
# .env.test
MODEL_PRECISION=fp16  # Use FP16 for faster tests
BATCH_SIZE_VISUAL=2   # Smaller batches for test data
BATCH_SIZE_TEXT=4
LOG_LEVEL=DEBUG       # Detailed logging for debugging
WORKER_THREADS=1      # Single thread for deterministic tests
```

### Configuration Mocks (Wave 2)

```python
class MockConfig:
    """Mock configuration for unit tests."""

    def __init__(self):
        self.model_name = 'mock-model'
        self.device = 'cpu'
        self.batch_size_visual = 2
        self.batch_size_text = 4
        self.chroma_host = 'localhost'
        self.chroma_port = 8001
```

---

## Contract Version

**Version**: 1.0
**Last Updated**: 2025-10-06
**Status**: Draft (pending Wave 1 review)

---

## Notes

- All configuration values have sensible defaults
- Environment variables support overrides at runtime
- Configuration validation prevents invalid combinations
- Health checks ensure services are ready before processing
- M1-specific optimizations (MPS device support)
- Production settings defer security configuration to deployment
