# DocuSearch Management Scripts

Complete reference for all management scripts in the DocuSearch system.

## Overview

DocuSearch provides 4 main scripts for managing services:

| Script | Purpose | Common Usage |
|--------|---------|--------------|
| `start-all.sh` | Start all services | `./scripts/start-all.sh` |
| `stop-all.sh` | Stop all services | `./scripts/stop-all.sh` |
| `status.sh` | Check system status | `./scripts/status.sh` |
| `run-worker-native.sh` | Native worker management | `./scripts/run-worker-native.sh setup` |

## start-all.sh

Start all DocuSearch services with optional GPU acceleration.

### Usage

```bash
./scripts/start-all.sh [option]
```

### Options

| Option | Description | Use Case |
|--------|-------------|----------|
| _(no option)_ | GPU mode (default) | M1/M2/M3 Mac with Metal support |
| `--gpu` | GPU mode (explicit) | Same as default |
| `--cpu` | CPU mode | No GPU setup, slower processing |
| `--docker-only` | Docker services only | Manual worker management |

### Examples

```bash
# Start with Metal GPU (default, recommended)
./scripts/start-all.sh

# Start with CPU (no setup required)
./scripts/start-all.sh --cpu

# Start only ChromaDB and Copyparty
./scripts/start-all.sh --docker-only
```

### What It Does

1. **Pre-flight checks**
   - Verifies Docker is running
   - Checks for port conflicts (8000, 8001, 8002)

2. **Starts Docker services**
   - ChromaDB (vector database)
   - Copyparty (file upload server)

3. **Starts worker** (mode-dependent)
   - **GPU mode**: Native worker with Metal acceleration
   - **CPU mode**: Docker worker with CPU
   - **Docker-only**: Skips worker

4. **Shows summary**
   - Service URLs
   - Worker mode (GPU/CPU)
   - Log file locations
   - Management commands

### Output

```
╔═══════════════════════════════════════════════════════════╗
║  DocuSearch - Starting All Services                       ║
╚═══════════════════════════════════════════════════════════╝

Mode: Native worker with Metal GPU acceleration

Pre-flight checks...
  ✓ Docker: Running

Starting Docker services...
  ✓ ChromaDB: Running on http://localhost:8001
  ✓ Copyparty: Running on http://localhost:8000

Starting native worker with Metal GPU...
  ✓ Worker (Native): Running on http://localhost:8002 (Metal GPU)
  ℹ Worker PID: 12345 (saved to .worker.pid)

╔═══════════════════════════════════════════════════════════╗
║  Services Started Successfully                            ║
╚═══════════════════════════════════════════════════════════╝

Available Services:
  → Upload UI:     http://localhost:8000
  → ChromaDB:      http://localhost:8001
  → Worker API:    http://localhost:8002
  → Worker Status: http://localhost:8002/status

Worker Mode: Native with Metal GPU
  ℹ Logs: logs/worker-native.log
  ℹ PID file: .worker.pid

Management:
  → Stop all:      ./scripts/stop-all.sh
  → View logs:     docker-compose -f docker/docker-compose.yml logs -f
  → Worker logs:   tail -f logs/worker-native.log

🚀 DocuSearch is running with Metal GPU acceleration!
```

---

## stop-all.sh

Stop all DocuSearch services gracefully or forcefully.

### Usage

```bash
./scripts/stop-all.sh [option]
```

### Options

| Option | Description | When to Use |
|--------|-------------|-------------|
| _(no option)_ | Graceful stop (SIGTERM) | Normal shutdown |
| `--force` | Force stop (SIGKILL) | Processes not responding |

### Examples

```bash
# Normal stop
./scripts/stop-all.sh

# Force stop if hanging
./scripts/stop-all.sh --force
```

### What It Does

1. **Stops native worker**
   - Checks for PID file (`.worker.pid`)
   - Sends SIGTERM (graceful) or SIGKILL (force)
   - Waits up to 10 seconds for graceful shutdown
   - Cleans up PID file
   - Detects and kills orphaned workers

2. **Stops Docker services**
   - Tries native worker compose config first
   - Falls back to standard compose config
   - Stops all docusearch-* containers
   - Force removes if `--force` specified

