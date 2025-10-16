# Audio Timestamp Architecture Fix - Orchestration Plan

## Executive Summary

**Goal**: Replace fragile markdown parsing with proper VTT file generation by extracting timestamps from markdown text into TextChunk fields.

**Problem**: Timestamps exist as `[time: X-Y]` text markers but aren't extracted to chunk.start_time/end_time fields, forcing frontend to parse markdown with regex instead of using standard VTT files.

**Solution**: Fix processing pipeline to extract timestamps during text chunking, generate VTT files automatically, and update frontend to use native HTML5 `<track>` element.

**Agents**: 4 specialized agents working in 3 waves
**Timeline**: Complete in 3 synchronization cycles
**Risk Level**: Low (preserve working system until proven)

---

## Wave 1: Foundation & Specification (Parallel)

**Duration**: Complete specification and analysis phase
**Gate Criteria**: All integration contracts validated and approved

### Agent 1: Backend Specification Agent
**Territory**: `.context-kit/orchestration/audio-timestamp-fix/integration-contracts/`
**Deliverables**:
- IC-001: TextChunk timestamp contract (data structure specification)
- IC-002: VTT generation pipeline contract (function signatures, flow)
- IC-003: Metadata flags contract (has_timestamps, vtt_available)
- IC-004: API response contract (documents endpoint with timestamps)

**Tasks**:
1. Document current TextChunk structure and identify why timestamps aren't extracted
2. Design timestamp extraction function signature and behavior
3. Specify VTT generation trigger conditions
4. Define metadata update requirements
5. Create comprehensive test scenarios for each contract

**Integration Points**:
- Contracts consumed by Wave 2 backend agents
- API contract consumed by Wave 2 frontend agents

**Success Criteria**:
- All contracts include: interface, data schemas, error handling, test cases
- Contracts reviewed and approved by dependent agents

---

### Agent 2: Frontend Specification Agent
**Territory**: `.context-kit/orchestration/audio-timestamp-fix/integration-contracts/`
**Deliverables**:
- IC-005: VTT track element contract (HTML5 usage pattern)
- IC-006: Caption display contract (cuechange event handling)
- IC-007: Accordion timestamp contract (chunk-based display)
- IC-008: Deprecation contract (what code to remove, when)

**Tasks**:
1. Document native `<track>` element usage pattern
2. Specify cuechange event handler interface
3. Define accordion chunk display requirements (without markdown parsing)
4. Create deprecation plan for parseMarkdownSegments
5. Design backward compatibility for documents without timestamps

**Integration Points**:
- Depends on IC-004 (API response contract)
- Contracts consumed by Wave 2 frontend agents

**Success Criteria**:
- Frontend contracts compatible with backend API contract
- Clear migration path from current to new implementation
- Backward compatibility strategy documented

---

## Wave 2: Implementation (Parallel)

**Duration**: Core implementation of backend and frontend fixes
**Gate Criteria**: All unit tests pass, integration contracts satisfied

### Agent 3: Backend Implementation Agent
**Territory**:
- `src/processing/text_processor.py` (timestamp extraction)
- `src/processing/test_timestamp_extraction.py` (new file)
- `src/processing/processor.py` (minimal changes to metadata flags)

**Deliverables**:
1. Timestamp extraction function in text_processor.py:
   ```python
   def extract_timestamps_from_text(text: str) -> tuple[Optional[float], Optional[float], str]:
       """Extract [time: X-Y] markers and return (start, end, cleaned_text)."""
   ```
2. Integration into text chunking pipeline
3. Metadata flag updates (has_timestamps, has_word_timestamps)
4. Comprehensive unit tests (15+ test cases)

**Dependencies**:
- IC-001: TextChunk timestamp contract
- IC-002: VTT generation pipeline contract
- IC-003: Metadata flags contract

