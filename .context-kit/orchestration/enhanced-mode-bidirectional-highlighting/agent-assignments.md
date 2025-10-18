# Agent Territory Assignments

**Project**: Enhanced Mode Bidirectional Highlighting
**Last Updated**: 2025-10-17

---

## Territorial Ownership Map

### Principle: Zero Overlap
Each agent has **exclusive ownership** of specific files and directories. No two agents modify the same file. When integration requires shared data, agents communicate through **interface contracts** only.

---

## Wave 1: Foundation (3 Agents)

### Agent 1: Docling Structure Validator
**Status**: Ready to Start
**Dependencies**: None

**Owned Files** (NEW):
```
tests/integration/test_docling_structure.py
integration-contracts/docling-structure-spec.md
```

**Responsibilities**:
1. Create integration test validating Docling extracts DocumentStructure
2. Test bbox coordinate format matches specification
3. Verify structure flows from Docling → Processor
4. Document bbox coordinate system (origin, scaling, units)
5. Generate sample structure JSON for other agents' tests

**Success Criteria**:
- Test passes: Docling returns DocumentStructure with bboxes
- Sample data created in `integration-contracts/sample-structure.json`
- Coordinate system documented
- No blockers for Wave 2 agents

---

### Agent 2: ChromaDB Schema Architect
**Status**: Ready to Start
**Dependencies**: None

**Owned Files** (NEW):
```
integration-contracts/chromadb-metadata-schema.md
integration-contracts/sample-metadata-visual.json
integration-contracts/sample-metadata-text.json
```

**Responsibilities**:
1. Complete ChromaDB metadata schema specification
2. Define compression strategy for DocumentStructure
3. Define flat metadata schema for ChunkContext
4. Create validation functions specification
5. Generate sample metadata for testing

**Success Criteria**:
- Schema spec complete and approved
- Sample metadata JSON files created
- Validation rules documented
- No ambiguities for storage agents

---

### Agent 3: API Contract Designer
**Status**: Ready to Start
**Dependencies**: None

**Owned Files** (NEW):
```
integration-contracts/api-contracts.md
integration-contracts/sample-api-responses.json
integration-contracts/coordinate-system-spec.md
```

**Responsibilities**:
1. Complete API contract specification
2. Define request/response schemas for all endpoints
3. Document bbox coordinate system for frontend
4. Define URL parameter contracts
5. Create sample API responses for testing

**Success Criteria**:
- API contracts complete and approved
- Sample responses created
- OpenAPI/Swagger spec generated (optional)
- No ambiguities for backend/frontend agents

---

## Wave 2: Backend Implementation (4 Agents)

### Agent 4: Enhanced Storage Enabler
**Status**: Waiting for Wave 1
**Dependencies**: Agent 2 (ChromaDB schema)

**Owned Files** (MODIFY):
```
src/processing/handlers/visual_embedding_handler.py
src/processing/handlers/text_embedding_handler.py
```

**Owned Files** (NEW):
```
src/processing/handlers/enhanced_metadata.py
tests/integration/test_enhanced_storage.py
tests/integration/test_page_chunk_mapping.py
```

**Boundaries**:
- ✅ Modify handler files to call enhanced metadata functions
- ✅ Create new helper module for enhanced metadata logic
- ❌ Do NOT modify `chroma_client.py` (already has needed functions)
- ❌ Do NOT modify `metadata_schema.py` (schema already defined)

**Responsibilities**:
1. Create `enhanced_metadata.py` helper module
2. Modify visual handler to call `_prepare_enhanced_visual_metadata()`
3. Modify text handler to call `_prepare_enhanced_text_metadata()`
4. Add page→chunk mapping logic
5. Integration tests validating storage

**Success Criteria**:
- Process test document with enhanced mode enabled
- Query ChromaDB confirms bboxes stored in visual collection
- Query confirms section_path in text collection
- Page→chunk query returns correct chunks
- All tests pass

---

### Agent 5: Structure API Builder
**Status**: Waiting for Wave 1
**Dependencies**: Agent 3 (API contracts), Agent 2 (ChromaDB schema)

**Owned Files** (NEW):
```
src/processing/api/structure_endpoints.py
tests/api/test_structure_api.py
tests/api/test_chunk_api.py
```

**Boundaries**:
- ✅ Create new module for structure/chunk endpoints
- ✅ Import endpoints into `documents_api.py` via router
- ❌ Do NOT directly modify existing endpoints in `documents_api.py`
- ✅ Use dependency injection for ChromaClient

