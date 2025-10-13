# Production Deployment Checklist

**Application**: DocuSearch Library Frontend
**Version**: 1.0.0
**Deployment Date**: (To be filled)
**Deployed By**: (To be filled)
**Environment**: Production
**URL**: `http://localhost:8002/frontend/`

---

## Checklist Legend

- [ ] NOT STARTED
- [P] IN PROGRESS
- [✓] COMPLETED
- [✗] FAILED / BLOCKED
- [~] PARTIAL / NEEDS REVIEW

---

## Phase 1: Pre-Deployment Validation

### 1.1 Code Quality

- [ ] All frontend files present in `/src/frontend/`
  - [ ] `index.html` (main HTML)
  - [ ] `library-manager.js` (application controller)
  - [ ] `websocket-client.js` (WebSocket manager)
  - [ ] `api-client.js` (API wrapper)
  - [ ] `document-card.js` (card component)
  - [ ] `filter-bar.js` (search/filter UI)
  - [ ] `upload-modal.js` (upload interface)
  - [ ] `styles.css` (complete stylesheet)
  - [ ] `README.md` (documentation)

- [ ] No console errors in browser DevTools
  - [ ] Chrome / Chromium
  - [ ] Firefox
  - [ ] Safari (if on macOS)

- [ ] No lint errors (if linter configured)
  ```bash
  # Check JavaScript syntax
  node --check src/frontend/*.js
  ```

- [ ] No broken imports
  ```bash
  # Verify all imports resolve
  grep -r "import.*from" src/frontend/*.js
  ```

**Status**: ______ **Notes**: ______________________________________________

---

### 1.2 Integration Tests

- [ ] WebSocketClient tests pass
  - [ ] Connection establishment
  - [ ] Message routing by type
  - [ ] Auto-reconnect with backoff
  - [ ] Event emission

- [ ] DocumentsAPIClient tests pass
  - [ ] List documents with filters
  - [ ] Get document details
  - [ ] Image URL generation
  - [ ] Error handling

- [ ] DocumentCard tests pass
  - [ ] Create completed card
  - [ ] Create loading card
  - [ ] Create processing card
  - [ ] Update card state
  - [ ] Variant detection (document/audio)

- [ ] FilterBar tests pass
  - [ ] Render controls
  - [ ] Search input with debounce
  - [ ] Filter change events
  - [ ] Pagination events

- [ ] UploadModal tests pass
  - [ ] File validation (type, size)
  - [ ] Upload progress tracking
  - [ ] Error handling
  - [ ] Event emission

- [ ] LibraryManager tests pass
  - [ ] Initialize application
  - [ ] Load documents
  - [ ] Handle status updates
  - [ ] Cross-component communication

**Test Script**:
```javascript
// In browser console at http://localhost:8002/frontend/
import('./test-integration.js').then(m => m.runAllTests());
```

**Status**: ______ **Notes**: ______________________________________________

---

### 1.3 E2E Testing

- [ ] Complete E2E testing checklist (150+ test cases)
  - [ ] See `src/frontend/E2E_TEST_RESULTS.md`
  - [ ] All critical paths tested
  - [ ] All PASS marks achieved

**Critical E2E Scenarios**:
- [ ] Page loads without errors
- [ ] WebSocket connects automatically
- [ ] Documents load and display
- [ ] Search filters documents correctly
- [ ] Sort changes document order
- [ ] File type filters work
- [ ] Pagination navigates pages
- [ ] Upload modal appears on drag
- [ ] Upload succeeds and triggers processing
- [ ] Real-time status updates appear
- [ ] Processing progress animates
- [ ] Completed state displays correctly

**Status**: ______ **Notes**: ______________________________________________

---

## Phase 2: Service Configuration Checks

### 2.1 Worker API Configuration

- [ ] Worker serves frontend at `/frontend` endpoint
  ```python
  # Verify in src/processing/worker_webhook.py:
  # FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
  # app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
  ```

- [ ] CORS headers configured correctly
  ```python
  # Verify CORS allows frontend origin
  app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
  ```

- [ ] WebSocket endpoint active at `/ws`
  ```bash
  # Test WebSocket connection
  wscat -c ws://localhost:8002/ws
  # Should receive: {"type":"connection","status":"connected",...}
  ```

