# Validation Strategy - Audio Album Art

**Feature**: Audio player album art display with fallback

**Approach**: Progressive validation through wave gates

**Philosophy**: Validate early, validate often, prevent integration failures

---

## Validation Levels

### Level 1: Unit Testing (Agent-Level)

**Scope**: Individual components in isolation

**Executed By**: Each agent during Wave 1

**Tools**: pytest, browser console

---

### Level 2: Integration Testing (Cross-Agent)

**Scope**: Components working together

**Executed By**: integration-test-agent during Wave 1

**Tools**: pytest (integration tests), manual browser testing

---

### Level 3: System Testing (End-to-End)

**Scope**: Complete feature with real data

**Executed By**: Orchestrator during Wave 2

**Tools**: Lighthouse, manual testing, multiple browsers

---

## Wave 1 Quality Gates

### Gate 1.1: Backend API (backend-api-agent)

**Must Pass Before**: frontend-ui-agent, integration-test-agent can proceed

#### Unit Tests

```bash
# Test suite: src/processing/test_audio_album_art.py
pytest src/processing/test_audio_album_art.py -v --cov=src.processing.documents_api

# Required tests:
# ✅ test_cover_endpoint_with_art
# ✅ test_cover_endpoint_without_art
# ✅ test_cover_endpoint_invalid_id
# ✅ test_cover_endpoint_mime_types (JPEG, PNG)
# ✅ test_metadata_has_album_art
# ✅ test_metadata_without_album_art
# ✅ test_metadata_non_audio_document
```

#### Manual Verification

```bash
# 1. Endpoint exists and responds
curl -I http://localhost:8002/documents/{test_doc_id}/cover
# Expected: 200 OK (if art exists) OR 404 (if not)

# 2. Metadata includes new fields
curl http://localhost:8002/documents/{test_doc_id} | jq '.metadata | {has_album_art, album_art_url}'
# Expected: {"has_album_art": true/false, "album_art_url": "..." or null}

# 3. MIME type correct
curl -I http://localhost:8002/documents/{test_doc_id}/cover | grep -i content-type
# Expected: image/jpeg OR image/png
```

#### Performance Requirements

- Endpoint response time < 50ms (local file)
- Metadata overhead < 1ms (file existence check)

#### Security Validation

```bash
# Path traversal prevention
curl http://localhost:8002/documents/../../../etc/passwd/cover
# Expected: 400 Bad Request

# Invalid characters
curl http://localhost:8002/documents/doc!@#$/cover
# Expected: 400 Bad Request
```

**Gate Status**: ✅ PASS if all tests pass + manual verification + security checks

---

### Gate 1.2: Frontend UI (frontend-ui-agent)

**Must Pass Before**: integration testing can complete

#### Visual Regression Tests

**Manual Checklist** (browser testing):

```
Test Case 1: Album Art Available
─────────────────────────────────
URL: /details.html?doc={doc_with_art}

✓ Album art image displays
✓ Image is 300x300px max (desktop)
✓ Border radius applied (8px)
✓ Box shadow visible
✓ Lazy loading working (check Network tab)
✓ Fade-in transition on load (200ms)
✓ No layout shift (container sized before image)

Test Case 2: Album Art Unavailable
───────────────────────────────────
URL: /details.html?doc={doc_without_art}

✓ Default SVG displays
✓ SVG is gray microphone icon
✓ No broken image icon
✓ Same size as case 1 (300x300px)
✓ No network request for cover art

Test Case 3: Album Art Load Error
──────────────────────────────────
Simulate: Block /documents/{doc}/cover in DevTools Network

✓ Image falls back to default SVG
✓ No broken image visible
✓ No console errors
✓ Fallback happens smoothly

Test Case 4: Responsive Mobile
──────────────────────────────
Resize: 375px viewport width

✓ Image scales to 200x200px
✓ Still centered
✓ Still has border radius
✓ Proportions maintained
```

#### Browser Compatibility

Test in:
- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile Safari (iOS 15+)
- ✅ Chrome Mobile (Android)

**Expected**: Identical rendering in all browsers

