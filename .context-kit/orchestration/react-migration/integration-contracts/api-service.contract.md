# API Service Integration Contract

**Provider:** infrastructure-agent
**Consumers:** library-agent, details-agent, research-agent
**File:** `frontend/src/services/api.js`

---

## Contract Overview

The API service provides a centralized interface for all HTTP requests to the Python backend. It wraps the existing REST API with consistent error handling, request/response formatting, and optional React Query integration.

---

## Base Configuration

```javascript
// Base API URL (proxy-aware)
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Default request timeout
const REQUEST_TIMEOUT = 30000; // 30 seconds

// Default headers
const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
};
```

---

## Documents API

### `api.documents.list(filters)`

**Purpose:** Fetch paginated list of documents with optional filters

**Parameters:**
```typescript
filters: {
  search?: string;           // Search query
  sort_by?: 'newest_first' | 'oldest_first' | 'name_asc' | 'name_desc';
  file_type_group?: string;  // 'all' | 'pdf' | 'audio' | 'office' | ...
  limit?: number;            // Page size (default: 50)
  offset?: number;           // Pagination offset (default: 0)
}
```

**Returns:**
```typescript
Promise<{
  documents: Array<{
    doc_id: string;
    filename: string;
    file_type: string;
    upload_date: string;
    num_pages?: number;
    thumbnail_url?: string;
    cover_art_url?: string;
    status: 'completed' | 'processing' | 'failed';
    error_message?: string;
  }>;
  total: number;
  limit: number;
  offset: number;
}>
```

**Endpoint:** `GET /api/documents`

---

### `api.documents.get(docId)`

**Purpose:** Fetch detailed metadata for a single document

**Parameters:**
```typescript
docId: string  // Document ID
```

**Returns:**
```typescript
Promise<{
  doc_id: string;
  filename: string;
  file_type: string;
  upload_date: string;
  num_pages?: number;
  thumbnail_url?: string;
  cover_art_url?: string;
  status: 'completed' | 'processing' | 'failed';
  error_message?: string;
  // Audio-specific fields
  audio_metadata?: {
    title?: string;
    artist?: string;
    album?: string;
    duration_seconds?: number;
  };
  // Document structure
  page_images?: string[];  // Array of page image URLs
  vtt_url?: string;        // VTT caption file URL (for audio)
}>
```

**Endpoint:** `GET /api/documents/:id`

---

### `api.documents.getMarkdown(docId)`

**Purpose:** Fetch extracted markdown content for a document

**Parameters:**
```typescript
docId: string  // Document ID
```

**Returns:**
```typescript
Promise<{
  sections: Array<{
    title: string;
    content: string;
    page?: number;
    timestamp?: number;  // For audio (seconds)
  }>;
}>
```

**Endpoint:** `GET /api/documents/:id/markdown`

---

### `api.documents.delete(docId)`

**Purpose:** Delete a document and all associated files

**Parameters:**
```typescript
docId: string  // Document ID
```

**Returns:**
```typescript
Promise<{
  success: boolean;
  message: string;
  deleted: {
    visual_deleted: boolean;
    text_deleted: boolean;
    page_images_deleted: number;
    cover_art_deleted: boolean;
    markdown_deleted: boolean;
    temp_dirs_cleaned: number;
  };
}>
```

**Endpoint:** `DELETE /api/documents/:id`

---

### `api.documents.getSupportedFormats()`

**Purpose:** Fetch server-supported file types and groupings

**Parameters:** None

**Returns:**
```typescript
Promise<{
  extensions: string[];  // ['.pdf', '.docx', '.mp3', ...]
  groups: Array<{
    id: string;
    label: string;
    extensions: string[];
  }>;
}>
```

**Endpoint:** `GET /api/documents/supported-formats`

---

## Upload API

### `api.upload.uploadFile(file, onProgress)`

**Purpose:** Upload a single file to Copyparty

**Parameters:**
```typescript
file: File                          // File object from input
onProgress?: (progress: number) => void  // Progress callback (0-100)
```

