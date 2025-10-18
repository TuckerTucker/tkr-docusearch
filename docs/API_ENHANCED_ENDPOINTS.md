# API Enhanced Endpoints Reference

**Version:** 1.0 (Enhanced Mode)
**Last Updated:** 2025-10-17
**Base URL:** `http://localhost:8002`

---

## Overview

This document describes the **Enhanced Mode API endpoints** that provide document structure data with bounding box coordinates for bidirectional highlighting.

### Enhanced Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/documents/{doc_id}/pages/{page}/structure` | Get structure data for a page |
| `GET` | `/documents/{doc_id}/chunks/{chunk_id}` | Get specific chunk with metadata |
| `GET` | `/documents/{doc_id}/markdown` | Get markdown with chunk markers |
| `POST` | `/api/research/ask` | Research query (now includes chunk_id) |

---

## Endpoints

### 1. Get Page Structure

Retrieve document structure with bounding boxes for a specific page.

**Endpoint:** `GET /documents/{doc_id}/pages/{page}/structure`

**Parameters:**

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `doc_id` | string | path | Yes | Document identifier |
| `page` | integer | path | Yes | Page number (1-indexed) |

**Request Example:**

```bash
curl -X GET "http://localhost:8002/documents/doc_abc123/pages/1/structure"
```

**Response Schema:**

```typescript
{
  doc_id: string;              // Document identifier
  page: number;                // Page number
  page_width: number;          // PDF page width in points
  page_height: number;         // PDF page height in points
  elements: Array<{            // Structural elements
    id: string;                // Element identifier (e.g., "elem_1_0")
    type: string;              // Element type (heading, paragraph, list, table, figure)
    bbox: {                    // Bounding box in PDF coordinates
      left: number;            // Left edge (points from left)
      bottom: number;          // Bottom edge (points from bottom)
      right: number;           // Right edge (points from left)
      top: number;             // Top edge (points from bottom)
    };
    text: string;              // Text content (truncated preview)
    chunk_id?: string;         // Associated chunk identifier (if chunked)
  }>;
  metadata_version: string;    // Schema version (e.g., "1.0")
  has_structure: boolean;      // True if structure extraction succeeded
}
```

**Response Example (Success):**

```json
{
  "doc_id": "doc_abc123",
  "page": 1,
  "page_width": 612,
  "page_height": 792,
  "elements": [
    {
      "id": "elem_1_0",
      "type": "heading",
      "bbox": {
        "left": 72,
        "bottom": 650,
        "right": 540,
        "top": 720
      },
      "text": "Executive Summary",
      "chunk_id": "chunk_abc123_0"
    },
    {
      "id": "elem_1_1",
      "type": "paragraph",
      "bbox": {
        "left": 72,
        "bottom": 580,
        "right": 540,
        "top": 640
      },
      "text": "This quarterly report presents financial results for Q4 2024...",
      "chunk_id": "chunk_abc123_1"
    },
    {
      "id": "elem_1_2",
      "type": "table",
      "bbox": {
        "left": 72,
        "bottom": 300,
        "right": 540,
        "top": 560
      },
      "text": "[Table: Revenue Breakdown]",
      "chunk_id": "chunk_abc123_2"
    }
  ],
  "metadata_version": "1.0",
  "has_structure": true
}
```

**Response (No Structure Data):**

```json
{
  "doc_id": "doc_abc123",
  "page": 1,
  "has_structure": false,
  "error": "Structure data not available for this document"
}
```

**Error Responses:**

| Status Code | Description | Response Body |
|-------------|-------------|---------------|
| `404` | Document not found | `{"error": "Document not found"}` |
| `400` | Invalid page number | `{"error": "Invalid page number"}` |
| `500` | Structure extraction failed | `{"error": "Structure extraction failed", "details": "..."}` |

