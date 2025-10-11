# Page Images & Document View Orchestration Plan

**Feature Goal:** Implement page image persistence during document processing and create a document browser tab in the monitoring UI

**Created:** 2025-10-11
**Status:** Planning
**Max Agents:** 6

---

## Executive Summary

This orchestration plan coordinates 6 specialized agents to implement page image persistence and a document viewing interface. The implementation is organized into 4 waves with clear synchronization gates to ensure zero-conflict integration.

### Key Objectives
1. Persist page images during document processing (currently discarded)
2. Generate thumbnails for efficient UI display
3. Create document browser API endpoints
4. Build document view tab in monitoring UI
5. Maintain <10% processing performance impact
6. Ensure backward compatibility with existing documents

### Success Criteria
- ✅ Page images saved to `data/page_images/{doc_id}/`
- ✅ Thumbnails generated (300x400px JPEG)
- ✅ ChromaDB metadata includes image paths
- ✅ `/documents` API returns paginated document list
- ✅ `/images/{doc_id}/{filename}` serves images
- ✅ Monitor UI has functional Documents tab
- ✅ All existing tests pass
- ✅ Integration tests validate end-to-end flow

---

## Components Analysis

### Component Breakdown

| Component | Agent | Territory | Key Deliverables |
|-----------|-------|-----------|------------------|
| **Infrastructure** | infra-agent | `src/config/`, `data/`, Docker files | Config constants, directory setup, volume mounts |
| **Image Utilities** | image-agent | `src/processing/image_utils.py` | Save, thumbnail, retrieve, delete operations |
| **Parser Integration** | parser-agent | `src/processing/docling_parser.py` | Save images during page extraction |
| **Storage Schema** | storage-agent | `src/storage/chroma_client.py` | Add image_path/thumb_path fields |
| **API Endpoints** | api-agent | `src/processing/documents_api.py`, `src/processing/worker_webhook.py` | `/documents`, `/documents/{id}`, `/images` |
| **Frontend UI** | ui-agent | `src/processing/static/monitor.html` | Documents tab, list rendering, thumbnails |

### Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                     Upload Pipeline                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Parser Agent: Extract pages & Save images                  │
│  ├─ Uses: image_utils.save_page_image()                     │
│  └─ Produces: Page(image_path=..., thumb_path=...)          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Storage Agent: Store metadata with image paths             │
│  └─ ChromaDB: {doc_id, page, image_path, thumb_path, ...}   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  API Agent: Query & serve documents                          │
│  ├─ GET /documents → list with metadata                     │
│  ├─ GET /documents/{id} → detailed view                     │
│  └─ GET /images/{id}/{file} → serve PNG/JPG                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  UI Agent: Display documents with thumbnails                │
│  └─ <img src="/images/{id}/page001_thumb.jpg">              │
└─────────────────────────────────────────────────────────────┘
```

---

## Wave Execution Plan

### Wave 0: Foundation & Contracts (Sequential)

**Duration:** Setup phase (no coding)
**Agents:** All (review contracts)
**Objective:** Establish shared specifications and territorial boundaries

**Deliverables:**
- ✅ Integration contracts defined (see `integration-contracts/`)
- ✅ Agent assignments documented
- ✅ Validation strategy agreed upon
- ✅ Coordination protocol established

**Synchronization Gate:** All agents acknowledge contracts

---

### Wave 1: Infrastructure & Core Utilities (Parallel: 3 agents)

**Prerequisites:** Wave 0 complete
**Objective:** Set up infrastructure and create foundational utilities

#### Agent: infra-agent
**Territory:** `src/config/`, `data/`, `docker/`, `.gitignore`

**Tasks:**
1. Create `data/page_images/` directory
2. Add to `.gitignore`: `data/page_images/`, `data/markdown/`
3. Update `docker/docker-compose.yml`: Add volume mount `../data/page_images:/page_images`
4. Create `src/config/image_config.py` with constants:
   - `PAGE_IMAGE_DIR`
   - `THUMBNAIL_SIZE = (300, 400)`
   - `THUMBNAIL_QUALITY = 85`
   - `IMAGE_FORMAT = "PNG"`
   - `THUMBNAIL_FORMAT = "JPEG"`

**Deliverables:**
- `src/config/image_config.py` (new file)
- Updated `docker/docker-compose.yml`
- Updated `.gitignore`
- Documentation in `docs/IMAGE_STORAGE.md`

**Contract Compliance:**
- Exports: `image_config.py` → All agents
- Configuration validation on import

#### Agent: image-agent
**Territory:** `src/processing/image_utils.py` (new file)

**Tasks:**
1. Implement `save_page_image(page: Page, doc_id: str, page_num: int) -> tuple[str, str]`
   - Save full PNG to `{PAGE_IMAGE_DIR}/{doc_id}/page{num:03d}.png`
   - Generate thumbnail to `{PAGE_IMAGE_DIR}/{doc_id}/page{num:03d}_thumb.jpg`
   - Return `(image_path, thumb_path)`
   - Handle errors: disk full, permissions, PIL errors
2. Implement `generate_thumbnail(image: PIL.Image, size: tuple, quality: int) -> PIL.Image`
3. Implement `get_image_path(doc_id: str, page_num: int, is_thumb: bool) -> str`
4. Implement `delete_document_images(doc_id: str) -> int` (returns count deleted)
5. Add comprehensive error handling and logging

**Deliverables:**
- `src/processing/image_utils.py` (new file)
- Unit tests: `tests/test_image_utils.py`
- Error handling for all edge cases

**Contract Compliance:**
- Imports: `image_config.py`
- Exports: All functions to parser-agent, api-agent
- Error contract: Raises `ImageStorageError` on failures

#### Agent: storage-agent
**Territory:** `src/storage/chroma_client.py` (modify existing)

**Tasks:**
1. Update `add_visual_embedding()` signature:
   - Add optional parameters: `image_path: Optional[str] = None`
   - Add optional parameters: `thumb_path: Optional[str] = None`
2. Include paths in metadata dict (if provided)
3. Update docstrings and type hints
4. Ensure backward compatibility (paths are optional)
5. Update tests to verify path storage

**Deliverables:**
- Modified `src/storage/chroma_client.py`
- Updated tests in `src/storage/test_storage.py`
- Migration notes for existing documents

**Contract Compliance:**
- Exports: Updated `add_visual_embedding()` to parser-agent
- Schema contract: `{image_path?: str, thumb_path?: str}`

**Synchronization Gate: Wave 1 Complete**
- ✅ `image_config.py` imports successfully
- ✅ `image_utils.py` unit tests pass (90%+ coverage)
- ✅ `chroma_client.py` tests pass (including new fields)
- ✅ No import errors across any modified files
- ✅ Docker compose validates (`docker-compose config`)

---

### Wave 2: Processing Integration (Parallel: 2 agents)

**Prerequisites:** Wave 1 complete
**Objective:** Integrate image persistence into document processing pipeline

#### Agent: parser-agent
**Territory:** `src/processing/docling_parser.py` (modify existing)

**Tasks:**
1. Import `image_utils` at top of file
2. Update `Page` dataclass:
   - Add `image_path: Optional[str] = None`
   - Add `thumb_path: Optional[str] = None`
3. Modify `_extract_pages_from_result()`:
   - After creating PIL image from `page.get_image()`
   - Call `save_page_image(page, doc_id, page_num)`
   - Store returned paths in Page object
   - Wrap in try/except, log errors but don't fail processing
4. Handle text-only documents (image_path stays None)
5. Add logging: "Saved page image: {image_path}"

**Deliverables:**
- Modified `src/processing/docling_parser.py`
- Updated tests in `src/processing/test_processing.py`
- Integration test verifying images are saved

**Contract Compliance:**
- Imports: `image_utils.save_page_image()`, `image_config`
- Exports: Updated `Page` dataclass to visual_processor
- Performance: Image saving adds <10% to processing time

#### Agent: visual-processor-integration-agent
**Territory:** `src/processing/visual_processor.py` (modify existing)

**Tasks:**
1. Update `process_pages()` to extract image paths from Page objects
2. Pass `image_path` and `thumb_path` to storage layer
3. Modify call to `chroma_client.add_visual_embedding()`:
   - Include `image_path=page.image_path`
   - Include `thumb_path=page.thumb_path`
4. Update logging to include image path info
5. Update tests to verify paths passed correctly

**Deliverables:**
- Modified `src/processing/visual_processor.py`
- Updated tests

**Contract Compliance:**
- Imports: Updated `Page` from parser-agent
- Calls: Updated `add_visual_embedding()` from storage-agent

**Synchronization Gate: Wave 2 Complete**
- ✅ End-to-end test: Upload PDF → Images saved to disk
- ✅ ChromaDB metadata includes `image_path` and `thumb_path`
- ✅ Existing tests still pass (backward compatibility)
- ✅ Performance test: Processing time increase <10%
- ✅ No disk space leaks (images in correct location)

---

### Wave 3: Backend API (Parallel: 1 agent)

**Prerequisites:** Wave 2 complete (images being saved)
**Objective:** Create HTTP endpoints to query documents and serve images

#### Agent: api-agent
**Territory:** `src/processing/documents_api.py` (new file), `src/processing/worker_webhook.py` (modify)

**Tasks:**

**Part A: Create documents_api.py**
1. Create FastAPI router with prefix `/documents`
2. Implement `GET /documents`:
   - Query ChromaDB visual + text collections
   - Extract unique doc_ids
   - Aggregate by doc_id: {filename, page_count, chunk_count, date_added}
   - Support pagination: `?limit=50&offset=0`
   - Support search: `?search=filename`
   - Support sort: `?sort_by=date_added` (date_added, filename, page_count)
   - Return `{documents: [...], total: int, limit: int, offset: int}`
3. Implement `GET /documents/{doc_id}`:
   - Query ChromaDB for specific doc_id
   - Return full metadata including all pages and chunks
   - Include `image_paths` and `thumb_paths` arrays
   - Return 404 if not found
4. Implement `GET /images/{doc_id}/{filename}`:
   - Validate doc_id format (prevent path traversal)
   - Serve file from `PAGE_IMAGE_DIR/{doc_id}/{filename}`
   - Set Content-Type: image/png or image/jpeg
   - Set Cache-Control: max-age=86400 (24 hours)
   - Return 404 if file missing
   - Add security: Only serve .png, .jpg files
5. Add comprehensive error handling and logging

**Part B: Integrate into worker_webhook.py**
6. Import `documents_api.router`
7. Add `app.include_router(documents_api.router)`
8. Ensure CORS allows `/documents` and `/images` endpoints

**Deliverables:**
- `src/processing/documents_api.py` (new file)
- Modified `src/processing/worker_webhook.py`
- API tests: `tests/test_documents_api.py`
- OpenAPI schema validation

**Contract Compliance:**
- Imports: `chroma_client`, `image_config`
- Exports: HTTP endpoints to ui-agent
- API contract: See `integration-contracts/documents-api.contract.md`

**Synchronization Gate: Wave 3 Complete**
- ✅ `GET /documents` returns valid JSON (manual curl test)
- ✅ `GET /documents/{doc_id}` returns document details
- ✅ `GET /images/{doc_id}/page001_thumb.jpg` serves image
- ✅ 404 responses for missing documents/images
- ✅ API tests pass (95%+ coverage)
- ✅ No security vulnerabilities (path traversal prevented)
- ✅ CORS headers correct (browser console check)

---

### Wave 4: Frontend UI (Parallel: 1 agent)

**Prerequisites:** Wave 3 complete (API functional)
**Objective:** Build document browser tab in monitoring UI

#### Agent: ui-agent
**Territory:** `src/processing/static/monitor.html` (modify existing)

**Tasks:**

**Part A: Tab Structure**
1. Add tab navigation HTML after header:
   ```html
   <div class="tabs">
     <button class="tab-button active" data-tab="processing">Processing</button>
     <button class="tab-button" data-tab="documents">Documents</button>
   </div>
   ```
2. Wrap existing content in `<div id="processing-view" class="tab-content active">`
3. Add new `<div id="documents-view" class="tab-content hidden">`
4. Add CSS for tabs (active state, hover effects)
5. Implement `switchTab(tabName)` JavaScript function

**Part B: Documents List UI**
6. Create documents table HTML in `#documents-view`:
   - Columns: Thumbnail, Filename, Doc ID, Pages, Chunks, Date
   - Search input field
   - Sort dropdown
   - Empty state message
