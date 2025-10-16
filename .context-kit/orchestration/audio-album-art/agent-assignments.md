# Agent Assignments - Audio Album Art

**Feature**: Audio player album art display with fallback

**Wave Model**: 2 waves (1 parallel, 1 sequential)

**Total Agents**: 3 parallel + 1 orchestrator

---

## Agent Roster

| Agent ID | Role | Wave | Files Owned | Dependencies |
|----------|------|------|-------------|--------------|
| backend-api-agent | API Layer | 1 | `documents_api.py` (new endpoint) | None |
| frontend-ui-agent | UI Components | 1 | `details.html`, `details.css`, `audio-player.js` | IC-001, IC-002 |
| integration-test-agent | Testing | 1 | `test_audio_album_art.py` (new) | IC-001, IC-002 |
| orchestrator | Integration & QA | 2 | Validation, documentation | Wave 1 complete |

---

## Agent 1: backend-api-agent

### Responsibilities

**Primary Goal**: Implement album art serving infrastructure

**Deliverables**:
1. New API endpoint: `GET /documents/{doc_id}/cover`
2. Extended `DocumentMetadata` schema with album art fields
3. Backend unit tests for album art functionality

### Territory (File Ownership)

**Exclusive Write Access**:
- `src/processing/documents_api.py` (add new endpoint)
  - Lines: New function `get_album_art()` (append to file)
  - Lines: Modify `DocumentMetadata` class (lines ~77-87)
  - Lines: Modify `get_document_by_id()` function (add album art logic)

**New Files**:
- `src/processing/test_audio_album_art.py` (backend tests only)

**Read-Only Access**:
- `src/processing/audio_metadata.py` (reference metadata schema)
- `data/images/` directory structure

### Integration Contracts Provided

- **IC-001**: Album Art API Endpoint
- **IC-002**: Album Art Metadata Extension

### Integration Contracts Consumed

- None (foundation layer)

### Validation Criteria

```bash
# All backend tests pass
pytest src/processing/test_audio_album_art.py::test_cover_endpoint_with_art -v
pytest src/processing/test_audio_album_art.py::test_cover_endpoint_without_art -v
pytest src/processing/test_audio_album_art.py::test_cover_endpoint_invalid_id -v
pytest src/processing/test_audio_album_art.py::test_metadata_has_album_art -v
pytest src/processing/test_audio_album_art.py::test_metadata_without_album_art -v

# Endpoint functional
curl -I http://localhost:8002/documents/{real_doc_id}/cover
# Expected: 200 OK, image/jpeg

# Metadata includes fields
curl http://localhost:8002/documents/{real_doc_id} | jq '.metadata.has_album_art'
# Expected: true or false
```

### Dependencies

**Prerequisites**: None (can start immediately)

**Blocks**: frontend-ui-agent, integration-test-agent (need IC-001, IC-002)

### Time Estimate

**Development**: 1.5 hours
- Endpoint implementation: 45 minutes
- Metadata extension: 30 minutes
- Unit tests: 15 minutes

---

## Agent 2: frontend-ui-agent

### Responsibilities

**Primary Goal**: Implement album art UI display with fallback

**Deliverables**:
1. HTML structure for album art display
2. CSS styling (responsive, 300px → 200px mobile)
3. JavaScript album art loading logic
4. Default SVG fallback (data URI)

### Territory (File Ownership)

**Exclusive Write Access**:
- `src/frontend/details.html`
  - Lines: 74-94 (audio container section ONLY)
  - Add: Album art `<div>` and `<img>` elements

- `src/frontend/details.css`
  - Lines: 120-150 (audio styles section ONLY)
  - Add: `.album-art-container` and `.album-art` styles
  - Add: Responsive styles for mobile

- `src/frontend/audio-player.js`
  - Lines: Add `DEFAULT_ALBUM_ART_SVG` constant at top
  - Lines: Modify `displayMetadata()` method (add album art display)
  - Lines: Add new `displayAlbumArt()` method

**Read-Only Access**:
- `.context-kit/_ref/details_page/default_audio_cover_art.svg` (convert to data URI)

### Integration Contracts Provided

- **IC-003**: Default SVG Fallback (internal only)

### Integration Contracts Consumed

- **IC-001**: Album Art API Endpoint (from backend-api-agent)
- **IC-002**: Album Art Metadata Extension (from backend-api-agent)

### Validation Criteria

```javascript
// Visual testing in browser console
const player = new AudioPlayer('audio-container', docId, metadata);

// Test 1: Album art with cover
assert(document.getElementById('album-art').src.includes('/cover'));

// Test 2: Album art without cover (fallback)
const metadataNoArt = { ...metadata, has_album_art: false };
const player2 = new AudioPlayer('audio-container', docId, metadataNoArt);
assert(document.getElementById('album-art').src.includes('data:image/svg'));

// Test 3: Responsive (resize browser to < 768px)
// Expected: Image scales to 200x200px
```

**Manual Testing Checklist**:
- [ ] Album art displays when available
- [ ] Default SVG displays when unavailable
- [ ] Image loads with lazy loading
- [ ] Error handler works (404 → fallback)
- [ ] Responsive on mobile (200x200px)
- [ ] Fade-in transition works
- [ ] No broken image placeholders

### Dependencies

**Prerequisites**: backend-api-agent complete (need IC-001, IC-002)

**Blocks**: integration-test-agent (provides UI for testing)

### Time Estimate

**Development**: 2 hours
- HTML structure: 15 minutes
- CSS styling: 30 minutes
- SVG data URI conversion: 15 minutes
- JavaScript logic: 45 minutes
- Manual testing: 15 minutes