**Notes:**
- Page numbers are 1-indexed (first page is 1, not 0)
- Bounding boxes use **PDF coordinate system** (origin at bottom-left, Y increases upward)
- Structure data is cached for performance (20 pages by default)
- If enhanced mode is disabled, endpoint returns `has_structure: false`

---

### 2. Get Chunk by ID

Retrieve a specific text chunk with full metadata including bounding box.

**Endpoint:** `GET /documents/{doc_id}/chunks/{chunk_id}`

**Parameters:**

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `doc_id` | string | path | Yes | Document identifier |
| `chunk_id` | string | path | Yes | Chunk identifier |

**Request Example:**

```bash
curl -X GET "http://localhost:8002/documents/doc_abc123/chunks/chunk_abc123_5"
```

**Response Schema:**

```typescript
{
  chunk_id: string;            // Chunk identifier
  doc_id: string;              // Parent document identifier
  text: string;                // Full chunk text
  page: number;                // Page number (1-indexed)
  chunk_index: number;         // Chunk position in document
  element_id?: string;         // Linked structure element ID
  bbox?: {                     // Bounding box (if available)
    left: number;
    bottom: number;
    right: number;
    top: number;
  };
  element_type?: string;       // Element type (heading, paragraph, etc.)
  context: {                   // Surrounding context
    prev_chunk?: string;       // Previous chunk ID
    next_chunk?: string;       // Next chunk ID
    section_heading?: string;  // Parent section heading
  };
  metadata_version: string;    // Schema version
}
```

**Response Example (Success):**

```json
{
  "chunk_id": "chunk_abc123_5",
  "doc_id": "doc_abc123",
  "text": "Revenue increased 15% year-over-year in Q4 2024, driven by strong product sales and international expansion. Operating expenses remained flat at $50M.",
  "page": 3,
  "chunk_index": 5,
  "element_id": "elem_3_2",
  "bbox": {
    "left": 72,
    "bottom": 400,
    "right": 540,
    "top": 450
  },
  "element_type": "paragraph",
  "context": {
    "prev_chunk": "chunk_abc123_4",
    "next_chunk": "chunk_abc123_6",
    "section_heading": "Financial Results"
  },
  "metadata_version": "1.0"
}
```

**Error Responses:**

| Status Code | Description | Response Body |
|-------------|-------------|---------------|
| `404` | Chunk not found | `{"error": "Chunk not found"}` |
| `400` | Invalid chunk ID format | `{"error": "Invalid chunk ID"}` |

**Notes:**
- Chunk IDs follow format: `chunk_{doc_id}_{index}`
- `bbox` field is `null` if enhanced mode is disabled or structure extraction failed
- `context` provides information about surrounding chunks for navigation

---

### 3. Get Markdown with Chunk Markers

Retrieve document markdown with HTML comments marking chunk boundaries and metadata.

**Endpoint:** `GET /documents/{doc_id}/markdown`

**Parameters:**

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `doc_id` | string | path | Yes | Document identifier |
| `include_markers` | boolean | query | No | Include chunk markers (default: true) |

**Request Example:**

```bash
curl -X GET "http://localhost:8002/documents/doc_abc123/markdown"
```

**Response Schema:**

```typescript
{
  doc_id: string;              // Document identifier
  filename: string;            // Original filename
  markdown: string;            // Markdown content with markers
  total_chunks: number;        // Number of chunks
  has_structure: boolean;      // Whether structure data is available
}
```

**Response Example (Success):**

```json
{
  "doc_id": "doc_abc123",
  "filename": "quarterly_report.pdf",
  "markdown": "<!-- CHUNK_START: chunk_abc123_0, PAGE: 1, BBOX: 72,650,540,720 -->\n# Executive Summary\n<!-- CHUNK_END: chunk_abc123_0 -->\n\n<!-- CHUNK_START: chunk_abc123_1, PAGE: 1, BBOX: 72,580,540,640 -->\nThis quarterly report presents financial results for Q4 2024...\n<!-- CHUNK_END: chunk_abc123_1 -->\n\n<!-- CHUNK_START: chunk_abc123_2, PAGE: 1, BBOX: 72,300,540,560 -->\n| Product | Revenue | Growth |\n|---------|---------|--------|\n| Product A | $50M | +20% |\n| Product B | $30M | +10% |\n<!-- CHUNK_END: chunk_abc123_2 -->",
  "total_chunks": 3,
  "has_structure": true
}
```

