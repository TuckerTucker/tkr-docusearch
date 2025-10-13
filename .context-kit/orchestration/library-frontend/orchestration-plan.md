# Library Frontend - Orchestration Plan

**Goal**: Implement production-ready document library UI at `/src/frontend` with WebSocket real-time updates, drag-drop uploads, and server-side filtering.

**Max Agents**: 6

**Target**: Single-page application served at `http://localhost:8002/frontend/`

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Browser Client                          │
├─────────────────────────────────────────────────────────────┤
│  index.html (Agent 1)                                        │
│  ├── LibraryManager (Agent 2)                               │
│  │   ├── WebSocketClient (Agent 2)                          │
│  │   ├── DocumentsAPIClient (Agent 2)                       │
│  │   └── DocumentCard (Agent 3)                             │
│  ├── FilterBar (Agent 4)                                     │
│  ├── UploadModal (Agent 5)                                   │
│  └── styles.css (Agent 6)                                    │
└─────────────────────────────────────────────────────────────┘
         ↓ WebSocket                    ↓ HTTP
┌─────────────────────────────────────────────────────────────┐
│              Worker (localhost:8002)                         │
│  ├── WebSocket: /ws (existing)                              │
│  ├── Documents API: /documents (existing)                   │
│  └── Static Mount: /frontend → src/frontend/                │
└─────────────────────────────────────────────────────────────┘
         ↓ Upload
┌─────────────────────────────────────────────────────────────┐
│              Copyparty (localhost:8000)                      │
│  └── Upload API (existing)                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Wave-Based Execution Plan

### **Wave 0: Foundation & Setup** (Single Agent)
**Agent**: infrastructure-agent
**Duration**: Setup phase

**Tasks**:
1. Create `/src/frontend` directory structure
2. Update `worker_webhook.py` to mount frontend:
   ```python
   FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
   if FRONTEND_DIR.exists():
       app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
   ```
3. Create empty placeholder files for all agents
4. Test access at `http://localhost:8002/frontend/`

**Deliverables**:
- Directory structure created
- Worker configured and tested
- Placeholder files ready for parallel work

**Validation Criteria**:
- [ ] Worker starts without errors
- [ ] `http://localhost:8002/frontend/` accessible
- [ ] All placeholder files exist

---

### **Wave 1: Parallel Component Development** (6 Agents)

All agents work simultaneously on independent files with no conflicts.

#### **Agent 1: HTML Structure** (`html-agent`)
**Territory**: `src/frontend/index.html`

**Responsibilities**:
- Create semantic HTML structure
- Sticky header with navigation
- Filter bar container (populated by Agent 4)
- Document grid container (populated by Agent 2)
- Upload modal container (controlled by Agent 5)
- Connection status indicator
- Loading states

**Dependencies**: None (uses contract specifications)

**Deliverables**: `index.html` with complete structure

**Integration Points**:
- Imports: `library-manager.js`, `filter-bar.js`, `upload-modal.js`, `styles.css`
- DOM IDs: `#document-grid`, `#filter-bar`, `#upload-modal`, `#connection-status`

---

#### **Agent 2: Core Library Logic** (`library-agent`)
**Territory**:
- `src/frontend/library-manager.js`
- `src/frontend/websocket-client.js`
- `src/frontend/api-client.js`

**Responsibilities**:
1. **library-manager.js**:
   - Document state management (Map<doc_id, HTMLElement>)
   - Initial API load
   - WebSocket message routing
   - Card lifecycle (add/update/remove)
   - Integration with FilterBar events
   - Integration with UploadModal events

2. **websocket-client.js**:
   - Connection to `ws://localhost:8002/ws`
   - Auto-reconnect with exponential backoff
   - Message type parsing (`status_update`, `log`, `stats`, `connection`)
   - Event emitter for status updates
   - Connection state management

3. **api-client.js**:
   - `GET /documents` wrapper
   - Query parameter builder (limit, offset, search, sort_by)
   - Error handling
   - Response parsing

**Dependencies**: DocumentCard API (contract only, not implementation)

**Deliverables**: 3 ES6 modules with exported classes

**Integration Points**:
- Calls: `createDocumentCard()`, `updateCardState()` (Agent 3)
- Listens: Filter change events (Agent 4), Upload complete events (Agent 5)
- Updates: Connection status DOM element

---

#### **Agent 3: Document Card Component** (`card-agent`)
**Territory**: `src/frontend/document-card.js`

**Responsibilities**:
- Migrate from copyparty POC
- Remove Lucide dependency → inline SVG icons
- Maintain API: `createDocumentCard(options)`, `updateCardState(card, status)`
- Support states: completed, loading, processing
- Two variants: document (tall), audio (square)

**Dependencies**: None (pure component)

**Deliverables**: ES6 module with exported functions

**Integration Points**:
- Consumed by: LibraryManager (Agent 2)

---

#### **Agent 4: Filter Bar** (`filter-agent`)
**Territory**: `src/frontend/filter-bar.js`

**Responsibilities**:
- Search input with debounce (300ms)
- Sort dropdown (date_added, filename, page_count)
- File type filter checkboxes (pdf, docx, pptx, audio)
- Event emission on filter change
- URL query param management
- Clear filters button

**Dependencies**: None (independent component)

**Deliverables**: ES6 module with FilterBar class

**Integration Points**:
- Emits: `filterChange` custom event with query params
- Consumed by: LibraryManager (Agent 2)

---

#### **Agent 5: Upload Modal** (`upload-agent`)
**Territory**: `src/frontend/upload-modal.js`

