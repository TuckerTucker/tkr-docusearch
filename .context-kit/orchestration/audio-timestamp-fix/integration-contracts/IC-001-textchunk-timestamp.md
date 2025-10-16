# IC-001: TextChunk Timestamp Contract

**Version**: 1.0
**Status**: ✅ Approved
**Author**: Backend Specification Agent
**Reviewers**: Backend Implementation Agent
**Date**: 2025-10-16

---

## Overview

Defines the data structure and extraction logic for timestamps in TextChunk objects. Timestamps are currently embedded as `[time: X-Y]` text markers but must be extracted to dedicated `start_time` and `end_time` fields.

---

## Current State Analysis

### Existing TextChunk Structure
```python
# From src/processing/types.py
@dataclass
class TextChunk:
    chunk_id: str
    text: str  # Currently contains "[time: X-Y] actual text"
    start_time: Optional[float] = None  # Currently always None
    end_time: Optional[float] = None    # Currently always None
    # ... other fields
```

### Problem
- Timestamps exist as text: `"[time: 0.62-3.96] Myth 1. Ideas come in a flash."`
- Fields `start_time` and `end_time` are not populated
- VTT generator expects these fields to be populated
- Frontend has to parse markdown with regex as workaround

---

## Required Changes

### 1. Function Signature

```python
def extract_timestamps_from_text(text: str) -> tuple[Optional[float], Optional[float], str]:
    """
    Extract [time: X-Y] timestamp markers from text.

    Args:
        text: Text potentially containing [time: START-END] marker at beginning

    Returns:
        Tuple of (start_time, end_time, cleaned_text):
        - start_time: float seconds or None if not found/invalid
        - end_time: float seconds or None if not found/invalid
        - cleaned_text: text with timestamp marker removed

    Parsing Rules:
        - Marker must be at start of text (after optional whitespace)
        - Format: [time: <float>-<float>]
        - Both timestamps must be valid floats
        - end_time must be > start_time
        - start_time must be >= 0.0
        - If invalid, return (None, None, original_text)

    Examples:
        >>> extract_timestamps_from_text("[time: 1.5-3.2] Hello")
        (1.5, 3.2, "Hello")

        >>> extract_timestamps_from_text("[time: 0.62-3.96]  Multiple spaces")
        (0.62, 3.96, "Multiple spaces")

        >>> extract_timestamps_from_text("No timestamp here")
        (None, None, "No timestamp here")

        >>> extract_timestamps_from_text("[time: 5.0-2.0] Invalid")
        (None, None, "[time: 5.0-2.0] Invalid")
    """
```

---

## Data Schema

### Updated TextChunk Usage

```python
# After extraction
chunk = TextChunk(
    chunk_id="chunk_abc123-chunk0001",
    text="Myth 1. Ideas come in a flash.",  # CLEANED - no marker
    start_time=0.62,  # EXTRACTED from marker
    end_time=3.96,    # EXTRACTED from marker
    # ... other fields
)
```

---

## Timestamp Format Specification

### Valid Format
```
[time: <START>-<END>]
```

**Components**:
- `[time:` - Literal opening (case-sensitive)
- `<START>` - Float value in seconds (e.g., `1.5`, `0.62`, `3600.0`)
- `-` - Literal separator
- `<END>` - Float value in seconds
- `]` - Literal closing

**Whitespace**:
- Optional whitespace before `[time:`
- Optional whitespace after `:`
- Optional whitespace before/after `-`
- Optional whitespace after `]` before text

### Examples
```python
# Valid
"[time: 1.5-3.2] Text"
"[time:1.5-3.2] Text"
" [time: 1.5-3.2] Text"
"[time: 0.0-5.5] Text"
"[time: 3600.5-3725.8] Text"

# Invalid
"[time: 1.5] Text"           # Missing end time
"[time: abc-def] Text"       # Non-numeric
"[time: -1.5-3.2] Text"      # Negative start
"[time: 5.0-2.0] Text"       # End < Start
"Text [time: 1.5-3.2]"       # Not at start
"[TIME: 1.5-3.2] Text"       # Wrong case
```

---

## Validation Rules

### Rule 1: Format Validation
- Must match regex: `^\s*\[time:\s*([\d.]+)-([\d.]+)\]`
- Both numbers must parse as valid floats

### Rule 2: Value Validation
- `start_time >= 0.0` (no negative timestamps)
- `end_time > start_time` (positive duration)
- `end_time - start_time >= 0.001` (minimum 1ms duration)

### Rule 3: Text Cleaning
- Remove entire `[time: X-Y]` marker from text
- Preserve leading/trailing whitespace of actual text
- Do not modify text content after marker

