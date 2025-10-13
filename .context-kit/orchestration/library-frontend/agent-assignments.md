# Agent Assignments - Library Frontend

**Total Agents**: 11
**Parallel Execution**: Wave 1 (6 agents simultaneously)
**Conflict Prevention**: Territorial file ownership, zero overlaps

---

## Territorial Ownership Model

Each agent owns specific files/directories with **zero overlap**. No two agents modify the same file.

---

## Wave 0: Foundation (1 Agent)

### **Infrastructure Agent**
**ID**: `infrastructure-agent`
**Territory**: Project setup, worker configuration

**Responsibilities**:
1. Create directory structure `/src/frontend`
2. Update `worker_webhook.py` to mount frontend
3. Create placeholder files for all agents
4. Test worker startup and access

**Files Created**:
- `/src/frontend/` (directory)
- `/src/frontend/index.html` (empty placeholder)
- `/src/frontend/library-manager.js` (empty placeholder)
- `/src/frontend/websocket-client.js` (empty placeholder)
- `/src/frontend/api-client.js` (empty placeholder)
- `/src/frontend/document-card.js` (empty placeholder)
- `/src/frontend/filter-bar.js` (empty placeholder)
- `/src/frontend/upload-modal.js` (empty placeholder)
- `/src/frontend/styles.css` (empty placeholder)

**Files Modified**:
- `/src/processing/worker_webhook.py` (add frontend mount)

**Deliverables**:
- Directory structure complete
- Worker configuration updated
- All placeholder files exist
- Access verified at `http://localhost:8002/frontend/`

**Validation**:
```bash
# Worker starts successfully
./scripts/start-all.sh

# Frontend accessible
curl http://localhost:8002/frontend/

# All files exist
ls -la /src/frontend/
```

---

## Wave 1: Parallel Component Development (6 Agents)

All agents work simultaneously with zero file conflicts.

---

### **Agent 1: HTML Structure Agent**
**ID**: `html-agent`
**Territory**: `/src/frontend/index.html`

