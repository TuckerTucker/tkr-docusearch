# Validation Strategy - Library Frontend

**Goal**: Ensure successful integration through progressive validation gates
**Approach**: Test after each wave, not at the end
**Philosophy**: Catch issues early, prevent cascading failures

---

## Validation Levels

### **Level 1: Syntactic Validation**
- Code parses without errors
- ES6 modules export expected symbols
- HTML is valid
- CSS has no syntax errors

### **Level 2: Contract Compliance**
- Functions match specified signatures
- Events contain required fields
- API responses match schemas
- DOM structure matches expectations

### **Level 3: Integration Validation**
- Components connect correctly
- Events propagate as expected
- WebSocket messages handled
- API calls work end-to-end

### **Level 4: Quality Validation**
- Performance targets met
- Accessibility standards met
- Security requirements met
- User experience validated

---

## Wave 0: Foundation Gate

### **Validation Criteria**

#### **1. Directory Structure**
```bash
# All directories exist
test -d /src/frontend && echo "✓ Frontend directory exists"

# All placeholder files exist
test -f /src/frontend/index.html && echo "✓ index.html exists"
test -f /src/frontend/library-manager.js && echo "✓ library-manager.js exists"
test -f /src/frontend/websocket-client.js && echo "✓ websocket-client.js exists"
test -f /src/frontend/api-client.js && echo "✓ api-client.js exists"
test -f /src/frontend/document-card.js && echo "✓ document-card.js exists"
test -f /src/frontend/filter-bar.js && echo "✓ filter-bar.js exists"
test -f /src/frontend/upload-modal.js && echo "✓ upload-modal.js exists"
test -f /src/frontend/styles.css && echo "✓ styles.css exists"
```

#### **2. Worker Configuration**
```bash
# Worker mounts frontend directory
grep -q "frontend" /src/processing/worker_webhook.py && echo "✓ Frontend mount configured"

# Worker starts successfully
./scripts/start-all.sh && echo "✓ Worker started"

# Frontend accessible
curl -s http://localhost:8002/frontend/ | grep -q "html" && echo "✓ Frontend accessible"
```

#### **3. Services Running**
```bash
# ChromaDB running
curl -s http://localhost:8001/api/v2/heartbeat && echo "✓ ChromaDB healthy"

# Worker running
curl -s http://localhost:8002/health && echo "✓ Worker healthy"

# Copyparty running
curl -s http://localhost:8000/ && echo "✓ Copyparty running"
```

**Gate Status**: ✅ All checks pass → Proceed to Wave 1

---

## Wave 1: Component Development Gate

### **Validation Criteria**

#### **1. Syntactic Validation**

**HTML (Agent 1)**:
```bash
# Valid HTML5
npx html-validator /src/frontend/index.html && echo "✓ HTML valid"

# All required IDs present
grep -q 'id="document-grid"' /src/frontend/index.html && echo "✓ #document-grid present"
grep -q 'id="filter-bar"' /src/frontend/index.html && echo "✓ #filter-bar present"
grep -q 'id="connection-status"' /src/frontend/index.html && echo "✓ #connection-status present"
```

**JavaScript Modules**:
```bash
# No syntax errors (use Node to parse)
node --check /src/frontend/library-manager.js && echo "✓ library-manager.js syntax valid"
node --check /src/frontend/websocket-client.js && echo "✓ websocket-client.js syntax valid"
node --check /src/frontend/api-client.js && echo "✓ api-client.js syntax valid"
node --check /src/frontend/document-card.js && echo "✓ document-card.js syntax valid"
node --check /src/frontend/filter-bar.js && echo "✓ filter-bar.js syntax valid"
node --check /src/frontend/upload-modal.js && echo "✓ upload-modal.js syntax valid"
```

**CSS**:
```bash
# No CSS errors
npx stylelint /src/frontend/styles.css && echo "✓ CSS valid"
```

---

#### **2. Export Validation**

**library-manager.js**:
```javascript
// Test in browser console or Node
import * as lib from './library-manager.js';
console.assert(typeof lib.LibraryManager === 'function', '✓ LibraryManager exported');
```

