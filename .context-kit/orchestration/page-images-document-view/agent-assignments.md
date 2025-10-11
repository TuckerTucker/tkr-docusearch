# Agent Assignments: Page Images & Document View

**Orchestration Plan:** page-images-document-view
**Created:** 2025-10-11
**Total Agents:** 6

---

## Territorial Ownership Model

Each agent has exclusive ownership of specific files/directories. **No two agents modify the same file.**

### File Ownership Matrix

| Agent | Territory (Write Access) | Read-Only Access |
|-------|--------------------------|------------------|
| **infra-agent** | `src/config/image_config.py` (new)<br>`docker/docker-compose.yml` (modify)<br>`.gitignore` (modify)<br>`docs/IMAGE_STORAGE.md` (new) | All config files |
| **image-agent** | `src/processing/image_utils.py` (new)<br>`tests/test_image_utils.py` (new) | `src/config/image_config.py` |
| **storage-agent** | `src/storage/chroma_client.py` (modify)<br>`src/storage/test_storage.py` (modify) | `src/config/image_config.py` |
| **parser-agent** | `src/processing/docling_parser.py` (modify)<br>`src/processing/test_processing.py` (modify) | `src/processing/image_utils.py`<br>`src/config/image_config.py` |
| **visual-processor-agent** | `src/processing/visual_processor.py` (modify) | `src/processing/docling_parser.py`<br>`src/storage/chroma_client.py` |
| **api-agent** | `src/processing/documents_api.py` (new)<br>`src/processing/worker_webhook.py` (modify)<br>`tests/test_documents_api.py` (new) | `src/storage/chroma_client.py`<br>`src/config/image_config.py` |
| **ui-agent** | `src/processing/static/monitor.html` (modify) | API endpoints via HTTP |

---

## Agent Responsibilities

### infra-agent

**Wave:** 1 (Foundation)
**Role:** Infrastructure setup and configuration

**Responsibilities:**
1. Create `data/page_images/` directory structure
2. Update `.gitignore` with image directories
3. Add Docker volume mount for `/page_images`
4. Create `src/config/image_config.py` with all constants
5. Validate configuration on import
6. Document image storage architecture

**Deliverables:**
- `src/config/image_config.py` - Configuration module
- Modified `docker/docker-compose.yml` - Volume mounts
- Modified `.gitignore` - Excluded directories
- `docs/IMAGE_STORAGE.md` - Architecture documentation

**Dependencies:** None (foundation layer)

**Contract Compliance:**
- **Exports:** `image_config.py` to all agents
- **Validation:** Config validates on import
- **Testing:** 100% test coverage for config module

**Success Criteria:**
- ✅ `PAGE_IMAGE_DIR` exists and is writable
- ✅ Docker Compose validates with new volume
- ✅ Configuration imports without errors
- ✅ All constants documented

---

### image-agent

**Wave:** 1 (Foundation)
**Role:** Image storage utilities provider

**Responsibilities:**
1. Implement `save_page_image()` - Save full image + thumbnail
2. Implement `generate_thumbnail()` - Create thumbnails
3. Implement `get_image_path()` - Path construction
4. Implement `delete_document_images()` - Cleanup
5. Implement `image_exists()` - Existence check
6. Comprehensive error handling (disk full, permissions, etc.)
7. Unit tests for all functions (95%+ coverage)

**Deliverables:**
- `src/processing/image_utils.py` - Utility module (new file)
- `tests/test_image_utils.py` - Unit tests (new file)

**Dependencies:**
- **Imports:** `image_config` from infra-agent

**Contract Compliance:**
- **Imports:** `image_config.PAGE_IMAGE_DIR`, etc.
- **Exports:** All functions to parser-agent, api-agent
- **Errors:** Raises `ImageStorageError` on failures
- **Performance:** <500ms for save, <100ms for thumbnail

**Success Criteria:**
- ✅ All functions implemented and tested
- ✅ 95%+ test coverage
- ✅ Performance targets met
- ✅ Error handling comprehensive
- ✅ No memory leaks (tested with 1000 images)

---

### storage-agent

**Wave:** 1 (Foundation)
**Role:** ChromaDB schema extension