7. Style table to match existing monitor theme

**Part C: JavaScript Logic**
8. Implement `fetchDocuments()`:
   - Call `GET /documents?limit=50`
   - Parse JSON response
   - Handle errors gracefully
   - Cache for 30 seconds
9. Implement `renderDocumentList(documents)`:
   - Generate table rows dynamically
   - Display thumbnails: `<img src="/images/{doc_id}/page001_thumb.jpg">`
   - Handle missing thumbnails (show placeholder icon)
   - Truncate doc_ids (first 8 chars with tooltip)
   - Format dates as relative time ("2 hours ago")
10. Implement search filter (client-side, case-insensitive)
11. Implement sort functionality (date, name, pages)
12. Call `fetchDocuments()` when Documents tab is clicked

**Part D: Error Handling**
13. Handle network errors (show retry button)
14. Handle empty state (no documents yet)
15. Handle slow loading (show spinner)

**Deliverables:**
- Modified `src/processing/static/monitor.html`
- Screenshot of Documents tab
- Browser compatibility testing (Chrome, Firefox, Safari)

**Contract Compliance:**
- Calls: API endpoints from api-agent
- UI contract: See `integration-contracts/ui-design.contract.md`

**Synchronization Gate: Wave 4 Complete**
- ✅ Documents tab visible in browser
- ✅ List displays correctly with real data
- ✅ Thumbnails load and display
- ✅ Search functionality works
- ✅ Sort functionality works
- ✅ No console errors
- ✅ Works in Chrome, Firefox, Safari
- ✅ Mobile responsive (basic test)

