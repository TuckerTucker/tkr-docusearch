# Native Worker Deployment on Apple Silicon (M1/M2/M3)

## Overview

For production deployment on Apple Silicon Macs, running the processing worker **natively** (outside Docker) provides significant performance benefits by leveraging Metal Performance Shaders (MPS) for GPU acceleration.

## Performance Comparison

| Metric | Native (MPS) | Docker (CPU) | Improvement |
|--------|-------------|--------------|-------------|
| Model Loading | 8s | 14s | **40% faster** |
| ColPali Inference | GPU-accelerated | CPU-only | **~3-5x faster** |
| Docling Processing | Metal-accelerated | Software rendering | **~2x faster** |
| Memory Overhead | Minimal | Container isolation | **Lower footprint** |

## Why Native Worker?

### ✅ Advantages

1. **MPS GPU Acceleration**
   - PyTorch uses Metal Performance Shaders
   - ColPali embeddings computed on GPU (7B model)
   - Significantly faster than CPU-only Docker

2. **Docling Metal Support**
   - Document rendering leverages Metal
   - AI models (DocLayNet, TableFormer) use GPU
   - Better performance for complex documents

3. **Direct File System Access**
   - No volume mounting overhead
   - Faster I/O for large documents
   - Simpler path management

4. **Lower Memory Overhead**
   - No container isolation costs
   - More memory available for models
   - Better resource utilization

### ⚠️ When to Use Docker Instead

Use Docker worker only for:
- **CI/CD testing** - Reproducible test environments
- **CPU-only cloud** - AWS/GCP instances without GPU
- **Cross-platform** - Testing on Linux/Windows

## Setup Instructions

### Prerequisites

- macOS with Apple Silicon (M1/M2/M3)
- Python 3.10 or 3.13
- Homebrew (optional, for system dependencies)

### 1. Create Virtual Environment

```bash
cd /path/to/tkr-docusearch

# Create virtual environment
python3 -m venv .venv-native

# Activate it
source .venv-native/bin/activate
```

### 2. Install Dependencies

```bash
# Install all requirements (includes Docling 2.55.1)
pip install -r requirements.txt

# Verify Docling installation
python -c "import docling; print(f'Docling {docling.__version__} installed')"

# Verify MPS availability
python -c "import torch; print(f'MPS available: {torch.backends.mps.is_available()}')"
```

Expected output:
```
Docling 2.55.1 installed
MPS available: True
```

### 3. Start ChromaDB (Docker)

ChromaDB can run in Docker as it's lightweight and doesn't need GPU:

```bash
docker start docusearch-chromadb

# Or if not created yet:
docker run -d \
  --name docusearch-chromadb \
  -p 8001:8000 \
  -v ./data/chroma_db:/data \
  -e IS_PERSISTENT=TRUE \
  -e ANONYMIZED_TELEMETRY=FALSE \
  chromadb/chroma:latest
```

### 4. Start Native Worker

```bash
# Activate environment
source .venv-native/bin/activate

# Set environment variables
export CHROMA_HOST=localhost
export CHROMA_PORT=8001
export DEVICE=mps
export MODEL_NAME=vidore/colpali-v1.2

# Start worker
python -m src.processing.worker_webhook
```

Expected startup output:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
Loading checkpoint shards: 100%|████| 2/2 [00:08<00:00, 4.19s/it]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8002
```

Note: **8 seconds** for model loading with MPS (vs 14s in Docker).

### 5. Verify MPS is Active

Check worker logs for MPS initialization:

```bash
# Look for MPS device selection
tail -f /path/to/worker.log | grep -i "device\|mps"
```

You should NOT see "falling back to CPU" - if you do, check PyTorch installation.

### 6. Test Document Processing

```bash
curl -X POST http://localhost:8002/process \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/test.pdf",
    "filename": "test.pdf"
  }'
```

Expected response:
```json
{
  "message": "Processing queued for test.pdf",
  "status": "queued"
}
```

## Production Deployment

### systemd Service (Linux)

Create `/etc/systemd/system/docusearch-worker.service`:

```ini
[Unit]
Description=DocuSearch Processing Worker
After=network.target docker.service

[Service]
Type=simple
User=docusearch
WorkingDirectory=/opt/docusearch
Environment="CHROMA_HOST=localhost"
Environment="CHROMA_PORT=8001"
Environment="DEVICE=mps"
ExecStart=/opt/docusearch/.venv-native/bin/python -m src.processing.worker_webhook
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
sudo systemctl enable docusearch-worker
sudo systemctl start docusearch-worker
sudo systemctl status docusearch-worker
```

### launchd Service (macOS)

Create `~/Library/LaunchAgents/com.docusearch.worker.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.docusearch.worker</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/.venv-native/bin/python</string>
        <string>-m</string>
        <string>src.processing.worker_webhook</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/tkr-docusearch</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>CHROMA_HOST</key>
        <string>localhost</string>
        <key>CHROMA_PORT</key>
        <string>8001</string>
        <key>DEVICE</key>
        <string>mps</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/docusearch-worker.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/docusearch-worker-error.log</string>