- [ ] Documents API endpoints functional
  ```bash
  # Test list documents
  curl -s http://localhost:8002/documents?limit=5 | jq .

  # Test get document (replace DOC_ID)
  curl -s http://localhost:8002/documents/DOC_ID | jq .
  ```

- [ ] Image serving endpoint functional
  ```bash
  # Test image URL (replace DOC_ID and FILENAME)
  curl -I http://localhost:8002/images/DOC_ID/page001_thumb.jpg
  # Should return: 200 OK
  ```

**Status**: ______ **Notes**: ______________________________________________

---

### 2.2 Copyparty Configuration

- [ ] Copyparty accessible at port 8000
  ```bash
  curl -I http://localhost:8000/
  # Should return: 200 OK
  ```

- [ ] Upload endpoint accepts files
  ```bash
  # Test upload
  curl -F "file=@test.pdf" http://localhost:8000/uploads
  # Should return: {"status":"ok","path":"/uploads/test.pdf"}
  ```

- [ ] Webhook configured to Worker
  ```bash
  # Check hooks/on_upload.py sends to http://host.docker.internal:8002/webhook
  grep "8002/webhook" data/copyparty/hooks/on_upload.py
  ```

- [ ] Webhook triggers document processing
  ```bash
  # Monitor logs while uploading test file
  tail -f logs/worker-native.log
  # Should show: "Processing document: test.pdf"
  ```

**Status**: ______ **Notes**: ______________________________________________

---

### 2.3 ChromaDB Configuration

- [ ] ChromaDB accessible at port 8001
  ```bash
  curl -s http://localhost:8001/api/v2/heartbeat | jq .
  # Should return: {"nanosecond heartbeat":...}
  ```

- [ ] Collections exist (visual, text)
  ```bash
  # List collections
  curl -s http://localhost:8001/api/v1/collections | jq .
  # Should show: visual_collection, text_collection
  ```

- [ ] Collections have documents
  ```bash
  # Count documents (replace COLLECTION_ID)
  curl -s "http://localhost:8001/api/v1/collections/COLLECTION_ID/count" | jq .
  ```

**Status**: ______ **Notes**: ______________________________________________

---

### 2.4 Docker Services

- [ ] All containers running
  ```bash
  docker ps
  # Should show: docusearch-copyparty, docusearch-chromadb, docusearch-worker (or native)
  ```

- [ ] Container health checks passing
  ```bash
  docker ps --format "table {{.Names}}\t{{.Status}}"
  # All should show: Up X minutes (healthy)
  ```

- [ ] Container logs show no errors
  ```bash
  docker-compose -f docker/docker-compose.yml logs --tail=50
  # Check for ERROR or FAIL messages
  ```

- [ ] Network connectivity between containers
  ```bash
  # Test ChromaDB from worker
  docker exec docusearch-worker curl -s http://chromadb:8000/api/v2/heartbeat | jq .
  # Should succeed
  ```

**Status**: ______ **Notes**: ______________________________________________

---

### 2.5 Native Worker (if using GPU mode)

- [ ] Native worker process running
  ```bash
  cat .worker.pid
  ps -p $(cat .worker.pid)
  # Should show: python process
  ```

- [ ] Worker accessible at port 8002
  ```bash
  curl -s http://localhost:8002/health | jq .
  # Should return: {"status":"healthy",...}
  ```

- [ ] Worker using MPS device
  ```bash
  grep "device=mps" logs/worker-native.log
  # Should show: Using device: mps
  ```

- [ ] Worker logs show no errors
  ```bash
  tail -n 100 logs/worker-native.log | grep -i error
  # Should return: (no results)
  ```

**Status**: ______ **Notes**: ______________________________________________

---

## Phase 3: Frontend Validation Steps

### 3.1 Page Load Validation

- [ ] Open `http://localhost:8002/frontend/` in browser

- [ ] Page loads in < 2 seconds
  - [ ] Check Network tab: DOMContentLoaded time
  - [ ] Check Lighthouse: Performance score > 90

