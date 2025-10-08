# Wave 4 Test Plan - Integration & Testing

**Wave**: 4 (Integration & Testing)
**Status**: 🔄 IN PROGRESS
**Date**: 2025-10-07
**Agents**: integration-test-agent, browser-test-agent

## Overview

Wave 4 focuses on validating the integration of all components from Waves 1-3 and ensuring the upload UI works correctly in real browsers.

## Test Strategy

### Phase 1: Static Analysis (Automated)
- Validate JavaScript syntax
- Check import/export consistency
- Validate HTML structure
- Check CSS classes referenced in JS

### Phase 2: Integration Testing (Automated)
- Mock API responses
- Test upload flow end-to-end
- Test monitoring flow end-to-end
- Test error handling

### Phase 3: Runtime Testing (Manual)
- Start services (worker, ChromaDB, Copyparty)
- Test in browser (Chrome, Firefox)
- Test upload and monitoring
- Performance testing

### Phase 4: Browser Compatibility (Manual)
- Chrome/Edge (Chromium)
- Firefox
- Safari (if available)

## Phase 1: Static Analysis

### JavaScript Syntax Validation

**Goal**: Ensure all JavaScript files are syntactically valid

**Files to Check**:
- `src/ui/upload.js`
- `src/ui/monitor.js`
- `src/ui/modules/file-validator.js`
- `src/ui/modules/copyparty-client.js`
- `src/ui/modules/processing-monitor.js`
- `src/ui/modules/queue-manager.js`

**Method**: Use Node.js to parse files and check for syntax errors

**Expected Result**: All files parse without syntax errors

### Import/Export Consistency

**Goal**: Ensure all imports match exports

**Checks**:
1. `upload.js` imports from `modules/file-validator.js`
   - Expected exports: `validateFile`, `getFormatType`, `estimateProcessingTime`, `formatFileSize`, `getFormatName`

2. `upload.js` imports from `modules/copyparty-client.js`
   - Expected exports: `uploadToCopyparty`, `uploadMultipleFiles`, `isTempDocId`, `resolveDocId`

3. `monitor.js` imports from `modules/processing-monitor.js`
   - Expected exports: `ProcessingMonitor`, `formatStatus`, `formatProgress`, `formatElapsedTime`, `calculateElapsedTime`, `formatError`

4. `monitor.js` imports from `modules/queue-manager.js`
   - Expected exports: `QueueManager`, `createStatusBadge`, `createProgressBar`

5. `queue-manager.js` imports from `modules/processing-monitor.js`
   - Expected exports: `formatStatus`, `formatProgress`, `formatElapsedTime`, `calculateElapsedTime`, `formatError`

**Method**: Grep for `export` statements and compare with `import` statements

**Expected Result**: All imports have matching exports

### HTML Structure Validation

**Goal**: Ensure all DOM elements referenced in JS exist in HTML

**Required Elements**:
- `#drop-zone` (upload.js)
- `#file-input` (upload.js)
- `#queue-items` (upload.js, monitor.js)
- `#queue-empty` (upload.js, monitor.js)
- `#queue-section` (upload.js, monitor.js)
- `#queue-active-count` (monitor.js)
- `#queue-completed-count` (monitor.js)
- `#toast-container` (upload.js, monitor.js)

**Method**: Grep for `getElementById()` calls in JS and check HTML files

**Expected Result**: All required elements exist in index.html and status.html

### CSS Class Validation

**Goal**: Ensure all CSS classes used in JS exist in styles.css

**Classes Used in JS**:
- `drop-zone--active`
- `drop-zone--error`
- `queue-item`
- `queue-item--processing`
- `queue-item--completed`
- `queue-item--failed`
- `toast`
- `toast--success`
- `toast--error`
- `toast--warning`
- `toast--hiding`

**Method**: Grep for class assignments in JS and check styles.css

**Expected Result**: All classes defined in styles.css

## Phase 2: Integration Testing

### Test 1: File Validation Flow

