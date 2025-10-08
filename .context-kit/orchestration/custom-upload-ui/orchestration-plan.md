# Custom Upload UI - Parallel Orchestration Plan

**Feature Goal**: Standalone upload interface with real-time processing progress monitoring

**Agents**: 6 specialized agents working in parallel waves

**Strategy**: Interface-first development with zero-conflict territorial ownership

---

## Wave 0: Specification & Contracts (Foundation)

**Duration**: Synchronous prerequisite for all waves
**Agents**: 1 (specification-agent)

### Deliverables
- API endpoint specifications (OpenAPI/JSON schemas)
- Data structure contracts (TypeScript interfaces or JSON schemas)
- Integration point documentation
- Validation test templates

### Agent Assignment
**specification-agent** owns:
- `.context-kit/orchestration/custom-upload-ui/integration-contracts/`
- All `.contract.md` and `.schema.json` files

### Prerequisites
- None (foundation wave)

### Validation Criteria
✅ All integration contracts published
✅ Schemas validate with test data
✅ No ambiguous specifications

---

## Wave 1: Backend API Extensions (Parallel - 2 agents)

**Dependencies**: Wave 0 complete
**Parallelism**: 2 agents, separate file ownership

### Agent 1: api-endpoints-agent

**Owns**:
- `src/processing/status_api.py` (NEW FILE)
- Updates to `src/processing/worker_webhook.py` (limited scope)

**Tasks**:
1. Create `status_api.py` with new endpoints:
   - `GET /status/{doc_id}` - Individual document status
   - `GET /status/queue` - All active processing
   - Helper functions for status formatting
2. Modify `worker_webhook.py`:
   - Import and mount status routes
   - Update webhook response to include `doc_id`
   - Add CORS verification

**Deliverables**:
- `src/processing/status_api.py` (FastAPI router)
- Modified `worker_webhook.py` (integration only)
- Unit tests for new endpoints

**Integration Points**:
- Reads from: `processing_status` global dict (existing)
- Provides: Status API endpoints (contract: `status-api.contract.md`)

### Agent 2: status-persistence-agent

**Owns**:
- `src/processing/status_manager.py` (NEW FILE)
- `src/processing/status_models.py` (NEW FILE)

**Tasks**:
1. Create `status_models.py`:
   - Pydantic models for status structures
   - Validation logic
   - Serialization helpers
2. Create `status_manager.py`:
   - StatusManager class wrapping `processing_status` dict
   - Thread-safe access methods
   - Cleanup logic for old statuses

**Deliverables**:
- `src/processing/status_models.py` (data models)
- `src/processing/status_manager.py` (state management)
- Unit tests for status manager

**Integration Points**:
- Provides: Thread-safe status access (contract: `status-manager.contract.md`)
- Used by: api-endpoints-agent, existing processor

### Validation Gate
✅ Status API endpoints return valid JSON
✅ `/status/{doc_id}` works for active and completed docs
✅ `/status/queue` returns array of status objects
✅ Webhook returns `doc_id` in response
✅ CORS allows requests from UI origin
✅ All unit tests pass

---

## Wave 2: UI Foundation (Parallel - 2 agents)

**Dependencies**: Wave 0 complete (contracts)
**Parallelism**: 2 agents, complete file separation

### Agent 3: ui-static-setup-agent

**Owns**:
- `src/ui/` directory (entire tree)
- `src/ui/index.html`
- `src/ui/status.html`
- Static file mounting in `worker_webhook.py`

**Tasks**:
1. Create UI directory structure
2. Build `index.html`:
   - Semantic HTML5 structure
   - Upload drop zone markup
   - Processing queue container
   - Format info section
3. Build `status.html`:
   - Queue-only monitoring page
4. Mount static files in worker:
   - Add StaticFiles mount to `worker_webhook.py`
   - Configure `/ui` route

**Deliverables**:
- Complete HTML structure
- Static file serving functional
- Accessible at `http://localhost:8002/ui`

**Integration Points**:
- Provides: HTML structure (contract: `ui-html.contract.md`)
- Calls: Status API endpoints (from Wave 1)

### Agent 4: ui-styling-agent

**Owns**:
- `src/ui/styles.css`
- `src/ui/components/` (CSS modules if needed)
- `src/ui/assets/` (icons, images)

**Tasks**:
1. Design color scheme and variables
2. Create base styles:
   - Layout system (grid/flexbox)
   - Typography
   - Component styles (buttons, cards, progress bars)
3. Implement responsive design
4. Add animations (progress, success, error)

**Deliverables**:
- Complete CSS styling
- Responsive layout
- UI components styled

**Integration Points**:
- Depends on: HTML class structure (from ui-static-setup-agent)
- Provides: Visual design (contract: `ui-design.contract.md`)

