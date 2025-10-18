# API Integration Contracts

**Version**: 1.0
**Last Updated**: 2025-10-17
**Status**: SPECIFICATION

---

## 1. Structure Metadata Endpoint

### GET /documents/{doc_id}/pages/{page}/structure

**Purpose**: Retrieve document structure metadata for a specific page, including bounding boxes for headings, tables, pictures, and other elements.

**Request**:
```http
GET /documents/{doc_id}/pages/{page}/structure HTTP/1.1
Host: localhost:8002
```

**Path Parameters**:
- `doc_id` (string, required): Document identifier (UUID or hash)
- `page` (integer, required): Page number (1-indexed)

**Response Schema** (200 OK):
```json
{
  "doc_id": "string",
  "page": "integer",
  "has_structure": "boolean",
  "headings": [
    {
      "text": "string",
      "level": "string (TITLE|SECTION_HEADER|SUB_SECTION_HEADER|PARAGRAPH_HEADER)",
      "section_path": "string",
      "bbox": [x1, y1, x2, y2],
      "chunk_ids": ["string"]
    }
  ],
  "tables": [
    {
      "caption": "string|null",
      "rows": "integer",
      "cols": "integer",
      "has_header": "boolean",
      "table_id": "string",
      "bbox": [x1, y1, x2, y2]
    }
  ],
  "pictures": [
    {
      "type": "string (chart|diagram|photo|logo|signature|other)",
      "caption": "string|null",
      "confidence": "float (0-1)",
      "picture_id": "string",
      "bbox": [x1, y1, x2, y2]
    }
  ],
  "code_blocks": [
    {
      "language": "string|null",
      "lines": "integer",
      "bbox": [x1, y1, x2, y2]
    }
  ],
  "formulas": [
    {
      "latex": "string|null",
      "bbox": [x1, y1, x2, y2]
    }
  ],
  "summary": {
    "total_sections": "integer",
    "max_depth": "integer",
    "has_toc": "boolean"
  },
  "coordinate_system": {
    "origin": "top-left",
    "units": "pixels",
    "image_width": "integer",
    "image_height": "integer"
  }
}
```

**Bounding Box Format**:
- `[x1, y1, x2, y2]` where:
  - `x1, y1`: Top-left corner coordinates
  - `x2, y2`: Bottom-right corner coordinates
  - Origin: Top-left of page image (0, 0)
  - Units: Pixels relative to original page image dimensions

**Error Responses**:
```json
// 404 Not Found - Document or page not found
{
  "error": "Page not found",
  "detail": "Document abc123 page 5 not found",
  "status_code": 404
}

// 200 OK - Page exists but no structure
{
  "doc_id": "abc123",
  "page": 5,
  "has_structure": false,
  "headings": [],
  "tables": [],
  "pictures": [],
  "code_blocks": [],
  "formulas": [],
  "summary": {
    "total_sections": 0,
    "max_depth": 0,
    "has_toc": false
  },
  "coordinate_system": null
}
```

**Consumer Agents**: Agent 8 (BoundingBox Overlay), Agent 9 (Details Page)

---

## 2. Chunk Metadata Endpoint

### GET /documents/{doc_id}/chunks/{chunk_id}

**Purpose**: Retrieve metadata for a specific text chunk, including its location, content, and bounding box.

**Request**:
```http
GET /documents/{doc_id}/chunks/abc123-chunk0012 HTTP/1.1
Host: localhost:8002
```

**Path Parameters**:
- `doc_id` (string, required): Document identifier
- `chunk_id` (string, required): Chunk identifier (`{doc_id}-chunk{NNNN}`)

**Response Schema** (200 OK):
```json
{
  "chunk_id": "string",
  "doc_id": "string",
  "page": "integer",
  "full_text": "string",
  "word_count": "integer",
  "parent_heading": "string|null",
  "section_path": "string",
  "element_type": "string (text|list_item|table_cell|caption|code|formula)",
  "bbox": [x1, y1, x2, y2] | null,
  "related_tables": ["string"],
  "related_pictures": ["string"],
  "is_page_boundary": "boolean",
  "start_time": "float|null",
  "end_time": "float|null"
}
```

**Error Responses**:
```json
// 404 Not Found
{
  "error": "Chunk not found",
  "detail": "Chunk abc123-chunk0012 not found",
  "status_code": 404
}
```