#### Accessibility

```bash
# Lighthouse audit
lighthouse http://localhost:8000/details.html?doc={test_doc} --only-categories=accessibility

# Requirements:
# ✓ Accessibility score ≥ 90
# ✓ Images have alt text
# ✓ Color contrast ≥ 4.5:1 (WCAG AA)
# ✓ No keyboard navigation issues
```

**Gate Status**: ✅ PASS if all visual tests pass + browser compatibility + accessibility score

---

### Gate 1.3: Integration Testing (integration-test-agent)

**Must Pass Before**: Wave 2 (orchestrator validation)

#### End-to-End Pipeline Tests

```bash
# Test suite: src/processing/test_audio_album_art.py (integration section)
pytest src/processing/test_audio_album_art.py::TestIntegration -v

# Required tests:
# ✅ test_full_pipeline_with_art (upload → extract → serve → display)
# ✅ test_full_pipeline_without_art (fallback path)
# ✅ test_multiple_audio_formats (MP3, WAV)
# ✅ test_large_album_art (>1MB images)
# ✅ test_album_art_formats (JPEG, PNG)
```

#### Cross-Component Integration

```python
def test_full_pipeline_with_art():
    """Test complete album art pipeline."""
    # 1. Upload audio file with embedded album art
    upload_result = upload_audio_file("test_audio_with_art.mp3")
    doc_id = upload_result["doc_id"]

    # 2. Wait for processing
    wait_for_processing(doc_id, timeout=30)

    # 3. Verify album art extracted to filesystem
    cover_path = Path(f"data/images/{doc_id}/cover.jpg")
    assert cover_path.exists()
    assert cover_path.stat().st_size > 0

    # 4. Verify metadata includes album art fields
    doc = get_document(doc_id)
    assert doc["metadata"]["has_album_art"] is True
    assert doc["metadata"]["album_art_url"] == f"/documents/{doc_id}/cover"

    # 5. Verify cover endpoint serves image
    response = client.get(f"/documents/{doc_id}/cover")
    assert response.status_code == 200
    assert response.headers["content-type"] in ["image/jpeg", "image/png"]

    # 6. Verify UI displays image (headless browser test)
    browser = Browser()
    browser.goto(f"http://localhost:8000/details.html?doc={doc_id}")
    album_art_src = browser.get_attribute("#album-art", "src")
    assert f"/documents/{doc_id}/cover" in album_art_src
```

#### Performance Testing

```python
def test_album_art_load_performance():
    """Verify album art loads within performance budget."""
    import time

    doc_id = create_test_doc_with_art()

    start = time.time()
    response = client.get(f"/documents/{doc_id}/cover")
    latency = time.time() - start

    assert latency < 0.05  # 50ms
    assert response.status_code == 200
```

**Gate Status**: ✅ PASS if all integration tests pass + performance within budget

---

## Wave 2 Quality Gates

### Gate 2.1: Cross-Browser Validation (Orchestrator)

#### Functional Testing

**Test Matrix**:

| Browser | Desktop | Mobile | Album Art | Fallback | Responsive |
|---------|---------|--------|-----------|----------|------------|
| Chrome 120+ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Firefox 120+ | ✅ | - | ✅ | ✅ | ✅ |
| Safari 17+ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Edge 120+ | ✅ | - | ✅ | ✅ | ✅ |

**Pass Criteria**: All cells must be ✅

---

### Gate 2.2: Accessibility Audit (Orchestrator)

#### WCAG 2.1 AA Compliance

```bash
# Lighthouse accessibility audit
lighthouse http://localhost:8000/details.html?doc={test_doc} \
  --only-categories=accessibility \
  --output=html \
  --output-path=./accessibility-report.html

# Requirements:
# ✓ Score ≥ 90
# ✓ All images have alt text
# ✓ Color contrast ratios meet AA (4.5:1)
# ✓ Keyboard navigation works
# ✓ Screen reader compatible
```

#### Manual Screen Reader Test

**NVDA (Windows)** or **VoiceOver (Mac)**:
- Navigate to audio player
- Verify album art alt text read correctly
- Verify controls accessible via keyboard

