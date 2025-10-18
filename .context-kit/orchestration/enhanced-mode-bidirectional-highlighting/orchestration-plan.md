# Enhanced Mode Bidirectional Highlighting - Orchestration Plan

**Feature Goal**: Enable enhanced document structure metadata storage with bidirectional highlighting between page images and text chunks on the details page, similar to audio player timestamp interactions.

**Max Agents**: 6 concurrent agents
**Estimated Waves**: 4 waves
**Total Tasks**: 27 (from implementation plan)

---

## Executive Summary

This orchestration enables parallel development of:
1. **Backend storage layer** (enhanced metadata in ChromaDB)
2. **Backend API layer** (structure and chunk endpoints)
3. **Frontend overlay system** (bounding box visualization)
4. **Frontend navigation** (research → details with chunk context)
5. **Integration layer** (markdown markers, shared state)
6. **Quality assurance** (testing, accessibility, optimization)

**Key Strategy**: Interface-first development with territorial ownership to enable maximum parallelism while preventing conflicts.

---

## Wave 1: Foundation & Interface Contracts (Parallel: 3 agents)

**Prerequisites**: None (starting point)

**Duration**: Validate Docling capability and create all interface contracts

**Agents & Territories**:

### Agent 1: Docling Structure Validator
**Territory**: `tests/integration/test_docling_structure.py` (new file)
**Deliverables**:
- Validate Docling extracts DocumentStructure with bboxes
- Test bbox coordinate format and accuracy
- Verify structure flows through processor
- Document bbox coordinate system (origin, scaling, units)
- Create sample structure data for testing

**Output**: `integration-contracts/docling-structure-spec.md`

### Agent 2: ChromaDB Schema Architect
**Territory**: `integration-contracts/chromadb-metadata-schema.md` (new file)
**Deliverables**:
- Define enhanced visual metadata schema (with structure)
- Define enhanced text metadata schema (with context)
- Define page→chunk mapping index structure
- Specify compression strategy for structure data
- Document metadata size limits and validation

**Output**: `integration-contracts/chromadb-metadata-schema.md`

### Agent 3: API Contract Designer
**Territory**: `integration-contracts/api-contracts.md` (new file)
**Deliverables**:
- `GET /documents/{doc_id}/pages/{page}/structure` specification
- `GET /documents/{doc_id}/chunks/{chunk_id}` specification
- Enhanced markdown endpoint response schema
- Research API SourceInfo extension (chunk_id field)
- Chunk navigation URL parameter contract

**Output**: `integration-contracts/api-contracts.md`

**Synchronization Gate**:
- ✅ Docling bbox validation passes
- ✅ All interface contracts reviewed and approved
- ✅ No schema conflicts identified
- ✅ Coordinate system documented

---

## Wave 2: Backend Implementation (Parallel: 4 agents)

**Prerequisites**: Wave 1 complete, all contracts approved

**Agents & Territories**:

### Agent 4: Enhanced Storage Enabler
**Territory**:
- `src/processing/handlers/visual_embedding_handler.py` (modify)
- `src/processing/handlers/text_embedding_handler.py` (modify)
- `tests/integration/test_enhanced_storage.py` (new)

**Dependencies**: ChromaDB schema contract (Agent 2)

**Deliverables**:
1. Enable `_prepare_enhanced_visual_metadata()` in visual handler
2. Enable `_prepare_enhanced_text_metadata()` in text handler
3. Add page number to text chunk metadata
4. Create page→chunk index helper
5. Integration tests validating storage

**Validation**:
- Test document processed with enhanced mode
- Query ChromaDB confirms bboxes stored
- Query confirms section_path in text chunks
- Page→chunk index queryable

### Agent 5: Structure API Builder
**Territory**:
- `src/processing/documents_api.py` (add new endpoints)
- `tests/api/test_structure_endpoints.py` (new)

**Dependencies**: API contracts (Agent 3), ChromaDB schema (Agent 2)

**Deliverables**:
1. Implement `GET /documents/{doc_id}/pages/{page}/structure`
2. Implement `GET /documents/{doc_id}/chunks/{chunk_id}`
3. Add chunk_id markers to markdown endpoint
4. Return chunk metadata with markdown
5. Unit and integration tests

**Validation**:
- All endpoints return data per contract
- Response schemas validated
- Error handling tested (404s, validation errors)

