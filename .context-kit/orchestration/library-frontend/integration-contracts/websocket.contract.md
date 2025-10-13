# WebSocket Integration Contract

**Provider**: Worker WebSocket endpoint (`ws://localhost:8002/ws`)
**Consumer**: `websocket-client.js` (Agent 2)
**Status**: Existing API (already implemented)

---

## Connection Protocol

### **Endpoint**
```
ws://localhost:8002/ws
```

### **Connection Lifecycle**

1. **Client Connects**
   ```javascript
   const ws = new WebSocket('ws://localhost:8002/ws');
   ```

2. **Server Accepts & Sends Welcome**
   ```json
   {
     "type": "connection",
     "status": "connected",
     "message": "Connected to DocuSearch monitoring",
     "timestamp": "2025-10-13T12:34:56.789Z"
   }
   ```

3. **Connection Maintained**
   - Client must handle incoming messages
   - No explicit ping/pong required (handled by browser)

4. **Disconnection**
   - Client detects via `ws.onclose` event
   - Client implements reconnection logic

---

## Message Types

All messages are JSON objects with a `type` field.

### **1. Connection Acknowledgment**

**Sent**: On initial connection
**Direction**: Server → Client

```json
{
  "type": "connection",
  "status": "connected",
  "message": "Connected to DocuSearch monitoring",
  "timestamp": "2025-10-13T12:34:56.789Z"
}
```

**Fields**:
- `type`: Always `"connection"`
- `status`: Always `"connected"`
- `message`: Human-readable welcome message
- `timestamp`: ISO 8601 UTC timestamp

---

### **2. Status Update**

**Sent**: During document processing (multiple times per document)
**Direction**: Server → Client

```json
{
  "type": "status_update",
  "doc_id": "abc123def456...",
  "status": "processing",
  "progress": 0.45,
  "filename": "quarterly-report.pdf",
  "stage": "Embedding images",
  "visual_embeddings": 12,
  "text_embeddings": 24,
  "timestamp": "2025-10-13T12:35:00.123Z"
}
```

**Required Fields**:
- `type`: Always `"status_update"`
- `doc_id`: Document SHA-256 hash (64 hex chars)
- `status`: One of: `"queued"`, `"processing"`, `"completed"`, `"failed"`
- `progress`: Float 0.0-1.0
- `filename`: Original filename

**Optional Fields**:
- `stage`: Current processing stage (string)
- `visual_embeddings`: Count of visual embeddings (on completion)
- `text_embeddings`: Count of text embeddings (on completion)
- `error`: Error message (only if `status === "failed"`)
- `timestamp`: ISO 8601 UTC timestamp

**Status Values**:
- `"queued"`: Document accepted, not yet processing
- `"processing"`: Active processing (progress 0.0-0.99)
- `"completed"`: Successfully processed (progress 1.0)
- `"failed"`: Processing failed (error field present)

**Stage Values** (during processing):
- `"started"` (progress: 0.0)
- `"Parsing document"` (progress: 0.0-0.2)
- `"Embedding images"` (progress: 0.2-0.7)
- `"Embedding text"` (progress: 0.7-0.9)
- `"Storing vectors"` (progress: 0.9-1.0)
- `"completed"` (progress: 1.0)
- `"failed"` (progress: varies)

---

### **3. Log Message**

**Sent**: For significant events
**Direction**: Server → Client

```json
{
  "type": "log",
  "level": "INFO",
  "message": "Started processing: quarterly-report.pdf",
  "doc_id": "abc123def456...",
  "timestamp": "2025-10-13T12:35:00.000Z"
}
```

**Required Fields**:
- `type`: Always `"log"`
- `level`: One of: `"INFO"`, `"WARNING"`, `"ERROR"`
- `message`: Human-readable log message

**Optional Fields**:
- `doc_id`: Related document (if applicable)
- `timestamp`: ISO 8601 UTC timestamp

---

### **4. Processing Statistics**

**Sent**: Periodically (future enhancement)
**Direction**: Server → Client

```json
{
  "type": "stats",
  "processing_count": 2,
  "completed_count": 45,
  "failed_count": 1,
  "timestamp": "2025-10-13T12:35:00.000Z"
}
```

**Fields**:
- `type`: Always `"stats"`
- `processing_count`: Documents currently processing
- `completed_count`: Total completed documents
- `failed_count`: Total failed documents
- `timestamp`: ISO 8601 UTC timestamp

---

## Client Implementation Requirements

### **Required Capabilities**