**Chunk Marker Format:**

```html
<!-- CHUNK_START: {chunk_id}, PAGE: {page}, BBOX: {left},{bottom},{right},{top} -->
{chunk text content}
<!-- CHUNK_END: {chunk_id} -->
```

**Example Usage (Frontend):**

```javascript
// Parse chunk markers to build chunk-to-bbox mapping
function parseChunkMarkers(markdown) {
    const chunkRegex = /<!-- CHUNK_START: (.*?), PAGE: (\d+), BBOX: (.*?) -->/g;
    const chunks = [];

    let match;
    while ((match = chunkRegex.exec(markdown)) !== null) {
        const [_, chunkId, page, bboxStr] = match;
        const [left, bottom, right, top] = bboxStr.split(',').map(Number);

        chunks.push({
            chunk_id: chunkId,
            page: parseInt(page),
            bbox: { left, bottom, right, top }
        });
    }

    return chunks;
}
```

**Error Responses:**

| Status Code | Description | Response Body |
|-------------|-------------|---------------|
| `404` | Document not found | `{"error": "Document not found"}` |
| `500` | Markdown generation failed | `{"error": "Failed to generate markdown"}` |

**Notes:**
- Chunk markers are HTML comments, so they're invisible when rendered
- If `include_markers=false`, returns plain markdown without chunk boundaries
- BBOX format is `left,bottom,right,top` in PDF coordinates

---

### 4. Research Ask (Enhanced)

Submit a research question and receive AI-generated answer with citations including chunk IDs.

**Endpoint:** `POST /api/research/ask`

**Request Schema:**

```typescript
{
  question: string;            // User's question
  num_sources?: number;        // Max sources to use (default: 10)
  model?: string;              // LLM model to use (default: from config)
}
```

**Request Example:**

```bash
curl -X POST "http://localhost:8002/api/research/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What were the Q4 financial results?",
    "num_sources": 10,
    "model": "gpt-4"
  }'
```

**Response Schema (Enhanced):**

```typescript
{
  question: string;            // Original question
  answer: string;              // AI-generated answer with citations
  sources: Array<{             // Source documents cited
    citation_number: number;   // Citation number [1], [2], etc.
    doc_id: string;            // Document identifier
    filename: string;          // Original filename
    page: number;              // Page number
    upload_date: string;       // ISO timestamp
    chunk_id?: string;         // NEW: Chunk identifier (if available)
    bbox?: {                   // NEW: Bounding box (if available)
      left: number;
      bottom: number;
      right: number;
      top: number;
    };
    element_type?: string;     // NEW: Element type (heading, paragraph, etc.)
    relevance_score: number;   // Search relevance (0-1)
  }>;
  processing_time_ms: number;  // Total processing time
  model_used: string;          // LLM model used
  sources_found: number;       // Number of relevant documents found
  context_truncated: boolean;  // Whether context exceeded token limit
}
```

**Response Example (Success):**