**websocket-client.js**:
```javascript
import * as ws from './websocket-client.js';
console.assert(typeof ws.WebSocketClient === 'function', '✓ WebSocketClient exported');
```

**api-client.js**:
```javascript
import * as api from './api-client.js';
console.assert(typeof api.DocumentsAPIClient === 'function', '✓ DocumentsAPIClient exported');
```

**document-card.js**:
```javascript
import * as card from './document-card.js';
console.assert(typeof card.createDocumentCard === 'function', '✓ createDocumentCard exported');
console.assert(typeof card.updateCardState === 'function', '✓ updateCardState exported');
console.assert(typeof card.Icons === 'object', '✓ Icons exported');
```

**filter-bar.js**:
```javascript
import * as filter from './filter-bar.js';
console.assert(typeof filter.FilterBar === 'function', '✓ FilterBar exported');
```

**upload-modal.js**:
```javascript
import * as upload from './upload-modal.js';
console.assert(typeof upload.UploadModal === 'function', '✓ UploadModal exported');
```

---

#### **3. Browser Console Validation**

Open `http://localhost:8002/frontend/` and check:

```javascript
// No console errors
// Expected output: Empty (no errors)

// Modules loaded
console.log(typeof LibraryManager);  // → "function"
console.log(typeof createDocumentCard);  // → "function"

// DOM elements present
console.log(document.getElementById('document-grid'));  // → HTMLElement
console.log(document.getElementById('filter-bar'));  // → HTMLElement
console.log(document.getElementById('connection-status'));  // → HTMLElement
```

---

#### **4. Contract Compliance Spot Checks**

**DocumentCard API**:
```javascript
// Create completed card
const card = createDocumentCard({
  filename: 'test.pdf',
  thumbnailUrl: '',
  dateAdded: new Date(),
  detailsUrl: '#test',
  state: 'completed'
});

// Validate result
console.assert(card instanceof HTMLElement, '✓ Returns HTMLElement');
console.assert(card.classList.contains('document-card'), '✓ Has base class');
console.assert(card.querySelector('.document-card__title'), '✓ Has title element');
console.assert(card.querySelector('.document-card__button'), '✓ Has button');

// Create processing card
const processingCard = createDocumentCard({
  filename: 'test2.pdf',
  thumbnailUrl: '',
  dateAdded: new Date(),
  detailsUrl: '#test2',
  state: 'processing',
  processingStatus: { stage: 'Embedding', progress: 0.5 }
});

console.assert(processingCard.classList.contains('document-card--processing'), '✓ Has processing class');
console.assert(processingCard.querySelector('.document-card__spinner'), '✓ Has spinner');
console.assert(processingCard.querySelector('.document-card__progress-bar'), '✓ Has progress bar');

// Test update
updateCardState(processingCard, { state: 'processing', stage: 'Storing', progress: 0.9 });
const progressBar = processingCard.querySelector('.document-card__progress-bar');
console.assert(progressBar.style.width === '90%', '✓ Progress bar updated');
```

**FilterBar Events**:
```javascript
// Listen for event
let eventReceived = false;
document.addEventListener('filterChange', (e) => {
  eventReceived = true;
  console.log('✓ filterChange event received', e.detail);
  console.assert('search' in e.detail, '✓ Event has search field');
  console.assert('sort_by' in e.detail, '✓ Event has sort_by field');
  console.assert('file_types' in e.detail, '✓ Event has file_types field');
});

// Trigger filter change (manually change dropdown or search)
// Then verify
setTimeout(() => {
  console.assert(eventReceived, '✓ Event was dispatched');
}, 1000);
```

---

**Gate Status**: ✅ All checks pass → Proceed to Wave 2

---

## Wave 2: Integration & Testing Gate

### **Validation Criteria**

#### **1. Integration Tests** (Agent 7)