- [ ] All assets load successfully
  - [ ] Check Network tab: No 404 errors
  - [ ] All JavaScript modules load
  - [ ] CSS stylesheet loads
  - [ ] Lucide icons load

- [ ] No console errors
  - [ ] Open DevTools (F12)
  - [ ] Check Console tab
  - [ ] Should show: "LibraryManager initialized"

**Status**: ______ **Notes**: ______________________________________________

---

### 3.2 WebSocket Connection Validation

- [ ] Connection status indicator displays
  - [ ] Initially shows "Disconnected" (gray)
  - [ ] Within 2 seconds, changes to "Connected" (green)

- [ ] WebSocket messages received
  ```javascript
  // In browser console
  window.wsClient.on('connection', (msg) => console.log('Connected:', msg));
  // Should log: Connected: {type: "connection", status: "connected", ...}
  ```

- [ ] Auto-reconnect works
  - [ ] Close WebSocket: `window.wsClient.disconnect()`
  - [ ] Wait 2-3 seconds
  - [ ] Connection status changes to "Reconnecting..." (yellow)
  - [ ] Connection status returns to "Connected" (green)

**Status**: ______ **Notes**: ______________________________________________

---

### 3.3 Document Loading Validation

- [ ] Documents load automatically on page load
  - [ ] Loading state appears briefly
  - [ ] Documents render in grid
  - [ ] Grid uses responsive layout (1-5 columns based on screen width)

- [ ] Document cards display correctly
  - [ ] Filename displays
  - [ ] Date added displays
  - [ ] Thumbnail displays (if available)
  - [ ] File type badge displays
  - [ ] Details button displays

- [ ] Empty state displays (if no documents)
  - [ ] Message: "No documents found"
  - [ ] Upload prompt displayed

- [ ] Pagination controls display (if > 50 docs)
  - [ ] Previous button (disabled on page 1)
  - [ ] Page indicator (e.g., "1-50 of 100")
  - [ ] Next button

**Status**: ______ **Notes**: ______________________________________________

---

### 3.4 Search and Filtering Validation

- [ ] Search input filters documents
  - [ ] Type query (e.g., "report")
  - [ ] Wait 300ms (debounce)
  - [ ] Grid updates to show matching documents
  - [ ] URL updates with search parameter

- [ ] Sort dropdown changes order
  - [ ] Select "Filename"
  - [ ] Documents re-order alphabetically
  - [ ] Select "Page Count"
  - [ ] Documents re-order by page count (descending)

- [ ] File type filters work
  - [ ] Uncheck "PDF"
  - [ ] PDF documents disappear from grid
  - [ ] Check "PDF" again
  - [ ] PDF documents reappear

- [ ] Clear filters resets state
  - [ ] Apply filters (search + sort + file types)
  - [ ] Click "Clear Filters"
  - [ ] All filters reset to defaults
  - [ ] All documents display

**Status**: ______ **Notes**: ______________________________________________

---

### 3.5 Upload Validation

- [ ] Drag-and-drop detection works
  - [ ] Drag file anywhere on page
  - [ ] Upload modal appears with backdrop
  - [ ] Drop zone highlights

- [ ] File validation works
  - [ ] Drop invalid file type (e.g., .exe)
  - [ ] Error message displays: "Unsupported file type"
  - [ ] Drop oversized file (> 100MB)
  - [ ] Error message displays: "File too large"

- [ ] Upload succeeds
  - [ ] Drop valid file (e.g., .pdf)
  - [ ] Progress bar appears
  - [ ] Progress updates to 100%
  - [ ] Success message displays
  - [ ] Modal closes after 2 seconds

- [ ] Upload triggers processing
  - [ ] New card appears in "Loading" state
  - [ ] Card transitions to "Processing" state
  - [ ] Progress updates in real-time
  - [ ] Card transitions to "Completed" state

**Status**: ______ **Notes**: ______________________________________________

---

### 3.6 Real-Time Updates Validation

- [ ] Status updates appear in real-time
  - [ ] Upload a document
  - [ ] Watch card state changes:
    - [ ] Loading (skeleton loaders)
    - [ ] Processing (stage + progress)
    - [ ] Completed (thumbnail + metadata)

