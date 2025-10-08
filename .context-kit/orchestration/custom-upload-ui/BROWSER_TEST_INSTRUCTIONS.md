# Browser Testing Instructions

**Date**: 2025-10-07
**Status**: Ready for Testing
**Services**: All running (ChromaDB, Copyparty, Worker with UI and Status API)

## Services Status

✅ All services are running:
- **Upload UI (Copyparty)**: http://localhost:8000
- **ChromaDB**: http://localhost:8001
- **Worker API**: http://localhost:8002
- **Custom Upload UI**: http://localhost:8002/ui/
- **Status API**: http://localhost:8002/status/queue

## Pre-Flight Checks ✅

1. **Status API**: ✅ Working - returns empty queue: `{"queue": [], "total": 0, "active": 0, "completed": 0, "failed": 0}`
2. **UI Static Files**: ✅ Serving - index.html accessible at http://localhost:8002/ui/
3. **Worker Health**: ✅ Healthy
4. **Route Ordering**: ✅ Fixed - `/queue` endpoint now comes before `/{doc_id}` to avoid conflicts

## Test Scenarios

### Test 1: Upload Page Load

**URL**: http://localhost:8002/ui/

**Expected**:
- [ ] Page loads without errors
- [ ] No console errors
- [ ] Drop zone visible
- [ ] "Browse" link clickable
- [ ] Format info accordion expands/collapses
- [ ] Queue section shows empty state or existing items

**Console Logs Expected**:
```
Upload module initialized
Monitor module initialized
```

### Test 2: File Validation - Invalid Format

**Steps**:
1. Create a test file with invalid extension (e.g., `.exe`, `.zip`, `.dmg`)
2. Drag file onto drop zone
3. Observe

**Expected**:
- [ ] Drop zone highlights on dragover (`drop-zone--active` class applied)
- [ ] Toast notification appears with error
- [ ] Error message: "Unsupported format: .exe"
- [ ] No queue item created
- [ ] No upload attempted

### Test 3: File Validation - Large File Warning

**Steps**:
1. Create or find a file > 10 MB (but < 100 MB)
2. Drag onto drop zone
3. Observe

**Expected**:
- [ ] Toast notification with warning
- [ ] Warning message: "Large file (X.XX MB) - processing may take longer"
- [ ] Upload proceeds
- [ ] Queue item created

### Test 4: Single PDF Upload

**Steps**:
1. Create or find a small PDF file (< 5 MB)
2. Drag onto drop zone
3. Observe upload and processing

**Expected Upload Phase**:
- [ ] Queue item appears immediately
- [ ] Filename shown correctly
- [ ] Status: "Uploading..."
- [ ] Progress bar moves (0% → 100%)
- [ ] Upload completes with success toast

**Expected Processing Phase**:
- [ ] Status changes to "Queued for processing..."
- [ ] Monitor.js starts polling (every 2 seconds)
- [ ] Status updates appear:
  - "Parsing document"
  - "Extracting structure"
  - "Creating chunks"
  - "Processing images"
  - "Generating visual embeddings"
  - "Processing text"
  - "Generating text embeddings"
  - "Storing in database"
  - "Completed"
- [ ] Progress bar updates (0% → 100%)
- [ ] Elapsed time updates
- [ ] Page progress shown (e.g., "Page 1/3")
- [ ] Completion toast appears
- [ ] Queue item marked as completed (green, `queue-item--completed`)
- [ ] Queue statistics update (Active decreases, Completed increases)

**Console Logs Expected**:
```
Processing 1 file(s)
filename.pdf: 100.0% (X.XX MB / X.XX MB)
Upload successful: filename.pdf (doc_id: abc123...)
Starting monitoring for abc123...
Status update: abc123... -> parsing
Status update: abc123... -> embedding_visual
...
Status update: abc123... -> completed
Document completed: abc123...
```

### Test 5: Multi-File Upload

**Steps**:
1. Select 3-5 PDF files
2. Drag onto drop zone simultaneously
3. Observe

**Expected**:
- [ ] All files appear in queue immediately
- [ ] Max 3 uploads running concurrently
- [ ] Upload progress shown for each file
- [ ] All files transition to processing after upload
- [ ] All files monitored independently
- [ ] All files complete successfully
- [ ] Queue statistics accurate (Active + Completed = Total)

### Test 6: Status Page

**URL**: http://localhost:8002/ui/status.html

**Steps**:
1. Upload a file via index.html
2. Open status.html in new tab
3. Observe

**Expected**:
- [ ] Page loads without errors
- [ ] Existing queue items loaded from `/status/queue` API
- [ ] Status updates in real-time
- [ ] Statistics shown (Active, Completed)
- [ ] No upload UI (only monitoring)
- [ ] Queue items update as processing continues

**Console Logs Expected**:
```
Monitor module initialized
Loaded existing queue from API
```

### Test 7: Error Handling - Oversized File

**Steps**:
1. Create a file > 100 MB (use `dd` or similar)
2. Try to upload
3. Observe

**Expected**:
- [ ] Error toast shown immediately
- [ ] Error message: "File too large: X.XX MB (max 100 MB)"
- [ ] No queue item created
- [ ] No upload attempted

### Test 8: Drag-and-Drop Interaction

**Steps**:
1. Drag a valid file over the drop zone
2. Drag it away (without dropping)
3. Drag it back and drop
4. Observe

**Expected**:
- [ ] Drop zone highlights on dragenter/dragover
- [ ] Drop zone un-highlights on dragleave
- [ ] Drop zone un-highlights on drop
- [ ] File upload starts on drop

### Test 9: Format Info Accordion

