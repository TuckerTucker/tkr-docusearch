# GPU Acceleration Setup

## Current Status

✅ **Runs natively on macOS with Metal GPU**

All services run natively — no Docker required. The processing worker uses Metal/MPS
automatically when running on Apple Silicon.

## Why Metal Acceleration Matters

Metal (MPS in PyTorch) provides significant performance gains for the embedding pipeline:

| Device | Speed | Use Case |
|--------|-------|----------|
| CPU | 1x (baseline) | Fallback only |
| Metal GPU | **10-20x faster** | Default on Apple Silicon |

## How It Works

PyTorch detects Metal via the MPS backend. The worker selects the device at startup:

1. If `DEVICE=mps` (or auto-detected Apple Silicon) → Metal GPU is used
2. If Metal is unavailable → falls back to CPU with a warning in the logs

The Shikomi embedding service also runs natively and benefits from Metal when performing
vision-transformer inference.

## Verifying Metal Is Active

Check the worker logs at startup:

```bash
# Check what device the worker is using
grep -i "device\|mps\|cpu" logs/worker.log

# Expected outputs:
# ✅ Metal: "Using device: mps"
# ❌ CPU:   "Warning: Requested device 'mps' not available, falling back to CPU"
```

Or check Activity Monitor → GPU tab while submitting a document for processing.

## Starting the Stack

```bash
# Start all services natively (Shikomi → Worker → Research API → Frontend)
./scripts/start-all.sh
```

See [NATIVE_WORKER_SETUP.md](./NATIVE_WORKER_SETUP.md) for detailed setup instructions,
architecture overview, troubleshooting, and performance benchmarks.

## Alternative: Cloud GPU

For production deployments without Apple Silicon:

### Option 1: Cloud with NVIDIA GPUs

Deploy to a GPU-enabled cloud instance and set `DEVICE=cuda`:

- AWS EC2 (g4dn, p3 instances)
- Google Cloud (T4, V100 GPUs)
- Azure (NC-series VMs)

Update `.env`:

```bash
DEVICE=cuda
```

### Option 2: CPU-Only Processing

CPU processing works for low-volume use cases:

- Low document volume (<100 docs/day)
- Non-time-critical processing
- Development and testing without GPU hardware

## Summary

**Architecture**: All services run natively on macOS — no containers needed.
**GPU**: Metal/MPS is used automatically on Apple Silicon.
**Benefit**: 10-20x faster document embedding compared to CPU.