**Scenario**: User selects invalid file

**Steps**:
1. Create mock file with `.exe` extension
2. Call `validateFile(mockFile)`
3. Check result

**Expected Behavior**:
- `result.valid === false`
- `result.error` contains "Unsupported format"
- `result.supportedFormats` is an array

**Test Code**:
```javascript
// Mock file
const mockFile = { name: 'virus.exe', size: 1024 };
const result = validateFile(mockFile);
assert(result.valid === false);
assert(result.error.includes('Unsupported format'));
```

### Test 2: File Upload Flow

**Scenario**: User uploads valid PDF file

**Steps**:
1. Create mock PDF file
2. Mock XHR (or use real upload to Copyparty)
3. Call `uploadToCopyparty(mockFile)`
4. Check result

**Expected Behavior**:
- Upload initiated via XHR POST
- Progress callbacks called
- Success result with `doc_id`

**Test Code**:
```javascript
// Mock file
const mockFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' });

// Track progress
let progressCalled = false;
const result = await uploadToCopyparty(mockFile, {
    onProgress: (pct) => { progressCalled = true; }
});

assert(result.success === true);
assert(result.doc_id !== undefined);
assert(progressCalled === true);
```

### Test 3: Status Monitoring Flow

**Scenario**: Monitor document processing

**Steps**:
1. Create ProcessingMonitor instance
2. Mock `/status/queue` endpoint response
3. Start monitoring document
4. Check status updates

**Expected Behavior**:
- Monitor polls `/status/queue`
- `onStatusUpdate` callback called
- Status tracked in `trackedDocs` map

**Test Code**:
```javascript
// Mock API
global.fetch = async (url) => ({
    ok: true,
    json: async () => ({
        active: [{ doc_id: 'abc123', status: 'parsing', progress: 0.5 }],
        completed: []
    })
});

let updateCalled = false;
const monitor = new ProcessingMonitor({
    pollInterval: 100,
    onStatusUpdate: (docId, status) => { updateCalled = true; }
});

monitor.startMonitoring('abc123');
await sleep(200); // Wait for poll
assert(updateCalled === true);
```

### Test 4: Queue Manager Flow

**Scenario**: Update queue item from status data

**Steps**:
1. Create QueueManager instance
2. Add queue item
3. Update with status data
4. Check DOM updates

**Expected Behavior**:
- Queue item created in DOM
- Status text updated
- Progress bar updated
- Statistics updated

**Test Code**:
```javascript
// Mock DOM
document.body.innerHTML = `
    <div id="queue-items"></div>
    <div id="queue-empty"></div>
    <span id="queue-active-count">0</span>
    <span id="queue-completed-count">0</span>
`;

const queueManager = new QueueManager();
queueManager.addQueueItem('abc123', { filename: 'test.pdf', status: 'parsing', progress: 0.5 });

const item = queueManager.getQueueItem('abc123');
assert(item !== null);
assert(item.querySelector('.queue-item-filename').textContent === 'test.pdf');
assert(item.querySelector('.progress-fill').style.width === '50%');
```

### Test 5: End-to-End Upload + Monitor

**Scenario**: Complete flow from file selection to completion

**Steps**:
1. Mock file selection (drag-and-drop)
2. Mock Copyparty upload
3. Mock status API
4. Trigger upload
5. Wait for completion

**Expected Behavior**:
- File validated
- Upload initiated
- Queue item created
- Status polling started
- Queue item updated to completed
- Toast notification shown

**Test Code**:
```javascript
// Setup mocks
setupMockDOM();
setupMockFetch();
setupMockXHR();

// Trigger upload
const mockFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });
await handleFiles([mockFile]);

// Wait for upload and monitoring
await sleep(5000);

// Check results
const queueItem = document.querySelector('[data-doc-id]');
assert(queueItem !== null);
assert(queueItem.classList.contains('queue-item--completed'));

const toast = document.querySelector('.toast--success');
assert(toast !== null);
```