</dict>
</plist>
```

Load service:
```bash
launchctl load ~/Library/LaunchAgents/com.docusearch.worker.plist
launchctl start com.docusearch.worker
launchctl list | grep docusearch
```

## Monitoring

### Check Worker Health

```bash
curl http://localhost:8002/health
```

### Monitor Logs

```bash
# Follow worker logs
tail -f /tmp/docusearch-worker.log

# Check for errors
grep -i "error\|exception" /tmp/docusearch-worker.log

# Monitor processing times
grep -i "processed document" /tmp/docusearch-worker.log
```

### Monitor GPU Usage

```bash
# Check GPU activity (Metal)
sudo powermetrics --samplers gpu_power -i 1000 -n 5

# Monitor process memory
ps aux | grep "worker_webhook"
```

### Performance Metrics

Expected processing times (M1 Max, MPS enabled):

| Document Type | Pages | Processing Time |
|--------------|-------|-----------------|
| PDF | 10 | ~15-20s |
| PDF | 50 | ~60-80s |
| DOCX | 5 | ~8-12s |
| PPTX | 10 | ~12-18s |

If times are significantly higher, verify MPS is active.

## Troubleshooting

### MPS Not Available

**Symptom:** Logs show "MPS not available, falling back to CPU"

**Solutions:**
1. Check macOS version: Requires macOS 12.3+
2. Verify PyTorch installation:
   ```bash
   pip uninstall torch torchvision
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
   ```
3. Check system: Only works on Apple Silicon (M1/M2/M3)

### Slow Model Loading

**Symptom:** Model loading takes >15s

**Possible causes:**
1. Running in Docker (expected)
2. Models downloading on first run (expected, one-time)
3. MPS not active (check logs)
4. Disk I/O bottleneck (check disk usage)

**Solutions:**
1. Ensure native worker (not Docker)
2. Wait for initial model download (~14GB)
3. Verify MPS active in logs
4. Use SSD for model cache

### Out of Memory

**Symptom:** Worker crashes during processing

**Solutions:**
1. Increase system memory allocation
2. Reduce batch sizes:
   ```bash
   export BATCH_SIZE_VISUAL=2
   export BATCH_SIZE_TEXT=4
   ```
3. Process smaller documents in parallel
4. Monitor memory: `top -pid <worker_pid>`

### ChromaDB Connection Failed

**Symptom:** "Failed to connect to ChromaDB"

**Solutions:**
1. Check ChromaDB is running:
   ```bash
   docker ps | grep chromadb
   ```
2. Verify port 8001 is accessible:
   ```bash
   curl http://localhost:8001/api/v1/heartbeat
   ```
3. Check environment variables:
   ```bash
   echo $CHROMA_HOST $CHROMA_PORT
   ```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CHROMA_HOST` | `chromadb` | ChromaDB hostname (use `localhost` for native) |
| `CHROMA_PORT` | `8000` | ChromaDB port (Docker maps to 8001) |
| `DEVICE` | `mps` | PyTorch device: `mps`, `cuda`, or `cpu` |
| `MODEL_NAME` | `vidore/colpali-v1.2` | ColPali model from HuggingFace |
| `BATCH_SIZE_VISUAL` | `4` | Visual embedding batch size |
| `BATCH_SIZE_TEXT` | `8` | Text embedding batch size |
| `TEXT_CHUNK_SIZE` | `250` | Words per text chunk |
| `TEXT_CHUNK_OVERLAP` | `50` | Word overlap between chunks |
| `PAGE_RENDER_DPI` | `150` | DPI for page rendering |

## Comparison: Native vs Docker

### Native Worker
```bash
# Faster startup, MPS acceleration
source .venv-native/bin/activate
CHROMA_HOST=localhost CHROMA_PORT=8001 \
  python -m src.processing.worker_webhook
```

**Pros:**
- 40% faster model loading (8s vs 14s)
- GPU-accelerated inference
- Lower memory overhead
- Direct file access

**Cons:**
- Platform-specific (macOS only)
- Manual dependency management
- No isolation

### Docker Worker
```bash
# Slower, CPU-only, but portable
docker-compose up -d processing-worker
```

**Pros:**
- Cross-platform compatible
- Isolated environment
- Easier deployment

**Cons:**
- No MPS support (CPU-only)
- 40% slower startup
- Higher memory overhead
- Volume mounting overhead

## Recommendations

**For Development (M1/M2/M3 Mac):**
- ✅ Use native worker for speed and GPU access

**For Production (Apple Silicon server):**
- ✅ Use native worker with systemd/launchd
- ✅ Monitor with health checks and alerts

**For Production (Linux/x86 server):**
- ⚠️ Use Docker worker (no MPS available anyway)
- Consider CUDA if NVIDIA GPU available

**For CI/CD:**
- ✅ Use Docker for reproducible tests
- Accept slower performance as trade-off

## See Also

- [Docling Documentation](https://github.com/DS4SD/docling)
- [PyTorch MPS Backend](https://pytorch.org/docs/stable/notes/mps.html)
- [ColPali Model](https://huggingface.co/vidore/colpali-v1.2)
- [ChromaDB Documentation](https://docs.trychroma.com/)