```json
{
  "question": "What were the Q4 financial results?",
  "answer": "According to the quarterly report [1], revenue increased 15% year-over-year in Q4 2024, reaching $80M [1]. This growth was driven by strong product sales [1] and international expansion [2]. Operating expenses remained flat at $50M [1], resulting in improved profit margins of 23% [2], which exceeded initial guidance [2].",
  "sources": [
    {
      "citation_number": 1,
      "doc_id": "doc_abc123",
      "filename": "q4_2024_report.pdf",
      "page": 3,
      "upload_date": "2025-01-15T10:30:00Z",
      "chunk_id": "chunk_abc123_5",
      "bbox": {
        "left": 72,
        "bottom": 400,
        "right": 540,
        "top": 450
      },
      "element_type": "paragraph",
      "relevance_score": 0.95
    },
    {
      "citation_number": 2,
      "doc_id": "doc_xyz789",
      "filename": "financial_analysis.pdf",
      "page": 7,
      "upload_date": "2025-01-16T14:20:00Z",
      "chunk_id": "chunk_xyz789_12",
      "bbox": {
        "left": 72,
        "bottom": 500,
        "right": 540,
        "top": 550
      },
      "element_type": "heading",
      "relevance_score": 0.87
    }
  ],
  "processing_time_ms": 2450,
  "model_used": "gpt-4",
  "sources_found": 15,
  "context_truncated": false
}
```

**Enhanced Features:**

1. **chunk_id** - Direct link to specific text chunk
2. **bbox** - Bounding box for precise visual highlighting
3. **element_type** - Structural context (heading, paragraph, etc.)

**Frontend Integration Example:**

```javascript
async function handleResearchAnswer(answer) {
    // Display answer with citations
    displayAnswer(answer.answer);

    // Render source references with "Details" buttons
    answer.sources.forEach(source => {
        const hasChunkNav = source.chunk_id && source.bbox;

        renderSourceCard({
            citationNumber: source.citation_number,
            filename: source.filename,
            page: source.page,
            detailsUrl: hasChunkNav
                ? `/documents/${source.doc_id}?chunk=${source.chunk_id}`
                : `/documents/${source.doc_id}`,
            chunkIndicator: hasChunkNav ? '📍' : ''
        });
    });
}
```

**Error Responses:**

| Status Code | Description | Response Body |
|-------------|-------------|---------------|
| `400` | Missing question | `{"error": "Question is required"}` |
| `404` | No relevant documents | `{"error": "No relevant documents found"}` |
| `429` | Rate limit exceeded | `{"error": "Rate limit exceeded", "retry_after": 60}` |
| `500` | LLM API error | `{"error": "LLM request failed", "details": "..."}` |
| `503` | Service unavailable | `{"error": "Research service unavailable"}` |

**Notes:**
- `chunk_id` and `bbox` are `null` for documents processed before enhanced mode
- Citations marked with 📍 icon in UI when chunk navigation is available
- Token limit varies by model (GPT-4: ~8K, Claude: ~100K)

---

## Data Models

### BoundingBox

Represents a rectangular region in PDF coordinate space.

```typescript
interface BoundingBox {
  left: number;      // X coordinate of left edge (points from left margin)
  bottom: number;    // Y coordinate of bottom edge (points from bottom margin)
  right: number;     // X coordinate of right edge (points from left margin)
  top: number;       // Y coordinate of top edge (points from bottom margin)
}
```

**Coordinate System:**
- Origin: Bottom-left corner
- X-axis: Left to right
- Y-axis: Bottom to top (⚠️ inverted compared to screen coordinates)
- Units: Points (1 point = 1/72 inch)

**Standard Page Sizes:**
- Letter: 612pt × 792pt
- A4: 595pt × 842pt

### ElementType

Structural element types recognized by the structure extractor.

```typescript
type ElementType =
  | "heading"      // Section headings (h1-h6)
  | "paragraph"    // Body text
  | "list"         // Bulleted or numbered lists
  | "table"        // Tabular data
  | "figure"       // Images, charts, diagrams
  | "code"         // Code blocks
  | "quote"        // Block quotes
  | "caption"      // Figure/table captions
  | "footer"       // Page footers
  | "header";      // Page headers
```

### MetadataVersion

Schema version for backward compatibility.

```typescript
type MetadataVersion = "0.0" | "1.0";
```

