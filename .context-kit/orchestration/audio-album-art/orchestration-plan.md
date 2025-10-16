# Audio Player Album Art - Orchestration Plan

**Feature Goal**: Add album art display to audio player with fallback to default SVG

**Status**: Wave 0 COMPLETE - Ready for Wave 1 execution

**Agents**: 3 parallel agents (backend-api, frontend-ui, integration-test)

**Estimated Duration**: 0.5 days with parallel execution

---

## Architecture Overview

### Components

```
┌─────────────────────────────────────────────────────┐
│                  AUDIO PLAYER UI                    │
│  ┌──────────────┐  ┌──────────────────────────┐   │
│  │  Album Art   │  │   Audio Metadata         │   │
│  │  (300x300)   │  │   Title, Artist, Album   │   │
│  │              │  │   Duration               │   │
│  │  + Default   │  └──────────────────────────┘   │
│  │    SVG       │                                  │
│  └──────────────┘  ┌──────────────────────────┐   │
│                     │   HTML5 Audio Player     │   │
│                     │   + VTT Captions         │   │
│                     └──────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                          ↓
                  ┌──────────────┐
                  │  API Layer   │
                  └──────────────┘
                          ↓
              GET /documents/{doc_id}/cover
                          ↓
              ┌──────────────────────┐
              │  File System         │
              │  data/images/{id}/   │
              │    cover.{jpg|png}   │
              └──────────────────────┘
```

### Data Flow

1. **Page Load** → Fetch document metadata (`GET /documents/{doc_id}`)
2. **Metadata Check** → `has_album_art` boolean flag
3. **Image Request** → `GET /documents/{doc_id}/cover` (if has_album_art)
4. **Display** → Show image OR default SVG fallback

---

## Wave Execution Plan

### **Wave 0: Specification** (Current - Orchestrator)

**Agent**: orchestrator

**Deliverables**:
- ✅ Integration contracts
- ✅ Agent assignments
- ✅ Validation strategy
- ✅ Coordination protocol

**Status**: COMPLETE

---

### **Wave 1: Parallel Implementation** (3 agents)

**Prerequisites**: Wave 0 complete

**Duration**: 2-3 hours (parallel execution)

#### **Agent 1: backend-api-agent**

**Territory**:
- `src/processing/documents_api.py` (add new endpoint)
- No shared file conflicts

**Deliverables**:
1. New endpoint: `GET /documents/{doc_id}/cover`
   - Serve image from `data/images/{doc_id}/cover.{ext}`
   - Return 404 if not found
   - Set correct MIME type from metadata
   - Security: validate doc_id pattern

2. Update `DocumentMetadata` schema:
   - Add `album_art_url: Optional[str]` field
   - Add `has_album_art: bool` field (computed from file existence)

3. Unit tests:
   - Test cover art serving
   - Test 404 handling
   - Test MIME type detection
   - Test invalid doc_id rejection

**Integration Points**:
- OUT: Album art URL → frontend-ui-agent
- OUT: `has_album_art` flag → frontend-ui-agent

**Validation**:
```bash
# Test endpoint exists
curl http://localhost:8002/documents/{test_doc_id}/cover

# Test metadata includes album art fields
curl http://localhost:8002/documents/{test_doc_id} | jq '.metadata.has_album_art'
```

---

#### **Agent 2: frontend-ui-agent**

**Territory**:
- `src/frontend/details.html` (audio container section only - lines 74-94)
- `src/frontend/details.css` (audio styles section only - lines 120-150)
- `src/frontend/audio-player.js` (displayMetadata method only)

**Deliverables**:
1. HTML structure (details.html):
   - Add album art container before audio metadata
   - Include `<img id="album-art">` element
   - Add inline default SVG as data URI fallback

2. CSS styling (details.css):
   - `.album-art-container` (center alignment, spacing)
   - `.album-art` (300x300px max, border-radius, shadow)
   - Responsive: 200x200px on mobile
   - Loading state placeholder

3. JavaScript logic (audio-player.js):
   - Modify `displayMetadata()` to load album art
   - Check `metadata.has_album_art`
   - Set image src to album art URL OR default SVG
   - Error handler: fallback to default SVG on 404
   - Lazy loading with fade-in transition

4. Default SVG integration:
   - Convert `.context-kit/_ref/details_page/default_audio_cover_art.svg` to data URI
   - Embed in audio-player.js as constant

**Integration Points**:
- IN: Album art URL ← backend-api-agent
- IN: `has_album_art` flag ← backend-api-agent