Run test suite:
```bash
# Run integration tests
node /src/frontend/test-integration.js

# Expected output:
# ✓ LibraryManager initializes
# ✓ WebSocketClient connects
# ✓ DocumentsAPIClient queries /documents
# ✓ DocumentCard renders
# ✓ FilterBar emits events
# ✓ UploadModal validates files
# ✓ All integration tests passed (X/X)
```

**Coverage Target**: >80%

---

#### **2. E2E Tests** (Agent 8)

Manual testing checklist in `E2E_TEST_RESULTS.md`:

**Initial Load**:
- [ ] Page loads without errors
- [ ] Documents fetched from API
- [ ] Cards rendered in grid
- [ ] Thumbnails loaded (or placeholders shown)
- [ ] Connection status shows "Connected"

**WebSocket Integration**:
- [ ] Upload a new document via Copyparty
- [ ] Loading card appears in grid
- [ ] WebSocket sends `status_update` messages
- [ ] Card updates to processing state
- [ ] Progress bar animates
- [ ] Stage label updates
- [ ] Card updates to completed state
- [ ] Thumbnail appears

**Filtering**:
- [ ] Search for filename works
- [ ] Sort by date works
- [ ] Sort by filename works
- [ ] Sort by page count works
- [ ] File type filter works
- [ ] Clear filters works
- [ ] URL params update

**Pagination**:
- [ ] Next button loads page 2
- [ ] Previous button returns to page 1
- [ ] Page numbers accurate
- [ ] Scroll to top on page change

**Upload Modal**:
- [ ] Drag file over page → modal shows
- [ ] Drop file → upload starts
- [ ] Progress bar shows during upload
- [ ] Multiple files upload in sequence
- [ ] Invalid file shows error
- [ ] Large file shows error
- [ ] Modal closes after completion

**Error States**:
- [ ] Stop worker → connection status shows "Disconnected"
- [ ] Restart worker → reconnects automatically
- [ ] Invalid API response handled gracefully
- [ ] Network error shown appropriately

**Responsive Design**:
- [ ] Desktop (1920×1080): Grid layout correct
- [ ] Tablet (768×1024): Grid adapts
- [ ] Mobile (375×667): Grid single column
- [ ] Sticky header works on all sizes
- [ ] Sticky filter bar works on all sizes

**Accessibility**:
- [ ] Keyboard navigation works (Tab, Enter, Esc)
- [ ] Focus visible on all interactive elements
- [ ] Modal focus trap works
- [ ] ARIA labels present
- [ ] Screen reader announces updates (test with VoiceOver/NVDA)
- [ ] Color contrast meets WCAG AA
- [ ] Alt text on images

---

#### **3. Performance Validation** (Agent 10)

**Metrics**:
```javascript
// In browser DevTools Performance tab
// Record page load

// Targets:
// - Load Time: <2s
// - First Contentful Paint: <1s
// - Time to Interactive: <3s
// - WebSocket connection: <500ms
// - API query: <300ms
// - Card render (50 docs): <100ms
```

**Memory**:
```javascript
// In DevTools Memory tab
// Take heap snapshot

// Check for:
// - No detached DOM nodes
// - WebSocket cleanup works
// - Event listeners removed on destroy
```

---

#### **4. Documentation Validation** (Agent 9)

**README Completeness**:
- [ ] Architecture overview present
- [ ] API integration documented
- [ ] WebSocket usage documented
- [ ] Development setup instructions
- [ ] Code examples provided

**Project Documentation**:
- [ ] `_context-kit.yml` updated with frontend section
- [ ] `QUICK_START.md` includes UI access
- [ ] All integration contracts referenced

---

**Gate Status**: ✅ All checks pass → Proceed to Wave 3

---

## Wave 3: Production Readiness Gate

### **Validation Criteria**

#### **1. Performance Report** (Agent 10)

**Report Must Include**:
- [ ] Load time benchmarks
- [ ] Bundle size analysis
- [ ] Memory usage profile
- [ ] WebSocket reconnection timing
- [ ] Lazy loading verification
- [ ] Optimizations implemented
- [ ] Before/after comparisons

**Targets**:
- Load time: <2s ✓
- FCP: <1s ✓
- TTI: <3s ✓
- Bundle size: <500KB ✓

