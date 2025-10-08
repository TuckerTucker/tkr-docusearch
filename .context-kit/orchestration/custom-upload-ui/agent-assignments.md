# Agent Assignments - Custom Upload UI

## Agent Roster (6 Agents)

### 1. specification-agent
**Role**: Contract Architect
**Wave**: 0 (Foundation)
**Expertise**: API design, data modeling, integration specifications

**Responsibilities**:
- Define all integration contracts
- Create JSON schemas for data structures
- Write OpenAPI specifications for endpoints
- Establish validation criteria for each wave
- Create test data fixtures

**Deliverables**:
- `integration-contracts/status-api.contract.md`
- `integration-contracts/status-manager.contract.md`
- `integration-contracts/ui-html.contract.md`
- `integration-contracts/ui-design.contract.md`
- `integration-contracts/schemas/*.json`

**Success Criteria**:
- All contracts have clear acceptance tests
- Schemas validate with example data
- No ambiguous specifications

---

### 2. api-endpoints-agent
**Role**: Backend API Developer
**Wave**: 1
**Expertise**: FastAPI, REST APIs, HTTP protocols

**Responsibilities**:
- Implement new status API endpoints
- Modify worker webhook to return doc_id
- Add CORS configuration
- Write endpoint unit tests
- Create API documentation

**File Ownership**:
- `src/processing/status_api.py` (NEW)
- `src/processing/worker_webhook.py` (limited modifications)
- `src/processing/test_status_api.py` (NEW)

**Integration Points**:
- **Reads**: `processing_status` dict (via StatusManager)
- **Provides**: HTTP endpoints conforming to `status-api.contract.md`
- **Depends on**: status-persistence-agent's StatusManager

**Acceptance Tests**:
```python
# GET /status/{doc_id}
assert response.status_code == 200
assert response.json()["doc_id"] == test_doc_id
assert "progress" in response.json()

# GET /status/queue
assert response.status_code == 200
assert isinstance(response.json(), list)
assert all("status" in item for item in response.json())

# POST /webhook returns doc_id
assert "doc_id" in webhook_response.json()
```

**Communication**:
- Publishes: `.context-kit/orchestration/custom-upload-ui/status/api-endpoints-agent.json`
- Reviews: status-persistence-agent's StatusManager interface

---

### 3. status-persistence-agent
**Role**: State Management Engineer
**Wave**: 1 (parallel with api-endpoints-agent)
**Expertise**: Data structures, thread safety, state management

**Responsibilities**:
- Create Pydantic models for status objects
- Build thread-safe StatusManager class
- Implement status cleanup/expiry logic
- Write state management tests
- Document state lifecycle

**File Ownership**:
- `src/processing/status_models.py` (NEW)
- `src/processing/status_manager.py` (NEW)
- `src/processing/test_status_manager.py` (NEW)

**Integration Points**:
- **Wraps**: `processing_status` dict (existing global)
- **Provides**: StatusManager interface per `status-manager.contract.md`
- **Used by**: api-endpoints-agent, existing DocumentProcessor

**Acceptance Tests**:
```python
# Thread-safe access
manager = StatusManager()
assert manager.get_status("doc_123") is not None
assert manager.list_active() returns list

# Model validation
status = ProcessingStatus(**test_data)
assert status.progress >= 0 and status.progress <= 1
assert status.status in VALID_STATUSES
```

**Communication**:
- Publishes: `.context-kit/orchestration/custom-upload-ui/status/status-persistence-agent.json`
- Coordinates: With api-endpoints-agent on StatusManager interface

---

### 4. ui-static-setup-agent
**Role**: UI Structure Architect
**Wave**: 2
**Expertise**: HTML5, semantic markup, accessibility

**Responsibilities**:
- Design HTML structure for upload page
- Create status monitoring page
- Mount static files in FastAPI worker
- Ensure accessibility (ARIA labels, keyboard nav)
- Write structural documentation

**File Ownership**:
- `src/ui/` (directory structure)
- `src/ui/index.html` (NEW)
- `src/ui/status.html` (NEW)
- `src/processing/worker_webhook.py` (StaticFiles mount only)

**Integration Points**:
- **Provides**: HTML structure per `ui-html.contract.md`
- **Used by**: ui-styling-agent (CSS classes), upload/monitoring agents (JS)
- **Calls**: Status API endpoints (via JavaScript)

**Acceptance Tests**:
```bash
# Static files accessible
curl http://localhost:8002/ui/ # Returns index.html
curl http://localhost:8002/ui/status.html # Returns status page

# HTML validation
validator src/ui/index.html # No errors

# Accessibility
axe-core audit # No violations
```

**Communication**:
- Publishes: `.context-kit/orchestration/custom-upload-ui/status/ui-static-setup-agent.json`
- Coordinates: With ui-styling-agent on class naming conventions

---

### 5. ui-styling-agent
**Role**: Visual Design Engineer
**Wave**: 2 (parallel with ui-static-setup-agent)
**Expertise**: CSS3, responsive design, animations

**Responsibilities**:
- Design color scheme and visual identity
- Implement responsive layout system
- Create component styles (buttons, progress bars, cards)
- Add animations and transitions
- Ensure mobile-first design

**File Ownership**:
- `src/ui/styles.css` (NEW)
- `src/ui/components/` (CSS modules if needed)
- `src/ui/assets/` (icons, images)

**Integration Points**:
- **Depends on**: ui-static-setup-agent's HTML structure
- **Provides**: Visual design per `ui-design.contract.md`
- **Reads**: HTML class names (read-only)

**Acceptance Tests**:
```bash
# CSS validates
css-validator src/ui/styles.css # No errors

# Responsive design
# - Mobile: 375px width
# - Tablet: 768px width
# - Desktop: 1200px width

# Color contrast
lighthouse --accessibility # Score > 95
```