---

## Edge Cases

### Edge Case 1: No Timestamp
**Input**: `"No timestamp here"`
**Output**: `(None, None, "No timestamp here")`
**Behavior**: Return original text unchanged

### Edge Case 2: Malformed Timestamp
**Input**: `"[time: abc-def] Text"`
**Output**: `(None, None, "[time: abc-def] Text")`
**Behavior**: Cannot parse, return original text unchanged

### Edge Case 3: Negative Start Time
**Input**: `"[time: -1.5-3.2] Text"`
**Output**: `(None, None, "[time: -1.5-3.2] Text")`
**Behavior**: Invalid, return original text unchanged

### Edge Case 4: Reversed Times
**Input**: `"[time: 5.0-2.0] Text"`
**Output**: `(None, None, "[time: 5.0-2.0] Text")`
**Behavior**: end < start is invalid, return original text unchanged

### Edge Case 5: Zero Duration
**Input**: `"[time: 2.0-2.0] Text"`
**Output**: `(None, None, "[time: 2.0-2.0] Text")`
**Behavior**: Zero duration invalid, return original text unchanged

### Edge Case 6: Multiple Timestamps
**Input**: `"[time: 1-2] First [time: 3-4] Second"`
**Output**: `(1.0, 2.0, "First [time: 3-4] Second")`
**Behavior**: Extract first only, leave rest in text

### Edge Case 7: Timestamp Not at Start
**Input**: `"Text [time: 1-2] More"`
**Output**: `(None, None, "Text [time: 1-2] More")`
**Behavior**: Must be at start, return unchanged

### Edge Case 8: Very Large Timestamps
**Input**: `"[time: 3600.5-7200.8] Hour"`
**Output**: `(3600.5, 7200.8, "Hour")`
**Behavior**: Accept any valid positive float

### Edge Case 9: High Precision Decimals
**Input**: `"[time: 0.6199999999-3.96] Text"`
**Output**: `(0.62, 3.96, "Text")`
**Behavior**: Parse full precision, may round in float

### Edge Case 10: Unicode Text
**Input**: `"[time: 1-2] Café résumé 你好"`
**Output**: `(1.0, 2.0, "Café résumé 你好")`
**Behavior**: Preserve all unicode characters

---

## Error Handling Strategy

### Graceful Degradation
- **Never raise exceptions** for invalid timestamps
- Always return valid tuple: `(Optional[float], Optional[float], str)`
- If parsing fails: return `(None, None, original_text)`
- Log warning for malformed timestamps (not errors)

### Logging Requirements
```python
# When invalid timestamp found
logger.warning(
    f"Malformed timestamp in text: {text[:50]}... "
    f"(reason: {reason})"
)

# When successfully extracted
logger.debug(
    f"Extracted timestamp: {start_time:.2f}-{end_time:.2f} "
    f"from chunk {chunk_id}"
)
```

**Reasons for failure**:
- "no_match" - No timestamp marker found
- "parse_error" - Cannot parse numbers
- "negative_start" - Start time < 0
- "invalid_duration" - End <= Start
- "wrong_position" - Timestamp not at start

---

## Integration Points

### Where It's Called
```python
# In text_processor.py or docling_parser.py (TBD in Wave 2)
def create_text_chunks(text: str, ...) -> List[TextChunk]:
    chunks = []
    for segment in segments:
        # Extract timestamp from segment text
        start_time, end_time, cleaned_text = extract_timestamps_from_text(segment.text)

        chunk = TextChunk(
            chunk_id=generate_chunk_id(...),
            text=cleaned_text,  # Use cleaned text
            start_time=start_time,
            end_time=end_time,
            # ... other fields
        )
        chunks.append(chunk)

    return chunks
```

### Impact on Downstream Systems

#### 1. VTT Generator (vtt_generator.py)
**Before**: Chunks have `None` timestamps, VTT generation skipped
**After**: Chunks have populated timestamps, VTT generation succeeds

#### 2. Metadata (processor.py)
**Before**: `has_timestamps = False`
**After**: `has_timestamps = True` when any chunk has both start_time and end_time

#### 3. API Response (documents_api.py)
**Before**: Chunks returned with null timestamps and `[time: X-Y]` in text
**After**: Chunks returned with float timestamps and clean text

#### 4. Frontend (accordion.js, audio-player.js)
**Before**: Must parse markdown with regex to get timestamps
**After**: Use `chunk.start_time` and `chunk.end_time` directly

---

## Test Scenarios (15 Required)

### Test Suite: `test_timestamp_extraction.py`

