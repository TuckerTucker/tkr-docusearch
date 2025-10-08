# Status API Contract

**Provider**: api-endpoints-agent
**Consumers**: monitoring-logic-agent, upload-logic-agent
**Wave**: 1
**Status**: Specification

## Overview

The Status API provides HTTP endpoints for querying document processing status and queue information. This contract defines the exact request/response formats that consumers can depend on.

## Endpoints

### 1. GET /status/{doc_id}

Retrieves the current processing status for a specific document.

**Request**:
```http
GET /status/{doc_id}
Host: localhost:8002
Accept: application/json
```

**Path Parameters**:
- `doc_id` (string, required): Unique document identifier (SHA-256 hash)

**Success Response** (200 OK):
```json
{
  "doc_id": "abc123...",
  "filename": "report.pdf",
  "status": "embedding_visual",
  "progress": 0.65,
  "stage": "visual_embeddings",
  "page": 13,
  "total_pages": 20,
  "elapsed_time": 45.2,
  "estimated_remaining": 25.1,
  "timestamp": "2025-10-07T19:30:00Z",
  "metadata": {
    "format": "pdf",
    "format_type": "visual",
    "file_size": 2458624
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "error": "Document not found",
  "doc_id": "abc123..."
}
```

**Field Specifications**:
- `status`: One of `["queued", "parsing", "embedding_visual", "embedding_text", "storing", "completed", "failed"]`
- `progress`: Float 0.0-1.0 representing completion percentage
- `stage`: Human-readable current stage
- `page`: Current page being processed (null if not applicable)
- `total_pages`: Total pages in document (null if not applicable)
- `elapsed_time`: Seconds since processing started
- `estimated_remaining`: Estimated seconds remaining (null if unavailable)
- `timestamp`: ISO 8601 timestamp of last status update

---

### 2. GET /status/queue

Retrieves all documents currently being processed or queued.

**Request**:
```http
GET /status/queue
Host: localhost:8002
Accept: application/json
```

**Query Parameters** (optional):
- `status`: Filter by status (e.g., `?status=embedding_visual`)
- `limit`: Max results to return (default: 100)

**Success Response** (200 OK):
```json
{
  "queue": [
    {
      "doc_id": "abc123...",
      "filename": "report.pdf",
      "status": "embedding_visual",
      "progress": 0.65,
      "elapsed_time": 45.2,
      "timestamp": "2025-10-07T19:30:00Z"
    },
    {
      "doc_id": "def456...",
      "filename": "notes.md",
      "status": "completed",
      "progress": 1.0,
      "elapsed_time": 12.5,
      "timestamp": "2025-10-07T19:25:00Z"
    }
  ],
  "total": 2,
  "active": 1,
  "completed": 1,
  "failed": 0
}
```

**Field Specifications**:
- `queue`: Array of status objects (simplified, without full metadata)
- `total`: Total documents in response
- `active`: Count of documents with status != completed/failed
- `completed`: Count of completed documents
- `failed`: Count of failed documents

---

### 3. POST /webhook (Modified)

**MODIFICATION REQUIRED**: Existing webhook endpoint must return `doc_id` in response.

**Request** (from Copyparty):
```http
POST /webhook
Content-Type: application/json

{
  "event": "upload",
  "path": "/uploads/report.pdf",
  "filename": "report.pdf"
}
```

**Success Response** (200 OK):
```json
{
  "status": "accepted",
  "doc_id": "abc123...",
  "filename": "report.pdf",
  "message": "Document queued for processing"
}
```

**Error Response** (400 Bad Request):
```json
{
  "status": "rejected",
  "error": "Unsupported format",
  "filename": "document.exe"
}
```

**NEW FIELD**:
- `doc_id`: Must be included in response so upload client can start monitoring

---

## CORS Configuration

All endpoints must support CORS headers for browser access:

```http
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

---

## Performance Requirements

- **GET /status/{doc_id}**: < 50ms response time
- **GET /status/queue**: < 100ms response time (for up to 100 items)
- **POST /webhook**: < 100ms response time

---

## Error Handling

All endpoints must return consistent error format:

```json
{
  "error": "Human-readable error message",
  "code": "ERROR_CODE",
  "details": {
    "additional": "context"
  }
}
```

**Standard Error Codes**:
- `DOCUMENT_NOT_FOUND`: doc_id doesn't exist
- `INVALID_REQUEST`: Malformed request
- `SERVER_ERROR`: Internal processing error

---

## Acceptance Tests

```python
# Test 1: Individual status retrieval
response = requests.get("http://localhost:8002/status/abc123")
assert response.status_code == 200
assert response.json()["doc_id"] == "abc123"
assert "progress" in response.json()
assert 0.0 <= response.json()["progress"] <= 1.0

# Test 2: Queue retrieval
response = requests.get("http://localhost:8002/status/queue")
assert response.status_code == 200
assert isinstance(response.json()["queue"], list)
assert "total" in response.json()
assert "active" in response.json()

# Test 3: Webhook returns doc_id
response = requests.post(
    "http://localhost:8002/webhook",
    json={"event": "upload", "path": "/uploads/test.pdf", "filename": "test.pdf"}
)
assert response.status_code == 200
assert "doc_id" in response.json()
assert response.json()["status"] == "accepted"

# Test 4: 404 for missing document
response = requests.get("http://localhost:8002/status/nonexistent")
assert response.status_code == 404
assert "error" in response.json()

# Test 5: CORS headers present
response = requests.options("http://localhost:8002/status/queue")
assert "Access-Control-Allow-Origin" in response.headers
```

---

## Integration Points

**Depends on**:
- `status-persistence-agent`: StatusManager class for accessing `processing_status` dict

**Provides to**:
- `monitoring-logic-agent`: Polling endpoints for progress tracking
- `upload-logic-agent`: doc_id from webhook for monitoring handoff

---

## Implementation Notes

- All timestamps must be UTC in ISO 8601 format
- `doc_id` is always a SHA-256 hash (64 hex characters)
- Status updates must be atomic (no partial updates)
- Queue endpoint should return most recent first (sorted by timestamp desc)
- Completed/failed documents should remain in status for 1 hour before cleanup
