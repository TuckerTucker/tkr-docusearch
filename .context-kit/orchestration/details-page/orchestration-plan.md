# Document Details Page - Orchestration Plan

**Feature Goal**: Build comprehensive document viewer with slideshow, audio player, and synchronized accordion navigation

**Max Agents**: 6
**Execution Model**: Wave-based with territorial ownership
**Conflict Prevention**: Interface-first development with progressive validation

---

## Agent Roster

### Backend Agents (3)

1. **data-layer-agent** - Core data structures and timestamp extraction
2. **vtt-agent** - VTT generation pipeline and utilities
3. **api-agent** - Document API endpoints (markdown, VTT, enhanced metadata)

### Frontend Agents (3)

4. **slideshow-agent** - Image slideshow component with keyboard navigation
5. **audio-agent** - Audio player with VTT caption support
6. **accordion-agent** - Text accordion with download/copy functionality

---

## Wave Execution Plan

### **Wave 0: Foundation & Contracts** (Sequential - 1 agent)

**Agent**: orchestrator (this session)

**Deliverables**:
- Integration contracts (all specifications below)
- Agent assignment documents
- Validation strategy
- Coordination protocol

**Duration**: Immediate (current task)

**Gate**: All contracts published and reviewed

---

### **Wave 1: Data Foundation** (Parallel - 2 agents)

**Prerequisites**: Wave 0 complete

**Agents**: data-layer-agent, vtt-agent

#### data-layer-agent
**Territory**:
- `src/processing/types.py` (TextChunk extension)
- `src/processing/docling_parser.py` (timestamp extraction)
- `src/processing/processor.py` (timestamp storage)

**Deliverables**:
1. Extended `TextChunk` with `start_time`/`end_time` fields
2. Timestamp extraction from docling provenance
3. Timestamp storage in ChromaDB metadata
4. Unit tests for timestamp extraction

**Integration Points**:
- OUT: `TextChunk` with timestamps → vtt-agent
- OUT: Stored timestamps → api-agent (Wave 2)

**Validation**:
```python
# Test: chunks have timestamps
assert chunk.start_time is not None
assert chunk.end_time is not None
assert chunk.end_time > chunk.start_time
```

#### vtt-agent
**Territory**:
- `src/processing/vtt_generator.py` (new file)
- `src/processing/vtt_utils.py` (new file - helpers)
- `data/vtt/` (output directory)

**Deliverables**:
1. VTT generator utility (`generate_vtt(chunks, filename) -> str`)
2. VTT file writer (`save_vtt(doc_id, vtt_content)`)
3. VTT integration into processor pipeline
4. Unit tests for VTT generation

**Integration Points**:
- IN: `TextChunk` with timestamps ← data-layer-agent
- OUT: VTT files in `data/vtt/{doc_id}.vtt` → api-agent (Wave 2)

**Validation**:
```python
# Test: VTT format compliance
vtt = generate_vtt(chunks, "test.mp3")
assert vtt.startswith("WEBVTT")
assert "00:00:10.000 --> 00:00:15.000" in vtt
```

**Wave 1 Gate**:
- ✅ TextChunk has timestamp fields
- ✅ Timestamps extracted from audio files
- ✅ VTT files generated and saved
- ✅ All unit tests pass

---

### **Wave 2: Backend APIs** (Parallel - 1 agent)

**Prerequisites**: Wave 1 complete

**Agent**: api-agent

**Territory**:
- `src/processing/documents_api.py` (extensions only, no edits to existing routes)
- `src/processing/markdown_utils.py` (new file - markdown helpers)

**Deliverables**:
1. `GET /documents/{doc_id}/markdown` endpoint with frontmatter
2. `GET /documents/{doc_id}/vtt` endpoint
3. Enhanced `GET /documents/{doc_id}` with timestamp data
4. API integration tests

**Integration Points**:
- IN: VTT files from `data/vtt/` ← vtt-agent
- IN: Timestamp metadata from ChromaDB ← data-layer-agent
- OUT: API responses → Frontend agents (Wave 3)

**Validation**:
```bash
# Test: API responses
curl http://localhost:8002/documents/{doc_id}/markdown
# Expected: YAML frontmatter + markdown content

curl http://localhost:8002/documents/{doc_id}/vtt
# Expected: text/vtt content-type, valid VTT

curl http://localhost:8002/documents/{doc_id}
# Expected: includes start_time/end_time in chunks[]
```

**Wave 2 Gate**:
- ✅ All three endpoints functional
- ✅ API integration tests pass
- ✅ Contract compliance verified

---

### **Wave 3: Frontend Components** (Parallel - 3 agents)

**Prerequisites**: Wave 2 complete (APIs available for testing)

**Agents**: slideshow-agent, audio-agent, accordion-agent