### Agent 6: Research Context Enhancer
**Territory**:
- `src/research/context_builder.py` (modify `get_source_metadata`)
- `src/research/types.py` (add chunk_id to SourceDocument)
- `src/api/research.py` (add chunk_id to SourceInfo)
- `tests/research/test_chunk_context.py` (new)

**Dependencies**: API contracts (Agent 3)

**Deliverables**:
1. Add `chunk_id` field to SourceDocument dataclass
2. Extract chunk_id from ChromaDB search results
3. Add `chunk_id` to SourceInfo API response
4. Handle both visual (page-level) and text (chunk-level) results
5. Backward compatibility tests

**Validation**:
- Research API returns chunk_id when available
- Visual-only search works (no chunk_id)
- Text search includes chunk_id
- Existing tests still pass

### Agent 7: Markdown Chunker
**Territory**:
- `src/storage/markdown_utils.py` (new functions)
- `src/processing/documents_api.py` (modify markdown endpoint)
- `tests/storage/test_markdown_chunks.py` (new)

**Dependencies**: API contracts (Agent 3), ChromaDB schema (Agent 2)

**Deliverables**:
1. Function to insert chunk markers in markdown
2. Format: `<!-- chunk:abc123-chunk0001 -->`
3. Wrap chunks in `<div data-chunk-id="...">`
4. Update markdown endpoint to include markers
5. Tests validating marker insertion

**Validation**:
- Markdown includes valid chunk markers
- Markers don't break markdown rendering
- Chunk IDs correspond to ChromaDB records

**Synchronization Gate**:
- ✅ Enhanced mode enabled and tested
- ✅ Structure API endpoints functional
- ✅ Research API includes chunk_id
- ✅ Markdown chunking works
- ✅ Integration tests pass
- ✅ No breaking changes to existing features

---

## Wave 3: Frontend Implementation (Parallel: 4 agents)

**Prerequisites**: Wave 2 complete, backend APIs functional

**Agents & Territories**:

### Agent 8: BoundingBox Overlay Component
**Territory**:
- `src/frontend/bounding-box-overlay.js` (new)
- `src/frontend/styles/bounding-box-overlay.css` (new)
- `integration-contracts/bbox-overlay-spec.md` (reference)

**Dependencies**: Structure API (Agent 5), API contracts (Agent 3)

**Deliverables**:
1. SVG overlay component for page images
2. Render rectangles from bbox coordinates
3. Handle coordinate scaling for responsive images
4. Hover and click event handlers
5. CSS for hover/active states

**Component Interface**:
```javascript
class BoundingBoxOverlay {
  constructor(imageElement, bboxes)
  render()
  highlightBbox(chunkId)
  clearHighlight()
  onBboxClick(callback)
  onBboxHover(callback)
}
```

**Validation**:
- Bboxes render correctly over images
- Coordinates scale with image size
- Click/hover events fire correctly
- Visual feedback matches design

### Agent 9: Details Page Integration
**Territory**:
- `src/frontend/details.html` (modify - add overlay container)
- `src/frontend/details-controller.js` (new - orchestrates page)
- `src/frontend/chunk-highlighter.js` (new - chunk text highlighting)

**Dependencies**: BoundingBox Overlay (Agent 8), Structure API (Agent 5)

**Deliverables**:
1. Load structure metadata when page loads
2. Initialize BoundingBoxOverlay component
3. Parse URL params (page, chunk_id)
4. Implement image region → chunk scroll
5. Implement chunk → image region highlight
6. Shared state management (activeChunkId, hoveredChunkId)

**Integration Points**:
- Uses BoundingBoxOverlay API from Agent 8
- Fetches data from Structure API (Agent 5)
- Triggers markdown chunk highlighting

**Validation**:
- Page loads with structure overlay
- URL params navigate correctly
- Click bbox scrolls to chunk
- Hover chunk highlights bbox
- State synchronized between components

### Agent 10: Research Navigation Enhancer
**Territory**:
- `src/frontend/reference-card.js` (modify - add chunk_id to links)
- `integration-contracts/research-navigation-spec.md` (reference)

**Dependencies**: Research API chunk_id (Agent 6), Details page URL params (Agent 9)

**Deliverables**:
1. Extract chunk_id from source data
2. Build URL: `/details.html?id={doc_id}&page={page}&chunk={chunk_id}`
3. Maintain backward compatibility (no chunk_id)
4. Visual indicator when chunk context available

**URL Format**:
```
With chunk: /frontend/details.html?id=abc123&page=5&chunk=abc123-chunk0012
Without chunk: /frontend/details.html?id=abc123&page=5
```