**Validation**:
```javascript
// Test with album art
const player = new AudioPlayer('audio-container', docId, metadata);
assert(document.getElementById('album-art').src.includes('/cover'));

// Test without album art (fallback)
const player2 = new AudioPlayer('audio-container', docId, metadataNoArt);
assert(document.getElementById('album-art').src.includes('data:image/svg'));
```

---

#### **Agent 3: integration-test-agent**

**Territory**:
- `src/processing/test_audio_album_art.py` (new file)
- `src/frontend/test_audio_player_album_art.html` (new file - manual testing)

**Deliverables**:
1. Backend integration tests:
   - Test full pipeline: audio upload → album art extraction → cover endpoint
   - Test with MP3 with embedded album art
   - Test with MP3 without album art
   - Test with WAV file

2. Frontend manual testing guide:
   - HTML page with test scenarios
   - Document expected behavior
   - Screenshots/visual regression tests

3. End-to-end validation:
   - Upload audio file
   - Verify cover art displays
   - Verify fallback works
   - Test on mobile viewport

**Integration Points**:
- IN: Cover endpoint ← backend-api-agent
- IN: UI components ← frontend-ui-agent

**Validation**:
```bash
# Run integration tests
pytest src/processing/test_audio_album_art.py -v

# Manual testing
open src/frontend/test_audio_player_album_art.html
```

---

### **Wave 2: Integration & Polish** (Sequential - Orchestrator)

**Prerequisites**: Wave 1 complete, all tests passing

**Duration**: 30 minutes

**Deliverables**:
1. Cross-agent integration verification
2. Accessibility audit (WCAG AA compliance)
3. Mobile responsiveness verification
4. Performance check (image loading)
5. Documentation updates

**Validation**:
- ✅ All unit tests pass
- ✅ Integration tests pass
- ✅ Manual testing checklist complete
- ✅ Accessibility score > 90
- ✅ Mobile responsive (3 viewport sizes)
- ✅ No console errors

---

## Territorial Boundaries

### File Ownership (Zero Conflicts)

| File | Agent | Modification Type | Lines |
|------|-------|-------------------|-------|
| `src/processing/documents_api.py` | backend-api | ADD new endpoint | New function |
| `src/processing/documents_api.py` | backend-api | EXTEND schema | DocumentMetadata class |
| `src/frontend/details.html` | frontend-ui | EDIT audio section | 74-94 only |
| `src/frontend/details.css` | frontend-ui | ADD styles | Append to audio section |
| `src/frontend/audio-player.js` | frontend-ui | EDIT method | displayMetadata() only |
| `src/processing/test_audio_album_art.py` | integration-test | CREATE new file | N/A |
| `src/frontend/test_audio_player_album_art.html` | integration-test | CREATE new file | N/A |

**Conflict Prevention**:
- No two agents modify the same file section
- New files preferred over modifying shared code
- Clear line ranges for HTML/CSS edits

---

## Integration Contracts

### IC-001: Album Art API Endpoint

**Provider**: backend-api-agent

**Consumers**: frontend-ui-agent, integration-test-agent

**Contract**: See `integration-contracts/01-album-art-api.md`

**Key Points**:
- Endpoint: `GET /documents/{doc_id}/cover`
- Response: Image file (JPEG/PNG) OR 404
- MIME type: Set from metadata (`album_art_mime`)
- Security: Validate doc_id, prevent path traversal

---

### IC-002: Album Art Metadata Extension

**Provider**: backend-api-agent

**Consumers**: frontend-ui-agent

**Contract**: See `integration-contracts/02-album-art-metadata.md`

**Key Points**:
- `DocumentMetadata.has_album_art: bool`
- `DocumentMetadata.album_art_url: Optional[str]` (e.g., `/documents/{doc_id}/cover`)
- Computed at request time (check file existence)

---

### IC-003: Default SVG Fallback

**Provider**: frontend-ui-agent (self-contained)

**Consumers**: None (internal to UI)

**Contract**: See `integration-contracts/03-default-svg-fallback.md`

**Key Points**:
- SVG converted to data URI
- Always available (no network request)
- Gray microphone icon on dark background

---

## Quality Gates

### Wave 1 Gate (Must Pass Before Wave 2)