- **"0.0"** - Legacy documents (no structure data)
- **"1.0"** - Enhanced mode documents (with structure data)

---

## Rate Limiting

### Limits

| Endpoint | Rate Limit | Burst |
|----------|------------|-------|
| `GET /documents/.../structure` | 100/min | 20 |
| `GET /documents/.../chunks/...` | 200/min | 50 |
| `GET /documents/.../markdown` | 50/min | 10 |
| `POST /api/research/ask` | 10/min | 3 |

### Headers

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1633024800
```

### Handling Rate Limits

**Response (429 Too Many Requests):**

```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60,
  "limit": 100,
  "window": "1m"
}
```

**Client Implementation:**

```javascript
async function fetchWithRateLimit(url) {
    try {
        const response = await fetch(url);

        if (response.status === 429) {
            const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
            await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
            return fetchWithRateLimit(url);  // Retry
        }

        return response;
    } catch (error) {
        console.error('Request failed:', error);
        throw error;
    }
}
```

---

## Versioning

### API Versioning Strategy

Currently: **v1.0** (unversioned endpoints)

**Future Versioning:**
- v2.0 will be introduced if breaking changes are needed
- Endpoints will include version prefix: `/v2/documents/...`
- v1.0 will be supported for at least 12 months after v2.0 release

### Metadata Version Handling

Documents have a `metadata_version` field:
- **"0.0"** - Legacy (pre-enhanced mode)
- **"1.0"** - Current (enhanced mode)

**Backward Compatibility:**

```python
# API gracefully handles both versions
def get_chunk_metadata(chunk_id: str):
    metadata = fetch_chunk(chunk_id)

    if metadata.version == "0.0":
        # Legacy document: no structure data
        return {
            "chunk_id": chunk_id,
            "text": metadata.text,
            "page": metadata.page,
            # bbox, element_id, element_type are null
        }
    else:
        # Enhanced document: full structure data
        return {
            "chunk_id": chunk_id,
            "text": metadata.text,
            "page": metadata.page,
            "bbox": metadata.bbox,
            "element_id": metadata.element_id,
            "element_type": metadata.element_type,
        }