### Validation Gate
✅ UI accessible at http://localhost:8002/ui
✅ HTML validates (W3C)
✅ CSS loads without errors
✅ Responsive on mobile/tablet/desktop
✅ No JavaScript errors in console
✅ Static file serving works in Docker

---

## Wave 3: Client-Side Logic (Parallel - 2 agents)

**Dependencies**: Wave 1 + Wave 2 complete
**Parallelism**: 2 agents, module-based separation

### Agent 5: upload-logic-agent

**Owns**:
- `src/ui/upload.js`
- `src/ui/modules/file-validator.js`
- `src/ui/modules/copyparty-client.js`

**Tasks**:
1. Create `file-validator.js`:
   - Format detection
   - Size validation
   - Extension checking
   - Processing time estimation
2. Create `copyparty-client.js`:
   - `uploadToCopyparty()` function
   - Progress tracking
   - Error handling
3. Create `upload.js`:
   - Drag-and-drop handlers
   - File input handling
   - Upload orchestration
   - UI updates for upload phase

**Deliverables**:
- File upload functionality complete
- Validation working
- Progress tracking during upload

**Integration Points**:
- Calls: Copyparty upload API (external)
- Calls: Worker webhook API (from Wave 1)
- Updates: UI elements (from Wave 2)

### Agent 6: monitoring-logic-agent

**Owns**:
- `src/ui/monitor.js`
- `src/ui/modules/processing-monitor.js`
- `src/ui/modules/queue-manager.js`

**Tasks**:
1. Create `processing-monitor.js`:
   - ProcessingMonitor class
   - Polling mechanism
   - Status update events
   - Completion detection
2. Create `queue-manager.js`:
   - Queue display logic
   - Multi-document tracking
   - Queue polling
   - History management
3. Create `monitor.js`:
   - Progress UI updates
   - Stage indicators
   - Time formatting
   - Error display

**Deliverables**:
- Real-time monitoring functional
- Queue display working
- Progress visualization complete

**Integration Points**:
- Calls: Status API (from Wave 1)
- Updates: UI elements (from Wave 2)
- Receives: doc_id from upload-logic-agent

### Validation Gate
✅ File upload works end-to-end
✅ File validation prevents unsupported formats
✅ Progress monitoring displays real-time updates
✅ Queue shows multiple uploads correctly
✅ Completed items show success summary
✅ All error states display properly
✅ No memory leaks in polling loops

---

## Wave 4: Integration & Testing (Synchronous)

**Dependencies**: All waves 1-3 complete
**Agents**: All 6 agents collaborate

### Integration Tasks

1. **Cross-Agent Integration Tests**
   - Upload → Monitor flow
   - API → UI data binding
   - Error propagation
   - Concurrent uploads

2. **End-to-End Scenarios**
   - Single file upload (PDF)
   - Multi-file upload (mixed formats)
   - Text-only format (fast completion)
   - Large file (progress tracking)
   - Upload failure scenarios
   - Worker offline scenarios

3. **Performance Testing**
   - 10+ concurrent uploads
   - Large files (>50MB)
   - Polling overhead measurement
   - Memory usage validation

4. **Browser Compatibility**
   - Chrome, Firefox, Safari
   - Mobile browsers
   - Drag-and-drop across browsers

### Agent Assignments

**specification-agent**: Creates integration test suite
**api-endpoints-agent**: Validates API contract compliance
**status-persistence-agent**: Load testing status manager
**ui-static-setup-agent**: Browser compatibility testing
**ui-styling-agent**: Visual regression testing
**upload-logic-agent**: Upload scenario testing
**monitoring-logic-agent**: Monitoring scenario testing

### Validation Gate
✅ All integration tests pass
✅ End-to-end flows work without errors
✅ Performance meets targets (<3s for small files)
✅ No console errors in any browser
✅ Works on mobile devices
✅ Graceful degradation when services offline

---

## Wave 5: Documentation & Deployment (Parallel - 3 agents)

**Dependencies**: Wave 4 complete
**Parallelism**: 3 agents, document-based separation

### Agent Assignments

**api-endpoints-agent**:
- API documentation (OpenAPI spec)
- Developer guide for status endpoints
- Integration examples

**ui-static-setup-agent**:
- User documentation
- Screenshots/walkthrough
- Deployment guide

**monitoring-logic-agent**:
- Troubleshooting guide
- Configuration reference
- FAQ document

### Deliverables
- Complete API documentation
- User guide with screenshots
- Developer integration guide
- Deployment instructions
- Updated QUICK_START.md

### Validation Gate
✅ Documentation complete and accurate
✅ Docker deployment tested
✅ README updated with new UI URL
✅ All screenshots current

