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

**Primary Interface**: **http://localhost:3333** (React UI)
**File Uploads**: **http://localhost:8002/uploads/** (Worker upload endpoint)

---

## Prerequisites

- **macOS 12.3+** (for Metal GPU support)
- **Python 3.10+**
- **Rust toolchain** (for building Shikomi embedding service)

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
# Start all services in CPU mode
./scripts/start-all.sh --cpu
```

## Daily Usage

### Start Services

```bash
# With GPU acceleration (default)
./scripts/start-all.sh

# CPU only (no GPU setup needed)
./scripts/start-all.sh --cpu
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

| Service | URL | Purpose | Notes |
|---------|-----|---------|-------|
| **React Frontend** | http://localhost:3333 | **Primary user interface** | Search, browse, research |
| **Worker API** | http://localhost:8002 | Processing + upload API | API only |
| **Research API** | http://localhost:8004 | LLM research (backend) | API only |
| **Shikomi** | localhost:50051 (gRPC) | Embedding service | gRPC only |

**Primary Interface**: Use the React frontend at **http://localhost:3333** for all user interactions (search, document viewing, research).

**File Uploads**: The worker at port 8002 handles file uploads via `POST /uploads/`.

## Architecture

### Native Services (All Modes)
```
┌─────────────────────────────────┐
│         Host (macOS)            │
│  ┌─────────────────────────┐    │
│  │ React Frontend (Vite)   │    │
│  │ Port: 3333              │    │
│  └─────────────────────────┘    │
│  ┌─────────────────────────┐    │
│  │  Shikomi (gRPC)         │    │
│  │  Port: 50051            │    │
│  └─────────────────────────┘    │
│  ┌─────────────────────────┐    │
│  │  Worker (Native - GPU)  │    │
│  │  Port: 8002             │    │
│  └─────────────────────────┘    │
│  ┌─────────────────────────┐    │
│  │  Research API           │    │
│  │  Port: 8004             │    │
│  └─────────────────────────┘    │
│  ┌─────────────────────────┐    │
│  │  Koji DB (Lance files)  │    │
│  │  data/koji.db/          │    │
│  └─────────────────────────┘    │
└─────────────────────────────────┘
```

**Pros:**
- Metal GPU acceleration for embedding generation
- Real-time document processing
- No container overhead
- Full native performance

## Workflow

### 1. Upload Documents

**Via Web UI:**
1. Open http://localhost:3333
2. Use the upload interface to drag & drop PDF/DOCX/PPTX files
3. Files are sent to the worker at http://localhost:8002/uploads/
4. Processing begins automatically

**Via CLI:**
```bash
# Upload file directly to worker
curl -F "file=@document.pdf" http://localhost:8002/uploads/
```

### 2. Processing Pipeline

1. **Worker** receives file upload at `POST /uploads/`
2. **Worker** processes document:
   - Parse document (Docling)
   - Extract pages as images
   - Generate visual embeddings (Shikomi gRPC + Metal GPU)
   - Extract text chunks
   - Generate text embeddings
   - Store in Koji (Lance-based file database at `data/koji.db/`)
3. **Status** available via http://localhost:8002/status

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

**All services log to `logs/`:**
```bash
# Follow worker logs
tail -f logs/worker.log

# Follow research API logs
tail -f logs/research.log

# Follow Shikomi logs
tail -f logs/shikomi.log

# Show last 100 lines of worker log
tail -100 logs/worker.log
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

### Monitor GPU Usage

```bash
# Real-time GPU monitoring
sudo powermetrics --samplers gpu_power -i 1000
```

## Troubleshooting

### Services Won't Start

```bash
# Check port conflicts
lsof -i :8002,8004,50051,3333

# Force stop and restart
./scripts/stop-all.sh --force
./scripts/start-all.sh
```

### Worker Not Processing

```bash
# Check worker logs
tail -50 logs/worker.log

# Test upload manually
curl -F "file=@test.pdf" http://localhost:8002/uploads/

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

### Koji Database Error

```bash
# Check Koji DB path exists
ls data/koji.db/

# Check worker health
curl http://localhost:8002/health | jq '.koji_connected'
```

### Shikomi Not Connecting

```bash
# Check Shikomi is running
curl http://localhost:8080/health  # Shikomi HTTP health port

# Check logs
tail -50 logs/shikomi.log

# Verify PID file
cat .shikomi.pid
```

## Advanced Usage

### Environment Variables

**GPU Mode:**
```bash
export DEVICE=mps
export SHIKOMI_GRPC_TARGET=127.0.0.1:50051
export SHIKOMI_USE_MOCK=false
export BATCH_SIZE_VISUAL=4
./scripts/start-all.sh
```

**CPU Mode / Mock Embeddings:**
```bash
export DEVICE=cpu
export SHIKOMI_USE_MOCK=true
export BATCH_SIZE_VISUAL=2
./scripts/start-all.sh --cpu
```

**Koji database path:**
```bash
export KOJI_DB_PATH=data/koji.db
```

### Development Mode

```bash
# Run worker manually with debug logging
export LOG_LEVEL=DEBUG
./scripts/run-worker-native.sh run
```

## Performance Tips

### GPU Mode
- **Batch size**: Increase `BATCH_SIZE_VISUAL` for faster processing (uses more memory)
- **Model precision**: Use `fp16` for speed, `fp32` for accuracy
- **Concurrent uploads**: Worker processes one document at a time (by design)

### CPU Mode / Mock Mode
- **Reduce batch size**: Set `BATCH_SIZE_VISUAL=1` to reduce memory
- **Use mock embeddings**: Set `SHIKOMI_USE_MOCK=true` for development without a model

## Next Steps

- [GPU Acceleration Guide](GPU_ACCELERATION.md)
- [Native Worker Setup](NATIVE_WORKER_SETUP.md)
- [Multi-Format Support](MULTI_FORMAT_SUPPORT.md)
- [API Documentation](API_REFERENCE.md)

## Getting Help

**Status Check:**
```bash
./scripts/status.sh
```

**View All Logs:**
```bash
# Worker
tail -f logs/worker.log

# All logs
tail -f logs/*.log
```

**Issue Reporting:**
Include output from:
```bash
./scripts/status.sh --json
./scripts/run-worker-native.sh check
```