---

## Final Validation (All Agents)

**Objective:** End-to-end integration testing and validation

### Integration Tests
1. **Full Pipeline Test:**
   - Upload new PDF document
   - Verify images saved to disk
   - Verify ChromaDB has metadata
   - Verify API returns document
   - Verify UI displays document with thumbnail

2. **Backward Compatibility Test:**
   - Query existing documents (without image paths)
   - Verify API handles gracefully (null paths)
   - Verify UI shows placeholder for missing thumbnails

3. **Performance Test:**
   - Process 10 documents (50 pages total)
   - Measure total processing time vs baseline
   - Verify <10% overhead

4. **Error Handling Test:**
   - Simulate disk full (small Docker volume)
   - Simulate permission errors
   - Verify graceful degradation (processing continues)

5. **Cross-Browser Test:**
   - Test Documents tab in Chrome, Firefox, Safari
   - Verify images load correctly
   - Verify no console errors

### Success Criteria Checklist
- [ ] All Wave gates passed
- [ ] All integration tests pass
- [ ] All unit tests pass (95%+ coverage)
- [ ] No performance regression (>10%)
- [ ] Backward compatible with existing documents
- [ ] Documentation updated
- [ ] No security vulnerabilities
- [ ] Production-ready

---

## Risk Management

### Identified Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Disk space exhaustion | Medium | High | Add disk usage monitoring, cleanup old images |
| Processing performance impact | Medium | Medium | Async image saving, optimize thumbnail generation |
| Path traversal vulnerability | Low | Critical | Strict doc_id validation, whitelist file extensions |
| Backward compatibility break | Low | High | Optional fields, null checks, migration path |
| Large document memory issues | Medium | Medium | Batch processing, stream image saves |

### Rollback Procedure
1. Revert parser-agent changes (stop saving images)
2. Revert UI changes (hide Documents tab)
3. Revert API changes (remove endpoints)
4. Keep infrastructure (harmless to leave in place)
5. Document rollback reason for future attempt

---

## Communication Protocol

### Status Updates
Each agent must update status after each task:
- ✅ Task complete
- 🚧 Task in progress
- ❌ Task blocked (with blocker description)

### Blocker Resolution
If blocked:
1. Document blocker in status update
2. Tag blocking agent
3. Escalate if unresolved in 1 hour

### Code Review Process
1. Consumer agents review provider code (API reviews backend, etc.)
2. Review checklist:
   - Contract compliance verified
   - Error handling adequate
   - Tests cover edge cases
   - Performance acceptable
   - Documentation clear

---

## Appendix

### Technology Stack
- **Backend:** Python 3.13, FastAPI, ChromaDB
- **Image Processing:** Pillow (PIL), Docling
- **Frontend:** Vanilla JavaScript, HTML5, CSS3
- **Storage:** Filesystem (data/page_images/)
- **Deployment:** Docker Compose

### File Ownership Map
```
infra-agent:
  - src/config/image_config.py
  - docker/docker-compose.yml
  - .gitignore
  - docs/IMAGE_STORAGE.md

image-agent:
  - src/processing/image_utils.py
  - tests/test_image_utils.py

storage-agent:
  - src/storage/chroma_client.py (modify)
  - src/storage/test_storage.py (modify)

parser-agent:
  - src/processing/docling_parser.py (modify)
  - src/processing/test_processing.py (modify)

visual-processor-agent:
  - src/processing/visual_processor.py (modify)

api-agent:
  - src/processing/documents_api.py
  - src/processing/worker_webhook.py (modify)
  - tests/test_documents_api.py

ui-agent:
  - src/processing/static/monitor.html (modify)
```

### Dependencies Graph
```
infra-agent (image_config.py)
    │
    ├─> image-agent (image_utils.py)
    │       │
    │       └─> parser-agent (docling_parser.py)
    │               │
    │               └─> visual-processor-agent (visual_processor.py)
    │                       │
    │                       └─> storage-agent (chroma_client.py)
    │
    └─> api-agent (documents_api.py)
            │
            └─> ui-agent (monitor.html)
```

---

**Plan Version:** 1.0
**Last Updated:** 2025-10-11
**Next Review:** After Wave 2 completion