```python
class TestTimestampExtraction:

    # Valid timestamps
    def test_simple_timestamp(self):
        """Basic valid timestamp"""
        start, end, text = extract_timestamps_from_text("[time: 1.5-3.2] Hello")
        assert start == 1.5
        assert end == 3.2
        assert text == "Hello"

    def test_timestamp_with_decimals(self):
        """High precision decimals"""
        start, end, text = extract_timestamps_from_text("[time: 0.6199999-3.96] Text")
        assert abs(start - 0.62) < 0.001
        assert end == 3.96

    def test_timestamp_at_zero(self):
        """Start at zero"""
        start, end, text = extract_timestamps_from_text("[time: 0.0-5.5] Start")
        assert start == 0.0
        assert end == 5.5

    def test_large_timestamp(self):
        """Hour-long timestamp"""
        start, end, text = extract_timestamps_from_text("[time: 3600.5-3725.8] Hour")
        assert start == 3600.5
        assert end == 3725.8

    def test_whitespace_variations(self):
        """Various whitespace patterns"""
        start, end, text = extract_timestamps_from_text(" [time: 1.5-3.2]  Text  ")
        assert start == 1.5
        assert text == " Text  "  # Preserve trailing whitespace

    # Text cleaning
    def test_text_cleaning(self):
        """Marker removed from text"""
        _, _, text = extract_timestamps_from_text("[time: 1-2] Clean")
        assert text == "Clean"
        assert "[time:" not in text

    def test_multiline_text(self):
        """Multiline text preserved"""
        _, _, text = extract_timestamps_from_text("[time: 1-2] Line1\nLine2")
        assert text == "Line1\nLine2"

    def test_unicode_preservation(self):
        """Unicode characters preserved"""
        _, _, text = extract_timestamps_from_text("[time: 1-2] Café 你好")
        assert text == "Café 你好"

    # Invalid cases
    def test_no_timestamp(self):
        """No timestamp marker"""
        start, end, text = extract_timestamps_from_text("No timestamp")
        assert start is None
        assert end is None
        assert text == "No timestamp"

    def test_malformed_timestamp(self):
        """Non-numeric values"""
        start, end, text = extract_timestamps_from_text("[time: abc-def] Text")
        assert start is None
        assert end is None
        assert text == "[time: abc-def] Text"

    def test_negative_start(self):
        """Negative start time"""
        start, end, text = extract_timestamps_from_text("[time: -1.5-3.2] Text")
        assert start is None
        assert end is None

    def test_reversed_times(self):
        """End before start"""
        start, end, text = extract_timestamps_from_text("[time: 5.0-2.0] Text")
        assert start is None
        assert end is None

    def test_zero_duration(self):
        """Same start and end"""
        start, end, text = extract_timestamps_from_text("[time: 2.0-2.0] Text")
        assert start is None
        assert end is None

    def test_incomplete_timestamp(self):
        """Missing end time"""
        start, end, text = extract_timestamps_from_text("[time: 1.5] Text")
        assert start is None
        assert end is None

    def test_multiple_timestamps(self):
        """Multiple markers - use first"""
        start, end, text = extract_timestamps_from_text("[time: 1-2] A [time: 3-4] B")
        assert start == 1.0
        assert end == 2.0
        assert "[time: 3-4]" in text  # Second marker remains
```

---

## Success Criteria

### Implementation Success
- [ ] Function signature matches specification exactly
- [ ] All 15+ test cases pass
- [ ] Code coverage ≥95% for extraction function
- [ ] No exceptions raised for any input
- [ ] Logging present for both success and failure

### Integration Success
- [ ] TextChunk objects have populated start_time/end_time
- [ ] Text content no longer contains `[time: X-Y]` markers
- [ ] VTT generation triggers for audio files
- [ ] Metadata flags accurate (has_timestamps)
- [ ] API returns chunks with timestamps

### Performance Success
- [ ] Extraction completes in <1ms per chunk
- [ ] No memory leaks (regex compiled once)
- [ ] Handles 1000+ chunks without issue

---

## Dependencies

**Depends On**:
- Python standard library: `re`, `typing`, `logging`
- Existing TextChunk dataclass (no changes needed)

**Consumed By**:
- IC-002 (VTT Pipeline Contract)
- IC-003 (Metadata Flags Contract)
- IC-004 (API Response Contract)
- Backend Implementation Agent (Wave 2)

---

## Review Checklist

- [x] Function signature clear and type-hinted
- [x] All edge cases documented (10+)
- [x] Test scenarios enumerated (15+)
- [x] Error handling strategy defined
- [x] Integration points specified
- [x] Success criteria measurable
- [x] Examples provided with expected output
- [x] Validation rules clearly stated

---

**Contract Status**: ✅ Ready for Implementation
