# Docker Deployment for M1 MacBook Pro

Complete guide to running the Copyparty + Docling + Embedding Models + ChromaDB + smolagents stack locally on Apple Silicon (M1/M2/M3).

**Target Hardware:** MacBook Pro M1/M2/M3 with 16GB+ RAM

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Directory Structure](#directory-structure)
4. [Docker Configuration](#docker-configuration)
5. [Building Images](#building-images)
6. [Running the Stack](#running-the-stack)
7. [Development Workflow](#development-workflow)
8. [Troubleshooting](#troubleshooting)
9. [Performance Optimization](#performance-optimization)

---

## Prerequisites

### 1. Install Docker Desktop for Mac

```bash
# Download from: https://www.docker.com/products/docker-desktop/
# Or install via Homebrew
brew install --cask docker

# Verify installation
docker --version  # Should be 24.0+
docker compose version  # Should be 2.20+
```

### 2. Configure Docker Desktop

**Settings → Resources:**
- **CPUs:** 6-8 cores (leave 2 for macOS)
- **Memory:** 12GB (for 16GB Mac) or 24GB (for 32GB Mac)
- **Swap:** 2GB
- **Disk:** 100GB+

**Settings → General:**
- ✅ Use VirtioFS (faster file sharing)
- ✅ Use Rosetta for x86/amd64 emulation on Apple Silicon

### 3. Install Additional Tools

```bash
# Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Additional utilities
brew install git wget tree htop
```

---

## Architecture Overview

### Container Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Host: MacBook Pro M1                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Docker Desktop (Apple Silicon)             │ │
│  │                                                          │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │ │
│  │  │  Copyparty   │  │  ChromaDB    │  │  Embedding   │ │ │
│  │  │   Server     │  │   Vector DB  │  │   Worker     │ │ │
│  │  │  (Python)    │  │  (Python)    │  │ (PyTorch MPS)│ │ │
│  │  │  Port: 8000  │  │  Port: 8001  │  │              │ │ │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │ │
│  │         │                  │                  │         │ │
│  │         └──────────────────┴──────────────────┘         │ │
│  │                            │                            │ │
│  │                    ┌───────┴────────┐                  │ │
│  │                    │  smolagents    │                  │ │
│  │                    │      API       │                  │ │
│  │                    │  (FastAPI)     │                  │ │
│  │                    │  Port: 8002    │                  │ │
│  │                    └────────────────┘                  │ │
│  └────────────────────────────────────────────────────────┘ │
│                            │                                │
│                    ┌───────┴────────┐                      │
│                    │  Shared Volumes │                      │
│                    │  ./data/*       │                      │
│                    └─────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions for M1

1. **Use Apple Silicon Native Images** - Build ARM64 images, not x86_64
2. **Use MPS (Metal Performance Shaders)** - Apple's GPU acceleration instead of CUDA
3. **Shared Memory** - Use Docker volumes for data sharing
4. **Lightweight** - Avoid heavy dependencies, optimize for 16GB RAM

---

## Directory Structure

```bash
/Volumes/tkr-riffic/@tkr-projects/tkr-smolagents/
├── docker/
│   ├── docker-compose.yml          # Main orchestration
│   ├── docker-compose.dev.yml      # Development overrides
│   ├── .env                         # Environment variables
│   │
│   ├── copyparty/
│   │   ├── Dockerfile
│   │   └── config.yaml
│   │
│   ├── chromadb/
│   │   └── Dockerfile               # Custom if needed
│   │
│   ├── embedding-worker/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── worker.py
│   │
│   └── smolagents-api/
│       ├── Dockerfile
│       ├── requirements.txt
│       └── api.py
│
├── data/                            # Shared data (Docker volumes)
│   ├── copyparty/
│   │   ├── uploads/
│   │   ├── processed/
│   │   └── hooks/
│   ├── chroma_db/
│   ├── models/                      # Cached model weights
│   └── logs/
│
├── scripts/
│   ├── setup.sh                     # Initial setup
│   ├── build.sh                     # Build all images
│   └── test.sh                      # Test deployment
│
└── _ref/                            # Documentation
    └── docker-deployment-m1.md      # This file
```

---

## Docker Configuration

### 1. Main docker-compose.yml

```yaml
# docker/docker-compose.yml

version: '3.8'

services:
  # ===================================================================
  # Copyparty - File server with event hooks
  # ===================================================================
  copyparty:
    build:
      context: ./copyparty
      dockerfile: Dockerfile
      platforms:
        - linux/arm64  # Apple Silicon
    container_name: copyparty
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ../data/copyparty/uploads:/data/uploads
      - ../data/copyparty/processed:/data/processed
      - ../data/copyparty/hooks:/hooks
      - ./copyparty/config.yaml:/config.yaml:ro
    environment:
      - TZ=America/Los_Angeles
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:8000"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ===================================================================
  # ChromaDB - Vector database
  # ===================================================================
  chromadb:
    image: chromadb/chroma:latest
    container_name: chromadb
    restart: unless-stopped
    ports:
      - "8001:8000"
    volumes:
      - ../data/chroma_db:/chroma/chroma
    environment:
      - IS_PERSISTENT=TRUE
      - ANONYMIZED_TELEMETRY=FALSE
      - ALLOW_RESET=TRUE
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:8000/api/v1/heartbeat"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ===================================================================
  # Embedding Worker - Process documents with ML models
  # ===================================================================
  embedding-worker:
    build:
      context: ./embedding-worker
      dockerfile: Dockerfile
      platforms:
        - linux/arm64
    container_name: embedding-worker
    restart: unless-stopped
    volumes:
      - ../data/copyparty:/data/copyparty
      - ../data/chroma_db:/data/chroma_db
      - ../data/models:/models  # Cache model weights
      - ../data/logs:/logs
    environment:
      - PYTORCH_ENABLE_MPS_FALLBACK=1  # Use MPS (Apple GPU)
      - HF_HOME=/models                 # Cache Hugging Face models
      - CHROMADB_HOST=chromadb
      - CHROMADB_PORT=8000
      - LOG_LEVEL=INFO
    depends_on:
      chromadb:
        condition: service_healthy
      copyparty:
        condition: service_healthy
    networks:
      - app-network
    # No GPU reservations needed - MPS is automatic on M1

  # ===================================================================
  # smolagents API - AI agent interface
  # ===================================================================
  smolagents-api:
    build:
      context: ./smolagents-api
      dockerfile: Dockerfile
      platforms:
        - linux/arm64
    container_name: smolagents-api
    restart: unless-stopped
    ports:
      - "8002:8000"
    volumes:
      - ../data/chroma_db:/data/chroma_db
      - ../data/models:/models
      - ../data/logs:/logs
    environment:
      - CHROMADB_HOST=chromadb
      - CHROMADB_PORT=8000
      - COPYPARTY_URL=http://copyparty:8000
      - HF_HOME=/models
      - LOG_LEVEL=INFO
    depends_on:
      chromadb:
        condition: service_healthy
      embedding-worker:
        condition: service_started
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  app-network:
    driver: bridge

volumes:
  chroma_data:
  model_cache:
```

### 2. Environment Variables

```bash
# docker/.env

# General
TZ=America/Los_Angeles
LOG_LEVEL=INFO

# Copyparty
COPYPARTY_PORT=8000

# ChromaDB
CHROMADB_PORT=8001
CHROMADB_HOST=chromadb

# Models
HF_HOME=/models
PYTORCH_ENABLE_MPS_FALLBACK=1

# API
API_PORT=8002
```

### 3. Development Override

```yaml
# docker/docker-compose.dev.yml

version: '3.8'

services:
  embedding-worker:
    # Development: mount source code for live reloading
    volumes:
      - ../embedding-worker:/app
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
    command: python -u worker.py  # Unbuffered output

  smolagents-api:
    volumes:
      - ../smolagents-api:/app
    environment:
      - DEBUG=true
      - RELOAD=true
    command: uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

---

## Building Images

### 1. Copyparty Dockerfile

```dockerfile
# docker/copyparty/Dockerfile

FROM python:3.11-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Copyparty
RUN pip install --no-cache-dir copyparty

# Create directories
RUN mkdir -p /data/uploads /data/processed /hooks

# Copy configuration
COPY config.yaml /config.yaml

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD wget -q --spider http://localhost:8000 || exit 1

# Run Copyparty
CMD ["copyparty", "--config", "/config.yaml"]
```

**Copyparty config:**

```yaml
# docker/copyparty/config.yaml

accounts:
  - user: admin
    password: changeme
    flags: a  # Admin

volumes:
  - path: /data/uploads
    alias: uploads
    flags: rw,ed

  - path: /data/processed
    alias: processed
    flags: r

event-hooks:
  - event: upload
    script: /hooks/process_upload.py

server:
  port: 8000
  host: 0.0.0.0
```

### 2. Embedding Worker Dockerfile

```dockerfile
# docker/embedding-worker/Dockerfile

FROM python:3.11-slim-bookworm

# Install system dependencies for M1 optimization
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    wget \
    ffmpeg \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python packages
# Note: PyTorch with MPS support is included in standard torch for ARM64
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY worker.py .
COPY process_documents.py .

# Create necessary directories
RUN mkdir -p /data /models /logs

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PYTORCH_ENABLE_MPS_FALLBACK=1

# Run worker
CMD ["python", "-u", "worker.py"]
```

**Requirements:**

```txt
# docker/embedding-worker/requirements.txt

# Core
torch>=2.0.0
torchvision>=0.15.0

# Document processing
docling>=2.0.0
pdf2image>=1.16.0
pillow>=10.0.0

# Vector database
chromadb>=0.4.0

# Embedding models
transformers>=4.35.0
sentence-transformers>=2.2.0

# ColNomic (ColPali)
git+https://github.com/illuin-tech/colpali.git

# Audio
openai-whisper>=20231117

# Utilities
python-dotenv>=1.0.0
watchdog>=3.0.0  # File system monitoring
```

**Worker code:**

```python
# docker/embedding-worker/worker.py

import os
import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import torch

from process_documents import DocumentProcessor

# Setup logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check if MPS is available (Apple Silicon GPU)
if torch.backends.mps.is_available():
    device = "mps"
    logger.info("✓ Using Apple Silicon GPU (MPS)")
elif torch.cuda.is_available():
    device = "cuda"
    logger.info("✓ Using NVIDIA GPU (CUDA)")
else:
    device = "cpu"
    logger.warning("⚠ Using CPU (slower)")

class UploadHandler(FileSystemEventHandler):
    """Monitor uploads directory for new files"""

    def __init__(self, processor):
        self.processor = processor
        self.processing = set()

    def on_created(self, event):
        if event.is_directory:
            return

        file_path = event.src_path

        # Ignore temp files
        if file_path.endswith('.tmp') or '/.~' in file_path:
            return

        # Avoid duplicate processing
        if file_path in self.processing:
            return

        self.processing.add(file_path)

        try:
            logger.info(f"New file detected: {file_path}")

            # Wait for file to finish writing
            time.sleep(2)

            # Process document
            self.processor.process_file(file_path)

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            import traceback
            traceback.print_exc()

        finally:
            self.processing.discard(file_path)

def main():
    logger.info("Starting Embedding Worker...")
    logger.info(f"Device: {device}")

    # Initialize document processor
    processor = DocumentProcessor(
        chromadb_host=os.getenv('CHROMADB_HOST', 'chromadb'),
        chromadb_port=int(os.getenv('CHROMADB_PORT', 8000)),
        device=device
    )

    # Setup file system monitoring
    upload_dir = "/data/copyparty/uploads"
    event_handler = UploadHandler(processor)
    observer = Observer()
    observer.schedule(event_handler, upload_dir, recursive=True)
    observer.start()

    logger.info(f"Monitoring {upload_dir} for new files...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Shutting down...")

    observer.join()

if __name__ == "__main__":
    main()
```

### 3. smolagents API Dockerfile

```dockerfile
# docker/smolagents-api/Dockerfile

FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api.py .
COPY tools/ ./tools/

RUN mkdir -p /data /models /logs

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD wget -q --spider http://localhost:8000/health || exit 1

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Requirements:**

```txt
# docker/smolagents-api/requirements.txt

smolagents>=1.0.0
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
chromadb>=0.4.0
python-dotenv>=1.0.0
```

**API code:**

```python
# docker/smolagents-api/api.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import sys

sys.path.append('./tools')

from smolagents import CodeAgent, InferenceClientModel
from semantic_search_tool import SemanticSearchTool

app = FastAPI(title="smolagents API")

# Initialize agent
model = InferenceClientModel(
    model_id=os.getenv('MODEL_ID', 'Qwen/Qwen2.5-Coder-32B-Instruct')
)

agent = CodeAgent(
    tools=[SemanticSearchTool()],
    model=model,
    stream_outputs=False
)

class QueryRequest(BaseModel):
    query: str
    n_results: int = 5

class QueryResponse(BaseModel):
    result: str
    success: bool

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    try:
        result = agent.run(request.query)
        return QueryResponse(result=result, success=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "smolagents API - Use POST /query to search"}
```

---

## Running the Stack

### 1. Setup Script

```bash
#!/bin/bash
# scripts/setup.sh

set -e

echo "🚀 Setting up tkr-smolagents on M1 Mac..."

# Check prerequisites
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not installed. Please install Docker Desktop."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose not available."
    exit 1
fi

# Create directory structure
echo "📁 Creating directories..."
mkdir -p data/{copyparty/{uploads,processed,hooks},chroma_db,models,logs}
mkdir -p docker/{copyparty,chromadb,embedding-worker,smolagents-api}

# Set permissions
chmod -R 755 data/

# Create .env if not exists
if [ ! -f docker/.env ]; then
    echo "📝 Creating .env file..."
    cat > docker/.env <<EOF
TZ=America/Los_Angeles
LOG_LEVEL=INFO
COPYPARTY_PORT=8000
CHROMADB_PORT=8001
API_PORT=8002
HF_HOME=/models
PYTORCH_ENABLE_MPS_FALLBACK=1
EOF
fi

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. cd docker/"
echo "  2. docker compose build"
echo "  3. docker compose up"
```

### 2. Build Script

```bash
#!/bin/bash
# scripts/build.sh

set -e

cd docker/

echo "🔨 Building Docker images for Apple Silicon..."

# Build all services
docker compose build --no-cache

echo "✅ Build complete!"
echo ""
echo "Images created:"
docker images | grep -E "copyparty|chromadb|embedding|smolagents"
```

### 3. Start Services

```bash
# Start all services
cd docker/
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f

# Stop services
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v
```

### 4. Development Mode

```bash
# Start with development overrides
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# This enables:
# - Live code reloading
# - Verbose logging
# - Source code mounting
```

---

## Development Workflow

### Typical Day-to-Day Usage

```bash
# Morning: Start the stack
cd docker/
docker compose up -d

# Check everything is running
docker compose ps

# View logs from specific service
docker compose logs -f embedding-worker

# Upload a test document
curl -F "file=@test.pdf" http://localhost:8000/uploads/

# Watch it get processed
docker compose logs -f embedding-worker

# Query via API
curl -X POST http://localhost:8002/query \
  -H "Content-Type: application/json" \
  -d '{"query": "find revenue data"}'

# Evening: Stop the stack
docker compose down
```

### Making Code Changes

```bash
# 1. Edit code in embedding-worker/
vim docker/embedding-worker/worker.py

# 2. Rebuild just that service
docker compose build embedding-worker

# 3. Restart just that service
docker compose up -d embedding-worker

# 4. Watch logs
docker compose logs -f embedding-worker

# Or: Use dev mode with auto-reload
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
# Now changes auto-reload!
```

### Debugging Inside Container

```bash
# Shell into container
docker compose exec embedding-worker bash

# Inside container:
python
>>> import torch
>>> torch.backends.mps.is_available()
True  # MPS working!
>>> exit()

# Check ChromaDB connection
docker compose exec embedding-worker python -c "
import chromadb
client = chromadb.HttpClient(host='chromadb', port=8000)
print(client.heartbeat())
"

# Exit container
exit
```

### Testing Changes

```bash
#!/bin/bash
# scripts/test.sh

set -e

echo "🧪 Testing deployment..."

# Wait for services to be healthy
echo "Waiting for services..."
sleep 10

# Test Copyparty
echo "Testing Copyparty..."
curl -f http://localhost:8000 || exit 1

# Test ChromaDB
echo "Testing ChromaDB..."
curl -f http://localhost:8001/api/v1/heartbeat || exit 1

# Test API
echo "Testing smolagents API..."
curl -f http://localhost:8002/health || exit 1

# Upload test document
echo "Testing document upload..."
echo "Test content" > /tmp/test.txt
curl -F "file=@/tmp/test.txt" http://localhost:8000/uploads/

# Wait for processing
sleep 5

# Query
echo "Testing query..."
curl -X POST http://localhost:8002/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

echo ""
echo "✅ All tests passed!"
```

---

## Troubleshooting

### Common Issues on M1 Mac

#### 1. "Platform mismatch" error

```
ERROR: The requested image's platform (linux/amd64) does not match
the detected host platform (linux/arm64/v8)
```

**Fix:**
```yaml
# In docker-compose.yml, add to each service:
build:
  platforms:
    - linux/arm64
```

#### 2. PyTorch not using MPS

```bash
# Inside container, check:
docker compose exec embedding-worker python -c "
import torch
print('MPS available:', torch.backends.mps.is_available())
print('MPS built:', torch.backends.mps.is_built())
"

# If False, ensure:
ENV PYTORCH_ENABLE_MPS_FALLBACK=1
```

**Also verify PyTorch version:**
```bash
docker compose exec embedding-worker python -c "
import torch
print(torch.__version__)  # Should be 2.0+
"
```

#### 3. Out of Memory

```
ERRO[0123] Out of memory
```

**Solutions:**

a) **Reduce Docker memory:**
```yaml
# docker-compose.yml
services:
  embedding-worker:
    deploy:
      resources:
        limits:
          memory: 8G
```

b) **Process documents one at a time:**
```python
# worker.py - add lock
from threading import Lock

processing_lock = Lock()

def on_created(self, event):
    with processing_lock:  # Only process one at a time
        self.processor.process_file(event.src_path)
```

c) **Use smaller models:**
```python
# For testing, use smaller embedding model
# embedding-worker/process_documents.py
model = ColQwen2_5.from_pretrained(
    "nomic-ai/colnomic-embed-multimodal-3b",  # 3B instead of 7B
    torch_dtype=torch.float16  # FP16 instead of BF16
)
```

#### 4. Slow Performance

**Check MPS usage:**
```bash
# In another terminal while processing
sudo powermetrics --samplers gpu_power -i1000 -n1

# Should show GPU activity
```

**Optimize:**

a) **Use FP16 (faster on M1):**
```python
model = model.to(dtype=torch.float16)  # Instead of bfloat16
```

b) **Batch processing:**
```python
# Process multiple pages at once
embeddings = model.embed_images(pages)  # Batch
# Instead of:
# for page in pages:
#     embedding = model.embed_image(page)  # One by one
```

c) **Reduce image resolution:**
```python
# pdf2image with lower DPI
pages = convert_from_path(
    pdf_path,
    dpi=150  # Instead of 300
)
```

#### 5. ChromaDB Connection Issues

```
ConnectionError: Cannot connect to ChromaDB
```

**Debug:**
```bash
# Check ChromaDB is running
docker compose ps chromadb

# Check network
docker compose exec embedding-worker ping chromadb

# Check ChromaDB logs
docker compose logs chromadb

# Manual connection test
docker compose exec embedding-worker python -c "
import chromadb
import time
time.sleep(5)  # Wait for startup
client = chromadb.HttpClient(host='chromadb', port=8000)
print(client.heartbeat())
"
```

**Fix:** Add health checks and depends_on:
```yaml
services:
  embedding-worker:
    depends_on:
      chromadb:
        condition: service_healthy
```

#### 6. Volume Permission Issues

```
Permission denied: '/data/chroma_db'
```

**Fix:**
```bash
# On host Mac:
chmod -R 777 data/

# Or in Dockerfile:
RUN mkdir -p /data && chmod 777 /data
```

#### 7. Models Not Downloading

```
HuggingFace model download failed
```

**Check:**
```bash
# Ensure volume is mounted
docker compose exec embedding-worker ls -la /models

# Manually download
docker compose exec embedding-worker python -c "
from transformers import AutoModel
model = AutoModel.from_pretrained(
    'nomic-ai/colnomic-embed-multimodal-7b',
    cache_dir='/models'
)
"

# Check disk space
df -h
```

---

## Performance Optimization

### 1. Model Caching

**Problem:** Models re-download every container restart.

**Solution:** Bind mount model cache:

```yaml
# docker-compose.yml
volumes:
  - ../data/models:/models  # Persistent cache
  - ~/.cache/huggingface:/root/.cache/huggingface  # Use host cache
```

### 2. Use Unified Memory (M1 Advantage)

M1 Macs have unified memory - RAM and GPU share memory!

```python
# Optimize for unified memory
import torch

# Don't copy to/from GPU - it's already there!
model = model.to('mps')
inputs = inputs.to('mps')  # This is instant on M1!

# Process in-place when possible
with torch.no_grad():
    output = model(inputs)  # No extra copies
```

### 3. Batch Processing

```python
# Process multiple documents together
def process_batch(file_paths, batch_size=4):
    for i in range(0, len(file_paths), batch_size):
        batch = file_paths[i:i+batch_size]

        # Load all at once
        images = [convert_to_image(f) for f in batch]

        # Embed in batch (faster!)
        embeddings = model.embed_images(images)

        # Store
        for img, emb in zip(images, embeddings):
            store(emb)
```

### 4. Reduce Memory Usage

```python
# Use FP16 (half precision)
model = model.to(dtype=torch.float16)

# Clear cache regularly
import gc
gc.collect()
torch.mps.empty_cache()  # M1 equivalent of torch.cuda.empty_cache()

# Process then delete
for file in files:
    embedding = process(file)
    store(embedding)
    del embedding  # Free memory immediately
```

### 5. Parallel Processing

```bash
# Run multiple embedding workers
docker compose up -d --scale embedding-worker=2

# Each worker processes different files
# Docker load balances automatically
```

### 6. Optimize Docker

```bash
# ~/.docker/daemon.json
{
  "builder": {
    "gc": {
      "enabled": true,
      "defaultKeepStorage": "20GB"
    }
  }
}

# Restart Docker Desktop after change
```

### 7. Monitor Performance

```bash
# Create monitoring script
# scripts/monitor.sh

#!/bin/bash

echo "=== Docker Stats ==="
docker stats --no-stream

echo ""
echo "=== Disk Usage ==="
docker system df

echo ""
echo "=== MPS Usage ==="
sudo powermetrics --samplers gpu_power -i1000 -n1 | grep -A5 "GPU"
```

---

## Quick Reference

### Essential Commands

```bash
# Start everything
docker compose up -d

# Stop everything
docker compose down

# Restart a service
docker compose restart embedding-worker

# View logs
docker compose logs -f [service]

# Shell into container
docker compose exec [service] bash

# Check status
docker compose ps

# Remove everything (including volumes)
docker compose down -v

# Build without cache
docker compose build --no-cache

# Scale a service
docker compose up -d --scale embedding-worker=3
```

### Useful Aliases

Add to `~/.zshrc`:

```bash
# Docker Compose shortcuts
alias dc='docker compose'
alias dcup='docker compose up -d'
alias dcdown='docker compose down'
alias dclogs='docker compose logs -f'
alias dcps='docker compose ps'
alias dcrestart='docker compose restart'

# Project specific
alias tkr-start='cd /Volumes/tkr-riffic/@tkr-projects/tkr-smolagents/docker && docker compose up -d'
alias tkr-stop='cd /Volumes/tkr-riffic/@tkr-projects/tkr-smolagents/docker && docker compose down'
alias tkr-logs='cd /Volumes/tkr-riffic/@tkr-projects/tkr-smolagents/docker && docker compose logs -f'
```

### File Locations (Inside Containers)

| Data | Container Path | Host Path |
|------|----------------|-----------|
| Uploaded files | `/data/copyparty/uploads` | `./data/copyparty/uploads` |
| ChromaDB data | `/chroma/chroma` | `./data/chroma_db` |
| Model cache | `/models` | `./data/models` |
| Logs | `/logs` | `./data/logs` |
| Hooks | `/hooks` | `./data/copyparty/hooks` |

### Port Mapping

| Service | Container Port | Host Port | URL |
|---------|---------------|-----------|-----|
| Copyparty | 8000 | 8000 | http://localhost:8000 |
| ChromaDB | 8000 | 8001 | http://localhost:8001 |
| smolagents API | 8000 | 8002 | http://localhost:8002 |

---

## Next Steps

1. **Run setup:**
   ```bash
   chmod +x scripts/*.sh
   ./scripts/setup.sh
   ```

2. **Build images:**
   ```bash
   ./scripts/build.sh
   ```

3. **Start services:**
   ```bash
   cd docker/
   docker compose up -d
   ```

4. **Test:**
   ```bash
   ./scripts/test.sh
   ```

5. **Upload document:**
   ```bash
   curl -F "file=@test.pdf" http://localhost:8000/uploads/
   ```

6. **Query:**
   ```bash
   curl -X POST http://localhost:8002/query \
     -H "Content-Type: application/json" \
     -d '{"query": "find revenue data"}'
   ```

**Happy coding! 🚀**