#### slideshow-agent
**Territory**:
- `src/frontend/slideshow.js` (new file)
- `src/frontend/slideshow.css` (new file)
- `src/frontend/details.html` (left column only)

**Deliverables**:
1. Slideshow component with prev/next navigation
2. Keyboard support (arrow keys)
3. Page counter: `[<input>] / Total`
4. Jump-to-page functionality
5. Image loading from `/images/{doc_id}/pageXXX.png`

**Integration Points**:
- IN: Page data from `GET /documents/{doc_id}` ← api-agent
- OUT: Navigation events → coordinator (Wave 4)

**API Contract**:
```javascript
class Slideshow {
  constructor(container, docId, pages) {}
  goToPage(pageNum) {}
  nextPage() {}
  prevPage() {}
  on(event, callback) {} // 'pagechange' event
}
```

**Validation**:
```javascript
// Test: slideshow navigation
slideshow.goToPage(3);
assert(slideshow.currentPage === 3);
```

#### audio-agent
**Territory**:
- `src/frontend/audio-player.js` (new file)
- `src/frontend/audio-player.css` (new file)
- `src/frontend/details.html` (left column alternative)

**Deliverables**:
1. Audio player with HTML5 `<audio>` element
2. VTT caption track support
3. Album art display
4. Time display and controls
5. Playback event emitters

**Integration Points**:
- IN: Audio metadata from `GET /documents/{doc_id}` ← api-agent
- IN: VTT track from `GET /documents/{doc_id}/vtt` ← api-agent
- OUT: Time update events → coordinator (Wave 4)

**API Contract**:
```javascript
class AudioPlayer {
  constructor(container, docId, audioMetadata) {}
  seek(timeSeconds) {}
  on(event, callback) {} // 'timeupdate', 'cuechange'
  getCurrentTime() {}
}
```

**Validation**:
```javascript
// Test: audio playback and seeking
audioPlayer.seek(10.5);
assert(audioPlayer.getCurrentTime() === 10.5);
```

#### accordion-agent
**Territory**:
- `src/frontend/accordion.js` (new file)
- `src/frontend/accordion.css` (new file)
- `src/frontend/details.html` (right column only)
- `src/frontend/clipboard-utils.js` (new file - copy helpers)
- `src/frontend/download-utils.js` (new file - download helpers)

**Deliverables**:
1. Accordion component with expand/collapse
2. Full markdown section (default open)
3. Per-chunk sections with download/copy buttons
4. VTT transcript section (for audio)
5. Download with frontmatter functionality
6. Copy to clipboard functionality

**Integration Points**:
- IN: Markdown from `GET /documents/{doc_id}/markdown` ← api-agent
- IN: Chunks from `GET /documents/{doc_id}` ← api-agent
- IN: VTT from `GET /documents/{doc_id}/vtt` ← api-agent
- OUT: Section click events → coordinator (Wave 4)

**API Contract**:
```javascript
class Accordion {
  constructor(container, docId, documentData) {}
  openSection(sectionId) {}
  closeSection(sectionId) {}
  on(event, callback) {} // 'sectionclick' event
  getSectionData(sectionId) {} // returns {page_num, start_time}
}
```

**Validation**:
```javascript
// Test: accordion interaction
accordion.openSection('chunk-0001');
assert(accordion.isOpen('chunk-0001') === true);
```

**Wave 3 Gate**:
- ✅ All three components render correctly
- ✅ Component APIs functional
- ✅ Individual component tests pass
- ✅ No integration yet (isolated testing)

---

### **Wave 4: Integration & Coordination** (Sequential - 1 agent)

**Prerequisites**: Wave 3 complete

**Agent**: orchestrator (this session) or dedicated integration-agent

**Territory**:
- `src/frontend/details-manager.js` (new file - main orchestrator)
- `src/frontend/details.html` (integration only, no component edits)

**Deliverables**:
1. Accordion → Slideshow navigation
2. Accordion → Audio seeking
3. Audio → Accordion auto-open synchronization
4. Component lifecycle management
5. Error handling and fallbacks

**Integration Logic**:
```javascript
// Accordion → Slideshow
accordion.on('sectionclick', (data) => {
  if (data.page_num && slideshow) {
    slideshow.goToPage(data.page_num);
  }
});

// Accordion → Audio
accordion.on('sectionclick', (data) => {
  if (data.start_time && audioPlayer) {
    audioPlayer.seek(data.start_time);
  }
});

// Audio → Accordion
audioPlayer.on('timeupdate', (currentTime) => {
  const activeChunk = findChunkAtTime(currentTime);
  if (activeChunk) {
    accordion.openSection(activeChunk.chunk_id);
  }
});
```