**Communication**:
- Publishes: `.context-kit/orchestration/custom-upload-ui/status/ui-styling-agent.json`
- Reviews: ui-static-setup-agent's HTML for class names

---

### 6. upload-logic-agent
**Role**: Upload Flow Developer
**Wave**: 3
**Expertise**: JavaScript, File API, HTTP clients

**Responsibilities**:
- Implement drag-and-drop upload
- Build file validation logic
- Create Copyparty upload client
- Handle upload progress tracking
- Write upload flow tests

**File Ownership**:
- `src/ui/upload.js` (NEW)
- `src/ui/modules/file-validator.js` (NEW)
- `src/ui/modules/copyparty-client.js` (NEW)

**Integration Points**:
- **Calls**: Copyparty upload API (external)
- **Calls**: Worker webhook API (from api-endpoints-agent)
- **Updates**: HTML elements (from ui-static-setup-agent)
- **Provides**: doc_id to monitoring-logic-agent

**Acceptance Tests**:
```javascript
// File validation
assert(validateFile("test.pdf") === true);
assert(validateFile("test.exe") === false);

// Upload flow
const result = await uploadFile(testFile);
assert(result.doc_id !== undefined);
assert(result.status === "accepted");

// Error handling
const badResult = await uploadFile(oversizedFile);
assert(badResult.error !== undefined);
```

**Communication**:
- Publishes: `.context-kit/orchestration/custom-upload-ui/status/upload-logic-agent.json`
- Coordinates: With monitoring-logic-agent on doc_id handoff

---

### 7. monitoring-logic-agent
**Role**: Real-Time Monitoring Developer
**Wave**: 3 (parallel with upload-logic-agent)
**Expertise**: JavaScript, event-driven programming, async patterns

**Responsibilities**:
- Build ProcessingMonitor class
- Implement status polling mechanism
- Create queue display logic
- Handle progress visualization
- Write monitoring flow tests

**File Ownership**:
- `src/ui/monitor.js` (NEW)
- `src/ui/modules/processing-monitor.js` (NEW)
- `src/ui/modules/queue-manager.js` (NEW)

**Integration Points**:
- **Calls**: Status API endpoints (from api-endpoints-agent)
- **Updates**: HTML elements (from ui-static-setup-agent)
- **Receives**: doc_id from upload-logic-agent
- **Provides**: Progress updates per `monitoring.contract.md`

**Acceptance Tests**:
```javascript
// ProcessingMonitor
const monitor = new ProcessingMonitor(doc_id);
monitor.start();
assert(monitor.polling === true);

// Queue manager
const queue = new QueueManager();
queue.addDocument(doc_id);
assert(queue.getActive().includes(doc_id));

// Progress updates
monitor.on('progress', (status) => {
  assert(status.progress >= 0 && status.progress <= 1);
});
```

**Communication**:
- Publishes: `.context-kit/orchestration/custom-upload-ui/status/monitoring-logic-agent.json`
- Coordinates: With upload-logic-agent on doc_id handoff

---

## Cross-Agent Dependencies

### Wave 1 Dependencies
```
status-persistence-agent (StatusManager)
    ↓ (provides interface)
api-endpoints-agent (Status API)
```

### Wave 2 Dependencies
```
ui-static-setup-agent (HTML structure)
    ↓ (provides class names)
ui-styling-agent (CSS styling)
```

### Wave 3 Dependencies
```
api-endpoints-agent (Status API)
    ↓ (provides endpoints)
monitoring-logic-agent (Polling)

upload-logic-agent (Upload flow)
    ↓ (provides doc_id)
monitoring-logic-agent (Progress tracking)

ui-static-setup-agent (HTML elements)
    ↓ (provides DOM structure)
upload-logic-agent + monitoring-logic-agent (DOM updates)
```

---

## Synchronization Points

### Wave 0 → Wave 1 Gate
- ✅ All contracts published
- ✅ Schemas validate
- ✅ Test fixtures created

### Wave 1 → Wave 2 Gate
- ✅ Status API endpoints working
- ✅ Webhook returns doc_id
- ✅ Unit tests pass
- ✅ CORS configured

### Wave 2 → Wave 3 Gate
- ✅ HTML accessible at http://localhost:8002/ui
- ✅ CSS loads without errors
- ✅ Responsive design verified
- ✅ No console errors

### Wave 3 → Wave 4 Gate
- ✅ Upload flow complete
- ✅ Monitoring displays progress
- ✅ Queue shows multiple uploads
- ✅ Integration tests pass

---

## Conflict Resolution Protocol

### If Multiple Agents Need Same File

1. **Check Territorial Boundaries**: Verify assignment
2. **Negotiate Interface**: Create shared interface file
3. **One Owns, Others Read**: Owner modifies, others read-only
4. **Escalate**: If unresolved, specification-agent mediates

### If Contract Violation Detected

1. **Consumer Reports**: Agent using interface reports issue
2. **Provider Fixes**: Agent providing interface fixes
3. **Contract Updated**: specification-agent updates contract
4. **Re-validate**: Both parties validate fix

### If Integration Test Fails

1. **Identify Boundary**: Which integration point failed?
2. **Responsible Agents**: Both sides investigate
3. **Root Cause**: Determine if contract issue or implementation
4. **Fix + Re-test**: Fix and validate before proceeding

---

## Agent Success Metrics

Each agent measured on:
- ✅ **Deliverables Complete**: All owned files delivered
- ✅ **Tests Passing**: Unit/integration tests green
- ✅ **Contract Compliance**: Validates against specifications
- ✅ **No Conflicts**: Zero merge conflicts
- ✅ **Documentation**: Code comments, README updates
- ✅ **On Schedule**: Completes within wave timeline
