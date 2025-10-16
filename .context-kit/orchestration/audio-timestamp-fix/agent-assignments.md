# Agent Assignments - Audio Timestamp Fix

## Territorial Ownership Model

Each agent has exclusive ownership of specific files/directories to prevent merge conflicts and enable true parallel development.

---

## Agent 1: Backend Specification Agent

### Role
Define all backend integration contracts, data structures, and API specifications.

### Territory (Read/Write)
- `.context-kit/orchestration/audio-timestamp-fix/integration-contracts/IC-001-textchunk-timestamp.md`
- `.context-kit/orchestration/audio-timestamp-fix/integration-contracts/IC-002-vtt-pipeline.md`
- `.context-kit/orchestration/audio-timestamp-fix/integration-contracts/IC-003-metadata-flags.md`
- `.context-kit/orchestration/audio-timestamp-fix/integration-contracts/IC-004-api-response.md`

### Territory (Read-Only)
- `src/processing/types.py` (analyze TextChunk structure)
- `src/processing/vtt_generator.py` (understand VTT requirements)
- `src/processing/processor.py` (understand metadata flow)
- `src/processing/documents_api.py` (understand API structure)

### Deliverables
1. **IC-001: TextChunk Timestamp Contract**
   - Current structure analysis
   - Required fields: `start_time: Optional[float]`, `end_time: Optional[float]`
   - Timestamp extraction function signature
   - Text cleaning requirements (remove `[time: X-Y]` markers)
   - Edge cases: malformed, missing, negative, overlapping
   - Test scenarios (15+ cases)

2. **IC-002: VTT Pipeline Contract**
   - VTT generation trigger conditions
   - Function signature: `extract_timestamps_from_text(text: str) -> tuple[Optional[float], Optional[float], str]`
   - Integration point in chunking pipeline
   - Error handling strategy
   - Logging requirements

3. **IC-003: Metadata Flags Contract**
   - `has_timestamps: bool` - set when any chunk has timestamps
   - `has_word_timestamps: bool` - distinguish segment vs word-level
   - `vtt_available: bool` - set when VTT file generated successfully
   - `vtt_path: Optional[str]` - path to VTT file
   - Update timing and location

4. **IC-004: API Response Contract**
   - Documents endpoint structure
   - Chunk object schema with timestamps
   - Metadata flags in response
   - Backward compatibility for null timestamps
   - Example JSON responses

### Dependencies
- None (specification agent runs first)

### Success Criteria
- All contracts reviewed by Backend Implementation Agent
- Frontend Specification Agent confirms API contract meets frontend needs
- Test scenarios comprehensive enough for TDD

### Estimated Effort
- 2-3 hours to analyze and document all contracts

---

## Agent 2: Frontend Specification Agent

### Role
Define frontend integration contracts, VTT usage patterns, and deprecation strategy.

### Territory (Read/Write)
- `.context-kit/orchestration/audio-timestamp-fix/integration-contracts/IC-005-vtt-track-element.md`
- `.context-kit/orchestration/audio-timestamp-fix/integration-contracts/IC-006-caption-display.md`
- `.context-kit/orchestration/audio-timestamp-fix/integration-contracts/IC-007-accordion-timestamp.md`
- `.context-kit/orchestration/audio-timestamp-fix/integration-contracts/IC-008-deprecation.md`

### Territory (Read-Only)
- `src/frontend/audio-player.js` (analyze current implementation)
- `src/frontend/accordion.js` (analyze current implementation)
- `src/frontend/details.html` (understand structure)

### Deliverables
1. **IC-005: VTT Track Element Contract**
   - HTML5 `<track>` element usage pattern
   - Track source URL structure: `/documents/{doc_id}/vtt`
   - Track attributes: `kind="captions"`, `srclang="en"`, `label="English"`
   - Browser compatibility requirements

2. **IC-006: Caption Display Contract**
   - `cuechange` event handler interface
   - `track.activeCues[0].text` access pattern
   - Caption update logic (only when changed)
   - Empty caption handling
   - Error handling for missing VTT

3. **IC-007: Accordion Timestamp Contract**
   - Chunk-based display (no markdown parsing)
   - Use `chunk.start_time` / `chunk.end_time` for titles
   - Use `chunk.text_content` (cleaned) for display
   - Click-to-seek using chunk timestamps
   - Section matching logic

4. **IC-008: Deprecation Contract**
   - Functions to remove:
     - `audio-player.js`: `fetchMarkdown()`, `parseMarkdownSegments()`
     - `accordion.js`: `parseMarkdownSegments()`
   - Timeline: Remove after Wave 3 validation
   - Backward compatibility for documents without VTT
   - Migration guide for any external dependencies

### Dependencies
- IC-004 (API Response Contract) - must align with backend

### Success Criteria
- Contracts reviewed by Frontend Implementation Agent
- Backward compatibility strategy covers edge cases
- Deprecation plan minimizes risk