- [ ] Processing stage updates
  - [ ] "Parsing document"
  - [ ] "Embedding images"
  - [ ] "Embedding text"
  - [ ] "Storing vectors"

- [ ] Progress percentage updates
  - [ ] Starts at ~0%
  - [ ] Increases gradually (10%, 25%, 50%, 75%)
  - [ ] Reaches 100%

- [ ] Thumbnail appears when ready
  - [ ] Initially: Placeholder background
  - [ ] After processing: First page thumbnail

**Status**: ______ **Notes**: ______________________________________________

---

## Phase 4: Performance Baselines

### 4.1 Page Load Performance

- [ ] Run Lighthouse audit
  ```
  Chrome DevTools > Lighthouse > Generate Report
  ```

- [ ] Performance score > 90
- [ ] Accessibility score > 95
- [ ] Best Practices score > 90
- [ ] SEO score > 80

**Metrics**:
- First Contentful Paint (FCP): ______ ms (target: < 1000ms)
- Largest Contentful Paint (LCP): ______ ms (target: < 2000ms)
- Time to Interactive (TTI): ______ ms (target: < 3000ms)
- Total Blocking Time (TBT): ______ ms (target: < 300ms)
- Cumulative Layout Shift (CLS): ______ (target: < 0.1)

**Status**: ______ **Notes**: ______________________________________________

---

### 4.2 API Performance

- [ ] List documents endpoint performance
  ```bash
  time curl -s http://localhost:8002/documents?limit=50 > /dev/null
  # Target: < 200ms
  ```
  **Actual**: ______ ms

- [ ] Get document endpoint performance
  ```bash
  time curl -s http://localhost:8002/documents/DOC_ID > /dev/null
  # Target: < 100ms
  ```
  **Actual**: ______ ms

- [ ] WebSocket message latency
  - Upload document
  - Measure time from upload complete to first status update
  - **Target**: < 500ms
  - **Actual**: ______ ms

**Status**: ______ **Notes**: ______________________________________________

---

### 4.3 Client-Side Performance

- [ ] Memory usage baseline
  ```javascript
  // In browser console after 5 minutes of use
  performance.memory.usedJSHeapSize / 1024 / 1024
  // Target: < 50 MB
  ```
  **Actual**: ______ MB

- [ ] No memory leaks detected
  - [ ] Open page
  - [ ] Upload 10 documents
  - [ ] Wait for processing to complete
  - [ ] Check memory usage
  - [ ] Refresh page
  - [ ] Check memory usage again
  - [ ] Memory should return to baseline

- [ ] Network request count
  - [ ] Check Network tab
  - [ ] Initial page load: ______ requests (target: < 20)
  - [ ] After loading 50 docs: ______ requests (target: < 100)

**Status**: ______ **Notes**: ______________________________________________

---

## Phase 5: Security Considerations

### 5.1 Input Validation

- [ ] Search input sanitized
  - [ ] Try XSS payload: `<script>alert('XSS')</script>`
  - [ ] Should NOT execute JavaScript
  - [ ] Should search for literal text

- [ ] File upload validation enforced
  - [ ] Server-side validation matches client-side
  - [ ] File type whitelist enforced
  - [ ] File size limit enforced

- [ ] No SQL injection vectors
  - [ ] Search query uses parameterized queries
  - [ ] Document ID validation

**Status**: ______ **Notes**: ______________________________________________

---

### 5.2 CORS Configuration

- [ ] CORS headers set correctly
  ```bash
  curl -I -X OPTIONS http://localhost:8002/documents \
    -H "Origin: http://localhost:8002" \
    -H "Access-Control-Request-Method: GET"
  # Should return: Access-Control-Allow-Origin header
  ```

- [ ] Only allowed origins accepted
  - [ ] Frontend origin allowed
  - [ ] Unknown origins rejected (if strict mode)

**Status**: ______ **Notes**: ______________________________________________

---

### 5.3 Content Security Policy

- [ ] CSP headers configured (if enabled)
  ```bash
  curl -I http://localhost:8002/frontend/ | grep -i "content-security"
  ```

- [ ] Inline scripts allowed (ES6 modules need `script-src 'self'`)
- [ ] External resources allowed (Lucide CDN)