## Phase 3: Runtime Testing

### Prerequisites

**Start Services**:
```bash
./scripts/start-all.sh
```

**Verify Services Running**:
- ChromaDB: http://localhost:8001/api/v2/heartbeat
- Copyparty: http://localhost:8000/
- Worker: http://localhost:8002/health
- UI: http://localhost:8002/ui/

### Test 1: Upload Page Load

**URL**: http://localhost:8002/ui/

**Checks**:
- [ ] Page loads without errors
- [ ] No console errors
- [ ] Drop zone visible
- [ ] "Browse" link clickable
- [ ] Format info accordion works
- [ ] Queue section visible (or empty state shown)

**Console Logs Expected**:
```
Upload module initialized
Monitor module initialized
```

### Test 2: File Validation - Invalid Format

**Steps**:
1. Create a `.exe` file (or rename any file to `.exe`)
2. Drag onto drop zone
3. Observe

**Expected Behavior**:
- [ ] Drop zone highlights on dragover
- [ ] Toast notification appears with error
- [ ] Error message: "Unsupported format: .exe"
- [ ] No queue item created

### Test 3: File Validation - Large File

**Steps**:
1. Create a 15 MB file (larger than 10 MB warning threshold)
2. Drag onto drop zone
3. Observe

**Expected Behavior**:
- [ ] Toast notification appears with warning
- [ ] Warning message: "Large file (15.00 MB) - processing may take longer"
- [ ] Upload proceeds

### Test 4: Single File Upload

**Steps**:
1. Create a small PDF file (< 1 MB)
2. Drag onto drop zone
3. Observe upload and processing

**Expected Behavior**:
- [ ] Queue item appears immediately
- [ ] Filename shown correctly
- [ ] Upload progress bar moves (0% → 100%)
- [ ] Status changes: "Uploading..." → "Queued..." → "Parsing document" → etc.
- [ ] Progress bar continues to update during processing
- [ ] Elapsed time updates every 1-2 seconds
- [ ] Page progress shown (e.g., "Page 1/5")
- [ ] Completion toast appears
- [ ] Queue item marked as completed (green)
- [ ] Queue statistics update (Active: 0, Completed: 1)

**Console Logs Expected**:
```
Processing 1 file(s)
test.pdf: 100.0% (1.2 MB / 1.2 MB)
Upload successful: test.pdf (doc_id: abc123...)
Starting monitoring for abc123... (test.pdf)
Status update: abc123... -> parsing
Status update: abc123... -> embedding_visual
...
Status update: abc123... -> completed
Document completed: abc123...
```

### Test 5: Multi-File Upload

**Steps**:
1. Select 5 PDF files
2. Drag onto drop zone simultaneously
3. Observe

**Expected Behavior**:
- [ ] All 5 files appear in queue immediately
- [ ] Max 3 uploads running concurrently
- [ ] Upload progress shown for each file
- [ ] All files transition to processing
- [ ] All files complete successfully
- [ ] Queue statistics: Active varies, Completed increases

### Test 6: Status Page

**Steps**:
1. Upload a file via index.html
2. Open http://localhost:8002/ui/status.html in new tab
3. Observe

**Expected Behavior**:
- [ ] Existing queue items loaded from API
- [ ] Status updates in real-time
- [ ] Statistics shown (Active, Completed)
- [ ] No upload UI (only monitoring)

**Console Logs Expected**:
```
Monitor module initialized
Loaded existing queue from API
```

### Test 7: Error Handling - Network Failure

**Steps**:
1. Stop worker: `./scripts/stop-all.sh`
2. Try to upload a file
3. Observe

**Expected Behavior**:
- [ ] Upload fails after retries
- [ ] Error toast shown
- [ ] Queue item marked as failed (red)
- [ ] Error message displayed in queue item

### Test 8: Error Handling - Oversized File

**Steps**:
1. Create a 150 MB file (larger than 100 MB limit)
2. Drag onto drop zone
3. Observe