### Estimated Effort
- 2-3 hours to document patterns and deprecation strategy

---

## Agent 3: Backend Implementation Agent

### Role
Implement timestamp extraction and integrate into processing pipeline.

### Territory (Read/Write)
- `src/processing/text_processor.py` (add timestamp extraction function)
- `src/processing/test_timestamp_extraction.py` (NEW FILE - unit tests)
- `src/processing/processor.py` (minimal metadata flag updates only)

### Territory (Read-Only)
- `src/processing/types.py` (TextChunk structure)
- `src/processing/vtt_generator.py` (understand VTT requirements)
- Integration contracts IC-001, IC-002, IC-003

### Deliverables
1. **Timestamp Extraction Function**
   ```python
   def extract_timestamps_from_text(text: str) -> tuple[Optional[float], Optional[float], str]:
       """
       Extract [time: X-Y] markers from text.

       Args:
           text: Text containing potential [time: X-Y] markers

       Returns:
           (start_time, end_time, cleaned_text)
           - start_time: float or None
           - end_time: float or None
           - cleaned_text: text with markers removed

       Examples:
           >>> extract_timestamps_from_text("[time: 1.5-3.2] Hello")
           (1.5, 3.2, "Hello")
           >>> extract_timestamps_from_text("No timestamps here")
           (None, None, "No timestamps here")
       """
   ```

2. **Integration into Chunking Pipeline**
   - Locate where TextChunk objects are created
   - Call `extract_timestamps_from_text()` on chunk text
   - Populate `chunk.start_time` and `chunk.end_time`
   - Store cleaned text in `chunk.text`

3. **Metadata Flag Updates**
   - After all chunks created, check if any have timestamps
   - Set `has_timestamps = True` if any chunk has both start_time and end_time
   - Ensure VTT generation triggers (processor.py line 311 condition)

4. **Comprehensive Unit Tests** (15+ test cases)
   - Valid timestamps: `[time: 1.5-3.2]`
   - Multiple timestamps in one text
   - Malformed: `[time: abc-def]`, `[time: 1.5]`
   - Missing: text without timestamps
   - Edge cases: negative, zero, overlapping
   - Text cleaning: verify markers removed
   - Unicode and special characters

### Dependencies
- IC-001 (TextChunk Timestamp Contract)
- IC-002 (VTT Pipeline Contract)
- IC-003 (Metadata Flags Contract)

### Integration Points
- Modified TextChunk objects consumed by `vtt_generator.py`
- Metadata flags consumed by API and frontend
- Must NOT break existing document processing

### Success Criteria
- All unit tests pass (pytest)
- VTT generator receives chunks with populated timestamps
- Existing tests still pass (no regression)
- Metadata flags accurate
- Code follows project style (PEP 8, type hints, docstrings)

### Estimated Effort
- 3-4 hours for implementation and testing

---

## Agent 4: Frontend Implementation Agent

### Role
Update frontend to use native VTT and remove markdown parsing.

### Territory (Read/Write)
- `src/frontend/audio-player.js` (update caption handling)
- `src/frontend/accordion.js` (update timestamp display)
- `src/frontend/test_vtt_integration.html` (NEW FILE - test page)

### Territory (Read-Only)
- Integration contracts IC-004, IC-005, IC-006, IC-007, IC-008
- `src/frontend/details.html` (understand structure)
- `src/frontend/details.css` (caption styling)

### Deliverables
1. **Updated audio-player.js**
   - Remove: `fetchMarkdown()`, `parseMarkdownSegments()`, `markdownContent`, `segments`
   - Update: `handleTimeUpdate()` to use `track.activeCues`
   - Add: Error handling for missing VTT
   - Add: Backward compatibility check (null timestamps)

   ```javascript
   handleTimeUpdate() {
       // Use native track cues for captions
       const track = this.trackElement.track;
       if (track && track.activeCues && track.activeCues.length > 0) {
           const activeCue = track.activeCues[0];
           if (this.captionElement.textContent !== activeCue.text) {
               this.captionElement.textContent = activeCue.text;
           }
       } else {
           if (this.captionElement.textContent !== '') {
               this.captionElement.textContent = '';
           }
       }

       // Accordion sync logic remains unchanged
       // ...
   }
   ```

2. **Updated accordion.js**
   - Remove: `parseMarkdownSegments()` method
   - Update: `addChunkSections()` to use chunk timestamps directly
   - Update: Section titles to use `chunk.start_time` / `chunk.end_time`
   - Update: Content to use cleaned `chunk.text_content`
   - Verify: Click-to-seek still works

3. **Test Page** (test_vtt_integration.html)
   - Simple audio player with VTT track
   - Sample VTT file for testing
   - Caption display area
   - Validates native track element works

### Dependencies
- IC-004, IC-005, IC-006, IC-007, IC-008 (all frontend contracts)
- Backend Implementation Agent complete (need working VTT files)