3. **Verifies shutdown**
   - Checks ports 8000, 8001, 8002
   - Reports any lingering processes
   - Shows log file locations

### Output

```
╔═══════════════════════════════════════════════════════════╗
║  DocuSearch - Stopping All Services                      ║
╚═══════════════════════════════════════════════════════════╝

Mode: Graceful stop (SIGTERM)

Stopping native worker...
  ℹ Worker PID: Found: 12345
  ℹ Worker: Gracefully stopping (SIGTERM)
  ✓ Worker: Stopped
  ✓ PID file: Cleaned up

Stopping Docker services...
  ℹ Docker Compose: Using native worker configuration
  ✓ Docker services: Stopped
  ✓ Containers: All stopped

Checking ports...
  ✓ Port 8000: Copyparty port is free
  ✓ Port 8001: ChromaDB port is free
  ✓ Port 8002: Worker port is free

Log files:
  ℹ Worker log: Saved (1.2M): logs/worker-native.log
  ℹ Docker logs: Available via: docker-compose -f docker/docker-compose.yml logs

╔═══════════════════════════════════════════════════════════╗
║  All Services Stopped                                     ║
╚═══════════════════════════════════════════════════════════╝

To restart services:
  → With GPU:  ./scripts/start-all.sh
  → CPU only:  ./scripts/start-all.sh --cpu

👋 DocuSearch stopped successfully
```

---

## status.sh

Check the current status of all DocuSearch services.

### Usage

```bash
./scripts/status.sh [option]
```

### Options

| Option | Description | Output Format |
|--------|-------------|---------------|
| _(no option)_ | Human-readable | Colored text with symbols |
| `--json` | JSON format | Machine-parseable JSON |

### Examples

```bash
# Check status (human-readable)
./scripts/status.sh

# Get status as JSON
./scripts/status.sh --json

# Use in scripts
if ./scripts/status.sh --json | jq -e '.all_running == true' > /dev/null; then
  echo "All services running"
fi
```

### What It Checks

