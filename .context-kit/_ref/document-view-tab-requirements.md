# Document View Tab Requirements

**Context:** Adding a document browser/viewer tab to the existing process monitoring UI to view stored documents in ChromaDB.

**Date:** 2025-10-11
**Status:** Design Phase

---

## Current Architecture

### Existing Monitoring UI (`monitor.html` @ port 8002)
- **WebSocket** connection for real-time updates
- **Stats Panel:** Active/completed/failed counts
- **Active Queue:** Documents currently processing
- **Real-time Logs:** Live processing events
- **Backend:** `status_api.py` with `/status/queue` and `/status/{doc_id}` endpoints

### Data Storage
- **ChromaDB** @ localhost:8001
  - **Visual Collection:** Page embeddings (metadata: filename, page_number, doc_id, image_path)
  - **Text Collection:** Text chunk embeddings (metadata: filename, chunk_id, doc_id, text_content)
- Each document has multiple entries (one per page/chunk)
- 128-dim embeddings stored with full sequences in compressed metadata

---

## Requirements for Document View Tab

### 1. Backend API Layer (New Routes)

#### New Router: `/documents`

**Purpose:** Query ChromaDB for stored documents (not just active processing queue)

**Endpoints:**

```python
GET /documents
# List all documents in ChromaDB
# Response:
{
  "documents": [
    {
      "doc_id": "sha256hash...",
      "filename": "report.pdf",
      "page_count": 5,
      "chunk_count": 23,
      "date_added": "2025-10-11T10:30:00Z",
      "collections": ["visual", "text"]
    }
  ],
  "total": 42,
  "storage_stats": {
    "total_pages": 210,
    "total_chunks": 1250
  }
}

GET /documents/{doc_id}
# Get detailed metadata for one document
# Response:
{
  "doc_id": "sha256hash...",
  "filename": "report.pdf",
  "pages": [
    {
      "page_number": 1,
      "image_path": "/path/to/page1.png",
      "embedding_id": "chroma_id_1"
    }
  ],
  "chunks": [
    {
      "chunk_id": "chunk_0",
      "text_content": "First paragraph...",
      "embedding_id": "chroma_id_100"
    }
  ],
  "metadata": {
    "date_added": "2025-10-11T10:30:00Z",
    "page_count": 5,
    "chunk_count": 23
  }
}

GET /documents/{doc_id}/pages
# Get page list with metadata (for thumbnails/preview)

DELETE /documents/{doc_id}
# Remove document from ChromaDB (optional)
```

**Implementation Details:**

```python
# documents_api.py
from src.storage.chroma_client import ChromaClient

router = APIRouter(prefix="/documents", tags=["documents"])

@router.get("/")
async def list_documents():
    # 1. Query visual collection for all items
    visual_items = chroma_client.get_collection("visual").get()

    # 2. Query text collection for all items
    text_items = chroma_client.get_collection("text").get()

    # 3. Extract unique doc_ids
    doc_ids = set()
    doc_ids.update(visual_items['metadatas'][i]['doc_id']
                   for i in range(len(visual_items['ids'])))
    doc_ids.update(text_items['metadatas'][i]['doc_id']
                   for i in range(len(text_items['ids'])))

    # 4. Aggregate metadata per doc_id
    documents = []
    for doc_id in doc_ids:
        pages = [m for m in visual_items['metadatas']
                 if m['doc_id'] == doc_id]
        chunks = [m for m in text_items['metadatas']
                  if m['doc_id'] == doc_id]

        documents.append({
            "doc_id": doc_id,
            "filename": pages[0]['filename'] if pages else "unknown",
            "page_count": len(pages),
            "chunk_count": len(chunks),
            "collections": ["visual", "text"]
        })

    return {"documents": documents, "total": len(documents)}
```

### 2. Frontend UI Components

#### Tab Navigation

**HTML Structure:**
```html
<div class="tabs">
  <button class="tab-button active" onclick="switchTab('processing')">
    Processing
  </button>
  <button class="tab-button" onclick="switchTab('documents')">
    Documents
  </button>
</div>

<div id="processing-view" class="tab-content active">
  <!-- Existing monitor UI -->
</div>

<div id="documents-view" class="tab-content hidden">
  <!-- New document browser -->
</div>
```

#### Documents Panel

**Features:**
- Document list table/grid
- Search/filter by filename
- Sort by date, name, page count
- Click to view details
- Delete button (with confirmation)

**Visual Design:**
```
+------------------------------------------------------------------+
| [Processing] [Documents*]                                         |
+------------------------------------------------------------------+
| Search: [___________]  Sort: [Date ▼]                            |
+------------------------------------------------------------------+
| Filename          | Doc ID    | Pages | Chunks | Date Added      |
|-------------------|-----------|-------|--------|-----------------|
| report.pdf        | a3b2c1... | 5     | 23     | Oct 11 10:30   |
| presentation.pptx | d4e5f6... | 12    | 45     | Oct 11 09:15   |
| invoice.docx      | g7h8i9... | 2     | 8      | Oct 10 16:42   |
+------------------------------------------------------------------+
```

#### Document Detail Modal

**Triggered by:** Click on document row

**Content:**
- Full doc_id
- Filename
- Date added
- Page thumbnails (if image paths available)
- Text chunks (expandable/collapsible)
- Metadata fields
- Delete button

### 3. Integration Points

#### ChromaDB Query Strategy

**Visual Collection:**
- Each entry = one page
- Metadata: `{filename, page_number, doc_id, image_path, embedding_full_sequence}`