**Validation**:
- Links include chunk_id when available
- Links work without chunk_id (legacy)
- Navigation triggers highlighting on details page

### Agent 11: Accessibility & Polish
**Territory**:
- `src/frontend/accessibility/` (new directory)
  - `keyboard-navigation.js`
  - `aria-labels.js`
  - `screen-reader.js`
- `src/frontend/styles/highlighting-animations.css` (new)

**Dependencies**: Details page integration (Agent 9), Overlay component (Agent 8)

**Deliverables**:
1. Keyboard navigation (Tab, Enter for chunks)
2. ARIA labels for bboxes: "Section: {heading}, Page {n}"
3. Screen reader announcements for navigation
4. Focus management
5. Smooth scroll animations
6. Highlight transition effects

**Accessibility Features**:
- Keyboard shortcuts: Tab (next chunk), Shift+Tab (prev), Enter (activate)
- ARIA live regions announce chunk navigation
- Focus visible on keyboard nav
- Skip links for navigation

**Validation**:
- Keyboard-only navigation works
- Screen reader testing (VoiceOver/NVDA)
- Color contrast meets WCAG AA
- Focus indicators visible

**Synchronization Gate**:
- ✅ Overlay component functional
- ✅ Details page bidirectional highlighting works
- ✅ Research navigation includes chunk context
- ✅ Accessibility features implemented
- ✅ Manual testing complete
- ✅ No console errors

---

## Wave 4: Integration, Testing & Optimization (Parallel: 3 agents)

**Prerequisites**: Wave 3 complete, all features functional

**Agents & Territories**:

### Agent 12: Integration Test Suite
**Territory**:
- `tests/e2e/test_bidirectional_highlighting.py` (new)
- `tests/e2e/test_research_to_details_navigation.py` (new)
- `integration-contracts/test-scenarios.md` (new)

**Dependencies**: All previous agents

**Deliverables**:
1. E2E test: Research → Details → Highlight
2. E2E test: Click bbox → Scroll to chunk
3. E2E test: Hover chunk → Highlight bbox
4. Test multiple document types (PDF, DOCX, PPTX)
5. Test edge cases (no structure, multi-page chunks)

**Test Scenarios**:
- PDF with complex layout (tables, multi-column)
- DOCX with simple structure
- PPTX with slide regions
- Document without structure metadata (fallback)
- Chunk spanning multiple pages

**Validation**:
- All E2E tests pass
- Coverage ≥80% for new code
- No regressions in existing tests

### Agent 13: Performance Optimizer
**Territory**:
- `src/frontend/performance/` (new directory)
  - `lazy-loading.js`
  - `debounce-utils.js`
  - `cache-manager.js`
- Performance testing scripts

**Dependencies**: All Wave 3 agents

**Deliverables**:
1. Lazy load structure (only for visible pages)
2. Debounce hover handlers (prevent lag)
3. CSS transforms for smooth animations
4. Cache structure data (avoid redundant fetches)
5. Performance benchmarks

**Performance Targets**:
- Initial page load: <500ms (structure fetch)
- Bbox hover response: <16ms (60fps)
- Chunk scroll: <300ms (smooth)
- Memory: <10MB additional for structure cache

**Validation**:
- Lighthouse performance score ≥90
- No jank during interactions
- Memory usage within targets

### Agent 14: Documentation & Migration
**Territory**:
- `docs/ENHANCED_MODE.md` (new)
- `docs/BIDIRECTIONAL_HIGHLIGHTING.md` (new)
- `docs/API_REFERENCE.md` (update)
- `scripts/migrate_enhanced_mode.py` (new)

**Dependencies**: All previous work

**Deliverables**:
1. Enhanced mode configuration guide
2. API documentation for new endpoints
3. Frontend component documentation
4. Developer guide for bbox coordinate system
5. Migration script for existing documents
6. User guide with screenshots

**Migration Strategy**:
```python
# Option 1: Reprocess all documents
python scripts/migrate_enhanced_mode.py --reprocess-all

# Option 2: Lazy migration on access
python scripts/migrate_enhanced_mode.py --lazy

# Option 3: Flag legacy documents
python scripts/migrate_enhanced_mode.py --flag-legacy
```

**Validation**:
- Documentation complete and accurate
- Migration script tested
- No broken links in docs

**Final Synchronization Gate**:
- ✅ All integration tests pass
- ✅ Performance targets met
- ✅ Documentation complete
- ✅ Migration strategy validated
- ✅ UAT complete
- ✅ Ready for production deployment

