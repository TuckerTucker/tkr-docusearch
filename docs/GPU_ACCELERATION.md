# GPU Acceleration Setup

## Current Status

❌ **Running on CPU** (in Docker container)
✅ **Can run with Metal GPU** (native macOS)

## Why Docker Doesn't Use Metal

Docker containers on macOS **cannot access Metal/MPS** because:

1. **Docker runs in Linux VM** - macOS Docker Desktop uses a Linux virtual machine
2. **Metal is macOS-only** - Metal APIs don't exist in Linux
3. **No GPU passthrough** - Unlike NVIDIA CUDA, Metal can't be passed through to containers

## Solution: Run Worker Natively

The processing worker can run **directly on macOS** to access Metal GPU while keeping other services in Docker.

### Quick Start

```bash
# 1. Setup Python environment with Metal support
./scripts/run-worker-native.sh setup

# 2. Start Docker services (ChromaDB + Copyparty only)
cd docker
docker-compose -f docker-compose.yml -f docker-compose.native-worker.yml up -d

# 3. Run worker natively with Metal
./scripts/run-worker-native.sh run
```

### Expected Performance

| Setup | Device | Speed | Use Case |
|-------|--------|-------|----------|
| Docker (current) | CPU | 1x (baseline) | Simple deployment, low volume |
| Native | Metal GPU | **10-20x faster** | High volume, development |

## Detailed Documentation

See [NATIVE_WORKER_SETUP.md](./NATIVE_WORKER_SETUP.md) for:
- Complete setup instructions
- Architecture diagram
- Troubleshooting guide
- Performance benchmarks
- Environment configuration

## Alternative: Cloud GPU

For production without macOS:

### Option 1: Cloud with NVIDIA GPUs
```yaml
# Use NVIDIA Docker runtime
services:
  processing-worker:
    runtime: nvidia
    environment:
      - DEVICE=cuda
```

Deploy to:
- AWS EC2 (g4dn, p3 instances)
- Google Cloud (T4, V100 GPUs)
- Azure (NC-series VMs)

### Option 2: Accept CPU Processing

Current Docker setup works fine for:
- Low document volume (<100 docs/day)
- Non-time-critical processing
- Development/testing

## Checking Your Current Setup

```bash
# Check what device worker is using
docker logs docusearch-worker 2>&1 | grep -i "device\|mps\|cpu"

# Expected outputs:
# ❌ CPU:   "Warning: Requested device 'mps' not available, falling back to CPU"
# ✅ Metal: "Using device: mps"
```

## Summary

**Problem**: Docker can't use macOS Metal GPU
**Solution**: Run worker natively with `./scripts/run-worker-native.sh`
**Benefit**: 10-20x faster processing with Metal acceleration