**Responsibilities**:
- Global drag-over detection (body dragenter/dragover)
- Lightbox modal display
- Drop zone with file validation
- Upload to Copyparty API at `http://localhost:8000/upload`
- Multi-file support
- Progress feedback
- Error handling (unsupported types, upload failures)
- Event emission on upload complete

**Dependencies**: None (independent component)

**Deliverables**: ES6 module with UploadModal class

**Integration Points**:
- Emits: `uploadComplete` custom event with file info
- Consumed by: LibraryManager (Agent 2)
- Uploads to: Copyparty API (external)

---

#### **Agent 6: Styles** (`style-agent`)
**Territory**: `src/frontend/styles.css`

**Responsibilities**:
- Design system tokens (CSS custom properties)
- Responsive grid layout
- Sticky header and filter bar positioning
- Modal/lightbox styles
- Connection status indicator
- Loading states and skeletons
- Hover/focus states
- Accessibility (focus outlines, color contrast)
- Mobile responsive breakpoints

**Dependencies**: None (pure CSS)

**Deliverables**: Complete stylesheet

**Integration Points**:
- Classes used by: All HTML components
- Follows: Existing design system from copyparty POC

---

**Wave 1 Synchronization Gate**:
- [ ] All 6 files created and syntactically valid
- [ ] ES6 modules export expected functions/classes
- [ ] No syntax errors in browser console
- [ ] Worker serves files without 404s

---

### **Wave 2: Integration & Testing** (3 Agents)

#### **Agent 7: Integration Testing** (`integration-agent`)
**Territory**: `src/frontend/test-integration.js` (test script)

**Responsibilities**:
- Test LibraryManager initialization
- Test WebSocket connection and reconnection
- Test API client with mock responses
- Test DocumentCard rendering
- Test FilterBar event emission
- Test UploadModal display logic
- Integration smoke tests

**Deliverables**: Test suite with coverage report

---

#### **Agent 8: End-to-End Testing** (`e2e-agent`)
**Territory**: Manual testing checklist

**Responsibilities**:
1. Initial load from `/documents` API
2. WebSocket connection status indicator
3. Real-time card updates during processing
4. Search/filter/sort functionality
5. Pagination controls
6. Drag-drop upload flow
7. Error states (connection lost, API errors)
8. Responsive design on mobile
9. Keyboard navigation
10. Screen reader compatibility

**Deliverables**: Test results document

---

#### **Agent 9: Documentation** (`docs-agent`)
**Territory**:
- `src/frontend/README.md`
- Updates to project docs

**Responsibilities**:
- Frontend architecture documentation
- API integration guide
- WebSocket message handling guide
- Development setup instructions
- Update `_context-kit.yml` with frontend info
- Update `QUICK_START.md` with UI access

**Deliverables**: Complete documentation

---

**Wave 2 Synchronization Gate**:
- [ ] All integration tests pass
- [ ] All E2E test cases pass
- [ ] Documentation complete
- [ ] No console errors in production build

---

### **Wave 3: Polish & Production Readiness** (2 Agents)

#### **Agent 10: Performance Optimization** (`perf-agent`)
**Territory**: Optimization layer

**Responsibilities**:
- Lazy load thumbnails (Intersection Observer)
- Debounce search (verify 300ms optimal)
- Request deduplication
- WebSocket message batching (if needed)
- Bundle size analysis
- Memory leak detection

**Deliverables**: Performance report + optimizations

---

#### **Agent 11: Cleanup & Migration** (`cleanup-agent`)
**Territory**: Cleanup tasks

**Responsibilities**:
1. Remove `data/copyparty/www/` POC pages
2. Verify no references remain
3. Update all documentation
4. Final validation of production deployment

**Deliverables**: Clean codebase, updated docs

---

**Wave 3 Synchronization Gate**:
- [ ] Performance targets met (load <2s, FCP <1s)
- [ ] POC pages removed
- [ ] Production deployment successful
- [ ] All documentation updated

---

## Critical Path

```
Wave 0 (Setup)
  ↓
Wave 1 (Parallel: 6 agents) ← Critical: All must complete
  ↓
Wave 2 (Integration: 3 agents)
  ↓
Wave 3 (Polish: 2 agents)
  ↓
Production Ready
```

**Total Agents**: 11
**Parallel Work**: Wave 1 (6 agents simultaneously)
**Sequential Gates**: 3 waves with validation

---

## Risk Mitigation

### **Conflict Prevention**:
- ✅ Each agent owns distinct files (no overlaps)
- ✅ Integration via contracts, not direct coupling
- ✅ Events for cross-component communication
- ✅ Progressive validation at wave gates

### **Integration Risks**:
- **Risk**: WebSocket message format mismatch
  - **Mitigation**: Contract spec in `integration-contracts/websocket.contract.md`

- **Risk**: DocumentCard API changes
  - **Mitigation**: Contract spec in `integration-contracts/document-card.contract.md`

- **Risk**: Filter event payload mismatch
  - **Mitigation**: Contract spec in `integration-contracts/filter-events.contract.md`

### **Quality Assurance**:
- Interface-first development (contracts before code)
- Progressive testing (after each wave)
- Automated validation gates
- Consumer-driven contract testing

---

## Success Metrics

**Wave 1 Complete**:
- 6 modules implemented
- No syntax errors
- All exports available

**Wave 2 Complete**:
- Integration tests pass (>90% coverage)
- E2E tests pass (100%)
- Documentation complete

**Wave 3 Complete**:
- Performance targets met
- POC removed
- Production deployed

**Overall Success**:
- Library UI accessible at `/frontend`
- Real-time updates working
- Upload flow functional
- Server-side filtering working
- Responsive and accessible
- Zero console errors