**Validation**:
```javascript
// Integration test: click chunk navigates slideshow
accordion.openSection('chunk-page2');
await nextTick();
assert(slideshow.currentPage === 2);

// Integration test: click chunk seeks audio
accordion.openSection('chunk-0001');
await nextTick();
assert(audioPlayer.getCurrentTime() === chunk.start_time);
```

**Wave 4 Gate**:
- ✅ All synchronization working
- ✅ Integration tests pass
- ✅ No console errors

---

### **Wave 5: Testing & Polish** (Parallel - 2 agents)

**Prerequisites**: Wave 4 complete

**Agents**: test-agent, polish-agent

#### test-agent
**Territory**:
- `src/processing/test_details_integration.py` (new file)
- `src/frontend/test-details-e2e.js` (new file)

**Deliverables**:
1. End-to-end test with real audio file
2. End-to-end test with real PDF
3. Error scenario tests (missing files, invalid data)
4. Performance validation

**Validation Scenarios**:
- Upload audio with word timestamps → verify VTT generation
- Upload multi-page PDF → verify slideshow works
- Click chunk → verify navigation/seeking
- Audio plays → verify accordion opens
- Download markdown → verify frontmatter

#### polish-agent
**Territory**:
- Error handling (all files, add only)
- Loading states
- Accessibility improvements
- Mobile responsiveness

**Deliverables**:
1. Graceful 404 handling (missing VTT/markdown)
2. Loading spinners for async operations
3. ARIA labels for accessibility
4. Mobile-friendly layout adjustments

**Wave 5 Gate**:
- ✅ All E2E tests pass
- ✅ Error scenarios handled
- ✅ Accessibility validated
- ✅ Production ready

---

## Territorial Boundaries

### File Ownership Matrix

| File/Directory | Owner | Wave | Mode |
|----------------|-------|------|------|
| `src/processing/types.py` | data-layer-agent | 1 | EDIT |
| `src/processing/docling_parser.py` | data-layer-agent | 1 | EDIT |
| `src/processing/processor.py` | data-layer-agent | 1 | EDIT |
| `src/processing/vtt_generator.py` | vtt-agent | 1 | NEW |
| `src/processing/vtt_utils.py` | vtt-agent | 1 | NEW |
| `src/processing/documents_api.py` | api-agent | 2 | EXTEND |
| `src/processing/markdown_utils.py` | api-agent | 2 | NEW |
| `src/frontend/details.html` | SHARED | 3 | SECTIONS |
| `src/frontend/slideshow.js` | slideshow-agent | 3 | NEW |
| `src/frontend/audio-player.js` | audio-agent | 3 | NEW |
| `src/frontend/accordion.js` | accordion-agent | 3 | NEW |
| `src/frontend/details-manager.js` | orchestrator | 4 | NEW |
| `data/vtt/` | vtt-agent | 1 | CREATE |

### Shared File Protocol: `details.html`

To prevent conflicts, `details.html` is divided into **non-overlapping sections**:

```html
<!-- SECTION: PAGE STRUCTURE (orchestrator - Wave 4) -->
<!DOCTYPE html>
<html>
<head>
  <title>Document Details</title>
  <!-- CSS imports -->
</head>
<body>
  <div class="details-container">

    <!-- SECTION: LEFT COLUMN (slideshow-agent + audio-agent - Wave 3) -->
    <div id="media-container" class="left-column">
      <!-- slideshow-agent writes slideshow HTML here -->
      <!-- audio-agent writes audio player HTML here -->
    </div>

    <!-- SECTION: RIGHT COLUMN (accordion-agent - Wave 3) -->
    <div id="text-container" class="right-column">
      <!-- accordion-agent writes accordion HTML here -->
    </div>

  </div>

  <!-- SECTION: SCRIPT IMPORTS (orchestrator - Wave 4) -->
  <script type="module" src="details-manager.js"></script>
</body>
</html>
```

---

## Risk Mitigation

### High-Risk Areas

1. **Timestamp Extraction Complexity** (Wave 1, data-layer-agent)
   - Risk: Provenance data structure unknown
   - Mitigation: Create mock data for testing, document actual structure
   - Fallback: Boolean flag only if timestamps unavailable

2. **VTT Format Compliance** (Wave 1, vtt-agent)
   - Risk: Browser rejects malformed VTT
   - Mitigation: Use VTT validation library, test in actual browser
   - Fallback: Plain text transcript if VTT fails

3. **Audio/Accordion Synchronization** (Wave 4, orchestrator)
   - Risk: Performance issues with frequent timeupdate events
   - Mitigation: Throttle timeupdate to 250ms, use binary search for chunk lookup
   - Fallback: Manual accordion navigation only

### Dependency Failures