**Consumer Agents**: Agent 9 (Details Page), Agent 10 (Research Navigation)

---

## 3. Enhanced Markdown Endpoint

### GET /documents/{doc_id}/markdown

**Purpose**: Retrieve document markdown with embedded chunk markers and metadata.

**Request**:
```http
GET /documents/{doc_id}/markdown HTTP/1.1
Host: localhost:8002
```

**Response Format** (200 OK):
```markdown
---
filename: Document.pdf
doc_id: abc123
date_added: 2025-10-17T00:00:00Z
has_timestamps: false
chunk_count: 30
---

# Document Title

<!-- chunk:abc123-chunk0000 page:1 section:"Introduction" -->
<div data-chunk-id="abc123-chunk0000" data-page="1" data-section="Introduction">
First paragraph content here...
</div>

<!-- chunk:abc123-chunk0001 page:1 section:"Introduction > Background" -->
<div data-chunk-id="abc123-chunk0001" data-page="1" data-section="Introduction > Background">
Second paragraph content...
</div>

## Section Header

<!-- chunk:abc123-chunk0002 page:2 section:"Methods" -->
<div data-chunk-id="abc123-chunk0002" data-page="2" data-section="Methods">
Methods section content...
</div>
```

**Chunk Marker Format**:
```html
<!-- chunk:{chunk_id} page:{page} section:"{section_path}" -->
<div data-chunk-id="{chunk_id}" data-page="{page}" data-section="{section_path}">
  {chunk_text}
</div>
```

**Consumer Agents**: Agent 9 (Details Page), Agent 7 (Markdown Chunker)

---

## 4. Research API SourceInfo Extension

### POST /api/research/ask

**Extension**: Add `chunk_id` field to SourceInfo in response.

**Current Implementation Status**: The research API currently returns SourceInfo **without** the `chunk_id` field. This field needs to be added in Wave 2 (Backend).

**Current SourceInfo Schema** (from `src/api/research.py`):
```python
class SourceInfo(BaseModel):
    id: int                           # Citation number (1-indexed)
    doc_id: str
    filename: str
    page: int
    extension: str
    thumbnail_path: Optional[str] = None
    date_added: str                   # ISO format
    relevance_score: float
    # chunk_id: Optional[str] = None  # TO BE ADDED
```

**Enhanced Response Schema** (Target):
```json
{
  "answer": "string",
  "citations": [...],
  "citation_map": {...},
  "sources": [
    {
      "id": "integer (citation number)",
      "doc_id": "string",
      "filename": "string",
      "page": "integer",
      "extension": "string",
      "thumbnail_path": "string|null",
      "date_added": "string (ISO)",
      "relevance_score": "float",
      "chunk_id": "string|null"  // NEW FIELD - TO BE ADDED
    }
  ],
  "metadata": {...}
}
```

**Field Specification**:
- `chunk_id`: String or null
  - Present when source is from text search (chunk-level)
  - Null when source is from visual search (page-level only)
  - Format: `{doc_id}-chunk{NNNN}` where NNNN is zero-padded 4 digits
  - Example: `"fin-crisis-2008-report-chunk0045"`

**Implementation Notes**:
- Search results from `ContextBuilder.build_context()` must preserve chunk_id from ChromaDB metadata
- Text search results: Extract chunk_id from metadata field `"chunk_id"` (formatted as `chunk_{N}`)
- Visual search results: Set chunk_id to null (page-level only)
- Format transformation: ChromaDB stores as `"chunk_0045"`, API returns as `"{doc_id}-chunk0045"`

**Consumer Agents**: Agent 10 (Research Navigation), Agent 6 (Research Context Enhancer)

---

## 5. Chunk Navigation URL Parameters

### Details Page URL Format

**Base URL**: `/frontend/details.html`

**Query Parameters**:
- `id` (string, required): Document ID
- `page` (integer, optional): Page number to display (default: 1)
- `chunk` (string, optional): Chunk ID to highlight and scroll to

**Examples**:
```
# Visual search result (page-level)
/frontend/details.html?id=abc123&page=5

# Text search result (chunk-level)
/frontend/details.html?id=abc123&page=5&chunk=abc123-chunk0012

# Document only (default to page 1)
/frontend/details.html?id=abc123
```