**Responsibilities**:
1. Implement `GET /documents/{doc_id}/pages/{page}/structure`
2. Implement `GET /documents/{doc_id}/chunks/{chunk_id}`
3. Decompress structure from ChromaDB metadata
4. Return JSON per API contract
5. Unit and integration tests

**Success Criteria**:
- Endpoints return data matching API contract
- Response schemas validated with sample data
- Error handling tested (404s, invalid params)
- Integration tests with real ChromaDB pass

---

### Agent 6: Research Context Enhancer
**Status**: Waiting for Wave 1
**Dependencies**: Agent 3 (API contracts)

**Owned Files** (MODIFY):
```
src/research/context_builder.py (get_source_metadata only)
```

**Owned Files** (NEW):
```
src/research/chunk_extractor.py
tests/research/test_chunk_context.py
tests/research/test_research_chunk_id.py
```

**Boundaries**:
- ✅ Modify `get_source_metadata()` to extract chunk_id
- ✅ Create new module for chunk extraction logic
- ❌ Do NOT modify other context_builder methods
- ❌ Do NOT modify types.py (Agent will do that separately)

**Responsibilities**:
1. Add `chunk_id` field to SourceDocument dataclass
2. Create chunk extraction module
3. Modify `get_source_metadata()` to extract chunk_id from ChromaDB
4. Handle visual (no chunk_id) vs text (has chunk_id) results
5. Backward compatibility tests

**Success Criteria**:
- SourceDocument has optional chunk_id field
- Research API returns chunk_id for text search results
- Visual-only search works (chunk_id=null)
- Existing research tests still pass

---

### Agent 7: Markdown Chunker
**Status**: Waiting for Wave 1
**Dependencies**: Agent 3 (API contracts), Agent 2 (ChromaDB schema)

**Owned Files** (NEW):
```
src/storage/markdown_chunking.py
tests/storage/test_markdown_chunks.py
tests/storage/test_chunk_markers.py
```

**Owned Files** (MODIFY):
```
src/processing/documents_api.py (markdown endpoint only)
```

**Boundaries**:
- ✅ Create new module for markdown chunking logic
- ✅ Modify ONLY the `/documents/{doc_id}/markdown` endpoint
- ❌ Do NOT modify other documents_api endpoints
- ✅ Import chunking logic from new module

**Responsibilities**:
1. Create markdown chunking module
2. Function: `insert_chunk_markers(markdown, chunks)`
3. Format: `<!-- chunk:{id} page:{n} section:"{path}" -->`
4. Wrap chunks in `<div data-chunk-id="...">`
5. Update markdown endpoint to use chunking

**Success Criteria**:
- Markdown includes valid chunk markers
- Markers don't break markdown rendering
- Chunk IDs correspond to ChromaDB records
- Tests validate marker format

---

## Wave 3: Frontend Implementation (4 Agents)

### Agent 8: BoundingBox Overlay Component
**Status**: Waiting for Wave 2
**Dependencies**: Agent 5 (Structure API), Agent 3 (API contracts)

**Owned Files** (NEW):
```
src/frontend/bounding-box-overlay.js
src/frontend/styles/bounding-box-overlay.css
src/frontend/utils/coordinate-scaler.js
tests/frontend/test-bbox-overlay.html
```

**Boundaries**:
- ✅ Create entirely new component (no shared files)
- ✅ Standalone SVG overlay implementation
- ❌ Do NOT modify existing frontend components
- ✅ Provide clean API for integration

**Responsibilities**:
1. Create BoundingBoxOverlay class
2. SVG rendering over page images
3. Coordinate scaling for responsive display
4. Hover and click event handlers
5. CSS for visual feedback

**Component API**:
```javascript
class BoundingBoxOverlay {
  constructor(imageElement, bboxes, options)
  render()
  highlightBbox(chunkId, isPermanent)
  clearHighlight()
  onBboxClick(callback)
  onBboxHover(callback)
  destroy()
}
```

**Success Criteria**:
- Bboxes render correctly over images
- Coordinates scale with responsive images
- Click/hover events fire correctly
- Visual states (hover, active) work
- Standalone test page validates component

---

### Agent 9: Details Page Integration
**Status**: Waiting for Wave 2
**Dependencies**: Agent 8 (BBoxOverlay), Agent 5 (Structure API), Agent 7 (Markdown chunking)

**Owned Files** (NEW):
```
src/frontend/details-controller.js
src/frontend/chunk-highlighter.js
src/frontend/url-params.js
tests/frontend/test-details-integration.html
```

**Owned Files** (MODIFY):
```
src/frontend/details.html (add script tags and overlay container)
```