### Integration Points
- Depends on API response with populated chunk timestamps
- Depends on VTT files at `/documents/{doc_id}/vtt`
- Must remain backward compatible with documents lacking VTT

### Success Criteria
- Captions display using native track element
- Accordion shows cleaned text with timestamps
- No markdown parsing code remains (~100 lines removed)
- Backward compatible (graceful degradation)
- Test page demonstrates VTT working

### Estimated Effort
- 2-3 hours for implementation and testing

---

## Agent 5: Integration Testing Agent

### Role
End-to-end validation, reprocessing script, production migration.

### Territory (Read/Write)
- `src/test_audio_timestamp_integration.py` (NEW FILE - integration test)
- `scripts/reprocess_audio_files.py` (NEW FILE - reprocessing script)
- `.context-kit/orchestration/audio-timestamp-fix/validation-results.md` (test report)
- `.context-kit/orchestration/audio-timestamp-fix/migration-checklist.md`

### Territory (Read-Only)
- All source files (for integration testing)
- All integration contracts

### Deliverables
1. **Integration Test** (`test_audio_timestamp_integration.py`)
   - Upload audio file with timestamp markers
   - Verify TextChunk fields populated
   - Verify VTT file generated at `data/vtt/{doc_id}.vtt`
   - Verify API response includes timestamps
   - Verify VTT endpoint returns valid content
   - Manual browser test instructions

2. **Reprocessing Script** (`scripts/reprocess_audio_files.py`)
   - Find all audio documents in system
   - Reprocess each to extract timestamps
   - Generate VTT files
   - Update metadata
   - Progress reporting

3. **Validation Report** (validation-results.md)
   - Test results (pass/fail)
   - Performance metrics (caption sync latency)
   - Regression testing results
   - Issues found and resolutions

4. **Migration Checklist** (migration-checklist.md)
   - Pre-migration steps
   - Reprocessing steps
   - Validation steps
   - Rollback procedure

### Dependencies
- All Wave 2 agents complete
- Backend and frontend implementations working independently

### Integration Points
- Tests entire pipeline: upload → processing → VTT generation → API → frontend display
- Validates all 8 integration contracts

### Success Criteria
- Integration test passes 100%
- Existing audio files reprocessed successfully
- VTT captions display in browser
- Performance meets requirements (<50ms)
- Zero regression in non-audio documents

### Estimated Effort
- 3-4 hours for testing, scripting, and documentation

---

## Coordination Protocol

### Status Broadcasting
Each agent posts status in `.context-kit/orchestration/audio-timestamp-fix/status.md`:

```markdown
## Agent Status

### Backend Specification Agent
- Status: ✅ Complete
- Wave: 1
- Deliverables: IC-001, IC-002, IC-003, IC-004
- Issues: None

### Frontend Specification Agent
- Status: 🔄 In Progress (2/4 contracts complete)
- Wave: 1
- Blocked: None
- ETA: 1 hour

### Backend Implementation Agent
- Status: ⏸️ Waiting (Gate 1)
- Wave: 2
- Dependencies: IC-001, IC-002, IC-003

### Frontend Implementation Agent
- Status: ⏸️ Waiting (Gate 1)
- Wave: 2
- Dependencies: IC-004, IC-005, IC-006, IC-007, IC-008

### Integration Testing Agent
- Status: ⏸️ Waiting (Gate 2)
- Wave: 3
- Dependencies: All Wave 2 agents
```

### Contract Change Protocol
If integration contract needs modification:
1. Post proposal in contract file with `[PROPOSAL]` tag
2. Notify dependent agents in status.md
3. Await approval from all affected agents
4. Update contract with `[APPROVED - v2]` tag
5. Dependent agents acknowledge and update implementation

### Failure Recovery
If agent encounters blocking issue:
1. Document in `.context-kit/orchestration/audio-timestamp-fix/issues.md`
2. Update status to ❌ Blocked
3. Propose resolution or request assistance
4. Other agents may need to pause if dependency broken

---

## File Ownership Summary

| File | Owner | Access |
|------|-------|--------|
| IC-001 through IC-004 | Backend Spec Agent | Write |
| IC-005 through IC-008 | Frontend Spec Agent | Write |
| `text_processor.py` | Backend Impl Agent | Write |
| `test_timestamp_extraction.py` | Backend Impl Agent | Write |
| `processor.py` (metadata only) | Backend Impl Agent | Limited Write |
| `audio-player.js` | Frontend Impl Agent | Write |
| `accordion.js` | Frontend Impl Agent | Write |
| `test_vtt_integration.html` | Frontend Impl Agent | Write |
| `test_audio_timestamp_integration.py` | Integration Agent | Write |
| `reprocess_audio_files.py` | Integration Agent | Write |
| All other files | All Agents | Read Only |

---

**Zero-Conflict Guarantee**: With this territorial ownership model, no two agents will ever modify the same file simultaneously, eliminating merge conflicts entirely.