**Responsibilities:**
1. Update `add_visual_embedding()` signature
2. Add optional `image_path` parameter
3. Add optional `thumb_path` parameter
4. Include paths in metadata dict
5. Ensure backward compatibility (fields optional)
6. Update tests to verify path storage

**Deliverables:**
- Modified `src/storage/chroma_client.py`
- Modified `src/storage/test_storage.py`
- Migration notes for existing documents

**Dependencies:**
- **Imports:** `image_config` from infra-agent

**Contract Compliance:**
- **Exports:** Updated `add_visual_embedding()` to parser-agent
- **Schema:** `{image_path?: str, thumb_path?: str}`
- **Backward Compatible:** Paths are optional

**Success Criteria:**
- ✅ New parameters accepted (optional)
- ✅ Paths stored in metadata
- ✅ Existing tests still pass
- ✅ Backward compatibility verified

---

### parser-agent

**Wave:** 2 (Integration)
**Role:** Document processing pipeline integration

**Responsibilities:**
1. Update `Page` dataclass with `image_path`, `thumb_path` fields
2. Import `image_utils` module
3. Call `save_page_image()` during page extraction
4. Store returned paths in Page objects
5. Handle errors gracefully (log but don't fail)
6. Update tests for new fields

**Deliverables:**
- Modified `src/processing/docling_parser.py`
- Modified `src/processing/test_processing.py`

**Dependencies:**
- **Imports:** `image_utils.save_page_image()` from image-agent
- **Imports:** `image_config` from infra-agent

**Contract Compliance:**
- **Exports:** Updated `Page` dataclass to visual-processor-agent
- **Performance:** Image saving adds <10% to processing time
- **Error Handling:** Catches and logs errors, doesn't fail pipeline

**Success Criteria:**
- ✅ Images saved during processing
- ✅ Page objects contain paths
- ✅ Processing performance <10% overhead
- ✅ Errors logged but pipeline continues
- ✅ Tests validate image persistence

---

### visual-processor-agent

**Wave:** 2 (Integration)
**Role:** Pass image paths to storage layer

**Responsibilities:**
1. Extract `image_path` and `thumb_path` from Page objects
2. Pass paths to `chroma_client.add_visual_embedding()`
3. Update logging to include path info
4. Update tests

**Deliverables:**
- Modified `src/processing/visual_processor.py`

**Dependencies:**
- **Imports:** Updated `Page` from parser-agent
- **Calls:** Updated `add_visual_embedding()` from storage-agent

**Contract Compliance:**
- **Imports:** `Page` with new fields
- **Calls:** Storage layer with image paths
- **Testing:** Verify paths passed correctly

**Success Criteria:**
- ✅ Image paths extracted from Pages
- ✅ Paths passed to storage layer
- ✅ Tests verify correct data flow
- ✅ ChromaDB metadata includes paths

---

### api-agent

**Wave:** 3 (Backend API)
**Role:** HTTP endpoints for document querying and image serving

**Responsibilities:**

**Part A: Documents API**
1. Create `documents_api.py` with FastAPI router
2. Implement `GET /documents` (list with pagination, search, sort)
3. Implement `GET /documents/{doc_id}` (detailed view)
4. Implement `GET /images/{doc_id}/{filename}` (serve images)
5. Query ChromaDB for document aggregation
6. Add security: path traversal prevention
7. Add caching headers for images
8. Comprehensive error handling

**Part B: Integration**
9. Import router in `worker_webhook.py`
10. Configure CORS for new endpoints
11. Write API tests (95%+ coverage)

**Deliverables:**
- `src/processing/documents_api.py` (new file)
- Modified `src/processing/worker_webhook.py`
- `tests/test_documents_api.py` (new file)

**Dependencies:**
- **Imports:** `chroma_client` from storage-agent
- **Imports:** `image_config` from infra-agent

**Contract Compliance:**
- **Exports:** HTTP endpoints to ui-agent
- **API Schema:** See `03-documents-api.contract.md`
- **Security:** Path traversal prevented
- **Performance:** <100ms for list, <50ms for detail, <20ms for images

**Success Criteria:**
- ✅ All endpoints functional
- ✅ Pagination, search, sort working
- ✅ Images served correctly with caching
- ✅ Security audit passes (no path traversal)
- ✅ CORS configured correctly
- ✅ API tests pass (95%+ coverage)
- ✅ Performance targets met

---

### ui-agent

**Wave:** 4 (Frontend)
**Role:** Document browser UI in monitoring interface

**Responsibilities:**

**Part A: Tab Structure**
1. Add tab navigation HTML
2. Create Documents tab content area
3. Style tabs to match existing theme
4. Implement tab switching logic

**Part B: Document List**
5. Create documents table HTML
6. Add search and sort controls
7. Style to match monitor.html theme

**Part C: JavaScript Logic**
8. Implement `fetchDocuments()` (HTTP GET)
9. Implement `renderDocumentList()` (dynamic table)
10. Display thumbnails via `/images/` endpoint
11. Implement search filter (client-side)
12. Implement sort functionality
13. Handle errors (network, empty state, etc.)

**Deliverables:**
- Modified `src/processing/static/monitor.html`
- Screenshot of Documents tab

**Dependencies:**
- **Calls:** API endpoints from api-agent (HTTP only)

**Contract Compliance:**
- **API Calls:** Uses documented endpoints
- **UI Design:** Matches existing monitor theme
- **Browser Support:** Chrome, Firefox, Safari

**Success Criteria:**
- ✅ Documents tab visible and functional
- ✅ List displays with real data
- ✅ Thumbnails load correctly
- ✅ Search and sort work
- ✅ No console errors
- ✅ Works in Chrome, Firefox, Safari
- ✅ Mobile responsive (basic)

---

## Communication Protocol

### Status Updates

Each agent must update their status:
- **In Progress:** When starting a task
- **Completed:** When task fully done and tested
- **Blocked:** When waiting on another agent

### Blocker Format

```
🚧 BLOCKED: waiting for image_utils.save_page_image()
Blocker: image-agent must complete Wave 1
Estimated unblock: 2 hours
```

### Code Review

**Cross-agent reviews:**
- parser-agent reviews image-agent's `image_utils.py`
- visual-processor-agent reviews parser-agent's `Page` changes
- ui-agent reviews api-agent's API responses
- api-agent reviews storage-agent's metadata schema

**Review checklist:**
- [ ] Contract compliance verified
- [ ] Error handling adequate
- [ ] Tests cover edge cases
- [ ] Performance acceptable
- [ ] Documentation clear

---

## Integration Testing

### Wave 1 Gate Test (by all agents)
```bash
# Test imports
python -c "from src.config.image_config import PAGE_IMAGE_DIR; print(PAGE_IMAGE_DIR)"
python -c "from src.processing.image_utils import save_page_image"

# Test config validation
pytest tests/test_image_utils.py -v
pytest src/storage/test_storage.py -v
```

### Wave 2 Gate Test (by parser + storage agents)
```bash
# Upload test document and verify images saved
curl -X POST -F "file=@test.pdf" http://localhost:8000/upload
ls data/page_images/  # Should see new doc_id directory

# Query ChromaDB and verify metadata has image_path
python -c "from src.storage.chroma_client import ChromaClient; ..."
```

### Wave 3 Gate Test (by api-agent)
```bash
# Test API endpoints
curl http://localhost:8002/documents
curl http://localhost:8002/documents/{doc_id}
curl http://localhost:8002/images/{doc_id}/page001_thumb.jpg
```

### Wave 4 Gate Test (by ui-agent)
```
# Open in browser
open http://localhost:8002/monitor
# Click Documents tab
# Verify list loads
# Verify thumbnails display
# Test search and sort
```

---

## Rollback Procedures

If Wave 2 fails:
1. **parser-agent:** Revert `docling_parser.py` changes
2. **visual-processor-agent:** Revert `visual_processor.py` changes
3. Keep Wave 1 (infra + utilities) - harmless to leave

If Wave 3 fails:
1. **api-agent:** Remove `documents_api.py`, revert `worker_webhook.py`
2. Keep Wave 1+2 (images still being saved)

If Wave 4 fails:
1. **ui-agent:** Revert `monitor.html` changes
2. API still functional for future UI attempt

---

**Document Version:** 1.0
**Last Updated:** 2025-10-11
