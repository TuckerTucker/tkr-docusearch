# WebSocket API Documentation

**Version:** 0.11.0
**Last Updated:** 2025-11-07

## Overview

The DocuSearch WebSocket API provides real-time bidirectional communication between the client and server for document processing updates. It enables:

- Real-time processing status updates
- Upload batch registration with duplicate detection
- Progress tracking during document processing
- Automatic reconnection with exponential backoff
- Cross-browser/tab synchronization

## Connection Details

**URL:** `ws://localhost:8002/ws` (configurable via environment)

**Protocol:** WebSocket (RFC 6455)

**Reconnection:** Automatic with exponential backoff (1s → 2s → 4s → 8s → max 30s)

**Max Reconnect Attempts:** 10

## WebSocket Manager

### Client Implementation

The frontend uses `WebSocketManager` class for connection management:

```javascript
import { WebSocketManager } from '../services/websocket.js';

const ws = new WebSocketManager('ws://localhost:8002/ws', {
  reconnectInterval: 3000,
  maxReconnectAttempts: 10,
  onMessage: (event) => handleMessage(event),
  onOpen: () => console.log('Connected'),
  onClose: () => console.log('Disconnected'),
  onError: (error) => console.error('Error:', error),
  onReconnectAttempt: (attempts) => console.log(`Reconnecting (${attempts})...`),
});

ws.connect();
```

### React Hook

The `useWebSocket` hook provides React integration:

```javascript
import { useWebSocket } from '../hooks/useWebSocket.js';

function MyComponent() {
  const { send, registerUploadBatch, isConnected, reconnectAttempts } = useWebSocket(
    'ws://localhost:8002/ws',
    {
      onMessage: handleMessage,
      reconnectInterval: 3000,
      maxReconnectAttempts: 10,
    }
  );

  const handleUpload = async (files) => {
    try {
      const registrations = await registerUploadBatch(files, false);
      console.log('Registered:', registrations);
    } catch (error) {
      console.error('Registration failed:', error);
    }
  };

  return (
    <div>
      <p>Connected: {isConnected ? 'Yes' : 'No'}</p>
      {reconnectAttempts > 0 && <p>Reconnecting... (attempt {reconnectAttempts})</p>}
    </div>
  );
}
```

## Message Format

All WebSocket messages use JSON format:

```json
{
  "type": "message_type",
  "data": { ... }
}
```

## Message Types

### Client → Server

#### 1. Register Upload Batch

Register multiple files for upload with duplicate detection.

```json
{
  "type": "register_upload_batch",
  "files": [
    {
      "filename": "document.pdf",
      "size": 1048576
    },
    {
      "filename": "presentation.pptx",
      "size": 2097152
    }
  ],
  "force_upload": false
}
```

**Parameters:**

- `files` (Array): List of file objects with `filename` and `size`
- `force_upload` (Boolean): If true, upload even if duplicates exist (default: false)

**Response:** See "Upload Batch Registered" below

#### 2. Ping (Keep-Alive)

```json
{
  "type": "ping"
}
```

**Response:**

```json
{
  "type": "pong"
}
```

### Server → Client

#### 1. Upload Batch Registered

Response to registration request with duplicate detection results.

```json
{
  "type": "upload_batch_registered",
  "registrations": [
    {
      "filename": "document.pdf",
      "doc_id": "abc123xyz789",
      "expected_size": 1048576,
      "is_duplicate": false
    },
    {
      "filename": "presentation.pptx",
      "doc_id": "def456uvw012",
      "expected_size": 2097152,
      "is_duplicate": true,
      "existing_doc": {
        "doc_id": "old789xyz456",
        "filename": "presentation.pptx",
        "upload_date": "2025-11-06T10:30:00Z",
        "file_type": "pptx",
        "status": "completed"
      }
    }
  ]
}
```

**Fields:**

- `registrations` (Array): Registration results for each file
  - `filename` (String): Original filename
  - `doc_id` (String): Generated document ID
  - `expected_size` (Number): Expected file size in bytes
  - `is_duplicate` (Boolean): Whether file already exists
  - `existing_doc` (Object, optional): Existing document metadata if duplicate

#### 2. Processing Update

Real-time updates during document processing.

```json
{
  "type": "processing_update",
  "doc_id": "abc123xyz789",
  "filename": "document.pdf",
  "status": "processing",
  "stage": "embedding",
  "progress": 0.65,
  "message": "Generating embeddings for page 13/20"
}
```

