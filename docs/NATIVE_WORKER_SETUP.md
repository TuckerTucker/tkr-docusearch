# Running Worker Natively for Metal/MPS GPU Acceleration

## Problem

Docker containers on macOS cannot access Metal/MPS (Metal Performance Shaders) because:
- Docker runs in a Linux VM on macOS
- Metal APIs are macOS-specific and not available in Linux
- PyTorch MPS backend requires native macOS process

**Symptom**: Worker logs show `Warning: Requested device 'mps' not available, falling back to CPU`

## Solution: Hybrid Architecture

Run a **hybrid setup**:
- ✅ **Worker runs natively** on macOS → Uses Metal GPU
- ✅ **ChromaDB in Docker** → Persistent vector database
- ✅ **Copyparty in Docker** → File upload server

## Quick Start

### 1. Setup Python Environment (First Time)

```bash
# Install dependencies and create virtual environment
./scripts/run-worker-native.sh setup
```

This will:
- Create a Python virtual environment (`.venv-native/`)
- Install PyTorch with Metal support
- Install all processing dependencies
- Verify Metal/MPS availability

### 2. Start Docker Services (ChromaDB + Copyparty)

```bash
cd docker
docker-compose -f docker-compose.yml -f docker-compose.native-worker.yml up -d
```

This starts:
- ChromaDB (vector database) on `localhost:8001`
- Copyparty (file upload) on `localhost:8000`
- **No containerized worker** (disabled via profile)

### 3. Run Worker Natively with Metal

```bash
# Run worker with Metal GPU acceleration
./scripts/run-worker-native.sh run
```

You should see:
```
✓ Metal/MPS is available!
Starting worker on http://0.0.0.0:8002
INFO: Application startup complete
```

### 4. Verify Metal Usage

Check the worker logs for:
```
✅ Good: Using device: mps
❌ Bad:  Warning: Requested device 'mps' not available, falling back to CPU
```

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│            Host (macOS)                 │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  Native Worker (Port 8002)      │   │
│  │  - Python 3.10+                 │   │
│  │  - PyTorch with Metal/MPS       │   │
│  │  - FastAPI HTTP server          │   │
│  │  - Accesses GPU via Metal       │   │
│  └─────────────────────────────────┘   │
│           ↓ HTTP              ↑         │
│  ┌────────────────┐   ┌───────────────┐│
│  │ Docker Network │   │               ││
│  │                │   │               ││
│  │  Copyparty     │   │  ChromaDB     ││
│  │  (Port 8000)   │   │  (Port 8001)  ││
│  │  - Webhooks    │   │  - Vectors    ││
│  └────────────────┘   └───────────────┘│
└─────────────────────────────────────────┘
```

## Requirements

- **macOS 12.3+** (for Metal/MPS support)
- **Python 3.10+**
- **Docker Desktop** (for ChromaDB and Copyparty)
- **Apple Silicon (M1/M2/M3)** or AMD GPU

## Verification Steps

### 1. Check Metal Availability

```bash
./scripts/run-worker-native.sh check
```

Expected output:
```
MPS Available: True
MPS Built: True
✓ Metal/MPS is available!
```

### 2. Test Processing Speed

With CPU (Docker):
```
Processing time: ~30-60 seconds per page
```

With Metal (Native):
```
Processing time: ~5-10 seconds per page
```

### 3. Monitor GPU Usage

```bash
# Terminal 1: Run worker
./scripts/run-worker-native.sh run

# Terminal 2: Monitor GPU
sudo powermetrics --samplers gpu_power -i 1000
```

## Environment Variables

The native worker script supports configuration via environment variables:

```bash
# Model configuration
export DEVICE="mps"                          # Use Metal GPU
export MODEL_NAME="vidore/colpali-v1.2"      # Model to use
export MODEL_PRECISION="fp16"                # Precision (fp16/fp32)

# ChromaDB connection
export CHROMA_HOST="localhost"               # ChromaDB host
export CHROMA_PORT="8001"                    # ChromaDB port

# Processing configuration
export BATCH_SIZE_VISUAL=4                   # Visual batch size
export BATCH_SIZE_TEXT=8                     # Text batch size

# Then run
./scripts/run-worker-native.sh run
```

## Troubleshooting

### Metal Not Available

**Problem**: `MPS Available: False`

**Solutions**:
1. Check macOS version: `sw_vers` (need 12.3+)
2. Update PyTorch: `pip install --upgrade torch`
3. Check GPU: `system_profiler SPDisplaysDataType`

### ChromaDB Connection Error

**Problem**: `Error: ChromaDB not accessible`

**Solution**:
```bash
# Start ChromaDB in Docker
cd docker
docker-compose up -d chromadb

# Verify it's running
curl http://localhost:8001/api/v2/heartbeat
```

### Webhook Not Triggering

**Problem**: Files uploaded but not processed

**Solution**:
```bash
# Check copyparty can reach native worker
docker-compose logs copyparty | grep -i error

# Verify worker is accessible from Docker
docker run --rm curlimages/curl curl http://host.docker.internal:8002/health
```

### Port Conflicts

**Problem**: `Address already in use: 8002`

**Solution**:
```bash
# Find process using port 8002
lsof -i :8002

# Kill process or use different port
export WORKER_PORT=8003
./scripts/run-worker-native.sh run
```

## Performance Comparison

| Configuration | Device | Pages/Second | Memory |
|--------------|--------|--------------|--------|
| Docker Worker | CPU | ~0.5 | 4GB |
| Native Worker | Metal | ~5-10 | 8GB |

**Speedup**: ~10-20x faster with Metal

## Switching Back to Docker

To return to fully containerized setup:

```bash
# Stop native worker (Ctrl+C)

# Start all services in Docker
cd docker
docker-compose up -d

# Worker will use CPU but everything runs in containers
```

## Development Workflow

### Daily Usage

```bash
# Morning: Start services
cd docker
docker-compose -f docker-compose.yml -f docker-compose.native-worker.yml up -d
./scripts/run-worker-native.sh run

# Work with GPU acceleration...

# Evening: Stop services
# Ctrl+C to stop native worker
docker-compose down
```

### Code Changes

When you modify worker code:

1. Stop native worker (Ctrl+C)
2. Make code changes
3. Restart: `./scripts/run-worker-native.sh run`

No rebuild needed - Python runs directly from source.

## Production Deployment

For production (without Metal):
- Use Docker Compose as-is
- Deploy to cloud with GPU instances
- Or accept CPU-only processing

For macOS production:
- Use native worker setup
- Add systemd/launchd service
- Monitor with process managers

## See Also

- [Docker Compose Configuration](../docker/docker-compose.yml)
- [Worker Implementation](../src/processing/worker_webhook.py)
- [Native Worker Script](../scripts/run-worker-native.sh)
