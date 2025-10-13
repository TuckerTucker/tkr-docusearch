# Documents API Integration Contract

**Provider**: Worker Documents API (`GET /documents`, `GET /documents/{doc_id}`)
**Consumer**: `api-client.js` (Agent 2)
**Status**: Existing API (already implemented in `documents_api.py`)

---

## Base URL

```
http://localhost:8002
```

---

## Endpoint 1: List Documents

### **Request**

```http
GET /documents?limit={int}&offset={int}&search={string}&sort_by={field}
```

**Query Parameters**:

| Parameter | Type   | Required | Default      | Description                          |
|-----------|--------|----------|--------------|--------------------------------------|
| `limit`   | int    | No       | 50           | Results per page (1-100)             |
| `offset`  | int    | No       | 0            | Pagination offset                    |
| `search`  | string | No       | null         | Filter by filename (case-insensitive)|
| `sort_by` | string | No       | `date_added` | Sort field                           |

**Valid `sort_by` Values**:
- `date_added` - Sort by upload date (newest first)
- `filename` - Sort alphabetically (A-Z)
- `page_count` - Sort by number of pages (most first)

---

### **Response**

**Status**: `200 OK`
**Content-Type**: `application/json`

```json
{
  "documents": [
    {
      "doc_id": "abc123def456789...",
      "filename": "quarterly-report.pdf",
      "page_count": 24,
      "chunk_count": 48,
      "date_added": "2025-10-12T14:23:00.123456",
      "collections": ["visual", "text"],
      "has_images": true,
      "first_page_thumb": "/images/abc123def456/page001_thumb.jpg"
    },
    {
      "doc_id": "def789abc123456...",
      "filename": "presentation.pptx",
      "page_count": 12,
      "chunk_count": 24,
      "date_added": "2025-10-11T09:15:30.654321",
      "collections": ["visual", "text"],
      "has_images": true,
      "first_page_thumb": "/images/def789abc123/page001_thumb.jpg"
    }
  ],
  "total": 156,
  "limit": 50,
  "offset": 0
}
```

**Response Schema**:

| Field            | Type     | Description                               |
|------------------|----------|-------------------------------------------|
| `documents`      | array    | List of document objects                  |
| `total`          | int      | Total documents matching filter           |
| `limit`          | int      | Requested limit                           |
| `offset`         | int      | Requested offset                          |

**Document Object**:

| Field              | Type     | Description                               |
|--------------------|----------|-------------------------------------------|
| `doc_id`           | string   | SHA-256 hash (64 hex chars)               |
| `filename`         | string   | Original filename with extension          |
| `page_count`       | int      | Number of pages/images                    |
| `chunk_count`      | int      | Number of text chunks                     |
| `date_added`       | string   | ISO 8601 timestamp                        |
| `collections`      | array    | Collections: `["visual"]`, `["text"]`, or both |
| `has_images`       | boolean  | True if page images exist                 |
| `first_page_thumb` | string\|null | URL to first page thumbnail, or null |

---

### **Error Responses**

**Database Error**:
```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "error": "Failed to retrieve documents",
  "code": "DATABASE_ERROR",
  "details": {
    "message": "Connection to ChromaDB failed"
  }
}
```

---

### **Example Requests**

**Get first page (default)**:
```http
GET /documents
```

**Get second page**:
```http
GET /documents?limit=50&offset=50
```

**Search for "report"**:
```http
GET /documents?search=report
```

**Sort by filename**:
```http
GET /documents?sort_by=filename
```

**Combined query**:
```http
GET /documents?search=quarterly&sort_by=date_added&limit=20&offset=0
```

---

## Endpoint 2: Get Document Details

### **Request**

```http
GET /documents/{doc_id}
```

**Path Parameters**:

| Parameter | Type   | Required | Description                    |
|-----------|--------|----------|--------------------------------|
| `doc_id`  | string | Yes      | Document SHA-256 hash          |

