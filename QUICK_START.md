# DocuSearch - Quick Start Guide

## TL;DR

```bash
# Start everything with Metal GPU acceleration (M1/M2/M3 Mac)
./scripts/start-all.sh

# Check status
./scripts/status.sh

# Stop everything
./scripts/stop-all.sh
```

Upload files at: **http://localhost:8000**

---

## Prerequisites

- **macOS 12.3+** (for Metal GPU support)
- **Docker Desktop** (running)
- **Python 3.10+**

## First-Time Setup

### Option 1: GPU Mode (Recommended - 10-20x faster)

```bash
# 1. Setup Python environment for native worker
./scripts/run-worker-native.sh setup

# 2. Start all services with GPU acceleration
./scripts/start-all.sh
```

### Option 2: CPU Mode (Simpler, slower)

```bash
# Start all services in Docker (CPU only)
./scripts/start-all.sh --cpu
```

## Daily Usage

### Start Services

```bash
# With GPU acceleration (default)
./scripts/start-all.sh

# CPU only (no GPU setup needed)
./scripts/start-all.sh --cpu

# Docker services only (no worker)
./scripts/start-all.sh --docker-only
```

### Check Status

```bash
# Human-readable status
./scripts/status.sh

# JSON output
./scripts/status.sh --json
```

### Stop Services

```bash
# Graceful shutdown
./scripts/stop-all.sh

# Force stop (if processes hang)
./scripts/stop-all.sh --force
```

## Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Upload UI** | http://localhost:8000 | Upload documents |
| **ChromaDB** | http://localhost:8001 | Vector database |
| **Worker API** | http://localhost:8002 | Document processing |
| **Worker Status** | http://localhost:8002/status | Processing stats |
| **Health Check** | http://localhost:8002/health | Worker health |

## Architecture Modes

### GPU Mode (Native Worker)
```
┌─────────────────────────────────┐
│         Host (macOS)            │
│  ┌─────────────────────────┐    │
│  │  Worker (Native - GPU)  │    │
│  │  Port: 8002             │    │
│  └─────────────────────────┘    │
│  ┌───────────┐ ┌───────────┐    │
│  │ Copyparty │ │ ChromaDB  │    │
│  │ (Docker)  │ │ (Docker)  │    │
│  └───────────┘ └───────────┘    │
└─────────────────────────────────┘
```

**Pros:**
- ✅ 10-20x faster processing (Metal GPU)
- ✅ Real-time document processing
- ✅ Better for development

**Cons:**
- ❌ Requires Python setup
- ❌ macOS only

### CPU Mode (Docker Worker)
```
┌─────────────────────────────────┐
│      Docker Containers          │
│  ┌───────────┐ ┌───────────┐    │
│  │  Worker   │ │ Copyparty │    │
│  │  (CPU)    │ │           │    │
│  └───────────┘ └───────────┘    │
│  ┌───────────┐                  │
│  │ ChromaDB  │                  │
│  └───────────┘                  │
└─────────────────────────────────┘
```

**Pros:**
- ✅ Simple deployment
- ✅ No Python setup
- ✅ Works anywhere

**Cons:**
- ❌ Slower (CPU only)
- ❌ No GPU acceleration

## Workflow

### 1. Upload Documents

**Via Web UI:**
- Open http://localhost:8000
- Drag & drop PDF/DOCX/PPTX files
- Files automatically trigger processing

**Via CLI:**
```bash
# Upload file
curl -F "f=@document.pdf" http://localhost:8000/u/

# Upload to folder
curl -F "f=@document.pdf" http://localhost:8000/u/my-folder/
```

### 2. Processing Pipeline

1. **Copyparty** receives file
2. **Webhook** triggers worker (HTTP POST)
3. **Worker** processes:
   - Parse document (Docling)
   - Extract pages as images
   - Generate visual embeddings (ColPali)
   - Extract text chunks
   - Generate text embeddings
   - Store in ChromaDB
4. **Status** updates via API

### 3. Search Documents

