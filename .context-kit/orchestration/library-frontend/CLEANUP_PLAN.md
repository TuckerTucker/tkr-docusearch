# Cleanup Plan - POC to Production Migration

**Document Type**: Cleanup Strategy
**Date Created**: 2025-10-13
**Status**: READY FOR EXECUTION
**Agent**: Agent 11 (Cleanup Agent)

---

## Executive Summary

This document outlines the strategy for safely removing the proof-of-concept (POC) pages from `/data/copyparty/www/` and migrating to the production frontend at `/src/frontend/`. The production frontend is complete, tested, and ready to replace the POC entirely.

**Migration Status**: Production frontend is feature-complete and supersedes all POC functionality.

---

## Analysis Results

### POC Directory Contents

**Location**: `/Volumes/tkr-riffic/@tkr-projects/tkr-docusearch/data/copyparty/www/`

**Files Found** (18 total):

```
HTML Pages (3):
- document-card-demo.html          (9.7 KB)
- index.html                       (7.4 KB)
- search.html                      (9.1 KB)
- status_dashboard.html            (4.6 KB)

JavaScript Files (5):
- monitor.js                       (8.8 KB)
- search.js                        (20 KB)
- status_dashboard.js              (12 KB)
- upload.js                        (14 KB)
- worker-status.js                 (472 B)

Stylesheets (1):
- styles.css                       (29 KB)

Modules (7):
modules/copyparty-client.js
modules/document-card.js
modules/file-validator.js
modules/processing-monitor.js
modules/queue-manager.js
modules/worker-health.js
modules/README-document-card.md

Assets (1):
- quarterly-report-q3-2023.png     (340 KB) - Test asset
```

---

## Files to Delete

### 1. POC HTML Pages (DELETE ALL)

**Rationale**: All POC pages have been replaced by production frontend.

```bash
data/copyparty/www/document-card-demo.html
data/copyparty/www/index.html
data/copyparty/www/search.html
data/copyparty/www/status_dashboard.html
```

**Replacement**: `/src/frontend/index.html` (unified library view)

**Migration Status**:
- POC `index.html` → Production `/frontend/` (unified library + upload + search)
- POC `search.html` → Production `/frontend/` with FilterBar component
- POC `status_dashboard.html` → Production `/frontend/` with real-time WebSocket updates
- POC `document-card-demo.html` → Obsolete (component now in production)

---

### 2. POC JavaScript Files (DELETE ALL)

**Rationale**: All functionality migrated to production components.

```bash
data/copyparty/www/monitor.js
data/copyparty/www/search.js
data/copyparty/www/status_dashboard.js
data/copyparty/www/upload.js
data/copyparty/www/worker-status.js
```

**Replacement**: Production ES6 modules in `/src/frontend/`:
- `monitor.js` → `websocket-client.js` + `library-manager.js`
- `search.js` → `filter-bar.js` + `api-client.js`
- `status_dashboard.js` → `websocket-client.js` + `document-card.js`
- `upload.js` → `upload-modal.js`
- `worker-status.js` → `websocket-client.js`

---

### 3. POC Stylesheets (DELETE)

**Rationale**: Production has comprehensive, optimized stylesheet.

```bash
data/copyparty/www/styles.css
```

**Replacement**: `/src/frontend/styles.css` (production version with all POC features + enhancements)

---

### 4. POC Modules (DELETE ALL)

**Rationale**: All modules replaced by production implementations.

```bash
data/copyparty/www/modules/copyparty-client.js
data/copyparty/www/modules/document-card.js
data/copyparty/www/modules/file-validator.js
data/copyparty/www/modules/processing-monitor.js
data/copyparty/www/modules/queue-manager.js
data/copyparty/www/modules/worker-health.js
data/copyparty/www/modules/README-document-card.md
```

**Replacement**: Production modules in `/src/frontend/`:
- `modules/copyparty-client.js` → `upload-modal.js` (integrated API)
- `modules/document-card.js` → `document-card.js` (enhanced production version)
- `modules/file-validator.js` → `upload-modal.js` (validation logic)
- `modules/processing-monitor.js` → `websocket-client.js` + `library-manager.js`
- `modules/queue-manager.js` → Not needed (worker manages queue)
- `modules/worker-health.js` → `websocket-client.js` (connection management)
- `modules/README-document-card.md` → `/src/frontend/README.md` (comprehensive docs)

