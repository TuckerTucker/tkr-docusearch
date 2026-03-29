# DocuSearch Scripts Directory

## Current Scripts (Active)

### Production Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| **start-all.sh** | Start all services (GPU/CPU) | `./scripts/start-all.sh [--gpu\|--cpu]` |
| **stop-all.sh** | Stop all services | `./scripts/stop-all.sh [--force]` |
| **status.sh** | Check service status | `./scripts/status.sh [--json]` |
| **run-worker-native.sh** | Native worker management | `./scripts/run-worker-native.sh [setup\|run\|check]` |
| **start-research-api.sh** | Start research API | `./scripts/start-research-api.sh` |

See [docs/SCRIPTS.md](../docs/SCRIPTS.md) for complete documentation.

## Quick Reference

### First Time Setup

```bash
# Install Python dependencies
pip install -e ".[dev]"

# Set up native worker (GPU)
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
# Run worker with debug logging
export LOG_LEVEL=DEBUG
./scripts/run-worker-native.sh run
```

## Script Locations

```
scripts/
├── start-all.sh          # Main startup script
├── stop-all.sh           # Main shutdown script
├── status.sh             # Status checker
├── run-worker-native.sh  # Native worker manager
├── start-research-api.sh # Research API launcher
├── legacy/               # Archived old scripts
│   └── README.md
└── README.md             # This file
```

## Environment Variables

All scripts respect these environment variables:

**Worker configuration:**
```bash
export DEVICE=mps                    # mps | cpu | cuda
export KOJI_DB_PATH=data/koji.db     # Koji database path
```

**Service ports:**
```bash
export WORKER_PORT=8002
export RESEARCH_API_PORT=8004
```

## Troubleshooting

### Scripts not executable

```bash
chmod +x scripts/*.sh
```

### Port conflicts

```bash
# Check ports
lsof -i :8002,8004

# Force stop everything
./scripts/stop-all.sh --force
```

---

For complete documentation, see:
- [Scripts Guide](../docs/SCRIPTS.md)
- [Main README](../README.md)