```bash
# Text search
curl -X POST http://localhost:8002/search \
  -H "Content-Type: application/json" \
  -d '{"query": "quarterly revenue", "top_k": 5}'

# Get all documents
curl http://localhost:8002/documents
```

## Monitoring

### View Logs

**Native Worker:**
```bash
# Follow worker logs
tail -f logs/worker-native.log

# Show last 100 lines
tail -100 logs/worker-native.log
```

**Docker Services:**
```bash
# All services
docker-compose -f docker/docker-compose.yml logs -f

# Specific service
docker logs -f docusearch-worker
docker logs -f docusearch-chromadb
docker logs -f docusearch-copyparty
```

### Check Processing Status

```bash
# Worker status
curl http://localhost:8002/status | jq

# Health check
curl http://localhost:8002/health

# Document stats
curl http://localhost:8002/status | jq '.stats'
```

### Monitor GPU Usage (Native Mode)

```bash
# Real-time GPU monitoring
sudo powermetrics --samplers gpu_power -i 1000
```

## Troubleshooting

### Services Won't Start

```bash
# Check Docker is running
docker info

# Check port conflicts
lsof -i :8000,8001,8002

# Force stop and restart
./scripts/stop-all.sh --force
./scripts/start-all.sh
```

### Worker Not Processing

```bash
# Check worker logs
tail -50 logs/worker-native.log

# Test webhook manually
docker exec docusearch-copyparty python3 /hooks/on_upload.py \
  up /u/test.pdf /uploads/test.pdf "*" "127.0.0.1"

# Restart worker
./scripts/stop-all.sh
./scripts/start-all.sh
```

### GPU Not Working

```bash
# Check Metal availability
./scripts/run-worker-native.sh check

# Should show:
# MPS Available: True
# MPS Built: True

# If False, verify:
sw_vers  # macOS 12.3+
python3 --version  # 3.10+
pip3 show torch  # PyTorch installed
```

### ChromaDB Connection Error

```bash
# Check ChromaDB is running
curl http://localhost:8001/api/v2/heartbeat

# Restart ChromaDB
docker restart docusearch-chromadb

# Check logs
docker logs docusearch-chromadb
```

## Advanced Usage

### Environment Variables

**GPU Mode:**
```bash
export DEVICE=mps
export MODEL_NAME=vidore/colpali-v1.2
export BATCH_SIZE_VISUAL=4
./scripts/start-all.sh
```

**CPU Mode:**
```bash
export DEVICE=cpu
export BATCH_SIZE_VISUAL=2
./scripts/start-all.sh --cpu
```

### Custom Ports

Edit `docker/docker-compose.yml`:
```yaml
services:
  copyparty:
    ports:
      - "9000:8000"  # Custom port
```

### Development Mode

```bash
# Start services
./scripts/start-all.sh --docker-only

# Run worker manually with debug logging
export LOG_LEVEL=DEBUG
./scripts/run-worker-native.sh run
```

## Performance Tips

### GPU Mode
- **Batch size**: Increase `BATCH_SIZE_VISUAL` for faster processing (uses more memory)
- **Model precision**: Use `fp16` for speed, `fp32` for accuracy
- **Concurrent uploads**: Worker processes one document at a time (by design)

### CPU Mode
- **Reduce batch size**: Set `BATCH_SIZE_VISUAL=1` to reduce memory
- **Limit concurrency**: Disable parallel processing if memory is limited

## Next Steps

- 📖 [GPU Acceleration Guide](docs/GPU_ACCELERATION.md)
- 📖 [Native Worker Setup](docs/NATIVE_WORKER_SETUP.md)
- 📖 [API Documentation](docs/API.md)
- 📖 [Architecture Overview](docs/ARCHITECTURE.md)

## Getting Help

**Status Check:**
```bash
./scripts/status.sh
```

**View All Logs:**
```bash
# Native worker
tail -f logs/worker-native.log

# Docker services
docker-compose -f docker/docker-compose.yml logs -f
```

**Issue Reporting:**
Include output from:
```bash
./scripts/status.sh --json
./scripts/run-worker-native.sh check
docker-compose -f docker/docker-compose.yml ps
```