---

### 5. POC Test Assets (DELETE)

**Rationale**: Test asset no longer needed.

```bash
data/copyparty/www/quarterly-report-q3-2023.png
```

**Replacement**: Users upload real documents to `/uploads/`

---

## Files to Keep

**NONE** - All POC files should be removed.

**Justification**:
1. Production frontend is feature-complete
2. Production frontend supersedes all POC functionality
3. No POC files are referenced by production code
4. Keeping POC files would create confusion and maintenance burden
5. Docker volume mount `/data/copyparty/www:/www` will be removed from `docker-compose.yml`

---

## References Found

### Critical Reference - Docker Compose

**File**: `/Volumes/tkr-riffic/@tkr-projects/tkr-docusearch/docker/docker-compose.yml`

**Line 14**:
```yaml
- ../data/copyparty/www:/www
```

**Action**: REMOVE this volume mount (POC pages no longer served)

**Justification**: Production frontend is served by Worker API at `/frontend` endpoint, not by Copyparty.

---

### Critical Reference - Setup Script

**File**: `/Volumes/tkr-riffic/@tkr-projects/tkr-docusearch/scripts/setup.sh`

**Lines**:
- Line 138: Creates `data/copyparty/www` directory
- Line 332: Generates POC `index.html`

**Action**: REMOVE POC directory creation and HTML generation

**Justification**: POC pages no longer needed; production frontend is standalone.

---

### Documentation References (UPDATE)

All references are in documentation/context files (safe to update):

1. **`.context-kit/orchestration/wave2-completion-report.md`**
   - Lines 475, 724: References to POC pages
   - Action: Add note that POC was replaced by production frontend

2. **`.context-kit/_ref/WAVE4_COMPLETION.md`**
   - Lines 113-114: References to POC JavaScript
   - Action: Add note about migration to production

3. **`.context-kit/_ref/document-view-tab-requirements.md`**
   - Line 405: Reference to POC processing monitor
   - Action: Update to point to production component

4. **`.context-kit/orchestration/library-frontend/validation-strategy.md`**
   - Lines 419, 422, 499: Validation checks for POC removal
   - Action: Keep these (they validate cleanup was successful)

5. **`.context-kit/orchestration/library-frontend/README.md`**
   - Lines 298-299: POC location references
   - Action: Update to indicate POC was removed

6. **`.context-kit/orchestration/library-frontend/orchestration-plan.md`**
   - Line 315: Agent 11 task to remove POC
   - Action: Mark as completed

7. **`.context-kit/orchestration/library-frontend/agent-assignments.md`**
   - Lines 195, 329, 469, 476, 511: POC references and cleanup tasks
   - Action: Mark Agent 11 tasks as completed

8. **`.context-kit/orchestration/docusearch-mvp/integration-contracts/config-interface.md`**
   - Line 107: Docker volume mount reference
   - Action: Update to show volume mount was removed

9. **`.context-kit/_ref/COMPLETION_SUMMARY.md`**
   - Line 90: POC pages reference
   - Action: Add note about migration

10. **`.context-kit/_ref/mvp-architecture.md`**
    - Line 166: Docker volume mount reference
    - Action: Update architecture diagram

---

## Execution Plan

### Phase 1: Pre-Deletion Validation (SAFETY CHECKS)

**Objective**: Ensure production frontend is fully operational before deleting POC.

**Checklist**:
- [ ] All services running (`./scripts/start-all.sh`)
- [ ] Production frontend accessible at `http://localhost:8002/frontend/`
- [ ] WebSocket connection working (status indicator green)
- [ ] Document loading working (grid displays documents)
- [ ] Search and filtering working
- [ ] Upload working (drag-drop)
- [ ] Real-time status updates working
- [ ] No console errors in browser DevTools
- [ ] Agent 10 E2E tests passing (see `src/frontend/E2E_TEST_RESULTS.md`)

**If ANY check fails**: STOP. Do not proceed with deletion until issues are resolved.

---

### Phase 2: Backup (SAFETY NET)

**Objective**: Create backup before deletion for rollback capability.

```bash
# Create backup archive
cd /Volumes/tkr-riffic/@tkr-projects/tkr-docusearch
tar -czf data/copyparty/www-backup-$(date +%Y%m%d-%H%M%S).tar.gz data/copyparty/www/

# Verify backup created
ls -lh data/copyparty/www-backup-*.tar.gz
```