1. **Connection Management**
   ```javascript
   class WebSocketClient {
     connect()           // Establish connection
     disconnect()        // Close connection
     reconnect()         // Reconnect with backoff
     isConnected()       // Check connection state
   }
   ```

2. **Message Handling**
   ```javascript
   on(messageType, callback)  // Register handler
   off(messageType, callback) // Unregister handler
   ```

3. **Error Handling**
   - Handle connection failures
   - Implement exponential backoff (1s, 2s, 4s, 8s, 16s, max 32s)
   - Emit connection state changes

4. **Event Emission**
   ```javascript
   // Must emit these events for LibraryManager
   'connected'          // Connection established
   'disconnected'       // Connection lost
   'reconnecting'       // Attempting reconnect
   'status_update'      // Document status changed
   'log'                // Log message received
   'stats'              // Statistics update
   ```

---

## Consumer Contract (LibraryManager)

**LibraryManager** must:

1. **Initialize WebSocket client**
   ```javascript
   this.ws = new WebSocketClient('ws://localhost:8002/ws');
   this.ws.on('status_update', this.handleStatusUpdate.bind(this));
   ```

2. **Handle status updates**
   ```javascript
   handleStatusUpdate(message) {
     const { doc_id, status, progress, stage, filename } = message;

     // Find or create card for this document
     let card = this.documentCards.get(doc_id);
     if (!card && status === 'processing') {
       // Create new loading card
       card = createDocumentCard({
         filename,
         thumbnailUrl: '',
         dateAdded: new Date(),
         detailsUrl: '#',
         state: 'processing',
         processingStatus: { stage, progress }
       });
       this.documentCards.set(doc_id, card);
       this.grid.appendChild(card);
     } else if (card) {
       // Update existing card
       updateCardState(card, { state: status, stage, progress });
     }
   }
   ```

3. **Handle connection state**
   ```javascript
   this.ws.on('connected', () => {
     this.updateConnectionStatus('connected');
   });
   this.ws.on('disconnected', () => {
     this.updateConnectionStatus('disconnected');
   });
   this.ws.on('reconnecting', () => {
     this.updateConnectionStatus('reconnecting');
   });
   ```

---

## Testing Requirements

### **Provider Validation** (Worker)
- [x] WebSocket endpoint exists at `/ws`
- [x] Sends connection acknowledgment on connect
- [x] Broadcasts status_update during processing
- [x] Broadcasts log messages
- [x] Handles client disconnections gracefully

### **Consumer Validation** (Client)
- [ ] Connects to `ws://localhost:8002/ws`
- [ ] Receives connection acknowledgment
- [ ] Parses status_update messages
- [ ] Emits events for LibraryManager
- [ ] Reconnects on disconnection
- [ ] Shows connection status in UI

---

## Error Scenarios

### **Connection Refused**
- Worker not running
- **Client Action**: Show "Disconnected" status, retry with backoff

### **Connection Dropped**
- Network interruption
- Worker restart
- **Client Action**: Detect via `onclose`, show "Reconnecting", attempt reconnect

### **Invalid Message**
- Malformed JSON
- Missing required fields
- **Client Action**: Log error, ignore message, continue processing

---

## Security Considerations

- WebSocket uses same-origin policy
- No authentication required (local development)
- Production: Consider WSS + auth tokens

---

## Example Full Message Flow

```
1. Client connects
   ← {"type": "connection", "status": "connected", ...}

2. User uploads document
   (Copyparty webhook triggers processing)

3. Processing starts
   ← {"type": "log", "level": "INFO", "message": "Started processing: report.pdf", ...}
   ← {"type": "status_update", "doc_id": "abc123", "status": "processing", "progress": 0.0, "stage": "started", ...}

4. Progress updates
   ← {"type": "status_update", "doc_id": "abc123", "status": "processing", "progress": 0.15, "stage": "Parsing document", ...}
   ← {"type": "status_update", "doc_id": "abc123", "status": "processing", "progress": 0.45, "stage": "Embedding images", ...}
   ← {"type": "status_update", "doc_id": "abc123", "status": "processing", "progress": 0.75, "stage": "Embedding text", ...}

5. Completion
   ← {"type": "status_update", "doc_id": "abc123", "status": "completed", "progress": 1.0, "stage": "completed", "visual_embeddings": 24, "text_embeddings": 48, ...}
   ← {"type": "log", "level": "INFO", "message": "Completed processing: report.pdf (visual: 24, text: 48)", ...}
```

---

## Change Log

- 2025-10-13: Initial contract based on existing implementation
- Status: **STABLE** (existing API, no changes planned)