**Boundaries**:
- ✅ Create new controller modules
- ✅ Minimal modification to details.html (add containers/scripts)
- ❌ Do NOT modify slideshow.js directly
- ✅ Use composition to integrate with existing components

**Responsibilities**:
1. Create details-controller.js (orchestrates page)
2. Create chunk-highlighter.js (markdown highlighting)
3. Create url-params.js (parse query params)
4. Initialize BoundingBoxOverlay
5. Implement bidirectional highlighting

**Integration Flow**:
```javascript
// details-controller.js
import { BoundingBoxOverlay } from './bounding-box-overlay.js';
import { ChunkHighlighter } from './chunk-highlighter.js';
import { parseURLParams } from './url-params.js';

class DetailsController {
  async init() {
    const params = parseURLParams();
    const structure = await fetchStructure(params.doc_id, params.page);
    this.overlay = new BoundingBoxOverlay(imageEl, structure.bboxes);
    this.highlighter = new ChunkHighlighter(markdownEl);

    if (params.chunk) {
      await this.navigateToChunk(params.chunk);
    }
  }
}
```

**Success Criteria**:
- Page loads with structure overlay
- URL params trigger navigation
- Click bbox scrolls to chunk
- Hover chunk highlights bbox
- State synchronized

---

### Agent 10: Research Navigation Enhancer
**Status**: Waiting for Wave 2
**Dependencies**: Agent 6 (Research chunk_id), Agent 9 (Details URL params)

**Owned Files** (MODIFY):
```
src/frontend/reference-card.js (createReferenceCard function only)
```

**Owned Files** (NEW):
```
src/frontend/utils/url-builder.js
tests/frontend/test-research-navigation.html
```

**Boundaries**:
- ✅ Modify ONLY the link generation in reference-card.js
- ✅ Create new module for URL building logic
- ❌ Do NOT modify other reference-card functions
- ❌ Do NOT modify research-controller.js

**Responsibilities**:
1. Create URL builder module
2. Extract chunk_id from source data
3. Build details URL with chunk parameter
4. Add visual indicator for chunk availability
5. Backward compatibility (no chunk_id)

**URL Building**:
```javascript
// url-builder.js
export function buildDetailsURL(source) {
  const params = new URLSearchParams({
    id: source.doc_id,
    page: source.page
  });

  if (source.chunk_id) {
    params.set('chunk', source.chunk_id);
  }

  return `/frontend/details.html?${params.toString()}`;
}
```

**Success Criteria**:
- Links include chunk_id when available
- Links work without chunk_id
- Visual indicator shows chunk context
- Navigation triggers highlighting

---

### Agent 11: Accessibility & Polish
**Status**: Waiting for Wave 3 (Agents 8, 9, 10)
**Dependencies**: Agents 8, 9, 10

**Owned Files** (NEW):
```
src/frontend/accessibility/keyboard-nav.js
src/frontend/accessibility/aria-labels.js
src/frontend/accessibility/screen-reader-announce.js
src/frontend/styles/highlighting-animations.css
src/frontend/styles/accessibility.css
tests/accessibility/test-keyboard-nav.html
tests/accessibility/test-screen-reader.html
```

**Boundaries**:
- ✅ Create entirely new accessibility modules
- ✅ Provide hooks for other components to use
- ❌ Do NOT modify other agents' files
- ✅ CSS-only enhancements where possible

**Responsibilities**:
1. Keyboard navigation module
2. ARIA labeling module
3. Screen reader announcements
4. Animation CSS
5. Focus management

**Integration Pattern**:
```javascript
// Other agents import and use
import { enableKeyboardNav } from './accessibility/keyboard-nav.js';
import { announceChunkNav } from './accessibility/screen-reader-announce.js';

// In details-controller.js
enableKeyboardNav(this.highlighter, this.overlay);

// On chunk navigation
announceChunkNav(chunk.parent_heading, chunk.page);
```

**Success Criteria**:
- Keyboard-only navigation works
- WCAG AA compliance verified
- Screen reader testing passes
- No focus traps
- Smooth animations

---

## Wave 4: Integration & QA (3 Agents)

### Agent 12: Integration Test Suite
**Status**: Waiting for Wave 3
**Dependencies**: All previous agents

**Owned Files** (NEW):
```
tests/e2e/test_enhanced_mode_e2e.py
tests/e2e/test_research_to_details_flow.py
tests/e2e/test_bidirectional_highlighting.py
tests/e2e/fixtures/sample_documents/
scripts/run_e2e_tests.sh
```