| If Agent Fails | Impact | Recovery |
|----------------|--------|----------|
| data-layer-agent | Wave 1 blocked | Continue with mock timestamps, re-integrate later |
| vtt-agent | Audio captions unavailable | Skip VTT, audio plays without captions |
| api-agent | Wave 2+ blocked | CRITICAL - must complete for frontend |
| slideshow-agent | No image viewer | Show text accordion only |
| audio-agent | No audio playback | Link to copyparty for download |
| accordion-agent | No text display | CRITICAL - core feature |

---

## Quality Gates

### Wave 1 Gate Criteria
```bash
# Run all unit tests
pytest src/processing/test_types.py -v
pytest src/processing/test_vtt_generator.py -v

# Validate timestamp extraction
python -c "from src.processing.docling_parser import DoclingParser; \
  parser = DoclingParser(); \
  pages, meta, doc = parser.parse_document('test_audio.mp3'); \
  assert meta.get('has_word_timestamps') == True"

# Validate VTT generation
ls data/vtt/*.vtt | wc -l  # Should be > 0
```

### Wave 2 Gate Criteria
```bash
# API health checks
curl http://localhost:8002/documents/{test_doc_id}/markdown
curl http://localhost:8002/documents/{test_doc_id}/vtt
curl http://localhost:8002/documents/{test_doc_id}

# Run API integration tests
pytest src/processing/test_documents_api.py -v
```

### Wave 3 Gate Criteria
```javascript
// Component isolation tests (run in browser console)
// Each component must work independently
const slideshow = new Slideshow('#container', 'test-doc', pages);
slideshow.goToPage(3);
console.assert(slideshow.currentPage === 3);

const audioPlayer = new AudioPlayer('#container', 'test-doc', metadata);
audioPlayer.seek(10);
console.assert(audioPlayer.getCurrentTime() >= 9.9);

const accordion = new Accordion('#container', 'test-doc', data);
accordion.openSection('chunk-0001');
console.assert(accordion.isOpen('chunk-0001'));
```

### Wave 4 Gate Criteria
```javascript
// Integration tests
// Test all synchronization paths
test('accordion click navigates slideshow', async () => {
  accordion.openSection('chunk-page3');
  await waitForNavigation();
  expect(slideshow.currentPage).toBe(3);
});

test('audio timeupdate opens accordion', async () => {
  audioPlayer.seek(15.0);
  await waitForSync();
  expect(accordion.activeSection).toBe('chunk-0002');
});
```

### Wave 5 Gate Criteria
- All E2E tests pass with real documents
- No console errors or warnings
- Lighthouse accessibility score > 90
- Mobile layout tested on 3 screen sizes

---

## Communication Protocol

### Status Broadcasting

Each agent must update status in: `.context-kit/orchestration/details-page/status/{agent-name}.json`

```json
{
  "agent": "data-layer-agent",
  "wave": 1,
  "status": "in_progress",
  "progress": 0.75,
  "completed_tasks": [
    "Extended TextChunk dataclass",
    "Added timestamp extraction logic"
  ],
  "current_task": "Storing timestamps in ChromaDB",
  "blockers": [],
  "last_update": "2025-10-14T18:30:00Z"
}
```

### Contract Compliance Checklist

Before marking wave complete, each agent must verify:

```markdown
- [ ] All integration contracts implemented exactly as specified
- [ ] Unit tests pass (if applicable)
- [ ] Documentation updated (if new APIs/components)
- [ ] No modifications to files outside territorial boundaries
- [ ] Status file updated with final state
- [ ] Hand-off document created for dependent agents
```

---

## Success Metrics

### Technical Success
- ✅ 0 merge conflicts (territorial boundaries prevent overlap)
- ✅ 100% contract compliance (all specs followed exactly)
- ✅ All quality gates pass (progressive validation)
- ✅ <2 integration bugs (interface-first development works)

### Delivery Success
- ✅ Wave 1-2: Backend complete in 1 day
- ✅ Wave 3: Frontend components complete in 1 day
- ✅ Wave 4-5: Integration and testing complete in 0.5 days
- ✅ Total: 2.5 days from start to production

### Quality Success
- ✅ Audio files play with synced captions
- ✅ PDFs display in slideshow with navigation
- ✅ All synchronization paths work correctly
- ✅ Graceful degradation if VTT unavailable
- ✅ Mobile responsive and accessible

---

## Next Steps

1. **Immediate**: Generate all integration contracts (next files)
2. **Wave 0 Complete**: Review contracts with stakeholders
3. **Wave 1 Start**: Launch data-layer-agent and vtt-agent in parallel
4. **Progressive Validation**: Gate reviews after each wave

**Estimated Total Duration**: 2-3 days with 6 agents working in parallel

**Risk Level**: LOW (interface-first development + territorial ownership)

**Confidence**: HIGH (clear contracts, no file conflicts, progressive validation)
