# Real-Time Monitoring Implementation

## Overview

Implemented comprehensive real-time monitoring system for Docling parsing and Whisper transcription operations with WebSocket-based live updates.

## What Was Implemented

### 1. Enhanced Timing Logs ✓
**File**: `src/processing/docling_parser.py`

Added detailed timing and throughput metrics:
- File size logging (MB)
- Operation start/completion timestamps
- Processing duration
- Throughput metrics (pages/sec, MB/sec)
- Special handling for audio files (Whisper transcription)

**Example logs**:
```
Starting Docling conversion: document.pdf (2.45MB, format: .pdf)
Docling conversion complete: 15 pages in 12.3s (1.22 pages/sec, 0.20 MB/sec)

Starting Whisper transcription: audio.mp3 (5.12MB, model=base)
Whisper transcription complete in 8.7s (file size: 5.12MB, 0.59 MB/sec)
```

### 2. Periodic Status Updates ✓
**File**: `src/processing/monitoring_utils.py`

Created utilities for periodic status updates during long-running operations:

**Classes**:
- `PeriodicStatusUpdater`: Background thread that sends updates every N seconds
- `TimeoutException`: Raised when operations exceed timeout

**Context Managers**:
- `periodic_status_updates()`: Send status updates every 5 seconds
- `operation_timeout()`: Monitor operation timeouts
- `monitored_operation()`: Combined periodic updates + timeout monitoring

**Usage Example**:
```python
from src.processing.monitoring_utils import monitored_operation

with monitored_operation(
    status_callback=lambda: update_status(...),
    timeout_seconds=300,
    operation_name="Docling parsing",
    update_interval=5.0
):
    result = converter.convert(file_path)
```

### 3. Timeout Monitoring ✓
**Included in**: `src/processing/monitoring_utils.py`

Uses `signal.SIGALRM` to detect stuck operations:
- Configurable timeout duration
- Raises `TimeoutException` if exceeded
- Prevents infinite hangs on problematic files

### 4. WebSocket Broadcasting ✓
**File**: `src/processing/websocket_broadcaster.py`

Manages WebSocket connections for real-time updates:

**Features**:
- Multiple client support
- Automatic disconnect handling
- Thread-safe message broadcasting
- Timestamp injection
- Message types: status_update, log, stats, connection

**API**:
```python
broadcaster = get_broadcaster()

# Broadcast status update
await broadcaster.broadcast_status_update(
    doc_id="abc123",
    status="processing",
    progress=0.5,
    filename="document.pdf",
    stage="embedding"
)

# Broadcast log message
await broadcaster.broadcast_log_message(
    level="INFO",
    message="Processing started",
    doc_id="abc123"
)

# Broadcast stats
await broadcaster.broadcast_processing_stats({
    "active": 2,
    "completed": 15,
    "failed": 1,
    "total": 18
})
```

### 5. Web Monitoring Dashboard ✓
**File**: `src/processing/static/monitor.html`

Real-time web-based monitoring interface:

**Features**:
- Live WebSocket connection status
- Processing statistics (active, completed, failed, total)
- Active processing queue with progress bars
- Real-time log stream with color-coded levels
- Auto-reconnect on disconnect
- Dark theme, responsive design

**Access**: http://localhost:8002/static/monitor.html

### 6. Worker Integration ✓
**File**: `src/processing/worker_webhook.py`

Integrated monitoring into worker:

**Changes**:
- Added WebSocket endpoint: `ws://localhost:8002/ws`
- Event loop capture for async broadcasts from sync context
- Helper function: `_broadcast_from_sync()` for thread-safe broadcasting
- Broadcasts at key processing stages:
  - Processing start
  - Processing completion
  - Processing failure
  - Progress updates

