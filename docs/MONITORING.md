# Process Monitoring Guide

**Status**: Current (2025-10-11)
**Applies to**: Docling parsing, Whisper ASR, and all document processing

---

## Overview

DocuSearch has built-in monitoring capabilities for tracking document processing. This guide covers:
1. **Current monitoring systems** (StatusManager, logs, API endpoints)
2. **What's visible** (status, progress, errors)
3. **What's NOT visible** (Docling/Whisper internals)
4. **How to improve monitoring** (recommendations)

---

## Current Monitoring Systems

### 1. StatusManager (Real-time Status Tracking)

**Location**: `src/processing/status_manager.py`

**What it tracks**:
- Document processing status (queued, parsing, embedding, storing, completed, failed)
- Progress percentage (0.0 - 1.0)
- Current stage description
- Page numbers (for multi-page documents)
- Elapsed time and estimated remaining time
- Error messages on failure

**Status Stages**:
```python
ProcessingStatusEnum:
    QUEUED           # Document queued for processing
    PARSING          # Docling/Whisper parsing in progress
    EMBEDDING_VISUAL # ColPali visual embeddings
    EMBEDDING_TEXT   # ColPali text embeddings
    STORING          # Saving to ChromaDB
    COMPLETED        # Successfully completed
    FAILED           # Processing failed
```

**API Endpoints**:
- `GET /status/{doc_id}` - Get status for specific document
- `GET /status/queue` - List all documents (queue view)
- `GET /status/active` - List currently processing documents
- `GET /status/stats` - Get summary statistics

**Example Usage**:
```bash
# Check status of a document
curl http://localhost:8002/status/abc123...

# View processing queue
curl http://localhost:8002/status/queue

# View active processes
curl http://localhost:8002/status/active
```

### 2. Structured Logging

**Location**: Logs written to `logs/worker-native.log` and stdout

**Log Levels**:
- `INFO`: Normal operations (started, completed, progress)
- `WARNING`: Non-critical issues (markdown extraction failed, using fallback)
- `ERROR`: Critical failures (parsing failed, ASR config error)
- `DEBUG`: Detailed information (ASR config details, compression ratios)

**What's logged**:

**Docling Parsing**:
```
INFO - Converting document with Docling: /path/to/file.pdf
INFO - Docling conversion complete: 10 pages
INFO - Extracted markdown: 15234 chars
WARNING - Markdown extraction failed: <error>
```

**Whisper ASR**:
```
INFO - Configuring ASR pipeline for .mp3 with model=turbo
DEBUG - ASR config: model=turbo, language=en, device=mps
WARNING - ASR disabled, audio file will have minimal processing
ERROR - Failed to configure ASR: <error>
```

**Markdown Compression**:
```
DEBUG - Compressed markdown: 15234 → 3421 chars
WARNING - Markdown compression failed: <error>, storing uncompressed
```

**Viewing Logs**:
```bash
# Tail logs in real-time
tail -f logs/worker-native.log

# View errors only
grep ERROR logs/worker-native.log

# View Whisper/ASR logs
grep -i "asr\|whisper" logs/worker-native.log

# View markdown logs
grep -i "markdown" logs/worker-native.log
```

### 3. Worker Health Endpoint

**Location**: `GET /health` on port 8002

**Returns**:
```json
{
  "status": "healthy",
  "embeddings_loaded": true,
  "chroma_connected": true,
  "uptime_seconds": 1234.5
}
```

---

## What's Currently Visible

### ✅ You CAN Monitor

1. **Overall Document Status**
   - Is it queued, parsing, embedding, or complete?
   - Progress percentage (updated at stage transitions)
   - Elapsed time and ETA

2. **Stage Transitions**
   - When document starts parsing
   - When parsing completes
   - When embeddings start
   - When storage begins
   - When fully complete

3. **High-Level Errors**
   - Parsing failures
   - ASR configuration errors
   - Storage failures
   - Error messages and stack traces

4. **Page-Level Progress** (for visual formats)
   - Current page being processed
   - Total pages in document

5. **Configuration Details** (in logs)
   - ASR model being used
   - Device (MPS/CPU/CUDA)
   - Language settings
   - Compression ratios

### ❌ You CANNOT Monitor (Currently)

1. **Docling Internal Progress**
   - OCR progress within a page
   - Table extraction progress
   - Image extraction progress
   - Model loading time

2. **Whisper Transcription Progress**
   - Audio decoding progress
   - Transcription % complete
   - Current audio segment
   - Token generation rate

3. **Real-time Throughput**
   - Pages per second
   - Tokens per second
   - MB processed per second

4. **Resource Usage**
   - GPU memory usage
   - CPU utilization
   - Disk I/O

---

