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

### Examples

```bash
# Start with Metal GPU (default, recommended)
./scripts/start-all.sh

# Start with CPU (no setup required)
./scripts/start-all.sh --cpu
```

### What It Does

1. **Pre-flight checks**
   - Checks for port conflicts (8002, 8004, 50051, 3333)
   - Verifies Koji DB path is accessible

2. **Starts Shikomi** (gRPC embedding service)
   - Listens on `127.0.0.1:50051`
   - HTTP health check on port 8080
   - PID saved to `.shikomi.pid`

3. **Starts worker** (mode-dependent)
   - **GPU mode**: Native worker with Metal acceleration on port 8002
   - **CPU mode**: Native worker with CPU on port 8002

4. **Starts Research API** on port 8004

5. **Starts Frontend** (Vite dev server) on port 3333

6. **Shows summary**
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
  ✓ Ports: Available

Starting Shikomi embedding service...
  ✓ Shikomi: Running on 127.0.0.1:50051 (PID: 12340)

Starting native worker with Metal GPU...
  ✓ Worker (Native): Running on http://localhost:8002 (Metal GPU)
  ℹ Worker PID: 12345 (saved to .worker.pid)

Starting Research API...
  ✓ Research API: Running on http://localhost:8004

Starting Frontend...
  ✓ Frontend: Running on http://localhost:3333

╔═══════════════════════════════════════════════════════════╗
║  Services Started Successfully                            ║
╚═══════════════════════════════════════════════════════════╝

Available Services:
  → Frontend:      http://localhost:3333
  → Worker API:    http://localhost:8002
  → Worker Status: http://localhost:8002/status
  → Research API:  http://localhost:8004
  → Shikomi gRPC:  127.0.0.1:50051

Worker Mode: Native with Metal GPU
  ℹ Logs: logs/worker.log
  ℹ PID file: .worker.pid

Management:
  → Stop all:      ./scripts/stop-all.sh
  → Worker logs:   tail -f logs/worker.log
  → All logs:      tail -f logs/*.log

DocuSearch is running with Metal GPU acceleration!
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

2. **Stops Shikomi**
   - Checks for PID file (`.shikomi.pid`)
   - Sends SIGTERM (graceful) or SIGKILL (force)
   - Cleans up PID file

3. **Stops Research API and Frontend**
   - Terminates processes by PID files

4. **Verifies shutdown**
   - Checks ports 8002, 8004, 50051, 3333
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

Stopping Shikomi...
  ℹ Shikomi PID: Found: 12340
  ✓ Shikomi: Stopped

Stopping Research API...
  ✓ Research API: Stopped

Stopping Frontend...
  ✓ Frontend: Stopped

Checking ports...
  ✓ Port 8002: Worker port is free
  ✓ Port 8004: Research API port is free
  ✓ Port 50051: Shikomi port is free
  ✓ Port 3333: Frontend port is free

Log files:
  ℹ Worker log: Saved (1.2M): logs/worker.log
  ℹ Shikomi log: Saved: logs/shikomi.log

╔═══════════════════════════════════════════════════════════╗
║  All Services Stopped                                     ║
╚═══════════════════════════════════════════════════════════╝

To restart services:
  → With GPU:  ./scripts/start-all.sh
  → CPU only:  ./scripts/start-all.sh --cpu

DocuSearch stopped successfully
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

1. **Shikomi embedding service**
   - HTTP health check (http://localhost:8080/health)
   - gRPC availability on 127.0.0.1:50051

2. **Processing worker**
   - Native worker PID file
   - Worker HTTP endpoint (http://localhost:8002/health)
   - Worker mode (Native/CPU)
   - Processing statistics

3. **Research API**
   - HTTP endpoint (http://localhost:8004/api/research/health)

4. **Frontend**
   - Vite dev server (http://localhost:3333)

5. **Port usage**
   - Lists what's listening on 8002, 8004, 50051, 3333
   - Shows process name and PID

### Output (Text)

```
╔═══════════════════════════════════════════════════════════╗
║  DocuSearch - System Status                              ║
╚═══════════════════════════════════════════════════════════╝

Embedding Service:
  ✓ Shikomi: Running on 127.0.0.1:50051

Processing Worker:
  ✓ Worker:    Running (Native with Metal GPU)
    → PID:     12345
    → Logs:    logs/worker.log
    → URL:     http://localhost:8002
    → Stats:   42 documents, 315 pages

Research API:
  ✓ Research:  Running on http://localhost:8004

Frontend:
  ✓ Frontend:  Running on http://localhost:3333

Port Usage:
  ✓ :8002  → Python (PID: 12345)
  ✓ :8004  → Python (PID: 12346)
  ✓ :50051 → shikomi-worker (PID: 12340)
  ✓ :3333  → node (PID: 12347)

System Status:
  ✓ All services running
```

### Output (JSON)

```json
{
  "services": {
    "shikomi": {
      "status": "running",
      "grpc_target": "127.0.0.1:50051"
    },
    "worker": {
      "status": "running",
      "url": "http://localhost:8002",
      "mode": "native",
      "pid": "12345"
    },
    "research": {
      "status": "running",
      "url": "http://localhost:8004"
    },
    "frontend": {
      "status": "running",
      "url": "http://localhost:3333"
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
4. **Installs processing**: pypdf, python-docx, PyMuPDF, docling
5. **Installs Koji** (Lance-based database client)
6. **Verifies Metal** availability

### Run Command

Starts the worker with Metal GPU:

1. **Activates venv** (if exists)
2. **Checks Shikomi** connection on `127.0.0.1:50051`
3. **Verifies uploads** directory (`data/uploads/`)
4. **Checks Metal** availability
5. **Shows config** (device, Shikomi target, endpoints)
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
# Device configuration
export DEVICE=mps                          # mps | cpu

# Shikomi embedding service
export SHIKOMI_GRPC_TARGET=127.0.0.1:50051
export SHIKOMI_USE_MOCK=false              # true for development without model

# Koji database
export KOJI_DB_PATH=data/koji.db

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
# Start with CPU and mock embeddings
export SHIKOMI_USE_MOCK=true
./scripts/start-all.sh --cpu
```

### Debugging

```bash
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

# Check specific service logs
tail -f logs/worker.log
tail -f logs/shikomi.log
tail -f logs/research.log

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
          export SHIKOMI_USE_MOCK=true
          ./scripts/run-worker-native.sh setup
          ./scripts/start-all.sh --cpu

      - name: Wait for services
        run: |
          timeout 60 sh -c 'until ./scripts/status.sh --json | jq -e ".all_running == true"; do sleep 2; done'

      - name: Run tests
        run: pytest tests/

      - name: Cleanup
        if: always()
        run: ./scripts/stop-all.sh
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

- [Quick Start Guide](QUICK_START.md)
- [GPU Acceleration](GPU_ACCELERATION.md)
- [Native Worker Setup](NATIVE_WORKER_SETUP.md)
- [Main README](../README.md)