---

### Gate 2.3: Mobile Responsiveness (Orchestrator)

#### Viewport Testing

| Viewport | Width | Album Art Size | Expected |
|----------|-------|----------------|----------|
| iPhone SE | 375px | 200x200px | ✅ PASS |
| iPhone 12 | 390px | 200x200px | ✅ PASS |
| iPhone 12 Pro Max | 428px | 200x200px | ✅ PASS |
| iPad | 768px | 300x300px | ✅ PASS |
| Desktop | 1280px | 300x300px | ✅ PASS |

**Test Method**:
```javascript
// Chrome DevTools responsive mode
// For each viewport:
const img = document.getElementById('album-art');
const width = img.offsetWidth;
const height = img.offsetHeight;
console.assert(width === height, "Must be square");
console.assert(width <= 200, "Mobile max 200px");
```

---

### Gate 2.4: Performance Validation (Orchestrator)

#### Core Web Vitals

```bash
# Lighthouse performance audit
lighthouse http://localhost:8000/details.html?doc={test_doc} \
  --only-categories=performance

# Requirements:
# ✓ LCP (Largest Contentful Paint) < 2.5s
# ✓ FID (First Input Delay) < 100ms
# ✓ CLS (Cumulative Layout Shift) < 0.1
```

#### Image Load Metrics

```javascript
// Measure album art load time
const img = document.getElementById('album-art');
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (entry.name.includes('/cover')) {
      console.log(`Album art load time: ${entry.duration}ms`);
      console.assert(entry.duration < 500, "Must load in < 500ms");
    }
  }
});
observer.observe({ entryTypes: ['resource'] });
```

---

## Regression Testing

### Existing Functionality Verification

**Must Not Break**:
- ✅ Audio playback still works
- ✅ VTT captions still work
- ✅ Audio metadata display intact
- ✅ Accordion synchronization functional
- ✅ No new console errors

**Test Coverage**:
```bash
# Run existing audio player tests
pytest src/processing/test_audio_metadata.py -v
pytest src/frontend/test_audio_player.py -v  # if exists

# Manual regression test
# Play audio file, verify:
# - Audio plays
# - Captions display
# - Title/artist shows
# - Accordion syncs on time
```

---

## Continuous Validation

### Pre-Commit Checks

```bash
# Backend tests (fast)
pytest src/processing/test_audio_album_art.py -v -x

# Frontend linting
npm run lint src/frontend/audio-player.js
```

### CI/CD Pipeline

```yaml
# .github/workflows/album-art-validation.yml
name: Album Art Validation

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run backend tests
        run: pytest src/processing/test_audio_album_art.py -v

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Lighthouse
        run: |
          npm install -g @lhci/cli
          lhci autorun
```

---

## Failure Handling

### What If a Gate Fails?

**Process**:
1. **Identify** failing test/check
2. **Assign** to responsible agent
3. **Fix** issue
4. **Re-validate** gate
5. **Document** fix in status file

**Example**:
```json
{
  "gate": "1.1-backend-api",
  "status": "FAILED",
  "failed_tests": [
    "test_cover_endpoint_mime_types"
  ],
  "assigned_to": "backend-api-agent",
  "fix_applied": "Updated MIME type detection logic",
  "re_validated": "2025-10-15T14:30:00Z",
  "final_status": "PASSED"
}
```

---

## Success Metrics

### Definition of Done

**Wave 1**:
- ✅ All unit tests pass (100%)
- ✅ All integration tests pass (100%)
- ✅ Manual testing checklists complete
- ✅ No blockers reported

**Wave 2**:
- ✅ Cross-browser compatibility verified
- ✅ Accessibility score ≥ 90
- ✅ Mobile responsive (5 viewports)
- ✅ Performance within budget
- ✅ No regressions

**Production Ready**:
- ✅ All gates passed
- ✅ Documentation complete
- ✅ Zero P0/P1 bugs
- ✅ Orchestrator sign-off

---

*Generated: 2025-10-15 | Orchestrator*