**Expected**: Backup archive ~400KB

---

### Phase 3: Remove POC Files (CLEANUP)

**Objective**: Delete POC directory.

```bash
# Remove entire POC directory
rm -rf /Volumes/tkr-riffic/@tkr-projects/tkr-docusearch/data/copyparty/www/

# Verify deletion
ls -la /Volumes/tkr-riffic/@tkr-projects/tkr-docusearch/data/copyparty/
# Should NOT show 'www' directory
```

---

### Phase 4: Update Docker Configuration (INFRASTRUCTURE)

**Objective**: Remove POC volume mount from Docker Compose.

**File**: `/Volumes/tkr-riffic/@tkr-projects/tkr-docusearch/docker/docker-compose.yml`

**Change**:
```diff
  copyparty:
    volumes:
      - ../data/uploads:/uploads
-     - ../data/copyparty/www:/www
      - ../data/copyparty/hooks:/hooks
```

**Note**: Production frontend is served by Worker API (no Copyparty volume needed).

---

### Phase 5: Update Setup Script (INFRASTRUCTURE)

**Objective**: Remove POC directory creation from setup script.

**File**: `/Volumes/tkr-riffic/@tkr-projects/tkr-docusearch/scripts/setup.sh`

**Changes**:

1. **Line 138** - Remove POC directory from creation list:
```diff
  "$PROJECT_ROOT/data/uploads" \
  "$PROJECT_ROOT/data/page_images" \
  "$PROJECT_ROOT/data/chroma_db" \
  "$PROJECT_ROOT/data/models" \
  "$PROJECT_ROOT/data/logs" \
- "$PROJECT_ROOT/data/copyparty/www" \
  "$PROJECT_ROOT/data/copyparty/hooks"
```

2. **Lines 332+** - Remove POC index.html generation:
```diff
-cat > "$PROJECT_ROOT/data/copyparty/www/index.html" << 'EOFHTML'
-[... POC HTML content ...]
-EOFHTML
```

**Note**: Setup script should only create directories for production system.

---

### Phase 6: Post-Deletion Validation (VERIFICATION)

**Objective**: Verify system works without POC files.