**Fields:**

- `doc_id` (String): Document ID
- `filename` (String): Document filename
- `status` (String): Processing status (`pending`, `processing`, `completed`, `failed`)
- `stage` (String): Current processing stage (`upload`, `parsing`, `chunking`, `embedding`, `storing`)
- `progress` (Number): Progress percentage (0.0 to 1.0)
- `message` (String, optional): Human-readable progress message

#### 3. Processing Complete

Sent when document processing completes successfully.

```json
{
  "type": "processing_complete",
  "doc_id": "abc123xyz789",
  "filename": "document.pdf",
  "chunks": 42,
  "pages": 20,
  "file_type": "pdf",
  "thumbnail_url": "http://localhost:8000/images/abc123xyz789_page_1.png"
}
```

**Fields:**

- `doc_id` (String): Document ID
- `filename` (String): Document filename
- `chunks` (Number): Number of chunks created
- `pages` (Number): Number of pages (visual documents only)
- `file_type` (String): File extension
- `thumbnail_url` (String, optional): Thumbnail URL for first page

#### 4. Processing Error

Sent when document processing fails.

```json
{
  "type": "processing_error",
  "doc_id": "abc123xyz789",
  "filename": "document.pdf",
  "stage": "parsing",
  "error": "Failed to parse PDF: Invalid PDF structure"
}
```

**Fields:**

- `doc_id` (String): Document ID
- `filename` (String): Document filename
- `stage` (String): Stage where error occurred
- `error` (String): Error message

#### 5. Error

General error message.

```json
{
  "type": "error",
  "message": "Invalid message format",
  "code": "INVALID_FORMAT"
}
```

**Fields:**

- `message` (String): Error description
- `code` (String, optional): Error code

## Connection States

The WebSocket connection has the following states:

1. **CONNECTING** (0): Connection is being established
2. **OPEN** (1): Connection is open and ready
3. **CLOSING** (2): Connection is closing
4. **CLOSED** (3): Connection is closed

## Event Handling

### Message Handlers

The WebSocketManager supports multiple message handlers for one-time requests:

```javascript
const ws = new WebSocketManager(url, options);

// Add temporary handler for specific response
const handleRegistration = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'upload_batch_registered') {
    console.log('Registered:', data.registrations);
    // Remove handler after receiving response
    ws.removeMessageHandler(handleRegistration);
  }
};

ws.addMessageHandler(handleRegistration);
ws.send({ type: 'register_upload_batch', files: [...] });
```

### Connection Events

```javascript
const ws = new WebSocketManager(url, {
  onOpen: () => {
    console.log('WebSocket connected');
    // Connection ready - can send messages
  },

  onClose: () => {
    console.log('WebSocket disconnected');
    // Connection closed - automatic reconnection will start
  },

  onError: (error) => {
    console.error('WebSocket error:', error);
    // Connection error occurred
  },

  onReconnectAttempt: (attempts) => {
    console.log(`Reconnecting... (attempt ${attempts})`);
    // Reconnection attempt in progress
  },
});
```

## Reconnection Logic

The WebSocket automatically reconnects on connection loss with exponential backoff:

1. **First attempt:** 1 second delay
2. **Second attempt:** 2 seconds delay
3. **Third attempt:** 4 seconds delay
4. **Fourth attempt:** 8 seconds delay
5. **Subsequent attempts:** 16s, 30s (capped at 30s)
6. **Max attempts:** 10 (configurable)

After max attempts, reconnection stops. User must refresh the page or manually reconnect.

## Error Handling

### Client-Side Errors

```javascript
// Registration timeout
try {
  const registrations = await registerUploadBatch(files);
} catch (error) {
  if (error.message === 'Registration request timeout') {
    // Request took longer than 10 seconds
    console.error('Registration timeout - try again');
  } else if (error.message === 'WebSocket not connected') {
    // Connection lost
    console.error('Connection lost - reconnecting...');
  }
}
```

### Server-Side Errors

```json
{
  "type": "error",
  "message": "File size exceeds limit (max 100MB)",
  "code": "FILE_TOO_LARGE"
}
```

**Common Error Codes:**

- `INVALID_FORMAT`: Malformed message
- `FILE_TOO_LARGE`: File exceeds size limit
- `UNSUPPORTED_TYPE`: Unsupported file type
- `DUPLICATE_FILE`: File already exists (when force_upload=false)
- `PROCESSING_FAILED`: Processing error