**Backend Tests**:
```bash
# Album art endpoint tests
pytest src/processing/test_audio_album_art.py::test_cover_endpoint_with_art -v
pytest src/processing/test_audio_album_art.py::test_cover_endpoint_without_art -v
pytest src/processing/test_audio_album_art.py::test_cover_endpoint_invalid_id -v

# Metadata extension tests
pytest src/processing/test_audio_album_art.py::test_metadata_has_album_art -v
```

**Frontend Tests**:
```javascript
// Manual testing checklist
✓ Album art displays when available
✓ Default SVG displays when unavailable
✓ Image loads with fade-in transition
✓ Error handler works (404 → fallback)
✓ Responsive on mobile (200x200px)
✓ Lazy loading works
```

**Integration Tests**:
```bash
# End-to-end pipeline
pytest src/processing/test_audio_album_art.py::test_full_pipeline_with_art -v
pytest src/processing/test_audio_album_art.py::test_full_pipeline_without_art -v
```

**Performance**:
- Image load time < 500ms (local files)
- No layout shift (fixed container size)
- Lazy loading prevents unnecessary requests

**Accessibility**:
- `alt` text includes audio title/artist
- No keyboard interaction needed (decorative image)
- Color contrast meets WCAG AA

---

## Risk Mitigation

### Risk 1: Image MIME Type Detection

**Risk**: Incorrect MIME type causes browser rendering issues

**Mitigation**:
- Use metadata `album_art_mime` field (extracted during processing)
- Fallback to file extension detection if metadata missing
- Test with JPEG and PNG

**Fallback**: Serve as `application/octet-stream` if unknown

---

### Risk 2: Large Image Files

**Risk**: Large album art slows page load

**Mitigation**:
- Lazy loading (`loading="lazy"`)
- CSS `max-width: 300px` prevents huge renders
- Browser caching (add `Cache-Control` header)

**Fallback**: Consider image resizing in future iteration

---

### Risk 3: Missing Default SVG

**Risk**: Data URI conversion fails

**Mitigation**:
- Test data URI in browser during development
- Keep original SVG as backup in comments
- Validate base64 encoding

**Fallback**: Plain gray placeholder div with text "🎵"

---

## Success Metrics

### Technical
- ✅ Zero merge conflicts (territorial boundaries)
- ✅ 100% contract compliance (all specs met)
- ✅ All quality gates pass
- ✅ < 2 integration bugs

### Delivery
- ✅ Wave 1 complete: 2-3 hours (parallel)
- ✅ Wave 2 complete: 30 minutes (sequential)
- ✅ **Total: 0.5 days**

### Quality
- ✅ Accessibility score > 90
- ✅ Mobile responsive (tested on 3 viewports)
- ✅ Image load time < 500ms
- ✅ Graceful fallback working

---

## Agent Launch Commands

### Wave 1 (Parallel - Launch All)

```bash
# Launch backend-api-agent
claude-code --agent backend-api-agent \
  --spec .context-kit/orchestration/audio-album-art/integration-contracts/01-album-art-api.md \
  --output .context-kit/orchestration/audio-album-art/status/backend-api.json

# Launch frontend-ui-agent
claude-code --agent frontend-ui-agent \
  --spec .context-kit/orchestration/audio-album-art/integration-contracts/02-album-art-metadata.md \
  --output .context-kit/orchestration/audio-album-art/status/frontend-ui.json

# Launch integration-test-agent
claude-code --agent integration-test-agent \
  --spec .context-kit/orchestration/audio-album-art/integration-contracts/integration-testing.md \
  --output .context-kit/orchestration/audio-album-art/status/integration-test.json
```

---

## Status Monitoring

Each agent updates: `.context-kit/orchestration/audio-album-art/status/{agent-name}.json`

```json
{
  "agent": "backend-api-agent",
  "wave": 1,
  "status": "complete",
  "progress": 1.0,
  "deliverables": {
    "cover_endpoint": "✅ DONE",
    "metadata_extension": "✅ DONE",
    "unit_tests": "✅ DONE"
  },
  "integration_points": {
    "album_art_url": "/documents/{doc_id}/cover",
    "has_album_art_field": true
  },
  "issues": []
}
```

---

## References

- Wireframes: `.context-kit/_ref/details_page/audio.svg`
- Default SVG: `.context-kit/_ref/details_page/default_audio_cover_art.svg`
- Current implementation: `src/frontend/audio-player.js`
- Audio metadata: `src/processing/audio_metadata.py`
- Documents API: `src/processing/documents_api.py`

---

*Generated: 2025-10-15 | Wave 0 Orchestrator*