1. **Docker services**
   - ChromaDB (http://localhost:8001/api/v2/heartbeat)
   - Copyparty (http://localhost:8000/)

2. **Processing worker**
   - Native worker PID file
   - Worker HTTP endpoint (http://localhost:8002/health)
   - Worker mode (Native/Docker)
   - Processing statistics

3. **Port usage**
   - Lists what's listening on 8000, 8001, 8002
   - Shows process name and PID

### Output (Text)

```
╔═══════════════════════════════════════════════════════════╗
║  DocuSearch - System Status                              ║
╚═══════════════════════════════════════════════════════════╝

Docker Services:
  ✓ ChromaDB:  Running on http://localhost:8001
  ✓ Copyparty: Running on http://localhost:8000

Processing Worker:
  ✓ Worker:    Running (Native with Metal GPU)
    → PID:     12345
    → Logs:    logs/worker-native.log
    → URL:     http://localhost:8002
    → Stats:   42 documents, 315 pages

Port Usage:
  ✓ :8000 → Python (PID: 12344)
  ✓ :8001 → docker-proxy (PID: 12343)
  ✓ :8002 → Python (PID: 12345)

System Status:
  ✓ All services running
```

### Output (JSON)

```json
{
  "services": {
    "chromadb": {
      "status": "running",
      "url": "http://localhost:8001"
    },
    "copyparty": {
      "status": "running",
      "url": "http://localhost:8000"
    },
    "worker": {
      "status": "running",
      "url": "http://localhost:8002",
      "mode": "native",
      "pid": "12345"
    }
  },
  "all_running": true
}
```

---

## run-worker-native.sh

Setup and run the processing worker natively on macOS for Metal GPU acceleration.

### Usage

```bash
./scripts/run-worker-native.sh [command]
```

### Commands

| Command | Description | When to Use |
|---------|-------------|-------------|
| `setup` | Install dependencies | First time setup |
| `run` | Run worker with Metal | Start processing worker |
| `check` | Check Metal availability | Verify GPU support |

### Examples

```bash
# First time setup
./scripts/run-worker-native.sh setup

# Run worker
./scripts/run-worker-native.sh run

# Check if Metal is available
./scripts/run-worker-native.sh check
```

### Setup Command

Creates a Python virtual environment and installs all dependencies:

1. **Creates venv**: `.venv-native/`
2. **Installs PyTorch** with Metal support
3. **Installs ML libraries**: transformers, sentence-transformers
4. **Installs processing**: pypdf, python-docx, PyMuPDF
5. **Installs ChromaDB** and utilities
6. **Installs ColPali** (from GitHub)
7. **Verifies Metal** availability

### Run Command

Starts the worker with Metal GPU:

1. **Activates venv** (if exists)
2. **Checks ChromaDB** connection
3. **Verifies uploads** directory
4. **Checks Metal** availability
5. **Shows config** (device, model, endpoints)
6. **Starts worker** on http://0.0.0.0:8002

### Check Command

Verifies Metal/MPS availability:

```bash
$ ./scripts/run-worker-native.sh check

Checking Metal/MPS availability...
  MPS Available: True
  MPS Built: True
✓ Metal/MPS is available!
```

### Environment Variables

Configure worker behavior:

```bash
# Model configuration
export DEVICE=mps                          # mps | cpu
export MODEL_NAME=vidore/colpali-v1.2
export MODEL_PRECISION=fp16                # fp16 | fp32

# ChromaDB connection
export CHROMA_HOST=localhost
export CHROMA_PORT=8001

# Performance tuning
export BATCH_SIZE_VISUAL=4
export BATCH_SIZE_TEXT=8

# Then run
./scripts/run-worker-native.sh run
```

---

## Common Workflows

### Daily Development

```bash
# Morning - start everything
./scripts/start-all.sh

# Work on code...

# Evening - stop everything
./scripts/stop-all.sh
```

### First Time Setup (GPU)

```bash
# 1. Setup Python environment
./scripts/run-worker-native.sh setup

# 2. Verify Metal
./scripts/run-worker-native.sh check

# 3. Start all services
./scripts/start-all.sh

# 4. Check status
./scripts/status.sh
```

### Quick CPU Setup (No GPU)

```bash
# Just start with CPU
./scripts/start-all.sh --cpu
```

### Debugging

```bash
# Start Docker services only
./scripts/start-all.sh --docker-only

# Run worker manually with debug logging
export LOG_LEVEL=DEBUG
./scripts/run-worker-native.sh run
```

### Troubleshooting

```bash
# Check status
./scripts/status.sh

# Force stop everything
./scripts/stop-all.sh --force

# Check specific service
docker logs docusearch-chromadb
tail -f logs/worker-native.log

# Restart everything
./scripts/stop-all.sh
./scripts/start-all.sh
```

---

## Integration with CI/CD

### GitHub Actions

```yaml
jobs:
  test:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup services
        run: |
          ./scripts/run-worker-native.sh setup
          ./scripts/start-all.sh

      - name: Wait for services
        run: |
          timeout 60 sh -c 'until ./scripts/status.sh --json | jq -e ".all_running == true"; do sleep 2; done'

      - name: Run tests
        run: pytest tests/

      - name: Cleanup
        if: always()
        run: ./scripts/stop-all.sh
```

### Docker Compose Alternative

```yaml
# Use scripts in docker-compose
version: '3.8'
services:
  test:
    build: .
    command: |
      sh -c "
        ./scripts/start-all.sh --cpu &&
        pytest tests/ &&
        ./scripts/stop-all.sh
      "
```

---

## Script Locations

All scripts are in `scripts/` directory:

```
scripts/
├── start-all.sh          # Start all services
├── stop-all.sh           # Stop all services
├── status.sh             # Check status
└── run-worker-native.sh  # Native worker management
```

Make executable:
```bash
chmod +x scripts/*.sh
```

---

## See Also

- [Quick Start Guide](../QUICK_START.md)
- [GPU Acceleration](GPU_ACCELERATION.md)
- [Native Worker Setup](NATIVE_WORKER_SETUP.md)
- [Main README](../README.md)