```

---

## Performance

### Response Times (p95)

| Endpoint | Cached | Uncached | Notes |
|----------|--------|----------|-------|
| `GET .../structure` | 5ms | 50ms | Decompression overhead |
| `GET .../chunks/...` | 2ms | 10ms | Database lookup |
| `GET .../markdown` | 20ms | 100ms | Markdown generation |
| `POST /api/research/ask` | N/A | 2500ms | LLM inference dominates |

### Caching Strategy

**Structure Data:**
- LRU cache, 20 pages by default
- Cache hit rate: ~80% for typical usage
- Cache invalidated on document reprocessing

**Chunk Metadata:**
- No caching (database is fast enough)
- ChromaDB provides efficient querying

**Markdown:**
- No caching (generated on-demand)
- Future: Consider caching for large documents

### Optimization Tips

**For Large Documents (100+ pages):**
1. Request structure data lazily (only for visible pages)
2. Use `include_markers=false` if chunk navigation not needed
3. Increase `STRUCTURE_CACHE_SIZE` environment variable

**For High-Traffic Scenarios:**
1. Implement client-side caching (localStorage, IndexedDB)
2. Use HTTP caching headers (`Cache-Control`, `ETag`)
3. Consider CDN for static structure data

---

## Error Handling

### Error Response Format

All errors follow consistent JSON format:

```json
{
  "error": "Human-readable error message",
  "details": "Technical details (optional)",
  "error_code": "MACHINE_READABLE_CODE",
  "timestamp": "2025-10-17T12:34:56Z"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `DOCUMENT_NOT_FOUND` | 404 | Document does not exist |
| `CHUNK_NOT_FOUND` | 404 | Chunk does not exist |
| `INVALID_PAGE` | 400 | Page number out of range |
| `STRUCTURE_UNAVAILABLE` | 404 | Structure data not available |
| `EXTRACTION_FAILED` | 500 | Structure extraction error |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INVALID_REQUEST` | 400 | Malformed request |
| `INTERNAL_ERROR` | 500 | Server error |

### Handling Missing Structure Data

**Scenario:** Document processed before enhanced mode enabled.

**API Behavior:**
- Endpoints return `has_structure: false`
- `bbox`, `element_id`, `element_type` fields are `null`
- No error thrown (graceful degradation)

**Client Handling:**

```javascript
async function renderDocumentPage(docId, page) {
    const structure = await fetchStructure(docId, page);

    if (!structure.has_structure) {
        // Fallback: render without bboxes
        renderPageImageOnly(docId, page);
        showNotification('Enhanced features not available for this document');
        return;
    }

    // Full enhanced mode
    renderPageWithStructure(docId, page, structure);
}
```

---

## Authentication

### Current Implementation

**None** - Running locally on `localhost:8002`

### Future Authentication (Planned)

When deployed in multi-user environments:

**API Key Authentication:**

```
Authorization: Bearer YOUR_API_KEY
```

**Request Example:**

```bash
curl -X GET "http://localhost:8002/documents/doc_123/structure" \
  -H "Authorization: Bearer api_key_abc123"
```

**Error Response (401 Unauthorized):**

```json
{
  "error": "Invalid or missing API key",
  "error_code": "UNAUTHORIZED"
}
```

---

## Examples

### Example 1: Fetch and Render Page Structure

**Goal:** Display a page with clickable bounding boxes.

**Steps:**

```javascript
async function renderEnhancedPage(docId, pageNum) {
    // 1. Fetch structure data
    const response = await fetch(
        `http://localhost:8002/documents/${docId}/pages/${pageNum}/structure`
    );
    const structure = await response.json();

    if (!structure.has_structure) {
        console.warn('No structure data available');
        return;
    }

    // 2. Create SVG overlay
    const svg = createSvgOverlay(structure);

    // 3. Attach click handlers
    structure.elements.forEach(element => {
        const rect = svg.querySelector(`[data-element-id="${element.id}"]`);
        rect.addEventListener('click', () => {
            jumpToChunk(element.chunk_id);
        });
    });

    // 4. Append to page
    document.querySelector(`#page-${pageNum}`).appendChild(svg);
}

function createSvgOverlay(structure) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    // ... (see BIDIRECTIONAL_HIGHLIGHTING.md for full implementation)
    return svg;
}
```

### Example 2: Navigate from Research Citation to Chunk

**Goal:** Click citation in research answer, jump to exact location in document.

**Steps:**

```javascript
async function handleCitationClick(citationNumber, sources) {
    // 1. Find source by citation number
    const source = sources.find(s => s.citation_number === citationNumber);

    if (!source.chunk_id) {
        // Fallback: open document at page level
        window.location.href = `/documents/${source.doc_id}?page=${source.page}`;
        return;
    }

    // 2. Navigate to document with chunk parameter
    window.location.href = `/documents/${source.doc_id}?chunk=${source.chunk_id}`;

    // 3. On document page, highlight the chunk
    // (Handled by document-details.js)
}
```

**Document Details Page Handler:**

```javascript
// On page load, check for chunk parameter
const urlParams = new URLSearchParams(window.location.search);
const targetChunkId = urlParams.get('chunk');