---

## Agent Communication Protocol

### Status Broadcasting
Each agent publishes status to `integration-contracts/agent-status.json`:
```json
{
  "agent_id": "agent-8-bbox-overlay",
  "status": "in_progress|complete|blocked|failed",
  "progress": 75,
  "blockers": ["Waiting for API contract approval"],
  "deliverables_complete": ["overlay.js", "overlay.css"],
  "validation_status": {
    "unit_tests": "passed",
    "integration_tests": "pending"
  }
}
```

### Contract Compliance
- All agents validate against specs in `integration-contracts/`
- Consumer agents review provider specifications
- Breaking changes require cross-agent approval

### Failure Recovery
Each agent documents rollback in `integration-contracts/rollback-{agent-id}.md`:
- What was changed
- How to revert
- Dependencies affected
- Alternative approaches

---

## Risk Mitigation

### Conflict Prevention
1. **Territorial Ownership**: No file overlap between agents
2. **New Files Preferred**: Minimize shared file modifications
3. **Interface-First**: Contracts before implementation
4. **Progressive Validation**: Tests after each wave

### Dependency Management
```
Wave 1: Foundation (no dependencies)
  ↓
Wave 2: Backend (depends on Wave 1 contracts)
  ├── Agent 4 ← Agent 2 (schema)
  ├── Agent 5 ← Agent 3 (API), Agent 2 (schema)
  ├── Agent 6 ← Agent 3 (API)
  └── Agent 7 ← Agent 3 (API), Agent 2 (schema)
  ↓
Wave 3: Frontend (depends on Wave 2 APIs)
  ├── Agent 8 ← Agent 5 (API), Agent 3 (contracts)
  ├── Agent 9 ← Agent 8 (overlay), Agent 5 (API)
  ├── Agent 10 ← Agent 6 (research API), Agent 9 (URL params)
  └── Agent 11 ← Agent 9 (details page), Agent 8 (overlay)
  ↓
Wave 4: Integration (depends on all)
```

### Quality Gates
- **Wave 1**: All contracts approved, Docling validated
- **Wave 2**: Backend APIs functional, tests pass
- **Wave 3**: Frontend features working, manual testing complete
- **Wave 4**: E2E tests pass, performance targets met

---

## Success Metrics

**Technical**:
- ✅ 100% of structure data flows from Docling → ChromaDB → API → Frontend
- ✅ Bounding boxes render accurately (±5px tolerance)
- ✅ Bidirectional highlighting works in both directions
- ✅ Research → Details navigation includes chunk context
- ✅ Performance: <500ms initial load, <16ms hover response
- ✅ Accessibility: WCAG AA compliant, keyboard navigable

**Quality**:
- ✅ Test coverage ≥80% for new code
- ✅ Zero regressions in existing features
- ✅ All integration tests pass
- ✅ Documentation complete

**User Experience**:
- ✅ Clicking page regions scrolls to text
- ✅ Hovering text highlights regions
- ✅ Smooth, responsive interactions
- ✅ Graceful degradation (no structure → text-only)

---

## Execution Timeline

**Wave 1** (Foundation): 3 agents, ~1-2 days
**Wave 2** (Backend): 4 agents, ~2-3 days
**Wave 3** (Frontend): 4 agents, ~2-3 days
**Wave 4** (Integration): 3 agents, ~1-2 days

**Total**: ~6-10 days with maximum parallelism

---

## Appendix: Territorial Map

```
Agent 1: tests/integration/test_docling_structure.py
Agent 2: integration-contracts/chromadb-metadata-schema.md
Agent 3: integration-contracts/api-contracts.md
Agent 4: src/processing/handlers/*_handler.py + tests
Agent 5: src/processing/documents_api.py (new endpoints) + tests
Agent 6: src/research/*.py (add chunk_id) + tests
Agent 7: src/storage/markdown_utils.py (new) + tests
Agent 8: src/frontend/bounding-box-overlay.js + css
Agent 9: src/frontend/details-controller.js + chunk-highlighter.js
Agent 10: src/frontend/reference-card.js (modify)
Agent 11: src/frontend/accessibility/* + animations.css
Agent 12: tests/e2e/*
Agent 13: src/frontend/performance/*
Agent 14: docs/* + scripts/migrate_enhanced_mode.py
```

**Zero Overlap**: Each agent has exclusive file ownership or creates new files.
