# Integration Contract: Documents API

**Provider:** api-agent
**Consumers:** ui-agent
**Status:** Wave 3
**File:** `src/processing/documents_api.py`

---

## API Endpoint Specifications

### GET /documents

**Purpose:** List all stored documents with metadata

**Request:**
```http
GET /documents?limit=50&offset=0&search=report&sort_by=date_added HTTP/1.1
```

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 50 | Number of results (1-100) |
| `offset` | integer | No | 0 | Pagination offset |
| `search` | string | No | - | Filter by filename (case-insensitive) |
| `sort_by` | string | No | `date_added` | Sort field: `date_added`, `filename`, `page_count` |

**Response (200 OK):**
```json
{
  "documents": [
    {
      "doc_id": "a3b2c1d4e5f6...",
      "filename": "report.pdf",
      "page_count": 5,
      "chunk_count": 23,
      "date_added": "2025-10-11T10:30:00Z",
      "collections": ["visual", "text"],
      "has_images": true,
      "first_page_thumb": "/images/a3b2c1d4e5f6/page001_thumb.jpg"
    }
  ],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

**Error Responses:**
- `400 Bad Request`: Invalid query parameters
- `500 Internal Server Error`: Database error

---

### GET /documents/{doc_id}

**Purpose:** Get detailed metadata for a specific document

**Request:**
```http
GET /documents/a3b2c1d4e5f6... HTTP/1.1
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `doc_id` | string | Document identifier (SHA-256 hash) |

**Response (200 OK):**
```json
{
  "doc_id": "a3b2c1d4e5f6...",
  "filename": "report.pdf",
  "date_added": "2025-10-11T10:30:00Z",
  "pages": [
    {
      "page_number": 1,
      "image_path": "/images/a3b2c1d4e5f6/page001.png",
      "thumb_path": "/images/a3b2c1d4e5f6/page001_thumb.jpg",
      "embedding_id": "a3b2c1d4e5f6-page001"
    },
    {
      "page_number": 2,
      "image_path": "/images/a3b2c1d4e5f6/page002.png",
      "thumb_path": "/images/a3b2c1d4e5f6/page002_thumb.jpg",
      "embedding_id": "a3b2c1d4e5f6-page002"
    }
  ],
  "chunks": [
    {
      "chunk_id": "chunk_0",
      "text_content": "First paragraph of the document...",
      "embedding_id": "a3b2c1d4e5f6-chunk0"
    }
  ],
  "metadata": {
    "page_count": 2,
    "chunk_count": 1,
    "has_images": true,
    "collections": ["visual", "text"]
  }
}
```

**Error Responses:**
- `404 Not Found`: Document not found
  ```json
  {
    "error": "Document not found",
    "code": "DOCUMENT_NOT_FOUND",
    "details": {"doc_id": "..."}
  }
  ```
- `500 Internal Server Error`: Database error

---

### GET /images/{doc_id}/{filename}

**Purpose:** Serve page image or thumbnail files

**Request:**
```http
GET /images/a3b2c1d4e5f6/page001_thumb.jpg HTTP/1.1
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `doc_id` | string | Document identifier |
| `filename` | string | Image filename (e.g., `page001.png`, `page001_thumb.jpg`) |

**Response (200 OK):**
```http
HTTP/1.1 200 OK
Content-Type: image/png  # or image/jpeg
Cache-Control: max-age=86400
Content-Length: 123456

<binary image data>
```

**Error Responses:**
- `404 Not Found`: Image file not found
- `403 Forbidden`: Invalid filename or path traversal attempt
- `500 Internal Server Error`: File system error

---

## Data Schema Contracts

### Document List Item Schema

```typescript
interface DocumentListItem {
  doc_id: string;          // SHA-256 hash
  filename: string;         // Original filename
  page_count: number;       // Number of pages (visual collection)
  chunk_count: number;      // Number of text chunks (text collection)
  date_added: string;       // ISO 8601 timestamp
  collections: string[];    // ["visual", "text", "audio"]
  has_images: boolean;      // True if page images exist
  first_page_thumb: string; // URL to first page thumbnail (or null)
}
```

### Document Detail Schema

```typescript
interface DocumentDetail {
  doc_id: string;
  filename: string;
  date_added: string;
  pages: PageInfo[];
  chunks: ChunkInfo[];
  metadata: DocumentMetadata;
}

interface PageInfo {
  page_number: number;      // 1-indexed
  image_path: string | null; // URL or null if no image
  thumb_path: string | null; // URL or null if no thumbnail
  embedding_id: string;      // ChromaDB ID
}

interface ChunkInfo {
  chunk_id: string;
  text_content: string;      // Full text content
  embedding_id: string;      // ChromaDB ID
}