**Steps**:
1. Load page
2. Click "Supported Formats" accordion
3. Observe

**Expected**:
- [ ] Accordion expands
- [ ] 21 formats listed in 4 categories:
  - Documents (9 formats)
  - Images (6 formats)
  - Data (2 formats)
  - Audio (3 formats)
  - Specialized (1 format)
- [ ] Click again to collapse

### Test 10: Toast Notifications

**Steps**:
1. Trigger various toast types (errors, warnings, success)
2. Observe behavior

**Expected**:
- [ ] Toasts appear in top-right corner
- [ ] Color-coded (green=success, red=error, yellow=warning)
- [ ] Auto-dismiss after 5 seconds
- [ ] Fade-out animation (`.toast--hiding` class)
- [ ] Multiple toasts stack vertically
- [ ] Toasts don't block UI interaction

## Developer Console Checks

**Open Dev Tools** (F12 or Cmd+Option+I)

### Console Tab

**Expected**: No errors, only log messages like:
```
Upload module initialized
Monitor module initialized
Processing 1 file(s)
filename.pdf: 100.0% (...)
Upload successful: filename.pdf (doc_id: ...)
Starting monitoring for ...
Status update: ... -> parsing
...
```

**Red Flags** (should NOT see):
- ❌ `Uncaught ReferenceError`
- ❌ `Uncaught TypeError`
- ❌ `Failed to load module`
- ❌ `404 Not Found` for JS/CSS files
- ❌ `CORS error`

### Network Tab

**During Upload**:
- [ ] `POST http://localhost:8000/` (Copyparty upload)
- [ ] Status: 200 OK
- [ ] Request shows FormData with file

**During Monitoring**:
- [ ] `GET http://localhost:8002/status/queue` (every 2 seconds)
- [ ] Status: 200 OK
- [ ] Response shows queue data

**During Page Load**:
- [ ] `GET http://localhost:8002/ui/` (200 OK)
- [ ] `GET http://localhost:8002/ui/styles.css` (200 OK)
- [ ] `GET http://localhost:8002/ui/upload.js` (200 OK)
- [ ] `GET http://localhost:8002/ui/monitor.js` (200 OK)
- [ ] `GET http://localhost:8002/ui/modules/file-validator.js` (200 OK)
- [ ] `GET http://localhost:8002/ui/modules/copyparty-client.js` (200 OK)
- [ ] `GET http://localhost:8002/ui/modules/processing-monitor.js` (200 OK)
- [ ] `GET http://localhost:8002/ui/modules/queue-manager.js` (200 OK)

### Elements Tab

**Inspect Drop Zone**:
- [ ] Has `id="drop-zone"`
- [ ] Has class `drop-zone`
- [ ] On dragover: class `drop-zone--active` added
- [ ] On dragleave: class `drop-zone--active` removed

**Inspect Queue Item** (after upload):
- [ ] Has `data-doc-id` attribute with SHA-256 hash
- [ ] Has `data-filename` attribute with filename
- [ ] Has class `queue-item`
- [ ] Has class `queue-item--processing` (during processing)
- [ ] Has class `queue-item--completed` (when done)

## Performance Checks

### Upload Performance

**Test**: Upload 10 MB PDF

**Expected**:
- Upload time: < 5 seconds on localhost
- Progress updates: At least 10 updates (smooth progress)
- CPU usage: < 20% during upload

### Polling Performance

**Test**: Monitor 5 documents simultaneously

**Expected**:
- Polling interval: Consistent 2 seconds
- CPU usage: < 10% during polling
- Network traffic: ~1 request every 2 seconds

### UI Responsiveness

**Test**: Scroll queue with 20 items

**Expected**:
- Smooth scrolling (60 FPS)
- No lag when updating items
- Toast notifications don't block UI

## Accessibility Checks

### Keyboard Navigation

**Steps**:
1. Tab through page
2. Press Enter on file input

**Expected**:
- [ ] Can tab to "browse" link
- [ ] Enter opens file picker
- [ ] Can tab through queue items
- [ ] Focus indicators visible

## Browser Compatibility

**Test in**:
- [ ] Chrome/Edge (Chromium 120+)
- [ ] Firefox (120+)
- [ ] Safari (17+) - if available

**Expected**:
- ES6 modules load correctly
- Fetch API works
- XHR upload progress works
- Drag-and-drop works
- CSS animations work

## Known Issues to Ignore

1. **Deprecation warnings in console**: FastAPI `@app.on_event` deprecation (non-critical)
2. **Model loading messages**: "Using a slow image processor" (expected)
3. **Empty queue on first load**: Normal - no documents uploaded yet

## Success Criteria

All tests must pass:
- ✅ Upload page loads without errors
- ✅ File validation works (errors and warnings)
- ✅ Single file upload and monitoring works end-to-end
- ✅ Multi-file upload works
- ✅ Status page loads existing queue
- ✅ Error handling works (oversized file)
- ✅ Drag-and-drop interaction works
- ✅ Toast notifications work
- ✅ No console errors
- ✅ Performance acceptable

## Reporting Results

After testing, document:
1. Browser and version tested
2. Tests passed (checkboxes above)
3. Tests failed (with details)
4. Screenshots of upload and monitoring
5. Console logs (if errors occurred)
6. Performance metrics (upload time, polling interval)

Save results to: `wave4-browser-test-results.md`

---

**Ready to Test**: ✅ YES
**Services Running**: ✅ YES
**API Endpoints Working**: ✅ YES
**UI Accessible**: ✅ YES

**Next Step**: Open http://localhost:8002/ui/ in browser and start testing! 🚀
