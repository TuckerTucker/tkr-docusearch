# Validation Strategy - Audio Timestamp Fix

## Overview

This document defines the comprehensive validation strategy across all waves of the audio timestamp architecture fix. Testing occurs at multiple levels: unit, integration, and end-to-end.

---

## Wave 1 Validation: Specification Quality

### Contract Validation Criteria

Each integration contract must meet these standards:

#### Completeness Checklist
- [ ] Clear interface definition (function signatures, data schemas)
- [ ] Input/output specifications with types
- [ ] Error handling strategy defined
- [ ] Edge cases documented (at least 5 per contract)
- [ ] Example usage provided (code snippets)
- [ ] Test scenarios enumerated (15+ for IC-001)
- [ ] Dependencies clearly stated
- [ ] Success criteria measurable

#### Review Process
1. **Self-Review**: Author validates against completeness checklist
2. **Peer Review**: Dependent agents review from consumer perspective
3. **Cross-Check**: Ensure contracts align (e.g., IC-004 API matches IC-005 frontend)
4. **Approval**: All reviewers approve before Wave 2 begins

#### Contract Quality Metrics
- **Clarity Score**: Reviewers rate 1-5 on clarity
- **Coverage Score**: % of edge cases covered
- **Alignment Score**: How well contracts interconnect

**Gate 1 Passes Only If**: All contracts rated ≥4/5 on clarity, ≥90% edge case coverage, 100% alignment between API/frontend contracts

---

## Wave 2 Validation: Implementation Testing

### Backend Unit Tests

**Location**: `src/processing/test_timestamp_extraction.py`

**Test Scenarios** (IC-001 requirements):

#### Category 1: Valid Timestamps
```python
def test_extract_simple_timestamp():
    """[time: 1.5-3.2] Hello"""
    assert start == 1.5, end == 3.2, text == "Hello"

def test_extract_timestamp_with_decimal():
    """[time: 0.6199999999-3.96] Text"""
    assert start == 0.62, end == 3.96

def test_extract_timestamp_at_start():
    """[time: 0.0-5.5] Start"""
    assert start == 0.0, end == 5.5

def test_extract_large_timestamp():
    """[time: 3600.5-3725.8] Hour mark"""
    assert start == 3600.5, end == 3725.8
```

#### Category 2: Text Cleaning
```python
def test_text_cleaning_removes_marker():
    """[time: 1-2] Hello"""
    assert cleaned == "Hello"  # No marker

def test_text_cleaning_preserves_content():
    """[time: 1-2]  Multiple   spaces"""
    assert cleaned == "Multiple   spaces"  # Preserved

def test_text_cleaning_multiple_lines():
    """[time: 1-2] Line 1\nLine 2"""
    assert cleaned == "Line 1\nLine 2"
```

#### Category 3: Edge Cases
```python
def test_no_timestamp():
    """No markers here"""
    assert start is None, end is None, text == "No markers here"

def test_malformed_timestamp():
    """[time: abc-def] Bad"""
    assert start is None, end is None  # Graceful failure

def test_incomplete_timestamp():
    """[time: 1.5] Missing end"""
    assert start is None, end is None

def test_negative_timestamp():
    """[time: -1.5-3.2] Negative"""
    assert start is None, end is None  # Invalid

def test_reversed_timestamp():
    """[time: 5.0-2.0] Backward"""
    assert start is None, end is None  # Invalid (end < start)

def test_zero_duration():
    """[time: 2.0-2.0] Same"""
    assert start is None, end is None  # Invalid (duration = 0)
```

#### Category 4: Multiple Timestamps
```python
def test_multiple_timestamps_uses_first():
    """[time: 1-2] First [time: 3-4] Second"""
    assert start == 1.0, end == 2.0  # Use first only

def test_nested_text_with_timestamp():
    """[time: 1-2] Text with [bracketed] content"""
    assert cleaned == "Text with [bracketed] content"
```

#### Category 5: Unicode and Special Characters
```python
def test_unicode_text():
    """[time: 1-2] Café résumé 你好"""
    assert cleaned == "Café résumé 你好"

def test_special_characters():
    """[time: 1-2] $100 & <tag>"""
    assert cleaned == "$100 & <tag>"
```

**Minimum Requirements**:
- **Coverage**: ≥95% code coverage on `extract_timestamps_from_text()`
- **Test Count**: ≥15 tests
- **All Tests Pass**: 100% pass rate
- **Performance**: <1ms per extraction