**Boundaries**:
- ✅ Create entirely new test files
- ✅ No modification to production code
- ✅ May create test fixtures and helpers
- ❌ Do NOT fix bugs (report to responsible agent)

**Responsibilities**:
1. E2E test: Research → Details → Highlight
2. E2E test: Click bbox → Scroll to chunk
3. E2E test: Hover chunk → Highlight bbox
4. Test multiple document types
5. Test edge cases

**Success Criteria**:
- All E2E scenarios pass
- Coverage ≥80% for new code
- No regressions detected
- Bug reports filed with responsible agents

---

### Agent 13: Performance Optimizer
**Status**: Waiting for Wave 3
**Dependencies**: All Wave 3 agents

**Owned Files** (NEW):
```
src/frontend/performance/lazy-loader.js
src/frontend/performance/debounce.js
src/frontend/performance/cache-manager.js
src/frontend/performance/metrics.js
scripts/benchmark_performance.js
```

**Boundaries**:
- ✅ Create new performance utility modules
- ✅ Provide hooks for other components
- ❌ Do NOT modify other agents' core logic
- ✅ CSS optimizations via new files

**Responsibilities**:
1. Lazy loading for structure data
2. Debounce utilities for hover handlers
3. Cache manager for structure data
4. Performance metrics collection
5. Optimization recommendations

**Success Criteria**:
- Initial load <500ms
- Hover response <16ms (60fps)
- Memory <10MB additional
- Lighthouse score ≥90

---

### Agent 14: Documentation & Migration
**Status**: Waiting for Wave 3
**Dependencies**: All previous work

**Owned Files** (NEW):
```
docs/ENHANCED_MODE.md
docs/BIDIRECTIONAL_HIGHLIGHTING.md
docs/API_ENHANCED_ENDPOINTS.md
docs/DEVELOPER_GUIDE_BBOX.md
scripts/migrate_enhanced_mode.py
scripts/validate_migration.py
```

**Owned Files** (MODIFY):
```
docs/API_REFERENCE.md (append new endpoints)
README.md (add enhanced mode section)
```

**Boundaries**:
- ✅ Create new documentation files
- ✅ Minimal updates to existing docs (append only)
- ✅ Create migration scripts
- ❌ Do NOT modify production code

**Responsibilities**:
1. Enhanced mode configuration guide
2. User guide with screenshots
3. API documentation updates
4. Developer bbox coordinate guide
5. Migration script with options

**Success Criteria**:
- Documentation complete
- Migration script tested
- No broken links
- Screenshots accurate

---

## Conflict Resolution Protocol

### If File Overlap Detected:
1. **Stop immediately** - Do not proceed
2. **Report to coordinator** via agent-status.json
3. **Propose resolution**:
   - Create new file instead
   - Use dependency injection
   - Refactor to extract interface
4. **Wait for approval** before proceeding

### Communication Channels:
- **Status**: `integration-contracts/agent-status.json`
- **Blockers**: `integration-contracts/blockers/{agent-id}.md`
- **Questions**: `integration-contracts/questions/{agent-id}.md`

---

## Territory Map Visualization

```
Wave 1 (Foundation)
├── Agent 1: tests/integration/test_docling_structure.py
├── Agent 2: integration-contracts/chromadb-metadata-schema.md
└── Agent 3: integration-contracts/api-contracts.md

Wave 2 (Backend)
├── Agent 4: src/processing/handlers/*_handler.py + enhanced_metadata.py
├── Agent 5: src/processing/api/structure_endpoints.py
├── Agent 6: src/research/context_builder.py + chunk_extractor.py
└── Agent 7: src/storage/markdown_chunking.py

Wave 3 (Frontend)
├── Agent 8: src/frontend/bounding-box-overlay.js
├── Agent 9: src/frontend/details-controller.js
├── Agent 10: src/frontend/utils/url-builder.js
└── Agent 11: src/frontend/accessibility/*

Wave 4 (QA)
├── Agent 12: tests/e2e/*
├── Agent 13: src/frontend/performance/*
└── Agent 14: docs/* + scripts/migrate_*
```

**Total Agents**: 14
**Total Files**: ~50 new, ~8 modified
**Overlap**: ZERO

---

## Success Metrics

**Per Agent**:
- ✅ All owned files created/modified
- ✅ All tests pass
- ✅ Contract compliance validated
- ✅ Status updated to "complete"

**Per Wave**:
- ✅ Synchronization gate criteria met
- ✅ Integration tests pass
- ✅ No blockers for next wave

**Overall**:
- ✅ Zero file conflicts
- ✅ All integration contracts honored
- ✅ Feature complete and tested
- ✅ Documentation complete