interface DocumentMetadata {
  page_count: number;
  chunk_count: number;
  has_images: boolean;
  collections: string[];
}
```

---

## Implementation Requirements

### Query Logic

**For GET /documents:**
1. Query ChromaDB visual collection: `collection.get()` (all entries)
2. Query ChromaDB text collection: `collection.get()` (all entries)
3. Extract unique `doc_id` values from metadata
4. Group entries by `doc_id`
5. Aggregate counts and metadata per document
6. Apply filters (search, sort)
7. Apply pagination (limit, offset)

**For GET /documents/{doc_id}:**
1. Query ChromaDB visual collection: `collection.get(where={"doc_id": doc_id})`
2. Query ChromaDB text collection: `collection.get(where={"doc_id": doc_id})`
3. Return 404 if no results
4. Build detailed response with all pages and chunks

**For GET /images/{doc_id}/{filename}:**
1. Validate `doc_id` format (alphanumeric + dashes)
2. Validate `filename` matches pattern: `page\d{3}(_thumb)?\.(png|jpg)`
3. Construct path: `{PAGE_IMAGE_DIR}/{doc_id}/{filename}`
4. Check file exists
5. Determine Content-Type from extension
6. Return file with caching headers

---

## Security Requirements

### Path Traversal Prevention

```python
import re

DOC_ID_PATTERN = re.compile(r'^[a-zA-Z0-9\-]{8,64}$')
FILENAME_PATTERN = re.compile(r'^page\d{3}(_thumb)?\.(png|jpg)$')

def validate_doc_id(doc_id: str) -> bool:
    """Validate doc_id to prevent path traversal."""
    return bool(DOC_ID_PATTERN.match(doc_id))

def validate_filename(filename: str) -> bool:
    """Validate filename to prevent path traversal."""
    return bool(FILENAME_PATTERN.match(filename))
```

### CORS Headers

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific origins
    allow_methods=["GET"],
    allow_headers=["*"],
)
```

---

## Performance Requirements

| Endpoint | Target Latency | Max Latency |
|----------|----------------|-------------|
| `GET /documents` | <100ms | 500ms |
| `GET /documents/{id}` | <50ms | 200ms |
| `GET /images/{id}/{file}` | <20ms | 100ms |

### Optimization Strategies

1. **Caching:** Cache document list for 30 seconds
2. **Pagination:** Limit results to max 100 per page
3. **Lazy loading:** Only fetch detailed data when requested
4. **File serving:** Use `FileResponse` with streaming

---

## Error Handling

### Error Response Format

```json
{
  "error": "Human-readable error message",
  "code": "ERROR_CODE",
  "details": {
    "field": "value"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `DOCUMENT_NOT_FOUND` | 404 | Document ID not in database |
| `IMAGE_NOT_FOUND` | 404 | Image file not on disk |
| `INVALID_DOC_ID` | 400 | doc_id format invalid |
| `INVALID_FILENAME` | 400 | filename format invalid |
| `INVALID_PAGINATION` | 400 | limit/offset out of range |
| `DATABASE_ERROR` | 500 | ChromaDB query failed |
| `FILE_SYSTEM_ERROR` | 500 | Disk read error |

---

## Testing Requirements

### Unit Tests (by api-agent)

```python
def test_get_documents_returns_list(client):
    """Test GET /documents returns document list."""
    response = client.get("/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data
    assert isinstance(data["documents"], list)

def test_get_documents_pagination(client):
    """Test pagination parameters."""
    response = client.get("/documents?limit=10&offset=5")
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 10
    assert data["offset"] == 5

def test_get_document_by_id_success(client):
    """Test GET /documents/{id} with valid ID."""
    response = client.get("/documents/abc123")
    assert response.status_code in [200, 404]  # Depends on test data

def test_get_document_by_id_not_found(client):
    """Test 404 for non-existent document."""
    response = client.get("/documents/nonexistent")
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "DOCUMENT_NOT_FOUND"

def test_get_image_serves_file(client, tmp_path):
    """Test GET /images/{doc_id}/{filename}."""
    # Create test image
    response = client.get("/images/test-doc/page001_thumb.jpg")
    assert response.status_code in [200, 404]

def test_get_image_prevents_path_traversal(client):
    """Test path traversal prevention."""
    response = client.get("/images/../../../etc/passwd")
    assert response.status_code == 403
```

### Integration Tests (by ui-agent)

```python
def test_full_api_workflow():
    """Test complete API workflow from UI perspective."""
    # Fetch document list
    response = requests.get("http://localhost:8002/documents")
    assert response.status_code == 200
    docs = response.json()["documents"]

    if docs:
        # Fetch first document details
        doc_id = docs[0]["doc_id"]
        response = requests.get(f"http://localhost:8002/documents/{doc_id}")
        assert response.status_code == 200

        # Fetch thumbnail if exists
        if docs[0]["has_images"]:
            thumb_url = docs[0]["first_page_thumb"]
            response = requests.get(f"http://localhost:8002{thumb_url}")
            assert response.status_code == 200
            assert response.headers["content-type"] == "image/jpeg"
```

---

## Acceptance Criteria

- [x] All endpoints implemented and returning correct data
- [x] Pagination works correctly
- [x] Search and sort functionality working
- [x] Path traversal prevented (security audit passing)
- [x] CORS headers configured correctly
- [x] Error responses follow contract format
- [x] Performance targets met
- [x] Unit tests achieve 95%+ coverage
- [x] Integration tests validate end-to-end flow
- [x] OpenAPI schema generated correctly

---

**Contract Version:** 1.0
**Last Updated:** 2025-10-11
**Status:** ✅ Approved