**Status**: ______ **Notes**: ______________________________________________

---

## Phase 6: Monitoring Setup

### 6.1 Logging Configuration

- [ ] Worker logs capture frontend requests
  ```bash
  tail -f logs/worker-native.log | grep "GET /frontend"
  # Should show: GET /frontend/index.html 200
  ```

- [ ] Error logs capture failures
  ```bash
  tail -f logs/worker-native.log | grep ERROR
  # Should show: (no results, or expected errors only)
  ```

- [ ] Log rotation configured
  ```bash
  ls -lh logs/worker-native.log*
  # Check file size: should not exceed 100MB
  ```

**Status**: ______ **Notes**: ______________________________________________

---

### 6.2 Health Checks

- [ ] Worker health endpoint functional
  ```bash
  curl -s http://localhost:8002/health | jq .
  # Should return: {"status":"healthy","uptime":...,"device":"mps",...}
  ```

- [ ] Status endpoint shows processing stats
  ```bash
  curl -s http://localhost:8002/status | jq .
  # Should return: {"documents_processed":...,"avg_time":...}
  ```

- [ ] Health check script created
  ```bash
  # Create scripts/health-check.sh
  # Test all service endpoints
  # Exit 1 if any service unhealthy
  ```

**Status**: ______ **Notes**: ______________________________________________

---

### 6.3 Metrics Collection (Optional)