**Returns:**
```typescript
Promise<{
  success: boolean;
  filename: string;
  temp_id: string;  // Temporary ID for optimistic UI
}>
```

**Endpoint:** `POST http://localhost:8000/uploads/` (Copyparty, not proxied)

**Implementation Notes:**
- Use `XMLHttpRequest` for progress tracking (not `fetch`)
- Send as `multipart/form-data`
- Generate `temp_id` client-side for optimistic updates

---

## Research API

### `api.research.ask(query)`

**Purpose:** Submit a research question and get AI-generated answer with citations

**Parameters:**
```typescript
query: string  // User's question (3-500 chars)
```

**Returns:**
```typescript
Promise<{
  answer: string;  // Markdown-formatted answer with inline citations [N]
  references: Array<{
    id: number;           // Citation number
    doc_id: string;       // Document ID
    filename: string;
    page?: number;        // Page number (for documents)
    timestamp?: number;   // Timestamp in seconds (for audio)
    thumbnail_url?: string;
    relevance_score: number;  // 0-1
  }>;
  query: string;          // Echo of original query
  model: string;          // LLM model used
}>
```

**Endpoint:** `POST /api/research/ask`

**Request Body:**
```json
{
  "query": "What are the main themes discussed?"
}
```

---

### `api.research.getHealth()`

**Purpose:** Check if research API is available

**Parameters:** None

**Returns:**
```typescript
Promise<{
  status: 'healthy' | 'unhealthy';
  litellm_available: boolean;
  model: string;
}>
```

**Endpoint:** `GET /api/research/health`

---

## Status API

### `api.status.get()`

**Purpose:** Get processing worker status

**Parameters:** None

**Returns:**
```typescript
Promise<{
  status: 'running' | 'stopped';
  processing_active: boolean;
  queue_length: number;
  documents_processed: number;
  uptime_seconds: number;
}>
```

**Endpoint:** `GET /api/status`

---

## Error Handling

All API functions should throw standardized errors:

```typescript
class APIError extends Error {
  constructor(
    message: string,
    statusCode: number,
    endpoint: string,
    originalError?: any
  ) {
    super(message);
    this.name = 'APIError';
    this.statusCode = statusCode;
    this.endpoint = endpoint;
    this.originalError = originalError;
  }
}
```

**Error Scenarios:**
- Network failure → `APIError('Network request failed', 0, endpoint)`
- 4xx errors → `APIError(errorMessage, statusCode, endpoint)`
- 5xx errors → `APIError('Server error', statusCode, endpoint)`
- Timeout → `APIError('Request timeout', 408, endpoint)`

---

## Usage Example (for consumers)

```javascript
import { api } from '@services/api';

// Fetch documents
try {
  const data = await api.documents.list({
    search: 'energy',
    sort_by: 'newest_first',
    limit: 50
  });
  console.log(`Found ${data.total} documents`);
} catch (error) {
  if (error instanceof APIError) {
    console.error(`API error (${error.statusCode}):`, error.message);
  }
}
```

---

## Testing Requirements

Provider (infrastructure-agent) must provide:
- ✅ Mock API responses for testing (MSW handlers)
- ✅ Unit tests for error handling
- ✅ Integration tests with real backend (optional)

Consumers must:
- ✅ Use provided mock handlers in tests
- ✅ Handle all error scenarios
- ✅ Test timeout behavior

---

## Migration Notes

**Current Implementation:** `src/frontend/api-client.js`
- Already exports DocumentsAPIClient class
- Methods: `listDocuments`, `getDocument`, `getMarkdown`, `deleteDocument`, `getSupportedFormats`

**Required Changes:**
- Rename to `api.js`
- Export flat API object (not class): `export const api = { documents: {...}, upload: {...}, research: {...} }`
- Add timeout handling
- Standardize error types
- Add TypeScript JSDoc annotations

---

## Validation Checklist

- [ ] All documented methods implemented
- [ ] Error handling consistent across methods
- [ ] Timeout configuration working
- [ ] Mock handlers provided for testing
- [ ] JSDoc annotations complete
- [ ] Integration test with real backend passes