**Expected Behavior**:
- [ ] Error toast shown immediately
- [ ] Error message: "File too large: 150.00 MB (max 100 MB)"
- [ ] No queue item created
- [ ] No upload attempted

## Phase 4: Browser Compatibility

### Chrome/Edge Testing

**Version**: Chrome 120+ or Edge 120+

**Tests**:
- [ ] ES6 modules load correctly
- [ ] Fetch API works
- [ ] XHR upload progress works
- [ ] Drag-and-drop works
- [ ] File input works
- [ ] Toast animations work
- [ ] Progress bars animate smoothly

### Firefox Testing

**Version**: Firefox 120+

**Tests**:
- [ ] ES6 modules load correctly
- [ ] Fetch API works
- [ ] XHR upload progress works
- [ ] Drag-and-drop works
- [ ] File input works
- [ ] Toast animations work
- [ ] Progress bars animate smoothly

### Safari Testing

**Version**: Safari 17+ (if available on macOS)

**Tests**:
- [ ] ES6 modules load correctly
- [ ] Fetch API works
- [ ] XHR upload progress works
- [ ] Drag-and-drop works
- [ ] File input works
- [ ] Toast animations work
- [ ] Progress bars animate smoothly

## Performance Testing

### Upload Performance

**Test**: Upload 10 MB PDF

**Metrics**:
- Upload time: Should be < 5 seconds on localhost
- Progress updates: Should be smooth (at least 10 updates)
- CPU usage: Should be < 20% during upload

### Polling Performance

**Test**: Monitor 10 documents simultaneously

**Metrics**:
- Polling interval: Should be consistent at 2 seconds
- CPU usage: Should be < 10% during polling
- Network traffic: ~1 request every 2 seconds

### UI Responsiveness

**Test**: Scroll queue with 50 items

**Metrics**:
- Scroll should be smooth (60 FPS)
- No lag when updating items
- Toast notifications don't block UI

## Accessibility Testing

### Keyboard Navigation

**Tests**:
- [ ] Tab to "browse" link (file input)
- [ ] Enter to open file picker
- [ ] Tab through queue items
- [ ] Screen reader announces status updates

### Screen Reader Testing

**Tool**: VoiceOver (macOS) or NVDA (Windows)

**Tests**:
- [ ] Drop zone label read correctly
- [ ] File input label read correctly
- [ ] Queue item status announced
- [ ] Toast notifications announced (aria-live)

## Validation Criteria

### All Tests Must Pass

- [ ] Phase 1: Static Analysis (100% pass)
- [ ] Phase 2: Integration Testing (100% pass)
- [ ] Phase 3: Runtime Testing (100% pass)
- [ ] Phase 4: Browser Compatibility (100% pass in Chrome/Firefox)

### Performance Criteria

- [ ] Upload time < 5s for 10 MB file
- [ ] Polling overhead < 10% CPU
- [ ] UI smooth at 60 FPS

### Accessibility Criteria

- [ ] Keyboard navigation works
- [ ] Screen reader support works
- [ ] ARIA labels correct

## Success Criteria

Wave 4 is considered complete when:

1. ✅ All static analysis tests pass
2. ✅ All integration tests pass
3. ✅ All runtime tests pass in at least 2 browsers
4. ✅ Performance metrics meet targets
5. ✅ Basic accessibility works

## Known Limitations

1. **No automated browser testing**: Manual testing required (no Selenium/Playwright setup)
2. **No unit tests**: Integration tests only (no Jest/Mocha setup)
3. **No performance profiling**: Manual observation only
4. **Limited error scenarios**: Only basic error handling tested

## Deliverables

1. **wave4-validation.md** - Validation report with test results
2. **Test logs** - Console logs from runtime testing
3. **Screenshots** - Browser screenshots showing upload and monitoring
4. **Performance data** - Upload times, polling metrics

---

**Test Plan Created**: 2025-10-07
**Next Step**: Execute Phase 1 (Static Analysis)