**Responsibilities**:
- Create complete HTML structure
- Semantic HTML5 elements
- Sticky header with navigation
- Filter bar container (#filter-bar)
- Document grid container (#document-grid)
- Upload modal container
- Connection status indicator
- Loading states markup
- Accessibility attributes (ARIA, roles)

**Dependencies**: None (uses contract specifications)

**Files Owned**:
- `/src/frontend/index.html` ✅ (exclusive)

**Integration Points**:
- Imports: `library-manager.js`, `filter-bar.js`, `upload-modal.js`, `document-card.js`, `styles.css`
- DOM IDs: `#document-grid`, `#filter-bar`, `#connection-status`
- Classes: All CSS classes from style contract

**Deliverables**:
- Complete HTML structure
- All required DOM elements
- Proper semantic markup
- Accessibility attributes
- Script imports

**Validation**:
- Valid HTML5 (W3C validator)
- All IDs present
- All ARIA attributes correct
- No broken links

---

### **Agent 2: Library Logic Agent**
**ID**: `library-agent`
**Territory**:
- `/src/frontend/library-manager.js`
- `/src/frontend/websocket-client.js`
- `/src/frontend/api-client.js`

**Responsibilities**:

**1. library-manager.js**:
- LibraryManager class
- Document state management (Map<doc_id, HTMLElement>)
- Initial load from API
- WebSocket message routing
- Card lifecycle (create/update/remove)
- Filter event listener
- Upload event listener
- Connection status updates
- Grid rendering

**2. websocket-client.js**:
- WebSocketClient class
- Connection to `ws://localhost:8002/ws`
- Auto-reconnect with exponential backoff (1s, 2s, 4s, 8s, 16s, max 32s)
- Message parsing (status_update, log, stats, connection)
- Event emission (connected, disconnected, reconnecting, status_update)
- Connection state tracking

**3. api-client.js**:
- DocumentsAPIClient class
- GET `/documents` wrapper
- Query builder (limit, offset, search, sort_by)
- GET `/documents/{doc_id}` wrapper
- Image URL generator
- Error handling
- Response parsing

**Dependencies**:
- DocumentCard contract (Agent 3) - API only
- FilterBar events (Agent 4) - event contract
- UploadModal events (Agent 5) - event contract

**Files Owned**:
- `/src/frontend/library-manager.js` ✅ (exclusive)
- `/src/frontend/websocket-client.js` ✅ (exclusive)
- `/src/frontend/api-client.js` ✅ (exclusive)

**Integration Points**:
- Calls: `createDocumentCard()`, `updateCardState()` (Agent 3)
- Listens: `filterChange`, `pageChange` (Agent 4)
- Listens: `uploadComplete`, `uploadError` (Agent 5)
- Updates: `#connection-status`, `#document-grid`

**Deliverables**:
- 3 ES6 modules
- Exported classes: `LibraryManager`, `WebSocketClient`, `DocumentsAPIClient`
- Complete functionality per contracts

**Validation**:
- All exports available
- WebSocket connects successfully
- API queries work
- Event listeners attached

---

### **Agent 3: Document Card Agent**
**ID**: `card-agent`
**Territory**: `/src/frontend/document-card.js`

**Responsibilities**:
- Migrate DocumentCard from copyparty POC
- Remove Lucide dependency → inline SVG icons
- Support 3 states: completed, loading, processing
- Support 2 variants: document (tall), audio (square)
- Export: `createDocumentCard(options)`
- Export: `updateCardState(card, status)`
- Export: `Icons` object
- File extension to variant mapping
- Thumbnail error handling
- Date formatting

**Dependencies**: None (pure component)

**Files Owned**:
- `/src/frontend/document-card.js` ✅ (exclusive)

**Source Reference**:
- `/data/copyparty/www/modules/document-card.js` (POC - read only, do not modify)

**Integration Points**:
- Consumed by: LibraryManager (Agent 2)

**Deliverables**:
- ES6 module with exports
- Function: `createDocumentCard(options)`
- Function: `updateCardState(card, status)`
- Object: `Icons`
- Inline SVG icons (no external deps)

**Validation**:
- Creates HTMLElement correctly
- All states render properly
- Variant detection works
- Update function works
- No Lucide dependency

---

### **Agent 4: Filter Bar Agent**
**ID**: `filter-agent`
**Territory**: `/src/frontend/filter-bar.js`

**Responsibilities**:
- FilterBar class
- Render filter UI in #filter-bar container
- Search input with 300ms debounce
- Sort dropdown (date_added, filename, page_count)
- File type checkboxes (pdf, docx, pptx, audio)
- Clear filters button
- Event emission: `filterChange`, `pageChange`
- URL query param management (read/write)
- State management
- Pagination controls (next/previous/page numbers)

**Dependencies**: None (independent component)

**Files Owned**:
- `/src/frontend/filter-bar.js` ✅ (exclusive)

**Integration Points**:
- Emits: `filterChange` CustomEvent (listened by Agent 2)
- Emits: `pageChange` CustomEvent (listened by Agent 2)
- Renders into: `#filter-bar` (created by Agent 1)

**Deliverables**:
- ES6 module
- FilterBar class
- Complete filter UI
- Event emission
- URL state sync

**Validation**:
- UI renders correctly
- Search debounce works (300ms)
- Events emitted with correct detail
- URL params sync
- Pagination works

---

### **Agent 5: Upload Modal Agent**
**ID**: `upload-agent`
**Territory**: `/src/frontend/upload-modal.js`

**Responsibilities**:
- UploadModal class
- Global drag-over detection (document.body)
- Lightbox modal display
- Drop zone UI
- File validation (extension, size)
- Upload to Copyparty API (`POST http://localhost:8000/uploads`)
- Multi-file support
- Progress tracking (XMLHttpRequest)
- Event emission: `uploadStart`, `uploadProgress`, `uploadComplete`, `uploadError`, `uploadBatchComplete`
- Error handling (network, validation)
- Focus trap
- Keyboard navigation (ESC to close)

**Dependencies**: None (independent component)

**Files Owned**:
- `/src/frontend/upload-modal.js` ✅ (exclusive)

**External Integration**:
- Copyparty API: `http://localhost:8000/uploads`

**Integration Points**:
- Emits: Upload events (listened by Agent 2)
- Renders: Modal appended to body

**Deliverables**:
- ES6 module
- UploadModal class
- Complete modal UI
- File upload functionality
- Event emission

**Validation**:
- Modal shows on drag-over
- File validation works
- Upload progress tracked
- Events emitted
- Error handling works
- Accessibility features work

---

### **Agent 6: Style Agent**
**ID**: `style-agent`
**Territory**: `/src/frontend/styles.css`

**Responsibilities**:
- Complete stylesheet for all components
- Design system tokens (CSS custom properties)
- Responsive grid layout
- Sticky header and filter bar
- DocumentCard styles (all states, both variants)
- Modal/lightbox styles
- Connection status indicator
- Loading states (spinners, skeletons)
- Hover/focus states
- Accessibility (focus outlines, color contrast)
- Mobile responsive breakpoints
- Animations (progress bars, spinners)

**Dependencies**: None (pure CSS)

**Files Owned**:
- `/src/frontend/styles.css` ✅ (exclusive)

**Reference**:
- `/data/copyparty/www/styles.css` (POC - read only)
- Design system from existing components

**Integration Points**:
- Classes used by: All HTML (Agent 1, 2, 3, 4, 5)

**Deliverables**:
- Complete stylesheet
- All component styles
- Responsive design
- Accessibility support

**Validation**:
- No CSS errors
- All classes defined
- Responsive breakpoints work
- Color contrast meets WCAG AA
- Focus indicators visible

---

## Wave 1 Summary

**Parallel Work**: All 6 agents work simultaneously
**Zero Conflicts**: Each owns distinct files
**Integration**: Via contracts and DOM events
**Duration**: Depends on agent execution, but all start together

---

## Wave 2: Integration & Testing (3 Agents)

### **Agent 7: Integration Test Agent**
**ID**: `integration-agent`
**Territory**: `/src/frontend/test-integration.js`

**Responsibilities**:
- Write integration test suite
- Test LibraryManager initialization
- Test WebSocket connection/reconnection
- Test API client with mock responses
- Test DocumentCard rendering
- Test FilterBar event emission
- Test UploadModal logic
- Test cross-component integration
- Generate coverage report

**Files Owned**:
- `/src/frontend/test-integration.js` ✅ (exclusive)

**Deliverables**:
- Test suite
- Coverage report (target >80%)

---

### **Agent 8: E2E Test Agent**
**ID**: `e2e-agent`
**Territory**: Manual testing, checklist document

**Responsibilities**:
- Manual E2E testing
- Test initial load from API
- Test WebSocket real-time updates
- Test search/filter/sort
- Test pagination
- Test drag-drop upload
- Test error states
- Test responsive design
- Test keyboard navigation
- Test screen reader compatibility

**Files Owned**:
- `/src/frontend/E2E_TEST_RESULTS.md` ✅ (exclusive)

**Deliverables**:
- Complete test results document

---

### **Agent 9: Documentation Agent**
**ID**: `docs-agent`
**Territory**:
- `/src/frontend/README.md`
- Project documentation updates

**Responsibilities**:
- Frontend architecture documentation
- API integration guide
- WebSocket message handling guide
- Development setup
- Update `_context-kit.yml`
- Update `QUICK_START.md`
- Update project README

**Files Owned**:
- `/src/frontend/README.md` ✅ (exclusive)

**Files Modified**:
- `/_context-kit.yml` (add frontend section)
- `/docs/QUICK_START.md` (add UI access info)

**Deliverables**:
- Complete frontend documentation
- Updated project docs

---

## Wave 3: Polish & Production (2 Agents)

### **Agent 10: Performance Agent**
**ID**: `perf-agent`
**Territory**: Performance optimization layer

**Responsibilities**:
- Implement lazy loading (Intersection Observer)
- Verify debounce timing (300ms optimal?)
- Request deduplication
- WebSocket message batching (if needed)
- Bundle size analysis
- Memory leak detection
- Performance report

**Files Modified**:
- Various (optimizations)

**Files Created**:
- `/src/frontend/PERFORMANCE_REPORT.md`

**Deliverables**:
- Performance report
- Optimizations implemented

---

### **Agent 11: Cleanup Agent**
**ID**: `cleanup-agent`
**Territory**: Cleanup and migration

**Responsibilities**:
- Remove `/data/copyparty/www/` POC pages
- Verify no references remain
- Update all documentation
- Final validation
- Production deployment checklist

**Files Deleted**:
- `/data/copyparty/www/` (entire directory)

**Files Modified**:
- Documentation updates

**Deliverables**:
- Clean codebase
- Updated documentation
- Production ready

---

## Territorial Map

```
/src/frontend/
├── index.html                 ← Agent 1 (html-agent)
├── library-manager.js         ← Agent 2 (library-agent)
├── websocket-client.js        ← Agent 2 (library-agent)
├── api-client.js              ← Agent 2 (library-agent)
├── document-card.js           ← Agent 3 (card-agent)
├── filter-bar.js              ← Agent 4 (filter-agent)
├── upload-modal.js            ← Agent 5 (upload-agent)
├── styles.css                 ← Agent 6 (style-agent)
├── test-integration.js        ← Agent 7 (integration-agent)
├── E2E_TEST_RESULTS.md        ← Agent 8 (e2e-agent)
├── README.md                  ← Agent 9 (docs-agent)
└── PERFORMANCE_REPORT.md      ← Agent 10 (perf-agent)

/src/processing/
└── worker_webhook.py          ← Agent 0 (infrastructure-agent) [add frontend mount]

/_context-kit.yml              ← Agent 9 (docs-agent) [update]
/docs/QUICK_START.md           ← Agent 9 (docs-agent) [update]

/data/copyparty/www/           ← Agent 11 (cleanup-agent) [DELETE]
```

**Total Files**: 14 owned, 3 modified, 1 deleted

---

## Communication Protocol

### **Wave Boundaries**
- Agents wait at wave gates for validation
- No agent proceeds until wave completes
- Progressive validation ensures quality

### **Integration**
- Agents communicate via contracts (specifications)
- No direct coupling between agents
- DOM events for runtime communication
- Contracts defined in `/integration-contracts/`

### **Status Updates**
- Each agent reports completion
- Deliverables validated at wave gates
- Issues escalated to coordination lead

---

## Conflict Prevention Guarantees

✅ **Zero File Overlaps**: Each file owned by exactly one agent
✅ **Interface Contracts**: Integration via specifications
✅ **Event-Based Communication**: Runtime decoupling
✅ **Progressive Validation**: Quality gates after each wave

**Result**: Guaranteed zero-conflict parallel execution