**Text Collection:**
- Each entry = one text chunk
- Metadata: `{filename, chunk_id, doc_id, text_content, embedding_full_sequence}`

**Document Listing Logic:**
```
1. Query both collections: .get()
2. Extract unique doc_ids from metadata
3. Group entries by doc_id
4. Count pages (visual) and chunks (text) per document
5. Get first page metadata for filename, date
6. Return aggregated list
```

#### API Flow

```
User clicks "Documents" tab
    ↓
monitor.html: fetch('/documents')
    ↓
documents_api.py: list_documents()
    ↓
ChromaClient.get_collection('visual').get()
ChromaClient.get_collection('text').get()
    ↓
Process results, aggregate by doc_id
    ↓
Return JSON to frontend
    ↓
Render document table
```

### 4. Key Differences from Current Monitor

| Feature | Processing Monitor | Document View |
|---------|-------------------|---------------|
| **Data Source** | Status API (in-memory queue) | ChromaDB (persistent storage) |
| **Update Method** | WebSocket (real-time) | HTTP polling or static load |
| **Scope** | Active processing only | All stored documents |
| **Lifetime** | Temporary (until complete) | Permanent (until deleted) |
| **Primary Use** | Watch processing progress | Browse stored documents |
| **Endpoints** | `/status/queue`, `/status/{doc_id}` | `/documents`, `/documents/{doc_id}` |
| **Display** | Progress bars, logs, stats | Metadata, content, thumbnails |

### 5. Simplest MVP Implementation

**Phase 1: Minimal Document List**
1. Add `/documents` endpoint (single route)
2. Add "Documents" tab to monitor.html
3. Fetch on tab switch
4. Display simple table: filename, doc_id, page_count, chunk_count

**Phase 2: Document Details**
5. Add `/documents/{doc_id}` endpoint
6. Add modal/detail view
7. Show full metadata and text chunks

**Phase 3: Enhanced Features**
8. Search/filter functionality
9. Pagination (if >100 documents)
10. Delete functionality
11. Thumbnails/previews (if images stored)
12. Export metadata (JSON/CSV)

### 6. Optional Enhancements

**Search & Filter:**
- Full-text search across filenames
- Filter by date range
- Filter by document type (PDF, DOCX, etc.)

**Pagination:**
- Limit results to 50-100 per page
- Previous/Next navigation
- Jump to page

**Statistics:**
- Total storage size
- Documents by type
- Average pages per document
- Most recent uploads

**Thumbnails:**
- Show page 1 preview
- Hover to see more pages
- Click to zoom

**Export:**
- Download document list as CSV
- Export metadata as JSON
- Bulk operations

**Delete Operations:**
- Delete single document
- Bulk delete (select multiple)
- Confirmation dialog
- Undo feature (archive instead of delete)

---

## Implementation Checklist

### Backend
- [ ] Create `documents_api.py` router
- [ ] Implement `GET /documents` endpoint
- [ ] Implement `GET /documents/{doc_id}` endpoint
- [ ] Implement `GET /documents/{doc_id}/pages` endpoint
- [ ] Add ChromaClient integration
- [ ] Add aggregation logic for doc_id grouping
- [ ] Add error handling (404, 500)
- [ ] Add pagination support
- [ ] (Optional) Implement `DELETE /documents/{doc_id}`

### Frontend
- [ ] Add tab navigation HTML/CSS
- [ ] Add documents panel HTML structure
- [ ] Implement tab switching logic
- [ ] Implement document fetching on tab load
- [ ] Render document table
- [ ] Add search/filter UI
- [ ] Add sort functionality
- [ ] (Optional) Implement detail modal
- [ ] (Optional) Add delete confirmation dialog

### Integration
- [ ] Register documents router in FastAPI app
- [ ] Update CORS settings for /documents
- [ ] Test ChromaDB queries with real data
- [ ] Test pagination with large datasets
- [ ] Add logging for document queries
- [ ] Update monitoring documentation

### Testing
- [ ] Test with empty ChromaDB
- [ ] Test with 1 document
- [ ] Test with 100+ documents
- [ ] Test search/filter functionality
- [ ] Test delete functionality
- [ ] Test error cases (missing doc_id, etc.)

---

## Technical Considerations

### Performance
- ChromaDB `.get()` can be slow with 1000s of documents
- Consider caching document list with TTL
- Implement pagination early if expecting >100 docs
- Use database-level filtering where possible

### Data Consistency
- Document might be in processing queue AND storage
- Handle race condition: doc completes while viewing
- Refresh document list after processing completes

### UI/UX
- Keep WebSocket active for Processing tab
- Don't poll ChromaDB on Documents tab unless needed
- Show loading states during fetch
- Handle empty state gracefully
- Provide feedback for delete operations

### Security
- Validate doc_id format (prevent injection)
- Rate limit document queries
- Require confirmation for delete operations
- Log all delete operations

---

## Future Considerations

### Search Integration
- Add "Search Documents" tab using existing search engine
- Link from document view to search results
- Show search relevance scores

### Analytics
- Track document views
- Show most accessed documents
- Document usage statistics

### Version Control
- Track document updates (re-uploads)
- Show document history
- Compare versions

### Collaboration
- Document annotations
- Share document links
- Access control

---

## References

- Existing monitoring UI: `src/processing/static/monitor.html`
- Status API: `src/processing/status_api.py`
- ChromaDB client: `src/storage/chroma_client.py`
- Processing monitor module: `data/copyparty/www/modules/processing-monitor.js`
- Architecture docs: `docs/MONITORING.md`