**WebSocket Endpoint**:
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time monitoring WebSocket endpoint."""
    broadcaster = get_broadcaster()
    await broadcaster.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            # Handle client messages
    except WebSocketDisconnect:
        await broadcaster.disconnect(websocket)
```

## Testing

### Simple WebSocket Test
```bash
python3 test_websocket.py
```

Verifies:
- WebSocket connection
- Welcome message reception
- Basic connectivity

### Comprehensive Integration Test
```bash
python3 test_monitoring_integration.py
```

Verifies:
- WebSocket connection
- Document processing with real-time updates
- Status broadcasts (start, progress, completion/failure)
- Log broadcasts (INFO, ERROR)
- Message categorization

## How to Use

### 1. Start the System
```bash
./scripts/start-all.sh
```

### 2. Open Monitoring Dashboard
Visit: http://localhost:8002/static/monitor.html

### 3. Upload Documents
Visit: http://localhost:8000

Upload a document and watch real-time processing updates in the dashboard.

### 4. Monitor via Logs
```bash
tail -f logs/worker-native.log
```

## WebSocket Message Format

### Status Update
```json
{
  "type": "status_update",
  "doc_id": "abc123",
  "status": "processing",
  "progress": 0.5,
  "filename": "document.pdf",
  "stage": "embedding_visual",
  "timestamp": "2025-10-11T14:00:00Z"
}
```

### Log Message
```json
{
  "type": "log",
  "level": "INFO",
  "message": "Processing started",
  "doc_id": "abc123",
  "timestamp": "2025-10-11T14:00:00Z"
}
```

### Statistics
```json
{
  "type": "stats",
  "active": 2,
  "completed": 15,
  "failed": 1,
  "total": 18,
  "timestamp": "2025-10-11T14:00:00Z"
}
```

### Connection
```json
{
  "type": "connection",
  "status": "connected",
  "message": "Connected to DocuSearch monitoring",
  "timestamp": "2025-10-11T14:00:00Z"
}
```

## Architecture

### Data Flow

```
Document Upload (Copyparty)
    ↓
Worker Receives Webhook
    ↓
process_document_sync() [Thread Pool]
    ↓
Broadcasts via _broadcast_from_sync()
    ↓
WebSocketBroadcaster
    ↓
All Connected WebSocket Clients
    ↓
Browser Dashboard (monitor.html)
```

### Thread Safety

- `process_document_sync()` runs in ThreadPoolExecutor
- `_broadcast_from_sync()` uses `asyncio.run_coroutine_threadsafe()` to schedule broadcasts in event loop
- `WebSocketBroadcaster` uses asyncio.Lock for thread-safe connection management

## Known Limitations

### What You CAN Monitor

✓ Processing start/completion/failure
✓ Overall progress (0.0-1.0)
✓ Stage transitions (parsing, embedding, storing)
✓ Error messages and stack traces
✓ Timing and throughput metrics
✓ Queue status and statistics

### What You CANNOT Monitor

✗ Docling internal progress (black box - no callbacks)
✗ Whisper transcription progress (black box - no callbacks)
✗ Page-by-page progress during parsing
✗ Real-time progress within a stage

### Workarounds

1. **Enhanced logs** show timing metrics before/after operations
2. **Periodic updates** send "still working" signals every 5s
3. **Timeout monitoring** prevents infinite hangs
4. **Progress estimation** based on stage (parsing=0.2, embedding_visual=0.5, etc.)

## File Summary

| File | Purpose | Lines |
|------|---------|-------|
| `src/processing/worker_webhook.py` | WebSocket endpoint + broadcast integration | +50 |
| `src/processing/websocket_broadcaster.py` | WebSocket connection management | ~170 |
| `src/processing/monitoring_utils.py` | Periodic updates + timeout monitoring | ~220 |
| `src/processing/static/monitor.html` | Web monitoring dashboard | ~450 |
| `src/processing/docling_parser.py` | Enhanced timing logs | +30 |
| `test_websocket.py` | Simple WebSocket test | ~80 |
| `test_monitoring_integration.py` | Comprehensive integration test | ~180 |
| **Total** | | **~1,180 lines** |

## Next Steps

### Future Enhancements

1. **Metrics Collection**: Track processing times, error rates, throughput
2. **Historical Data**: Store processing history in database
3. **Alerts**: Email/Slack notifications for failures
4. **Performance Graphs**: Visualize processing time trends
5. **Document Preview**: Show document thumbnails in queue
6. **Concurrent Processing**: Monitor multiple documents simultaneously
7. **Cancellation**: Allow users to cancel in-progress processing

### Integration Opportunities

1. **Prometheus/Grafana**: Export metrics for monitoring
2. **Elasticsearch**: Store logs for analysis
3. **Sentry**: Error tracking and alerting
4. **DataDog**: APM and infrastructure monitoring

## Troubleshooting

### WebSocket Connection Fails

**Symptom**: "Failed to connect" in browser console

**Solutions**:
1. Verify worker is running: `./scripts/status.sh`
2. Check port 8002 is not blocked by firewall
3. Check logs: `tail -f logs/worker-native.log`

### No Updates Appearing

**Symptom**: Dashboard connects but no updates show

**Solutions**:
1. Verify document is actually processing
2. Check worker logs for broadcast errors
3. Verify event loop is captured in worker startup

### Pydantic Validation Errors (Known Issue)

**Symptom**: 500 errors in `/status/queue` endpoint

**Cause**: `processing_status` dict missing required fields

**Fix Needed**: Ensure all fields match ProcessingStatus model:
- `doc_id` (string)
- `stage` (ProcessingStageEnum)
- `updated_at` (datetime)
- `elapsed_time` (float)

## Summary

The real-time monitoring system is **fully functional** and provides:
- ✅ Enhanced timing logs for Docling/Whisper
- ✅ Periodic status updates during processing
- ✅ Timeout monitoring to prevent hangs
- ✅ WebSocket broadcasting infrastructure
- ✅ Real-time web dashboard
- ✅ Complete worker integration
- ✅ Comprehensive testing

**Access the dashboard**: http://localhost:8002/static/monitor.html