**Behavior Specification**:
1. Parse URL parameters on page load
2. If `chunk` parameter present:
   - Fetch chunk metadata via Chunk Metadata Endpoint
   - Navigate to specified `page`
   - Highlight chunk in markdown
   - Highlight bbox on page image (if bbox available)
   - Scroll both image and text to make chunk visible
3. If only `page` parameter:
   - Navigate to page
   - No highlighting
4. If neither parameter:
   - Show page 1, no highlighting

**Consumer Agents**: Agent 9 (Details Page), Agent 10 (Research Navigation)

---

## Coordinate System Specification

### Bounding Box Coordinates

**Reference System**:
- **Origin**: Top-left corner of page image (0, 0)
- **Units**: Pixels
- **Dimensions**: Relative to original page image size

**Format**: `[x1, y1, x2, y2]`
```
(0,0) ────────────────────> X
  │
  │   (x1,y1)──────┐
  │      │         │
  │      │  BBOX   │
  │      │         │
  │      └─────(x2,y2)
  │
  v
  Y
```

**Scaling for Display**:
```javascript
// Frontend must scale coordinates to displayed image size
const scaleX = displayedImageWidth / originalImageWidth;
const scaleY = displayedImageHeight / originalImageHeight;

const displayedBbox = {
  x1: bbox[0] * scaleX,
  y1: bbox[1] * scaleY,
  x2: bbox[2] * scaleX,
  y2: bbox[3] * scaleY
};
```

**Validation**:
- `x1 < x2`
- `y1 < y2`
- All coordinates ≥ 0
- All coordinates within image dimensions

---

## Integration Testing Checklist

### Structure Endpoint
- [ ] Returns valid JSON for PDF with structure
- [ ] Returns empty structure for document without metadata
- [ ] Returns 404 for non-existent document
- [ ] Returns 404 for non-existent page
- [ ] Bounding boxes have valid coordinates
- [ ] Chunk IDs in headings exist in text collection

### Chunk Endpoint
- [ ] Returns valid chunk metadata
- [ ] Returns 404 for non-existent chunk
- [ ] Bbox coordinates valid (if present)
- [ ] Related tables/pictures IDs valid

### Markdown Endpoint
- [ ] Contains valid chunk markers
- [ ] Chunk IDs match ChromaDB records
- [ ] HTML div wrappers don't break rendering
- [ ] Frontmatter includes chunk_count

### Research API
- [ ] SourceInfo includes chunk_id for text results
- [ ] SourceInfo chunk_id is null for visual results
- [ ] Chunk IDs are valid and queryable

### URL Navigation
- [ ] Details page parses all URL params correctly
- [ ] Missing params don't cause errors
- [ ] Invalid chunk ID shows error gracefully
- [ ] Deep links work (shareable URLs)

---

## Implementation Status Summary

### Existing Endpoints (No Changes Needed)
- ✅ `GET /documents/{doc_id}/markdown` - Already returns markdown with frontmatter
- ✅ `POST /api/research/ask` - Exists but needs `chunk_id` field added to SourceInfo

### New Endpoints (To Be Implemented)
- ❌ `GET /documents/{doc_id}/pages/{page}/structure` - Wave 2 Backend (Agent 4)
- ❌ `GET /documents/{doc_id}/chunks/{chunk_id}` - Wave 2 Backend (Agent 5)

### Enhanced Endpoints (To Be Modified)
- 🔄 `GET /documents/{doc_id}/markdown` - Add chunk markers (Agent 7)
- 🔄 `POST /api/research/ask` - Add chunk_id to SourceInfo (Agent 6)

### API Implementation Matrix

| Endpoint | Current Status | Changes Required | Agent |
|----------|---------------|------------------|-------|
| Structure API | Not implemented | New endpoint | Agent 4 |
| Chunk Metadata API | Not implemented | New endpoint | Agent 5 |
| Markdown Enhancement | Exists | Add chunk markers | Agent 7 |
| Research API | Exists | Add chunk_id field | Agent 6 |

---

## Version History

**v1.1** (2025-10-17):
- Added implementation status section
- Clarified current vs. target state for Research API
- Documented chunk_id format transformation rules
- Added notes on existing implementation in `src/api/research.py`

**v1.0** (2025-10-17):
- Initial specification
- Structure endpoint defined
- Chunk endpoint defined
- Markdown enhancement specified
- Research API extension defined
- URL parameter contract established
- Coordinate system documented