**Validation**:
- Must match pattern: `^[a-zA-Z0-9\-]{8,64}$`
- Invalid format → 400 Bad Request

---

### **Response**

**Status**: `200 OK`
**Content-Type**: `application/json`

```json
{
  "doc_id": "abc123def456789...",
  "filename": "quarterly-report.pdf",
  "date_added": "2025-10-12T14:23:00.123456",
  "pages": [
    {
      "page_number": 1,
      "image_path": "/images/abc123def456/page001.png",
      "thumb_path": "/images/abc123def456/page001_thumb.jpg",
      "embedding_id": "visual_abc123_page1"
    },
    {
      "page_number": 2,
      "image_path": "/images/abc123def456/page002.png",
      "thumb_path": "/images/abc123def456/page002_thumb.jpg",
      "embedding_id": "visual_abc123_page2"
    }
  ],
  "chunks": [
    {
      "chunk_id": "chunk_0",
      "text_content": "Executive Summary\n\nThis quarter showed...",
      "embedding_id": "text_abc123_chunk0"
    },
    {
      "chunk_id": "chunk_1",
      "text_content": "Revenue increased by 23% compared to...",
      "embedding_id": "text_abc123_chunk1"
    }
  ],
  "metadata": {
    "page_count": 24,
    "chunk_count": 48,
    "has_images": true,
    "collections": ["visual", "text"],
    "raw_metadata": {
      "doc_id": "abc123def456789...",
      "filename": "quarterly-report.pdf",
      "timestamp": "2025-10-12T14:23:00.123456",
      "format": "pdf",
      "file_size": 2456789
    }
  }
}
```

**Response Schema**:

| Field       | Type   | Description                          |
|-------------|--------|--------------------------------------|
| `doc_id`    | string | Document identifier                  |
| `filename`  | string | Original filename                    |
| `date_added`| string | ISO 8601 timestamp                   |
| `pages`     | array  | List of page objects                 |
| `chunks`    | array  | List of text chunk objects           |
| `metadata`  | object | Document metadata                    |

**Page Object**:

| Field          | Type         | Description                     |
|----------------|--------------|---------------------------------|
| `page_number`  | int          | Page number (1-indexed)         |
| `image_path`   | string\|null | URL to full-resolution image    |
| `thumb_path`   | string\|null | URL to thumbnail                |
| `embedding_id` | string       | ChromaDB embedding ID           |

**Chunk Object**:

| Field          | Type   | Description                     |
|----------------|--------|---------------------------------|
| `chunk_id`     | string | Chunk identifier                |
| `text_content` | string | Full text content               |
| `embedding_id` | string | ChromaDB embedding ID           |

**Metadata Object**:

| Field          | Type    | Description                    |
|----------------|---------|--------------------------------|
| `page_count`   | int     | Total pages                    |
| `chunk_count`  | int     | Total chunks                   |
| `has_images`   | boolean | True if images exist           |
| `collections`  | array   | Collections containing doc     |
| `raw_metadata` | object  | Raw ChromaDB metadata          |

---

### **Error Responses**