**Checklist**:
- [ ] Restart services: `./scripts/stop-all.sh && ./scripts/start-all.sh`
- [ ] Production frontend still accessible: `http://localhost:8002/frontend/`
- [ ] No 404 errors for POC pages (expected - they're removed)
- [ ] Copyparty still accessible: `http://localhost:8000`
- [ ] Upload still works via Copyparty
- [ ] Worker webhook still triggers on upload
- [ ] No errors in worker logs: `tail -f logs/worker-native.log`
- [ ] No errors in Docker logs: `docker-compose -f docker/docker-compose.yml logs`
- [ ] Search for POC references returns no results:
  ```bash
  grep -r "copyparty/www" src/ 2>/dev/null
  # Should return: (no results)
  ```

**Expected**: All checks pass, system fully operational without POC files.

---

### Phase 7: Update Documentation (HOUSEKEEPING)

**Objective**: Update all documentation to reflect POC removal.

See **Documentation Updates Needed** section below for specific file changes.

---

## Documentation Updates Needed

### 1. Update Context Kit (HIGH PRIORITY)

**File**: `/Volumes/tkr-riffic/@tkr-projects/tkr-docusearch/.context-kit/_context-kit.yml`

**Action**: Add note to `semantic` section:
```yaml
semantic:
  ~poc_removed: "POC pages removed, production frontend at /src/frontend/"
```

---

### 2. Update Orchestration README (HIGH PRIORITY)

**File**: `.context-kit/orchestration/library-frontend/README.md`

**Section**: Lines 298-299

**Change**:
```diff
-### POC Pages (To Be Removed)
-- `/data/copyparty/www/` - Proof of concept pages
-- `/data/copyparty/www/modules/document-card.js` - Original component
+### POC Pages (REMOVED - Wave 3)
+- POC pages at `/data/copyparty/www/` were removed in Wave 3
+- Replaced by production frontend at `/src/frontend/`
```

---

### 3. Update Agent Assignments (HIGH PRIORITY)

**File**: `.context-kit/orchestration/library-frontend/agent-assignments.md`

**Section**: Agent 11 tasks (lines 469+)

**Change**:
```diff
-**Status**: PENDING
+**Status**: COMPLETED (2025-10-13)

-**Deliverables**: Clean codebase, updated docs
+**Deliverables**:
+- CLEANUP_PLAN.md created
+- PRODUCTION_CHECKLIST.md created
+- WAVE_3_COMPLETION.md created
+- POC directory removed
+- Docker volume mount removed
+- Setup script updated
+- All documentation updated
```

---

### 4. Update Wave Completion Reports (MEDIUM PRIORITY)

**Files**:
- `.context-kit/orchestration/wave2-completion-report.md`
- `.context-kit/_ref/WAVE4_COMPLETION.md`

**Action**: Add note at top:
```markdown
> **Update (2025-10-13)**: POC pages referenced in this document were replaced by production frontend in Wave 3. See `/src/frontend/` for current implementation.
```

---

### 5. Update Architecture Docs (MEDIUM PRIORITY)

**Files**:
- `.context-kit/_ref/mvp-architecture.md`
- `.context-kit/orchestration/docusearch-mvp/integration-contracts/config-interface.md`

**Action**: Update Docker Compose examples to remove POC volume mount.

---

### 6. Update Quick Start Guide (HIGH PRIORITY)

**File**: `docs/QUICK_START.md` (if exists)

**Action**: Ensure frontend URL is `http://localhost:8002/frontend/` (not POC paths).

---

## Migration Verification Steps

### Automated Verification

**Script**: Create verification script (run after cleanup)

```bash
#!/bin/bash
# verify-poc-removal.sh

echo "Verifying POC removal..."

# 1. Check POC directory does not exist
if [ -d "data/copyparty/www" ]; then
  echo "✗ FAIL: POC directory still exists"
  exit 1
fi
echo "✓ PASS: POC directory removed"

# 2. Check Docker volume mount removed
if grep -q "data/copyparty/www:/www" docker/docker-compose.yml; then
  echo "✗ FAIL: Docker volume mount still present"
  exit 1
fi
echo "✓ PASS: Docker volume mount removed"

# 3. Check no POC references in src/
if grep -r "copyparty/www" src/ 2>/dev/null | grep -v "Binary"; then
  echo "✗ FAIL: POC references found in src/"
  exit 1
fi
echo "✓ PASS: No POC references in src/"

# 4. Check production frontend exists
if [ ! -f "src/frontend/index.html" ]; then
  echo "✗ FAIL: Production frontend missing"
  exit 1
fi
echo "✓ PASS: Production frontend exists"

# 5. Check services are running
if ! curl -sf http://localhost:8002/frontend/ > /dev/null; then
  echo "✗ FAIL: Production frontend not accessible"
  exit 1
fi
echo "✓ PASS: Production frontend accessible"

echo ""
echo "=========================================="
echo "All verification checks passed!"
echo "=========================================="
```

**Usage**:
```bash
chmod +x scripts/verify-poc-removal.sh
./scripts/verify-poc-removal.sh
```

---

### Manual Verification

1. **Browser Check**:
   - Open `http://localhost:8002/frontend/`
   - Verify page loads without errors
   - Check browser console (F12) - no 404 errors for POC files
   - Check Network tab - all requests succeed

2. **Functional Check**:
   - Upload a document (drag-drop)
   - Verify processing status updates in real-time
   - Search for document
   - Filter by file type
   - Verify all features work

3. **Code Check**:
   ```bash
   # Search for any remaining POC references
   grep -r "data/copyparty/www" . 2>/dev/null | grep -v ".git" | grep -v ".tar.gz" | grep -v "CLEANUP_PLAN.md"
   # Should only show documentation files
   ```

4. **Docker Check**:
   ```bash
   docker-compose -f docker/docker-compose.yml config | grep -A 5 "volumes:"
   # Should NOT show data/copyparty/www:/www mount
   ```

---

## Rollback Plan

**If issues arise after POC removal:**

### Step 1: Restore POC Files
```bash
cd /Volumes/tkr-riffic/@tkr-projects/tkr-docusearch
tar -xzf data/copyparty/www-backup-[timestamp].tar.gz
```

### Step 2: Restore Docker Volume Mount
```bash
# Edit docker/docker-compose.yml
# Re-add: - ../data/copyparty/www:/www
```

### Step 3: Restart Services
```bash
./scripts/stop-all.sh
./scripts/start-all.sh
```

### Step 4: Verify POC Restored
```bash
curl http://localhost:8000/index.html
# Should return POC page
```

**NOTE**: Rollback should only be needed if production frontend has critical issues. Production frontend has been thoroughly tested and should work without POC files.

---

## Risk Assessment

### Low Risk
- **POC files are self-contained**: No production code imports from POC
- **Production is independent**: Uses different port, different architecture
- **Copyparty unaffected**: Upload functionality unchanged
- **Backup available**: Can rollback if needed

### Medium Risk
- **Docker configuration change**: Volume mount removal requires service restart
- **Documentation references**: Some old docs reference POC (will update)

### High Risk
- **NONE**: All production functionality is independent of POC

**Overall Risk Level**: LOW

---

## Success Criteria

Cleanup is successful when:

1. ✓ POC directory removed (`data/copyparty/www/` does not exist)
2. ✓ Docker volume mount removed from `docker-compose.yml`
3. ✓ Setup script updated (no POC directory creation)
4. ✓ Production frontend accessible at `http://localhost:8002/frontend/`
5. ✓ All production features working (upload, search, WebSocket)
6. ✓ No POC references in production source code (`src/`)
7. ✓ No errors in worker logs
8. ✓ No errors in Docker logs
9. ✓ No console errors in browser
10. ✓ Documentation updated to reflect migration
11. ✓ Backup created (can restore if needed)
12. ✓ Verification script passes all checks

---

## Timeline

**Estimated Duration**: 2-3 hours

**Phase Breakdown**:
- Phase 1 (Pre-Deletion Validation): 30 minutes
- Phase 2 (Backup): 5 minutes
- Phase 3 (Remove POC Files): 5 minutes
- Phase 4 (Update Docker): 10 minutes
- Phase 5 (Update Setup Script): 10 minutes
- Phase 6 (Post-Deletion Validation): 30 minutes
- Phase 7 (Update Documentation): 60 minutes

**Total**: ~2.5 hours

---

## Next Steps

1. **Review this cleanup plan** with project stakeholders
2. **Execute pre-deletion validation** (Phase 1)
3. **Create backup** (Phase 2)
4. **Execute cleanup** (Phases 3-5)
5. **Validate cleanup** (Phase 6)
6. **Update documentation** (Phase 7)
7. **Create production checklist** (see PRODUCTION_CHECKLIST.md)
8. **Create Wave 3 completion report** (see WAVE_3_COMPLETION.md)

---

## Appendix: File Size Summary

**POC Directory Total Size**: ~440 KB

**Breakdown**:
- HTML: 30.8 KB (4 files)
- JavaScript: 55.3 KB (5 main files + 7 modules)
- CSS: 29 KB (1 file)
- Assets: 340 KB (1 test image)
- Documentation: 4 KB (1 README)

**Disk Space Freed**: ~440 KB (negligible, but reduces clutter)

---

## Appendix: Production Frontend Comparison

**POC Features** → **Production Implementation**

| POC Feature | POC Location | Production Location | Status |
|------------|-------------|-------------------|--------|
| Document library grid | `index.html` | `src/frontend/index.html` | ✓ Enhanced |
| Document search | `search.html` | `src/frontend/filter-bar.js` | ✓ Enhanced |
| Status dashboard | `status_dashboard.html` | `src/frontend/library-manager.js` | ✓ Integrated |
| Document card | `modules/document-card.js` | `src/frontend/document-card.js` | ✓ Enhanced |
| File upload | `upload.js` | `src/frontend/upload-modal.js` | ✓ Enhanced |
| WebSocket status | `monitor.js` | `src/frontend/websocket-client.js` | ✓ Enhanced |
| Worker health | `modules/worker-health.js` | `src/frontend/websocket-client.js` | ✓ Integrated |
| File validation | `modules/file-validator.js` | `src/frontend/upload-modal.js` | ✓ Integrated |
| Copyparty client | `modules/copyparty-client.js` | `src/frontend/upload-modal.js` | ✓ Integrated |
| Processing monitor | `modules/processing-monitor.js` | `src/frontend/library-manager.js` | ✓ Enhanced |
| Queue manager | `modules/queue-manager.js` | Worker API | ✓ Server-side |

**Summary**: All POC features have production equivalents with enhancements. No functionality lost.

---

*End of Cleanup Plan*