**Run Command**:
```bash
pytest src/processing/test_timestamp_extraction.py -v --cov=src.processing.text_processor --cov-report=term-missing
```

---

### Frontend Manual Testing

**Test Page**: `src/frontend/test_vtt_integration.html`

**Sample VTT File** (test-sample.vtt):
```
WEBVTT

1
00:00:01.000 --> 00:00:03.000
First caption text

2
00:00:03.500 --> 00:00:06.000
Second caption text

3
00:00:06.500 --> 00:00:10.000
Third caption with longer text
spanning multiple lines
```

**Manual Test Cases**:

#### Test Case 1: Caption Display
1. Open test page in browser
2. Play audio
3. **Verify**: Captions appear at correct timestamps
4. **Verify**: Caption text matches VTT file
5. **Verify**: Old caption clears before new one appears

#### Test Case 2: Caption Styling
1. Play audio with captions enabled
2. **Verify**: Caption overlay positioned correctly on album art
3. **Verify**: Background opacity correct (55% white)
4. **Verify**: Text readable against album art

#### Test Case 3: Error Handling
1. Load audio without VTT file
2. **Verify**: Audio plays normally
3. **Verify**: No JavaScript errors in console
4. **Verify**: Caption area remains empty (graceful degradation)

#### Test Case 4: Seek Behavior
1. Play audio to timestamp 5s
2. Seek to timestamp 2s
3. **Verify**: Caption updates immediately to correct text
4. **Verify**: No lag or flash of wrong caption

#### Test Case 5: Accordion Integration
1. Open document with audio
2. Verify accordion segments show:
   - Cleaned text (no `[time: X-Y]` markers)
   - Timestamps in title (formatted as MM:SS)
   - Click-to-seek works

**Success Criteria**:
- All 5 test cases pass
- No console errors
- Caption sync latency <50ms (measured via browser DevTools)

---

### Code Review Checklist

#### Backend Code Review (by Frontend Agent)
```markdown
## Backend Code Review - Timestamp Extraction

### Interface Compliance
- [ ] Function signature matches IC-001
- [ ] Return type correct: `tuple[Optional[float], Optional[float], str]`
- [ ] Docstring complete with examples

### Error Handling
- [ ] Malformed timestamps handled gracefully
- [ ] Invalid values return (None, None, original_text)
- [ ] Logging adequate for debugging

### Code Quality
- [ ] PEP 8 compliant
- [ ] Type hints on all functions
- [ ] No obvious bugs
- [ ] Edge cases covered

### Testing
- [ ] All 15+ tests present
- [ ] Tests cover edge cases from IC-001
- [ ] Coverage ≥95%
- [ ] All tests pass

### Performance
- [ ] No obvious performance issues
- [ ] Regex efficient (compiled)
- [ ] No unnecessary string copies

**Approval**: ✅ Approved / ❌ Changes Requested
**Reviewer**: [Frontend Agent Name]
**Date**: [Timestamp]
```

#### Frontend Code Review (by Backend Agent)
```markdown
## Frontend Code Review - VTT Integration

### Interface Compliance
- [ ] Uses track.activeCues per IC-006
- [ ] API response consumed correctly per IC-004
- [ ] Backward compatibility for null timestamps

### Implementation Quality
- [ ] Markdown parsing code removed
- [ ] Native track element used correctly
- [ ] Error handling for missing VTT
- [ ] No hardcoded values

### Code Reduction
- [ ] ~100 lines removed (parseMarkdownSegments)
- [ ] fetchMarkdown removed
- [ ] Code cleaner and simpler

### User Experience
- [ ] Captions display correctly
- [ ] No visual glitches
- [ ] Graceful degradation
- [ ] Click-to-seek works

**Approval**: ✅ Approved / ❌ Changes Requested
**Reviewer**: [Backend Agent Name]
**Date**: [Timestamp]
```

---

## Wave 3 Validation: Integration Testing

### Integration Test Suite

**Location**: `src/test_audio_timestamp_integration.py`

**Test Flow**:

#### Test 1: Full Pipeline Validation
```python
def test_audio_processing_pipeline():
    """Test complete flow: upload → process → VTT generation → API"""

    # 1. Upload test audio file
    test_file = "test-audio-with-timestamps.mp3"
    doc_id = upload_file(test_file)

    # 2. Wait for processing
    wait_for_processing(doc_id, timeout=30)

    # 3. Verify TextChunk timestamps
    chunks = get_chunks(doc_id)
    assert all(c.start_time is not None for c in chunks)
    assert all(c.end_time is not None for c in chunks)
    assert all(c.end_time > c.start_time for c in chunks)

    # 4. Verify text cleaned
    for chunk in chunks:
        assert "[time:" not in chunk.text_content

    # 5. Verify VTT generated
    vtt_path = Path(f"data/vtt/{doc_id}.vtt")
    assert vtt_path.exists()

    # 6. Verify VTT valid
    with open(vtt_path) as f:
        vtt_content = f.read()
    assert vtt_content.startswith("WEBVTT")
    assert "-->" in vtt_content

    # 7. Verify API response
    response = requests.get(f"http://localhost:8002/documents/{doc_id}")
    data = response.json()
    assert data["metadata"]["has_timestamps"] == True
    assert data["metadata"]["vtt_available"] == True
    assert "vtt_path" in data["metadata"]

    # 8. Verify VTT endpoint
    vtt_response = requests.get(f"http://localhost:8002/documents/{doc_id}/vtt")
    assert vtt_response.status_code == 200
    assert "WEBVTT" in vtt_response.text
```

#### Test 2: Backward Compatibility
```python
def test_backward_compatibility_no_timestamps():
    """Verify documents without timestamps still work"""

    # Upload document without timestamp markers
    test_file = "test-audio-no-timestamps.mp3"
    doc_id = upload_file(test_file)
    wait_for_processing(doc_id)

    # Verify graceful handling
    chunks = get_chunks(doc_id)
    assert all(c.start_time is None for c in chunks)
    assert all(c.end_time is None for c in chunks)

    # Verify metadata accurate
    response = requests.get(f"http://localhost:8002/documents/{doc_id}")
    data = response.json()
    assert data["metadata"]["has_timestamps"] == False
    assert data["metadata"]["vtt_available"] == False

    # Verify VTT endpoint returns 404
    vtt_response = requests.get(f"http://localhost:8002/documents/{doc_id}/vtt")
    assert vtt_response.status_code == 404
```

#### Test 3: Reprocessing Existing Files
```python
def test_reprocess_existing_audio():
    """Test reprocessing script on existing audio file"""

    # Get existing audio doc_id
    doc_id = "5e57bdeb-f37b-43e3-80ca-63bacaebeaab"  # "Myth 1.mp3"

    # Run reprocessing
    from scripts.reprocess_audio_files import reprocess_document
    result = reprocess_document(doc_id)

    assert result["success"] == True
    assert result["vtt_generated"] == True

    # Verify updated
    response = requests.get(f"http://localhost:8002/documents/{doc_id}")
    data = response.json()
    assert data["metadata"]["has_timestamps"] == True
    assert data["metadata"]["vtt_available"] == True
```

#### Test 4: Performance Benchmarking
```python
def test_performance_caption_sync():
    """Measure caption sync latency"""

    # This is a manual test with browser automation
    # Use Selenium or Playwright to:
    # 1. Load details page for audio document
    # 2. Start audio playback
    # 3. Monitor caption updates
    # 4. Measure timestamp accuracy
    # 5. Calculate average latency

    # Success: <50ms latency between audio time and caption update
    pass  # Implementation TBD
```

#### Test 5: Regression Testing
```python
def test_regression_non_audio_documents():
    """Ensure non-audio documents unaffected"""

    # Upload PDF document
    test_file = "test-document.pdf"
    doc_id = upload_file(test_file)
    wait_for_processing(doc_id)

    # Verify normal processing
    response = requests.get(f"http://localhost:8002/documents/{doc_id}")
    data = response.json()
    assert data["metadata"]["format_type"] == "pdf"
    assert data["metadata"]["has_timestamps"] == False
    assert data["metadata"]["vtt_available"] == False

    # Verify pages rendered
    assert len(data["pages"]) > 0
```

**Run Command**:
```bash
pytest src/test_audio_timestamp_integration.py -v --tb=short
```

**Success Criteria**:
- All 5 integration tests pass
- No warnings or errors
- Test execution <60 seconds

---

### Manual Browser Testing

**Test Document**: "Myth 1.mp3" (existing audio file, reprocessed)

**Test Steps**:

1. **Load Document**
   ```
   Navigate to: http://localhost:8002/documents/5e57bdeb-f37b-43e3-80ca-63bacaebeaab
   ```

2. **Verify Audio Player**
   - [ ] Audio player visible
   - [ ] Album art displays
   - [ ] Audio loads and plays
   - [ ] No console errors