**Tasks**:
1. Implement `extract_timestamps_from_text()` with regex parsing
2. Integrate into existing chunking logic (identify exact integration point)
3. Update chunk creation to populate start_time/end_time
4. Clean timestamp markers from chunk.text field
5. Update metadata flags based on chunk timestamp presence
6. Write unit tests covering all edge cases from IC-001
7. Verify VTT generation triggers correctly

**Integration Points**:
- Modifies TextChunk objects consumed by vtt_generator.py
- Updates metadata consumed by API and frontend

**Success Criteria**:
- All unit tests pass (IC-001 test scenarios)
- VTT generator receives chunks with populated timestamps
- Metadata flags accurately reflect timestamp presence
- Text content no longer contains `[time: X-Y]` markers

---

### Agent 4: Frontend Implementation Agent
**Territory**:
- `src/frontend/audio-player.js` (VTT track integration)
- `src/frontend/accordion.js` (chunk-based display)
- `src/frontend/test_vtt_integration.html` (new file for testing)

**Deliverables**:
1. Updated audio-player.js using native `<track>` element
2. Updated accordion.js using chunk timestamps directly
3. Removed markdown parsing logic from both components
4. Test page for validating VTT caption display

**Dependencies**:
- IC-004: API response contract (chunks with start_time/end_time)
- IC-005: VTT track element contract
- IC-006: Caption display contract
- IC-007: Accordion timestamp contract
- Wave 2 Backend Agent completion (need working VTT files)

**Tasks**:
1. Update audio-player.js handleTimeUpdate to use track.activeCues
2. Remove fetchMarkdown, parseMarkdownSegments from audio-player.js
3. Update accordion.js to use chunk.start_time/end_time directly
4. Remove parseMarkdownSegments from accordion.js
5. Add backward compatibility checks (null timestamp handling)
6. Create test page with sample VTT file
7. Update comments to reflect VTT-based architecture

**Integration Points**:
- Consumes API response with populated chunk timestamps
- Uses VTT files generated by backend pipeline

**Success Criteria**:
- Captions display correctly using native track element
- Accordion segments show cleaned text with timestamps
- No markdown parsing code remains
- Backward compatible with documents lacking timestamps
- Code reduced by ~100 lines (removed regex parsing)

---

## Wave 3: Validation & Migration (Sequential)

**Duration**: End-to-end testing and production migration
**Gate Criteria**: All integration tests pass, reprocessing complete

### Agent 5: Integration Testing Agent
**Territory**:
- `src/test_audio_timestamp_integration.py` (new file)
- `.context-kit/orchestration/audio-timestamp-fix/validation-results.md`

**Deliverables**:
1. End-to-end integration test
2. Reprocessing script for existing audio files
3. Validation report with test results
4. Production migration checklist

**Dependencies**:
- All Wave 2 agents complete
- Backend and frontend implementations tested independently

**Tasks**:
1. Create integration test:
   - Upload audio file with markdown timestamps
   - Verify TextChunk fields populated
   - Verify VTT file generated
   - Verify API response includes timestamps
   - Verify frontend displays captions correctly
2. Write reprocessing script for existing audio files
3. Test with "Myth 1.mp3" (existing file)
4. Verify backward compatibility (documents without timestamps)
5. Performance testing (caption sync latency)
6. Document any issues found and resolution

**Integration Points**:
- Tests entire pipeline from upload to display
- Validates all integration contracts (IC-001 through IC-008)

**Success Criteria**:
- Integration test passes 100%
- Existing audio file reprocessed successfully
- VTT captions display correctly in browser
- Accordion shows cleaned text
- Performance meets requirements (<50ms caption sync)
- Zero regression in non-audio documents

---

## Synchronization Gates

### Gate 1: Specification Complete (After Wave 1)
**Criteria**:
- [ ] All 8 integration contracts written and reviewed
- [ ] Test scenarios defined for each contract
- [ ] API response contract matches frontend expectations
- [ ] Deprecation plan approved
- [ ] All agents acknowledge readiness for Wave 2

**Validation**: Review meeting with all agents present

---