- [ ] Request count metrics
  - [ ] GET /frontend/
  - [ ] GET /documents
  - [ ] GET /images/*
  - [ ] POST /webhook

- [ ] Response time metrics
  - [ ] Average response time per endpoint
  - [ ] P95 response time

- [ ] Error rate metrics
  - [ ] 4xx errors (client errors)
  - [ ] 5xx errors (server errors)

**Tools**: Prometheus, Grafana, or simple log analysis

**Status**: ______ **Notes**: ______________________________________________

---

## Phase 7: Rollback Plan

### 7.1 Backup Verification

- [ ] Current production state backed up
  ```bash
  # Backup entire src/frontend/
  tar -czf backups/frontend-$(date +%Y%m%d-%H%M%S).tar.gz src/frontend/

  # Verify backup
  tar -tzf backups/frontend-*.tar.gz | head
  ```

- [ ] Database state documented
  ```bash
  # Count documents in ChromaDB
  curl -s http://localhost:8001/api/v1/collections | jq .
  # Record counts for rollback verification
  ```

**Status**: ______ **Notes**: ______________________________________________

---

### 7.2 Rollback Procedure

**If critical issues arise post-deployment:**

1. **Stop services**:
   ```bash
   ./scripts/stop-all.sh
   ```

2. **Restore backup**:
   ```bash
   # Remove current frontend
   rm -rf src/frontend/

   # Restore backup
   tar -xzf backups/frontend-[timestamp].tar.gz
   ```

3. **Restart services**:
   ```bash
   ./scripts/start-all.sh
   ```

4. **Verify rollback**:
   ```bash
   curl -I http://localhost:8002/frontend/
   # Should return: 200 OK
   ```

5. **Document issue**:
   - Create incident report
   - Document root cause
   - Plan fix and re-deployment

**Status**: ______ **Notes**: ______________________________________________

---

## Phase 8: Post-Deployment Verification

### 8.1 Smoke Tests (First 15 Minutes)

- [ ] Page loads successfully
  ```bash
  curl -I http://localhost:8002/frontend/
  # Should return: 200 OK
  ```

- [ ] WebSocket connects
  ```javascript
  // In browser console
  window.wsClient.isConnected()
  // Should return: true
  ```

- [ ] Documents load
  ```bash
  curl -s http://localhost:8002/documents?limit=5 | jq .documents[0]
  # Should return: First document object
  ```

- [ ] Upload works
  - Drag-drop test file
  - Verify upload completes
  - Verify processing starts

- [ ] No critical errors in logs
  ```bash
  tail -n 50 logs/worker-native.log | grep -i "critical\|fatal"
  # Should return: (no results)
  ```

**Status**: ______ **Notes**: ______________________________________________

---

### 8.2 Functional Tests (First Hour)

- [ ] Complete user workflow
  1. Open frontend
  2. Search for document
  3. Filter by file type
  4. Upload new document
  5. Watch processing in real-time
  6. Verify completed document appears

- [ ] Test edge cases
  - [ ] Upload multiple files simultaneously
  - [ ] Upload during heavy processing
  - [ ] Search with special characters
  - [ ] Pagination with exactly 50/100/150 docs

- [ ] Test error scenarios
  - [ ] Upload invalid file type
  - [ ] Upload oversized file
  - [ ] Disconnect WebSocket (check auto-reconnect)
  - [ ] Slow network (throttle in DevTools)

**Status**: ______ **Notes**: ______________________________________________

---

### 8.3 Performance Tests (First 24 Hours)

- [ ] Monitor page load times
  - [ ] Record average FCP over 24 hours
  - [ ] Check for degradation over time

- [ ] Monitor API response times
  ```bash
  # Log response times
  for i in {1..100}; do
    time curl -s http://localhost:8002/documents?limit=50 > /dev/null
    sleep 5
  done
  ```

- [ ] Monitor memory usage
  - [ ] Check worker memory usage
  ```bash
  docker stats docusearch-worker --no-stream
  # Or for native worker:
  ps aux | grep python | grep worker
  ```

- [ ] Monitor WebSocket stability
  - [ ] Check connection uptime
  - [ ] Check reconnection count
  - [ ] Check message delivery success rate

**Status**: ______ **Notes**: ______________________________________________

---

## Phase 9: Sign-Off

### 9.1 Technical Sign-Off

- [ ] All pre-deployment validation checks passed
- [ ] All service configuration checks passed
- [ ] All frontend validation checks passed
- [ ] Performance baselines met
- [ ] Security considerations addressed
- [ ] Monitoring setup complete
- [ ] Rollback plan tested
- [ ] Post-deployment verification passed

**Signed**: ______________________ **Date**: ______________

**Role**: Technical Lead / Developer

**Notes**: ______________________________________________

---

### 9.2 Product Sign-Off

- [ ] All features working as expected
- [ ] User experience meets requirements
- [ ] No critical bugs identified
- [ ] Documentation complete and accurate
- [ ] Ready for production use

**Signed**: ______________________ **Date**: ______________

**Role**: Product Owner / Manager

**Notes**: ______________________________________________

---

## Deployment Notes

### Deployment Date/Time
**Date**: ______________
**Time**: ______________
**Deployed By**: ______________

### Pre-Deployment State
- Documents in ChromaDB: ______
- Services version: ______
- Frontend version: ______

### Post-Deployment State
- Documents in ChromaDB: ______ (should match)
- Services version: ______
- Frontend version: ______

### Issues Encountered
(List any issues encountered during deployment)

1. ______________________________________________________
2. ______________________________________________________
3. ______________________________________________________

### Resolutions Applied
(List resolutions for each issue)

1. ______________________________________________________
2. ______________________________________________________
3. ______________________________________________________

---

## Success Metrics

### Performance Metrics
- Page Load Time: ______ ms (target: < 2000ms)
- API Response Time: ______ ms (target: < 200ms)
- WebSocket Latency: ______ ms (target: < 500ms)
- Memory Usage: ______ MB (target: < 50MB)

### Functionality Metrics
- Document Load Success Rate: ______% (target: 100%)
- Upload Success Rate: ______% (target: 100%)
- Search Accuracy: ______% (target: 100%)
- WebSocket Uptime: ______% (target: 99.9%)

### User Experience Metrics
- Lighthouse Performance Score: ______ (target: > 90)
- Lighthouse Accessibility Score: ______ (target: > 95)
- Console Errors: ______ (target: 0)
- Failed Requests: ______ (target: 0)

---

## Conclusion

**Deployment Status**: [ ] SUCCESS [ ] PARTIAL [ ] FAILED

**Overall Assessment**:
______________________________________________
______________________________________________
______________________________________________

**Recommendations**:
______________________________________________
______________________________________________
______________________________________________

**Next Steps**:
1. ______________________________________________
2. ______________________________________________
3. ______________________________________________

---

*Production Deployment Checklist - Version 1.0*
*Last Updated: 2025-10-13*