3. **Verify Captions**
   - [ ] Caption appears on album art
   - [ ] Caption text updates as audio plays
   - [ ] Caption synced within 50ms (subjective)
   - [ ] Caption styling correct (white background, dark text)
   - [ ] Caption clears when no active cue

4. **Verify Accordion**
   - [ ] Segments display with timestamps in titles
   - [ ] Text content clean (no `[time: X-Y]` markers)
   - [ ] Full text visible (not truncated)
   - [ ] Only one section open at a time
   - [ ] Click segment title to seek audio

5. **Test Seek Behavior**
   - [ ] Seek forward → caption updates immediately
   - [ ] Seek backward → caption updates immediately
   - [ ] Accordion section highlights active segment

6. **Test Browser Compatibility**
   - [ ] Chrome/Edge (Chromium)
   - [ ] Firefox
   - [ ] Safari (if on macOS)

**Documentation**: Record test results with screenshots in validation-results.md

---

## Performance Benchmarks

### Backend Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Timestamp extraction | <1ms per chunk | `pytest` with timing |
| VTT generation | <50ms for 100 cues | `vtt_generator.py` timing log |
| Document processing overhead | <10% increase | Compare with/without extraction |

### Frontend Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Caption sync latency | <50ms | Browser DevTools timeline |
| Accordion render time | <100ms | React DevTools profiler |
| Code size reduction | ~100 lines removed | Git diff stats |

---

## Regression Testing

### Automated Regression Suite

Run existing test suite to ensure no breakage:

```bash
# All processing tests
pytest src/processing/test_*.py -v

# All frontend tests (if any)
pytest src/frontend/test_*.py -v

# All integration tests
pytest src/test_*.py -v
```

**Success Criteria**: 100% of existing tests still pass

### Manual Regression Checklist

Test with various document types:

- [ ] PDF document (multipage)
- [ ] DOCX document
- [ ] PPTX presentation
- [ ] Plain text file
- [ ] Image file (JPG)
- [ ] Audio file WITHOUT timestamps
- [ ] Audio file WITH timestamps

**Verify**: All document types process and display correctly

---

## Validation Report Template

**Location**: `.context-kit/orchestration/audio-timestamp-fix/validation-results.md`

```markdown
# Validation Results - Audio Timestamp Fix

## Test Execution Summary
- **Date**: [Timestamp]
- **Executed By**: Integration Testing Agent
- **Environment**: [Development/Staging/Production]
- **Status**: [✅ PASSED | ❌ FAILED]

## Unit Test Results
- **Backend Tests**: [X/Y passed]
- **Coverage**: [XX%]
- **Duration**: [Xs]
- **Failures**: [None | List failures]

## Integration Test Results
- **Test 1 (Pipeline)**: [✅ PASSED | ❌ FAILED]
- **Test 2 (Backward Compat)**: [✅ PASSED | ❌ FAILED]
- **Test 3 (Reprocessing)**: [✅ PASSED | ❌ FAILED]
- **Test 4 (Performance)**: [✅ PASSED | ❌ FAILED]
- **Test 5 (Regression)**: [✅ PASSED | ❌ FAILED]

## Manual Browser Testing
- **Chrome**: [✅ PASSED | ❌ FAILED]
- **Firefox**: [✅ PASSED | ❌ FAILED]
- **Safari**: [✅ PASSED | ❌ FAILED | N/A]

## Performance Benchmarks
| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Timestamp extraction | <1ms | [X]ms | [✅|❌] |
| Caption sync latency | <50ms | [X]ms | [✅|❌] |
| Code reduction | 100 lines | [X] lines | [✅|❌] |

## Regression Testing
- **Existing Tests**: [X/Y passed]
- **Document Types**: [X/7 tested successfully]

## Issues Found
[List any issues discovered, with severity and proposed fixes]

## Conclusion
[Overall assessment: Ready for production | Needs fixes | Requires redesign]

## Attachments
- Screenshots: [links]
- Performance profiles: [links]
- Logs: [links]
```

---

## Quality Gates Summary

| Gate | Validation Type | Pass Criteria |
|------|----------------|---------------|
| **Gate 1** | Contract review | All contracts approved, ≥4/5 clarity, ≥90% coverage |
| **Gate 2** | Unit + Code review | All tests pass, ≥95% coverage, code reviews approved |
| **Gate 3** | Integration + Manual | Integration tests 100%, manual tests pass, perf targets met |

**Final Approval**: Only proceed to production after Gate 3 passes completely.