**Invalid doc_id**:
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "Invalid document ID format",
  "code": "INVALID_DOC_ID",
  "details": {
    "doc_id": "invalid-id"
  }
}
```

**Document not found**:
```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "error": "Document not found",
  "code": "DOCUMENT_NOT_FOUND",
  "details": {
    "doc_id": "abc123def456..."
  }
}
```

**Database error**:
```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "error": "Failed to retrieve document",
  "code": "DATABASE_ERROR",
  "details": {
    "message": "Connection error"
  }
}
```

---

## Endpoint 3: Serve Images

### **Request**

```http
GET /images/{doc_id}/{filename}
```

**Path Parameters**:

| Parameter  | Type   | Required | Description                    |
|------------|--------|----------|--------------------------------|
| `doc_id`   | string | Yes      | Document SHA-256 hash          |
| `filename` | string | Yes      | Image filename                 |

**Valid Filename Patterns**:
- `page001.png`, `page002.png`, ... (full-resolution)
- `page001_thumb.jpg`, `page002_thumb.jpg`, ... (thumbnails)
- `cover.jpg`, `cover.jpeg`, `cover.png` (audio album art)

**Validation**:
- `doc_id`: Must match `^[a-zA-Z0-9\-]{8,64}$`
- `filename`: Must match `^(page\d{3}(_thumb\.jpg|\.png)|cover\.(jpg|jpeg|png))$`

---

### **Response**

**Status**: `200 OK`
**Content-Type**: `image/png` or `image/jpeg`
**Headers**:
- `Cache-Control: max-age=86400` (24 hours)

**Body**: Binary image data

---

### **Error Responses**

**Invalid doc_id or filename**:
```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "error": "Invalid document ID format",
  "code": "INVALID_DOC_ID",
  "details": {
    "doc_id": "../../etc/passwd"
  }
}
```

**Image not found**:
```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "error": "Image file not found",
  "code": "IMAGE_NOT_FOUND",
  "details": {
    "doc_id": "abc123",
    "filename": "page999.png"
  }
}
```

---

## Client Implementation Requirements

### **API Client Class**

```javascript
class DocumentsAPIClient {
  constructor(baseUrl = 'http://localhost:8002') {
    this.baseUrl = baseUrl;
  }

  /**
   * List documents with filtering and pagination
   * @param {Object} options
   * @param {number} options.limit - Results per page (1-100)
   * @param {number} options.offset - Pagination offset
   * @param {string} options.search - Filename filter
   * @param {string} options.sort_by - Sort field
   * @returns {Promise<Object>} Response with documents array
   */
  async listDocuments({ limit = 50, offset = 0, search = null, sort_by = 'date_added' }) {
    // Build query string
    // Fetch and return response
  }

  /**
   * Get detailed document information
   * @param {string} docId - Document ID
   * @returns {Promise<Object>} Document details
   */
  async getDocument(docId) {
    // Validate docId format
    // Fetch and return response
  }

  /**
   * Get image URL
   * @param {string} docId - Document ID
   * @param {string} filename - Image filename
   * @returns {string} Full image URL
   */
  getImageUrl(docId, filename) {
    return `${this.baseUrl}/images/${docId}/${filename}`;
  }
}
```

---

## Testing Requirements

### **Provider Validation** (Worker)
- [x] Endpoint exists at `/documents`
- [x] Returns paginated results
- [x] Supports search filtering
- [x] Supports sorting (date_added, filename, page_count)
- [x] Returns valid JSON schema
- [x] Handles errors gracefully

### **Consumer Validation** (Client)
- [ ] Can query `/documents` with all parameters
- [ ] Parses response correctly
- [ ] Handles pagination
- [ ] Handles empty results
- [ ] Handles error responses
- [ ] Validates doc_id format before requests

---

## Example Full Flow

```javascript
// Initialize client
const api = new DocumentsAPIClient();

// Get first page of documents
const page1 = await api.listDocuments({ limit: 50, offset: 0 });
console.log(page1.documents); // Array of 50 documents
console.log(page1.total);     // Total count (e.g., 156)

// Search for "report"
const results = await api.listDocuments({ search: 'report', sort_by: 'date_added' });

// Get document details
const doc = await api.getDocument(results.documents[0].doc_id);
console.log(doc.pages);  // Array of page objects
console.log(doc.chunks); // Array of text chunks

// Get thumbnail URL
const thumbUrl = api.getImageUrl(doc.doc_id, doc.pages[0].thumb_path);
// Returns: "http://localhost:8002/images/abc123.../page001_thumb.jpg"
```

---

## Change Log

- 2025-10-13: Initial contract based on existing implementation
- Status: **STABLE** (existing API, no changes planned)