if (targetChunkId) {
    // Fetch chunk metadata
    const response = await fetch(
        `http://localhost:8002/documents/${docId}/chunks/${targetChunkId}`
    );
    const chunk = await response.json();

    // Scroll to chunk
    scrollToChunk(targetChunkId);

    // Highlight chunk
    highlightChunk(targetChunkId);

    // Highlight bbox on page image
    highlightBbox(chunk.bbox, chunk.page);
}
```

### Example 3: Extract All Headings from Document

**Goal:** Build a table of contents from structure data.

**Steps:**

```javascript
async function buildTableOfContents(docId, totalPages) {
    const headings = [];

    // Fetch structure for all pages
    for (let page = 1; page <= totalPages; page++) {
        const response = await fetch(
            `http://localhost:8002/documents/${docId}/pages/${page}/structure`
        );
        const structure = await response.json();

        if (!structure.has_structure) continue;

        // Extract headings
        const pageHeadings = structure.elements
            .filter(el => el.type === 'heading')
            .map(el => ({
                text: el.text,
                page: page,
                chunk_id: el.chunk_id,
                level: inferHeadingLevel(el.bbox.height)  // Infer h1/h2/h3 from size
            }));

        headings.push(...pageHeadings);
    }

    // Render TOC
    renderTOC(headings);
}

function inferHeadingLevel(height) {
    if (height > 40) return 1;  // h1
    if (height > 30) return 2;  // h2
    return 3;  // h3
}

function renderTOC(headings) {
    const tocHTML = headings.map(h => `
        <a href="#chunk-${h.chunk_id}" class="toc-level-${h.level}">
            ${h.text} <span class="page-num">p.${h.page}</span>
        </a>
    `).join('\n');

    document.querySelector('#toc').innerHTML = tocHTML;
}
```

---

## Migration from Standard to Enhanced API

### Breaking Changes

**None** - Enhanced endpoints are additive, not breaking.

### New Fields

Research API response now includes:

```diff
{
  "sources": [
    {
      "citation_number": 1,
      "doc_id": "doc_123",
      "filename": "report.pdf",
      "page": 3,
      "upload_date": "2025-01-15T10:30:00Z",
+     "chunk_id": "chunk_123_5",           // NEW
+     "bbox": { ... },                     // NEW
+     "element_type": "paragraph",         // NEW
      "relevance_score": 0.95
    }
  ]
}
```

### Client Compatibility

**Backward Compatible:**

```javascript
// Old clients ignore new fields (no errors)
function renderSource(source) {
    return `
        <div class="source">
            <span>${source.filename}</span>
            <span>Page ${source.page}</span>
        </div>
    `;
}

// New clients use new fields if available
function renderEnhancedSource(source) {
    const hasChunkNav = source.chunk_id && source.bbox;

    return `
        <div class="source">
            <span>${source.filename}</span>
            <span>Page ${source.page}</span>
            ${hasChunkNav ? '<span class="chunk-indicator">📍</span>' : ''}
            <a href="${buildDetailsUrl(source)}">Details</a>
        </div>
    `;
}

function buildDetailsUrl(source) {
    if (source.chunk_id) {
        return `/documents/${source.doc_id}?chunk=${source.chunk_id}`;
    }
    return `/documents/${source.doc_id}?page=${source.page}`;
}
```

---

## Changelog

### v1.0 (2025-10-17)

**Added:**
- `GET /documents/{doc_id}/pages/{page}/structure` - Page structure with bboxes
- `GET /documents/{doc_id}/chunks/{chunk_id}` - Chunk metadata
- Enhanced markdown with chunk markers
- `chunk_id`, `bbox`, `element_type` fields in research API

**Changed:**
- Research API sources now include chunk-level metadata

**Fixed:**
- N/A (initial release)

---

## Support

**Documentation:**
- [Enhanced Mode User Guide](ENHANCED_MODE.md)
- [Bidirectional Highlighting Guide](BIDIRECTIONAL_HIGHLIGHTING.md)
- [Developer Guide: Bounding Boxes](DEVELOPER_GUIDE_BBOX.md)

**Issues:**
- GitHub: https://github.com/your-org/tkr-docusearch/issues
- Email: support@docusearch.example

**API Status:**
- Status Page: http://localhost:8002/health
- Metrics: http://localhost:8002/metrics

---

**Happy Integrating! 🚀**