## Why Docling/Whisper Progress is Not Visible

### Technical Limitations

1. **Docling is a black box**:
   - `DocumentConverter.convert()` is a synchronous call
   - No callback hooks for progress updates
   - No way to intercept internal stages

2. **Whisper is also a black box**:
   - Transcription happens inside Docling's ASR pipeline
   - No progress callbacks exposed
   - No way to track segment-by-segment processing

3. **Blocking Operations**:
   - Both operations block the thread until complete
   - Can't update status mid-operation
   - Status only updates before/after the call

### What We Currently Do

```python
# Before Docling/Whisper call
status_manager.update_status(
    doc_id=doc_id,
    status="parsing",
    progress=0.1,
    stage="Parsing document with Docling"
)

# Blocking call (no progress visibility)
result = converter.convert(file_path)  # <-- BLACK BOX

# After completion
status_manager.update_status(
    doc_id=doc_id,
    status="embedding_visual",
    progress=0.4,
    stage="Generating visual embeddings"
)
```

---

## Recommendations for Improved Monitoring

### Option 1: Enhance Logging (Easy, Low Impact)

**What**: Add more detailed log messages

**Implementation**:
```python
# In docling_parser.py
logger.info(f"Starting Docling conversion: {file_path} ({file_size_mb:.1f}MB)")
start_time = time.time()

result = converter.convert(file_path)

duration = time.time() - start_time
logger.info(
    f"Docling conversion complete: {len(pages)} pages in {duration:.1f}s "
    f"({len(pages)/duration:.2f} pages/sec)"
)

# For audio files
if ext in ['.mp3', '.wav']:
    logger.info(f"Starting Whisper transcription: {audio_duration:.1f}s audio")
    start_time = time.time()

    result = converter.convert(file_path)  # Includes transcription

    duration = time.time() - start_time
    logger.info(
        f"Whisper transcription complete in {duration:.1f}s "
        f"({audio_duration/duration:.2f}x realtime)"
    )
```

**Benefit**: Better visibility into processing time without code changes

**Drawback**: Still no real-time progress during long operations

---

### Option 2: Periodic Status Updates (Medium, Some Impact)

**What**: Use threading to update status periodically during processing

**Implementation**:
```python
import threading
import time

def update_status_periodically(doc_id, status_manager, stop_event):
    """Update status every 5 seconds while processing."""
    while not stop_event.is_set():
        status_manager.update_status(
            doc_id=doc_id,
            status="parsing",
            progress=0.2,  # Can't accurately calculate, use fixed value
            stage="Processing with Docling (please wait...)"
        )
        time.sleep(5)

# Before Docling call
stop_event = threading.Event()
status_thread = threading.Thread(
    target=update_status_periodically,
    args=(doc_id, status_manager, stop_event)
)
status_thread.start()

try:
    result = converter.convert(file_path)  # Blocking
finally:
    stop_event.set()
    status_thread.join()
```

**Benefit**: User sees that processing is still active

**Drawback**: Progress % is fake, just keeps document from appearing "stuck"

---

### Option 3: Timeout Monitoring (Easy, High Value)

**What**: Add timeout warnings for long-running operations

**Implementation**:
```python
import signal

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Operation timed out")

# Set timeout (e.g., 5 minutes for large documents)
timeout_seconds = 300
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(timeout_seconds)

try:
    result = converter.convert(file_path)
    signal.alarm(0)  # Cancel alarm
except TimeoutException:
    logger.error(f"Docling conversion timed out after {timeout_seconds}s")
    status_manager.mark_failed(
        doc_id=doc_id,
        error=f"Processing timed out after {timeout_seconds}s"
    )
    raise
```

**Benefit**: Prevents indefinitely stuck processes

**Drawback**: Still no progress during operation

---

### Option 4: External Monitoring Tools (Advanced)

**What**: Use external monitoring to track resource usage

**Tools**:

1. **GPU Monitoring** (for M1/M2/M3 Macs):
   ```bash
   # Monitor Metal GPU usage
   sudo powermetrics --samplers gpu_power -i 1000

   # Or use Activity Monitor
   # View → GPU History
   ```

2. **System Monitoring**:
   ```bash
   # CPU and memory usage
   htop

   # Or Activity Monitor GUI
   ```

3. **Log Aggregation**:
   ```bash
   # Use tail with filtering
   tail -f logs/worker-native.log | grep -E "INFO|ERROR|WARNING"

   # Or use structured logging tools
   # - Loki + Grafana
   # - ELK Stack
   # - Datadog
   ```

4. **Custom Dashboard**:
   - Poll `/status/queue` endpoint every 2 seconds
   - Display in web UI
   - Show: active docs, progress bars, elapsed time

**Benefit**: Professional monitoring without changing code