---

## Agent 3: integration-test-agent

### Responsibilities

**Primary Goal**: Validate end-to-end album art functionality

**Deliverables**:
1. Backend integration tests (full pipeline)
2. Frontend manual testing guide (HTML page)
3. End-to-end validation documentation

### Territory (File Ownership)

**Exclusive Write Access**:
- `src/processing/test_audio_album_art.py`
  - Integration tests only (not unit tests - backend-api-agent owns those)
  - Tests: Full pipeline, multiple file formats

- `src/frontend/test_audio_player_album_art.html` (new file)
  - Manual testing page
  - Test scenarios with screenshots

**Read-Only Access**:
- All files from other agents (for testing)

### Integration Contracts Provided

- None (consumer only)

### Integration Contracts Consumed

- **IC-001**: Album Art API Endpoint (test coverage)
- **IC-002**: Album Art Metadata Extension (test coverage)
- **IC-003**: Default SVG Fallback (visual testing)

### Validation Criteria

```bash
# Integration tests pass
pytest src/processing/test_audio_album_art.py::test_full_pipeline_with_art -v
pytest src/processing/test_audio_album_art.py::test_full_pipeline_without_art -v
pytest src/processing/test_audio_album_art.py::test_multiple_audio_formats -v

# Manual testing complete
open src/frontend/test_audio_player_album_art.html
# Complete checklist in browser
```

**Integration Test Coverage**:
- [ ] Upload MP3 with album art → cover displays
- [ ] Upload MP3 without album art → default SVG displays
- [ ] Upload WAV file → handles correctly
- [ ] Multiple formats (JPEG, PNG album art)
- [ ] Large files (>1MB album art)
- [ ] Mobile viewport (responsive)

### Dependencies

**Prerequisites**: backend-api-agent AND frontend-ui-agent complete

**Blocks**: None (final validation)

### Time Estimate

**Development**: 1 hour
- Integration tests: 30 minutes
- Manual testing page: 20 minutes
- Documentation: 10 minutes

---

## Orchestrator (Wave 2)

### Responsibilities

**Primary Goal**: Cross-agent integration and quality assurance

**Deliverables**:
1. Integration verification across all agents
2. Accessibility audit (WCAG AA)
3. Performance validation
4. Documentation updates
5. Production readiness sign-off

### Tasks

**Integration Validation**:
- Verify all contracts met (IC-001, IC-002, IC-003)
- Cross-agent smoke testing
- Resolve any integration issues

**Quality Assurance**:
- Run accessibility audit (Lighthouse)
- Test on 3 mobile viewports (320px, 375px, 414px)
- Performance check (image load time < 500ms)
- Browser compatibility (Chrome, Firefox, Safari)

**Documentation**:
- Update API documentation
- Update frontend component docs
- Add troubleshooting guide

### Validation Criteria

**Must Pass**:
- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ Manual testing checklist complete
- ✅ Accessibility score > 90 (Lighthouse)
- ✅ Mobile responsive (3 viewports)
- ✅ No console errors
- ✅ Image load time < 500ms

**Quality Metrics**:
- Zero merge conflicts (territorial boundaries)
- 100% contract compliance
- < 2 integration bugs

---

## Communication Protocol

### Status Updates

Each agent must update: `.context-kit/orchestration/audio-album-art/status/{agent-name}.json`

```json
{
  "agent": "backend-api-agent",
  "wave": 1,
  "status": "in_progress",  // pending | in_progress | complete | blocked
  "progress": 0.75,
  "deliverables": {
    "cover_endpoint": "✅ DONE",
    "metadata_extension": "⏳ IN PROGRESS",
    "unit_tests": "⬜ TODO"
  },
  "integration_points": {
    "album_art_url": "/documents/{doc_id}/cover",
    "has_album_art_field": true
  },
  "blockers": [],
  "issues": [
    "Minor: MIME type detection needs refinement"
  ]
}
```

### Handoff Notifications

When providing integration contract:
```json
{
  "from": "backend-api-agent",
  "to": ["frontend-ui-agent", "integration-test-agent"],
  "contract": "IC-001",
  "status": "COMPLETE",
  "verification_url": "http://localhost:8002/documents/test-doc/cover",
  "notes": "Endpoint functional, supports JPEG and PNG"
}
```

---

## Conflict Prevention

### File Modification Matrix

| File | backend-api | frontend-ui | integration-test | Conflict Risk |
|------|-------------|-------------|------------------|---------------|
| `documents_api.py` | WRITE (new endpoint) | READ | READ | ✅ None |
| `details.html` | - | WRITE (lines 74-94) | READ | ✅ None |
| `details.css` | - | WRITE (audio section) | READ | ✅ None |
| `audio-player.js` | - | WRITE (displayMetadata) | READ | ✅ None |
| `test_audio_album_art.py` | WRITE (unit tests) | - | WRITE (integration) | ⚠️ Partition |

**Conflict Resolution**:
- `test_audio_album_art.py` partitioned:
  - backend-api-agent: Unit tests (top of file)
  - integration-test-agent: Integration tests (bottom of file)
  - Clear comment delimiter

---

## Success Criteria

### Wave 1 Complete When:
- ✅ All 3 agents mark status "complete"
- ✅ All quality gates pass (unit tests, integration tests)
- ✅ No blockers reported

### Wave 2 Complete When:
- ✅ Orchestrator validation passes
- ✅ Documentation updated
- ✅ Production ready

**Estimated Total Time**: 0.5 days (4 hours with parallel execution)

---

*Generated: 2025-10-15 | Orchestrator*