## Best Practices

### 1. Connection Management

```javascript
// Always disconnect on component unmount
useEffect(() => {
  const ws = new WebSocketManager(url, options);
  ws.connect();

  return () => {
    ws.disconnect(); // Prevents memory leaks
  };
}, []);
```

### 2. Message Validation

```javascript
const handleMessage = (event) => {
  try {
    const data = JSON.parse(event.data);

    // Validate message type
    if (!data.type) {
      console.warn('Message missing type field:', data);
      return;
    }

    // Handle message
    switch (data.type) {
      case 'processing_update':
        handleProcessingUpdate(data);
        break;
      // ...
    }
  } catch (error) {
    console.error('Failed to parse message:', error);
  }
};
```

### 3. Request Timeouts

```javascript
// Always use timeouts for request/response patterns
const registerWithTimeout = (files, timeout = 10000) => {
  return Promise.race([
    registerUploadBatch(files),
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Timeout')), timeout)
    ),
  ]);
};
```

### 4. State Synchronization

```javascript
// Use WebSocket updates to sync state
const handleMessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'processing_update') {
    // Update temp documents store
    updateTempDocument(data.doc_id, {
      status: data.status,
      stage: data.stage,
      progress: Math.round(data.progress * 100),
    });
  }
};
```

## Integration with React Query

WebSocket updates can invalidate React Query caches:

```javascript
import { useQueryClient } from '@tanstack/react-query';

const queryClient = useQueryClient();

const handleProcessingComplete = (data) => {
  // Invalidate documents list to fetch updated data
  queryClient.invalidateQueries({ queryKey: ['documents'] });

  // Remove from temp documents
  removeTempDocument(data.doc_id);
};
```

## Security Considerations

1. **Origin Validation:** Server validates WebSocket origin header
2. **Message Validation:** All messages validated before processing
3. **Rate Limiting:** Connection rate limiting to prevent abuse
4. **Timeout Protection:** Request timeouts prevent hanging connections
5. **Size Limits:** Message size limits enforced

## Performance Notes

- **Message Size:** Keep messages under 64KB for optimal performance
- **Polling Fallback:** Query active queue every 5 seconds as fallback
- **Batching:** Register multiple files in single batch to reduce round trips
- **Reconnection:** Exponential backoff prevents server overload during outages

## Debugging

Enable WebSocket logging:

```javascript
// Set debug flag in WebSocketManager
const ws = new WebSocketManager(url, {
  ...options,
  debug: true, // Logs all messages
});
```

Browser DevTools:

1. Open DevTools → Network tab
2. Click "WS" filter
3. Select WebSocket connection
4. View Messages tab for real-time message log

## Examples

### Complete Upload Flow

```javascript
import { useWebSocket } from '../hooks/useWebSocket.js';
import { useDocumentStore } from '../stores/useDocumentStore.js';

function UploadComponent() {
  const { registerUploadBatch, isConnected } = useWebSocket(
    'ws://localhost:8002/ws'
  );
  const addTempDocument = useDocumentStore(state => state.addTempDocument);
  const updateTempDocument = useDocumentStore(state => state.updateTempDocument);

  const handleUpload = async (files) => {
    if (!isConnected) {
      alert('WebSocket not connected');
      return;
    }

    try {
      // 1. Register files
      const registrations = await registerUploadBatch(files, false);

      // 2. Handle duplicates
      const duplicates = registrations.filter(r => r.is_duplicate);
      if (duplicates.length > 0 && !confirm('Upload duplicates?')) {
        return;
      }

      // 3. Add to temp documents
      registrations.forEach(reg => {
        addTempDocument(reg.doc_id, reg.filename);
      });

      // 4. Upload files (HTTP)
      for (const reg of registrations) {
        const file = files.find(f => f.name === reg.filename);
        await uploadFile(reg.doc_id, file);
      }
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  return <UploadButton onClick={() => handleUpload(files)} />;
}
```

## Related Documentation

- [API Reference](./API_REFERENCE.md) - HTTP API endpoints
- [Quick Start](./QUICK_START.md) - Getting started guide
- [Developer Guide](./DEVELOPER_GUIDE_BBOX.md) - Development setup

## Support

For issues or questions:
- GitHub: https://github.com/TuckerTucker/tkr-docusearch
- Documentation: See README.md