---

#### **2. Cleanup Validation** (Agent 11)

**POC Removal**:
```bash
# Verify POC pages removed
test ! -d /data/copyparty/www && echo "✓ POC directory removed"

# No references remain
! grep -r "copyparty/www" /src/ /docs/ && echo "✓ No references to POC"
```

**Documentation Updated**:
- [ ] All references to POC removed
- [ ] New frontend documented
- [ ] Migration guide provided (if needed)

---

#### **3. Production Deployment**

**Pre-deployment Checklist**:
- [ ] All tests pass
- [ ] Performance targets met
- [ ] Accessibility validated (WCAG AA)
- [ ] Security review complete (XSS, CSRF, path traversal)
- [ ] Error handling comprehensive
- [ ] Logging appropriate
- [ ] Documentation complete

**Deployment Verification**:
```bash
# Start all services
./scripts/start-all.sh

# Verify frontend accessible
curl -s http://localhost:8002/frontend/ | grep -q "DocuSearch" && echo "✓ Frontend deployed"

# Verify WebSocket working
# (Use browser test or wscat)

# Verify upload working
# (Upload test file via Copyparty)

# Verify search working
# (Query /documents API)
```

---

**Gate Status**: ✅ All checks pass → **PRODUCTION READY**

---

## Automated Validation Script

Create `/src/frontend/validate.sh`:

```bash
#!/bin/bash
set -e

echo "========================================="
echo "Library Frontend Validation"
echo "========================================="

# Wave 0: Foundation
echo "Checking Wave 0: Foundation..."
test -d src/frontend || { echo "✗ Frontend directory missing"; exit 1; }
test -f src/frontend/index.html || { echo "✗ index.html missing"; exit 1; }
echo "✓ Wave 0: Foundation complete"

# Wave 1: Syntax
echo "Checking Wave 1: Syntax..."
node --check src/frontend/*.js || { echo "✗ JavaScript syntax errors"; exit 1; }
npx html-validator src/frontend/index.html || { echo "✗ HTML validation failed"; exit 1; }
echo "✓ Wave 1: Syntax valid"

# Wave 2: Integration
echo "Checking Wave 2: Integration..."
node src/frontend/test-integration.js || { echo "✗ Integration tests failed"; exit 1; }
echo "✓ Wave 2: Integration tests passed"

# Wave 3: Production
echo "Checking Wave 3: Production readiness..."
test -f src/frontend/PERFORMANCE_REPORT.md || { echo "✗ Performance report missing"; exit 1; }
test ! -d data/copyparty/www || { echo "✗ POC not removed"; exit 1; }
echo "✓ Wave 3: Production ready"

echo "========================================="
echo "✓ ALL VALIDATION CHECKS PASSED"
echo "========================================="
```

Usage:
```bash
chmod +x src/frontend/validate.sh
./src/frontend/validate.sh
```

---

## Failure Recovery

### **Wave 1 Failure**

**Scenario**: Agent 3 (document-card) has syntax error

**Action**:
1. Identify failing agent
2. Review contract compliance
3. Fix syntax error
4. Re-run validation
5. Do NOT proceed to Wave 2 until fixed

### **Wave 2 Failure**

**Scenario**: WebSocket integration broken

**Action**:
1. Review integration contract
2. Check message format
3. Verify event handling
4. Fix integration issue
5. Re-run E2E tests
6. Do NOT proceed to Wave 3 until fixed

### **Wave 3 Failure**

**Scenario**: Performance targets not met

**Action**:
1. Review performance report
2. Identify bottlenecks
3. Implement optimizations
4. Re-measure performance
5. Do NOT deploy until targets met

---

## Success Criteria Summary

**Wave 0**: Infrastructure ready ✓
**Wave 1**: All components implemented and syntactically valid ✓
**Wave 2**: Integration working, tests passing ✓
**Wave 3**: Performance targets met, production ready ✓

**Overall Success**: Fully functional Library UI with real-time updates, accessible at `http://localhost:8002/frontend/`
