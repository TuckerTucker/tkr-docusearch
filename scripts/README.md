# DocuSearch Scripts Directory

## Current Scripts (Active)

### Production Scripts (Use These!)

| Script | Purpose | Usage |
|--------|---------|-------|
| **start-all.sh** | Start all services (GPU/CPU) | `./scripts/start-all.sh [--gpu\|--cpu]` |
| **stop-all.sh** | Stop all services | `./scripts/stop-all.sh [--force]` |
| **status.sh** | Check service status | `./scripts/status.sh [--json]` |
| **run-worker-native.sh** | Native worker management | `./scripts/run-worker-native.sh [setup\|run\|check]` |

**📖 See [docs/SCRIPTS.md](../docs/SCRIPTS.md) for complete documentation**

### Legacy/Utility Scripts

| Script | Purpose | Notes |
|--------|---------|-------|
| `setup.sh` | Initial project setup | Docker, directories, model download |
| `start.sh` | Docker services only | Redundant with `start-all.sh --docker-only` |
| `stop.sh` | Stop Docker services | Redundant with `stop-all.sh` |

## Script Comparison

### Start Scripts

```bash
# Modern (recommended)
./scripts/start-all.sh              # Full system with GPU
./scripts/start-all.sh --cpu        # Full system with CPU
./scripts/start-all.sh --docker-only # Docker only

# Legacy/utility
./scripts/start.sh                  # Docker only (basic)
./scripts/setup.sh                  # First-time setup
```

### Stop Scripts

```bash
# Modern (recommended)
./scripts/stop-all.sh               # Stop everything gracefully
./scripts/stop-all.sh --force       # Force stop

# Legacy
./scripts/stop.sh                   # Docker only (basic)
```

## Quick Reference

### First Time Setup

```bash
# Option 1: Full setup (includes model download)
./scripts/setup.sh

# Option 2: Native worker setup (for GPU)
./scripts/run-worker-native.sh setup
```

### Daily Workflow

```bash
# Start
./scripts/start-all.sh

# Check status
./scripts/status.sh

# Stop
./scripts/stop-all.sh
```

### Development

```bash
# Start Docker only
./scripts/start-all.sh --docker-only

# Run worker with debug logging
export LOG_LEVEL=DEBUG
./scripts/run-worker-native.sh run
```

## Archived Scripts

**Location**: `scripts/legacy/`

Old scripts for the pre-webhook architecture (Wave 3+4):
- `legacy/start-all.sh` - Old full system startup
- `legacy/stop-all.sh` - Old system shutdown
- `legacy/start-api.sh` - Standalone API server
- `legacy/start-ui.sh` - Old UI startup

**Don't use these** - they're for the old `src.api.server` architecture.

See [legacy/README.md](legacy/README.md) for details.

## Documentation

- [Complete Scripts Guide](../docs/SCRIPTS.md) - Full reference
- [Quick Start Guide](../QUICK_START.md) - Getting started
- [GPU Setup](../docs/GPU_ACCELERATION.md) - Metal GPU guide
- [Native Worker](../docs/NATIVE_WORKER_SETUP.md) - Detailed setup

## Script Locations

```
scripts/
├── start-all.sh          # ✅ Main startup script
├── stop-all.sh           # ✅ Main shutdown script
├── status.sh             # ✅ Status checker
├── run-worker-native.sh  # ✅ Native worker manager
├── setup.sh              # Utility: first-time setup
├── start.sh              # Utility: Docker only (redundant)
├── stop.sh               # Utility: Docker stop (redundant)
├── legacy/               # Archived old scripts
│   ├── README.md
│   ├── start-all.sh      # ⚠️ Old architecture
│   ├── stop-all.sh       # ⚠️ Old architecture
│   ├── start-api.sh      # ⚠️ Old architecture
│   └── start-ui.sh       # ⚠️ Old architecture
└── README.md             # This file
```

## Choosing the Right Script

**For normal use:**
```bash
./scripts/start-all.sh    # Start everything
./scripts/status.sh        # Check status
./scripts/stop-all.sh      # Stop everything
```

**For first-time setup:**
```bash
./scripts/setup.sh                    # Project setup
./scripts/run-worker-native.sh setup  # GPU worker setup
```

**For development:**
```bash
./scripts/start-all.sh --docker-only  # Docker services only
./scripts/run-worker-native.sh run    # Worker separately
```

**Don't use:**
```bash
./scripts/legacy/*        # Old architecture scripts
```

## Environment Variables

All scripts respect these environment variables:

**Worker configuration:**
```bash
export DEVICE=mps                    # mps | cpu | cuda
export MODEL_NAME=vidore/colpali-v1.2
export BATCH_SIZE_VISUAL=4
```

**Service ports:**
```bash
export COPYPARTY_PORT=8000
export CHROMADB_PORT=8001
export WORKER_PORT=8002
```

**ChromaDB connection:**
```bash
export CHROMA_HOST=localhost
export CHROMA_PORT=8001
```

## Troubleshooting

### Scripts not executable

```bash
chmod +x scripts/*.sh
```

### Port conflicts

```bash
# Check ports
lsof -i :8000,8001,8002

# Force stop everything
./scripts/stop-all.sh --force
```

### Legacy script errors

If you see errors about `src.api.server`:
```bash
# Don't use legacy scripts
# Use modern scripts instead
./scripts/start-all.sh
```

## Migration Guide

**From legacy scripts:**

| Old | New |
|-----|-----|
| `./start-all.sh` (root) | `./scripts/start-all.sh` |
| `./stop-all.sh` (root) | `./scripts/stop-all.sh` |
| `./start-api.sh` (root) | `./scripts/start-all.sh` |
| `./start-ui.sh` (root) | Copyparty UI (auto-started) |

**The root-level scripts have been moved to `scripts/legacy/`**

---

For complete documentation, see:
- [📖 Scripts Guide](../docs/SCRIPTS.md)
- [📖 Quick Start](../QUICK_START.md)
- [📖 Main README](../README.md)