**Drawback**: Setup complexity

---

## Practical Monitoring Setup

### Basic Setup (Recommended)

1. **Monitor Logs**:
   ```bash
   # Terminal 1: Follow worker logs
   tail -f logs/worker-native.log

   # Terminal 2: Watch status
   watch -n 2 'curl -s http://localhost:8002/status/queue | jq .'
   ```

2. **Check Health**:
   ```bash
   # Verify worker is running
   curl http://localhost:8002/health
   ```

3. **View Processing Stats**:
   ```bash
   # Get counts
   curl http://localhost:8002/status/stats
   ```

### Advanced Setup (Optional)

1. **Create Monitoring Script**:
   ```bash
   #!/bin/bash
   # monitor.sh

   echo "=== DocuSearch Status Monitor ==="
   echo ""

   # Worker health
   echo "Worker Health:"
   curl -s http://localhost:8002/health | jq .
   echo ""

   # Processing stats
   echo "Processing Stats:"
   curl -s http://localhost:8002/status/stats | jq .
   echo ""

   # Active documents
   echo "Active Documents:"
   curl -s http://localhost:8002/status/active | jq '.[] | {filename, status, progress, elapsed_time}'
   ```

2. **Run in Loop**:
   ```bash
   watch -n 5 ./monitor.sh
   ```

---

## Troubleshooting

### Problem: "Document appears stuck at parsing"

**Diagnosis**:
```bash
# Check if worker is actually running
curl http://localhost:8002/health

# Check logs for errors
tail -n 100 logs/worker-native.log | grep -i error

# Check if process is consuming CPU (indicates still working)
ps aux | grep python | grep worker
```

**Causes**:
- Large document taking a long time (normal)
- Docling/Whisper crashed silently
- Out of memory
- ffmpeg missing (for MP3 files)

**Solutions**:
- Wait longer (some documents take 5-10 minutes)
- Check system resources
- Look for error messages in logs
- Restart worker if truly stuck

---

### Problem: "No progress updates for audio files"

**Diagnosis**:
```bash
# Check if ASR is enabled
grep "ASR" logs/worker-native.log

# Check if ffmpeg is installed (required for MP3)
which ffmpeg

# Check for ASR errors
grep -i "asr\|whisper" logs/worker-native.log | grep -i error
```

**Causes**:
- ASR disabled (`ASR_ENABLED=false`)
- ffmpeg not installed
- Whisper model not downloaded
- Invalid audio file

**Solutions**:
```bash
# Enable ASR
export ASR_ENABLED=true

# Install ffmpeg
brew install ffmpeg

# Pre-download Whisper model (optional)
python -c "
from transformers import AutoProcessor, AutoModel
model_id = 'openai/whisper-large-v3-turbo'
processor = AutoProcessor.from_pretrained(model_id)
model = AutoModel.from_pretrained(model_id)
print('Model downloaded successfully')
"
```

---

### Problem: "Markdown extraction failed"

**Diagnosis**:
```bash
# Look for markdown errors
grep "markdown" logs/worker-native.log | grep -i "error\|failed"
```

**Causes**:
- Document has no extractable text
- Docling export_to_markdown() failed
- Document is image-only

**Impact**:
- **Non-blocking**: Document still processes
- Markdown just won't be available for retrieval
- Other features (search, embeddings) work normally

---

## Summary

### What Works Well ✅
- High-level status tracking (queued → parsing → embedding → completed)
- Error detection and reporting
- Log-based monitoring
- API endpoints for programmatic access
- Page-level progress for multi-page documents

### Current Limitations ❌
- No real-time progress during Docling/Whisper operations
- No visibility into internal stages (OCR, table extraction, transcription)
- No throughput metrics (pages/sec, tokens/sec)
- No resource usage tracking (GPU, memory)

### Recommended Improvements
1. **Short term**: Add detailed timing logs (easy)
2. **Medium term**: Implement periodic status updates (moderate)
3. **Long term**: Integrate external monitoring tools (advanced)

### Key Takeaway
**Docling and Whisper are "black boxes"** - we can only monitor before and after, not during. For long operations (large PDFs, long audio files), use:
- Log timestamps to estimate throughput
- System monitoring tools to verify activity
- Timeout mechanisms to prevent indefinitely stuck processes

---

## Next Steps

To improve monitoring, consider implementing:
1. ✅ **Easy Win**: Add timing logs (see Option 1) - 30 minutes
2. ✅ **Better UX**: Periodic status updates (see Option 2) - 2 hours
3. ⏭️ **Production**: Timeout mechanism (see Option 3) - 1 hour
4. ⏭️ **Advanced**: External monitoring dashboard - 1 day

Would you like me to implement any of these improvements?