---

## Territorial Boundaries

### File Ownership Matrix

| Agent | Owns | Never Touches |
|-------|------|---------------|
| specification-agent | `.context-kit/orchestration/` | All implementation files |
| api-endpoints-agent | `src/processing/status_api.py` | UI files, status_manager internals |
| status-persistence-agent | `src/processing/status_manager.py`, `status_models.py` | API routing, UI files |
| ui-static-setup-agent | `src/ui/*.html`, static mounting | CSS details, JS logic |
| ui-styling-agent | `src/ui/styles.css`, `src/ui/assets/` | HTML structure, JS files |
| upload-logic-agent | `src/ui/upload.js`, `src/ui/modules/file-*`, `copyparty-client.js` | Monitoring logic, CSS |
| monitoring-logic-agent | `src/ui/monitor.js`, `src/ui/modules/processing-*`, `queue-manager.js` | Upload logic, CSS |

### Integration Points (Read-Only Access)

**Shared resources accessed read-only:**
- `processing_status` dict (api-endpoints-agent reads, status-persistence-agent wraps)
- HTML class names (ui-styling-agent reads from ui-static-setup-agent's HTML)
- API endpoints (monitoring-logic-agent calls api-endpoints-agent's endpoints)

---

## Conflict Prevention Strategies

### 1. New File Preference
- 95% of work creates NEW files
- Only 5% modifies existing (`worker_webhook.py`)
- Modifications limited to integration points only

### 2. Interface Contracts
- Wave 0 creates all interfaces upfront
- Agents implement against contracts, not each other's code
- Contract violations caught early by validation

### 3. Module Boundaries
- JavaScript modules prevent global namespace pollution
- Each agent's JS files are self-contained
- Communication via documented interfaces only

### 4. Progressive Integration
- Each wave has validation gate
- Integration issues caught immediately
- No "big bang" integration at end

### 5. Consumer-Driven Testing
- Monitoring agent writes tests for API agent's endpoints
- UI agent writes tests for HTML structure
- Forces contract compliance

---

## Communication Protocol

### Status Broadcasting
Each agent updates: `.context-kit/orchestration/custom-upload-ui/status/{agent-name}.json`

```json
{
  "agent": "api-endpoints-agent",
  "wave": 1,
  "status": "in-progress",
  "completion": 0.75,
  "deliverables": {
    "status_api.py": "complete",
    "worker_webhook.py": "in-progress",
    "tests": "pending"
  },
  "blockers": [],
  "timestamp": "2025-10-07T19:00:00Z"
}
```

### Daily Sync Points
- Each wave has explicit validation gate
- No agent proceeds to next wave until gate passes
- Blockers escalated immediately

---

## Risk Mitigation

### Risk 1: API Changes Break UI
**Mitigation**: OpenAPI contract validation in CI
**Fallback**: UI degrades gracefully with API errors

### Risk 2: Concurrent File Modifications
**Mitigation**: Strict territorial boundaries
**Fallback**: Git merge conflict resolution protocol

### Risk 3: Integration Test Failures
**Mitigation**: Each wave has validation gate
**Fallback**: Rollback to previous wave, fix issues

### Risk 4: Performance Issues
**Mitigation**: Load testing in Wave 4
**Fallback**: Polling interval tuning, caching strategies

---

## Success Criteria

### Technical Metrics
- ✅ Upload works for all 21 formats
- ✅ Progress updates every 2-3 seconds
- ✅ Queue handles 10+ concurrent uploads
- ✅ <100ms API response time
- ✅ Zero console errors in production

### Quality Metrics
- ✅ 100% integration test pass rate
- ✅ Zero merge conflicts during implementation
- ✅ All contracts validated
- ✅ Documentation complete

### User Experience
- ✅ Intuitive upload flow (no training needed)
- ✅ Real-time feedback (user always knows status)
- ✅ Graceful error handling (clear messages)
- ✅ Mobile-friendly interface

---

## Estimated Completion

**Wave 0**: 2-4 hours (specifications)
**Wave 1**: 4-6 hours (2 agents parallel)
**Wave 2**: 4-6 hours (2 agents parallel)
**Wave 3**: 6-8 hours (2 agents parallel)
**Wave 4**: 4-6 hours (integration)
**Wave 5**: 2-4 hours (3 agents parallel)

**Total**: 22-34 hours with 6 agents
**Sequential**: ~80 hours (70% time savings)

---

## Next Steps

1. Create integration contracts (Wave 0)
2. Assign agents to waves
3. Execute Wave 1 in parallel
4. Validate and gate
5. Continue through waves
6. Final integration validation
7. Deploy and document