### Gate 2: Implementation Complete (After Wave 2)
**Criteria**:
- [ ] Backend: All unit tests pass (15+ tests)
- [ ] Backend: VTT generation triggers correctly
- [ ] Backend: Metadata flags accurate
- [ ] Frontend: Native track element working
- [ ] Frontend: Markdown parsing removed
- [ ] Frontend: Backward compatibility implemented
- [ ] Code review completed by peer agents

**Validation**:
- Run backend unit tests: `pytest src/processing/test_timestamp_extraction.py -v`
- Manual frontend testing with test page

---

### Gate 3: Integration Validated (After Wave 3)
**Criteria**:
- [ ] End-to-end test passes
- [ ] Existing audio file reprocessed successfully
- [ ] VTT captions display in browser
- [ ] Accordion displays cleaned text
- [ ] Performance requirements met
- [ ] Zero regression in other document types
- [ ] Documentation updated

**Validation**:
- Run integration test: `pytest src/test_audio_timestamp_integration.py -v`
- Manual browser testing
- Performance profiling

---

## Risk Mitigation

### Risk 1: Breaking Existing Functionality
**Mitigation**:
- Preserve working system until Wave 3 validation complete
- Don't remove markdown parsing until VTT approach proven
- Implement backward compatibility for null timestamps

### Risk 2: Timestamp Extraction Failures
**Mitigation**:
- Comprehensive unit tests in Wave 2
- Handle malformed timestamps gracefully
- Log warnings for unparseable timestamps

### Risk 3: VTT Generation Not Triggering
**Mitigation**:
- Verify metadata flags in Wave 2 (has_timestamps, has_word_timestamps)
- Add logging to VTT generation pipeline
- Integration test validates entire flow

### Risk 4: Frontend-Backend Contract Mismatch
**Mitigation**:
- Wave 1 specification phase ensures contract alignment
- API response contract reviewed by both backend and frontend agents
- Integration test validates contract compliance

---

## Success Metrics

### Quantitative
- **Code Reduction**: Remove ~100 lines of regex parsing from frontend
- **Test Coverage**: Add 15+ backend unit tests, 1 integration test
- **Performance**: Caption sync latency <50ms (native track element)
- **Correctness**: 100% of audio files generate valid VTT

### Qualitative
- **Maintainability**: Use web standards instead of custom parsing
- **Reliability**: Eliminate fragile regex-based approach
- **Separation of Concerns**: Backend owns data structure, frontend uses standards
- **Developer Experience**: Clear, testable architecture

---

## Rollback Plan

If integration testing fails in Wave 3:
1. Frontend agents revert changes (markdown parsing remains)
2. Backend changes remain (improves data structure even if frontend doesn't use yet)
3. Analyze root cause before retry
4. Update integration contracts based on findings

---

## Communication Protocol

### Status Updates
Each agent reports:
- **Start**: "Starting [wave] - [agent name]"
- **Progress**: "Completed [task X/Y] - [agent name]"
- **Blocked**: "Blocked on [dependency] - [agent name]"
- **Complete**: "Wave [N] complete - [agent name] - [validation status]"

### Integration Contract Changes
- Must notify all dependent agents
- Requires re-validation of affected contracts
- May delay wave transition if breaking change

### Failure Protocol
- Document failure in `.context-kit/orchestration/audio-timestamp-fix/issues.md`
- Notify dependent agents immediately
- Propose resolution or rollback
- Update integration contracts if needed

---

## Next Steps

1. **Review this plan** with all agents
2. **Assign agent roles** (Backend Spec, Frontend Spec, Backend Impl, Frontend Impl, Integration)
3. **Begin Wave 1** (specification phase)
4. **First synchronization** after Wave 1 complete
5. **Execute Wave 2** (implementation phase)
6. **Second synchronization** after Wave 2 complete
7. **Execute Wave 3** (validation and migration)
8. **Final validation** and production deployment

---

**Orchestration Status**: Ready to begin Wave 1
**Plan Version**: 1.0
**Last Updated**: 2025-10-16
