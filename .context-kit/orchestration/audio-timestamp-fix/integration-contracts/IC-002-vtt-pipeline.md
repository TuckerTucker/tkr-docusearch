# IC-002: VTT Generation Pipeline Contract

**Version**: 1.0
**Status**: ✅ Approved
**Author**: Backend Specification Agent
**Reviewers**: Backend Implementation Agent
**Date**: 2025-10-16

---

## Overview

Defines how timestamp extraction integrates into the document processing pipeline and triggers VTT file generation. Specifies the flow from document parsing through chunk creation to VTT file creation.

---

## Current VTT Generator

### Existing Implementation
The VTT generator already exists at `src/processing/vtt_generator.py`:

```python
def generate_vtt(chunks: List[TextChunk], filename: str) -> str:
    """Generate WebVTT content from text chunks with timestamps."""
    # Filters chunks where start_time and end_time are not None
    # Generates VTT format output
    # Returns VTT string

def save_vtt(doc_id: str, vtt_content: str, output_dir: Optional[Path] = None) -> Path:
    """Save VTT content to filesystem."""
    # Saves to data/vtt/{doc_id}.vtt
    # Returns path to saved file
```

### Current Trigger Condition (processor.py line 311)
```python
if parsed_doc.metadata.get("has_word_timestamps") and parsed_doc.text_chunks:
    has_timestamps = any(
        chunk.start_time is not None
        for chunk in parsed_doc.text_chunks
    )
    if has_timestamps:
        # Generate VTT
```

**Problem**: `has_word_timestamps` is never set to True, so VTT generation never runs.

---

## Integration Architecture

### Pipeline Flow

```
Document Upload
    ↓
Docling Parser (docling_parser.py)
    ├─→ Visual Processing (images)
    └─→ Text Processing (text_processor.py)
            ↓
        Extract segments/chunks from markdown
            ↓
        For each chunk:
            ├─→ Call extract_timestamps_from_text(chunk.text) [IC-001]
            ├─→ Get (start_time, end_time, cleaned_text)
            ├─→ Create TextChunk with populated fields
            └─→ Store cleaned_text (no markers)
            ↓
        Return List[TextChunk] with timestamps
            ↓
Document Processor (processor.py)
    ├─→ Check if any chunks have timestamps
    ├─→ Set metadata flags [IC-003]
    ├─→ If has_timestamps: Call VTT generator
    └─→ Save VTT file to data/vtt/
            ↓
    Store metadata in ChromaDB
            ↓
API serves chunks with timestamps [IC-004]
```

---

## Integration Point 1: Text Chunking

### Location
**File**: `src/processing/text_processor.py` OR `src/processing/docling_parser.py`
**TBD in Wave 2**: Backend Implementation Agent will identify exact location

### Current Chunking (Hypothetical)
```python
def create_chunks_from_markdown(markdown: str) -> List[TextChunk]:
    """Current implementation (approximate)"""
    chunks = []
    # Split markdown into segments
    for i, segment_text in enumerate(segments):
        chunk = TextChunk(
            chunk_id=f"chunk_{doc_id}-chunk{i:04d}",
            text=segment_text,  # Contains "[time: X-Y] actual text"
            start_time=None,    # Not extracted
            end_time=None,      # Not extracted
        )
        chunks.append(chunk)
    return chunks
```

### Required Integration
```python
from .text_processor import extract_timestamps_from_text  # New function

def create_chunks_from_markdown(markdown: str, doc_id: str) -> List[TextChunk]:
    """Updated implementation"""
    chunks = []
    for i, segment_text in enumerate(segments):
        # INTEGRATION POINT: Extract timestamps
        start_time, end_time, cleaned_text = extract_timestamps_from_text(segment_text)

        chunk = TextChunk(
            chunk_id=f"chunk_{doc_id}-chunk{i:04d}",
            text=cleaned_text,      # CHANGED: Use cleaned text
            start_time=start_time,  # CHANGED: Populate from extraction
            end_time=end_time,      # CHANGED: Populate from extraction
        )
        chunks.append(chunk)

        # Optional logging
        if start_time is not None:
            logger.debug(
                f"Extracted timestamp {start_time:.2f}-{end_time:.2f} "
                f"for chunk {i}"
            )

    return chunks
```

---

## Integration Point 2: Metadata Updates

### Location
**File**: `src/processing/processor.py`
**Lines**: Around 280-340 (Stage 3: Embedding generation)

### Current Metadata Logic (Lines 311-339)
```python
# Stage 3.5: VTT Generation (audio with timestamps only)
if parsed_doc.metadata.get("has_word_timestamps") and parsed_doc.text_chunks:
    has_timestamps = any(
        chunk.start_time is not None
        for chunk in parsed_doc.text_chunks
    )

    if has_timestamps:
        # Generate VTT (this code already works)
        ...
```

### Required Changes

#### Change 1: Set has_timestamps Before VTT Check
```python
# AFTER text chunks created, BEFORE VTT generation
# This should be around line 280-300

# Check if any chunks have timestamps
has_timestamps = parsed_doc.text_chunks and any(
    chunk.start_time is not None and chunk.end_time is not None
    for chunk in parsed_doc.text_chunks
)

# Store in metadata for use by VTT generator and API
parsed_doc.metadata["has_timestamps"] = has_timestamps

# If audio file and has timestamps, set has_word_timestamps
# (This makes the existing VTT generation trigger)
if parsed_doc.metadata.get("format_type") == "audio" and has_timestamps:
    parsed_doc.metadata["has_word_timestamps"] = True

logger.info(
    f"Document has timestamps: {has_timestamps} "
    f"({sum(1 for c in parsed_doc.text_chunks if c.start_time is not None)} chunks)"
)
```

#### Change 2: VTT Generation Trigger (Already Exists)
```python
# Stage 3.5: VTT Generation (audio with timestamps only)
# This code ALREADY EXISTS and works correctly
# It will now trigger because has_word_timestamps will be True

if parsed_doc.metadata.get("has_word_timestamps") and parsed_doc.text_chunks:
    has_timestamps = any(
        chunk.start_time is not None
        for chunk in parsed_doc.text_chunks
    )

    if has_timestamps:
        try:
            from .vtt_generator import generate_vtt, save_vtt

            logger.info(f"Generating VTT for audio file: {filename}")

            vtt_content = generate_vtt(parsed_doc.text_chunks, filename)
            vtt_path = save_vtt(doc_id, vtt_content)

            parsed_doc.metadata["vtt_path"] = str(vtt_path)
            parsed_doc.metadata["vtt_available"] = True

            logger.info(f"Generated VTT: {vtt_path}")
        except Exception as e:
            logger.warning(f"VTT generation failed: {e}")
            parsed_doc.metadata["vtt_available"] = False
```

---

## VTT File Output

### File Location
```
data/vtt/{doc_id}.vtt
```

### Example Output
```
WEBVTT

NOTE Generated from Myth 1.mp3

1
00:00:00.620 --> 00:00:03.960
Myth 1. Ideas come in a flash.

2
00:00:05.920 --> 00:00:12.040
Ideas may feel like they come in a flash, but it's actually after your brain has done a lot of work.

3
00:00:12.600 --> 00:00:19.100
If you get frustrated and can't seem to figure out a certain problem or get past a certain limitation in your understanding,
```

---

## Error Handling

### Scenario 1: No Timestamps in Audio File
```python
# Audio file processed but no timestamp markers found
# Result:
#   - has_timestamps = False
#   - has_word_timestamps = False (not set)
#   - VTT generation skipped
#   - vtt_available = False
```

### Scenario 2: Malformed Timestamps
```python
# Some chunks have valid timestamps, some don't
# Result:
#   - has_timestamps = True (at least one valid)
#   - VTT generator filters out chunks with None timestamps
#   - VTT file created with valid cues only
#   - Warning logged for malformed timestamps
```

### Scenario 3: VTT Generation Fails
```python
# Exception during VTT generation
# Result:
#   - Exception caught in processor.py
#   - vtt_available = False
#   - Warning logged
#   - Processing continues (non-fatal)
```

### Scenario 4: Non-Audio Document
```python
# PDF/DOCX with no timestamps
# Result:
#   - has_timestamps = False
#   - VTT generation not attempted
#   - Normal document processing
```

---

## Logging Requirements

### Success Path
```python
# During chunk creation
logger.debug(f"Extracted timestamp {start:.2f}-{end:.2f} for chunk {i}")

# After metadata set
logger.info(
    f"Document has timestamps: {has_timestamps} "
    f"({count} chunks with timestamps)"
)

# During VTT generation
logger.info(f"Generating VTT for audio file: {filename}")
logger.info(f"Generated VTT: {vtt_path}")
```

### Failure Path
```python
# Malformed timestamp
logger.warning(
    f"Malformed timestamp in chunk {chunk_id}: {text[:50]}... "
    f"(reason: {reason})"
)

# VTT generation failure
logger.warning(f"VTT generation failed: {e}")

# No timestamps in audio
logger.info(
    f"No chunks with timestamps in {filename}, skipping VTT generation"
)
```

---

## Performance Considerations

### Timestamp Extraction
- **Per-chunk overhead**: <1ms (regex compiled once)
- **Total overhead**: Negligible for typical audio (<100 chunks)
- **Impact**: <10% increase in processing time

### VTT Generation
- **Existing implementation**: Already tested and working
- **File I/O**: Single write to disk (~50ms)
- **Memory**: Minimal (string concatenation)

---

## Testing Integration

### Unit Test: Chunk Creation
```python
def test_chunk_creation_with_timestamps():
    """Test chunks created with extracted timestamps"""
    markdown = """
[time: 0.62-3.96] First segment
[time: 5.92-12.04] Second segment
"""
    chunks = create_chunks_from_markdown(markdown, "test_doc")

    assert len(chunks) == 2
    assert chunks[0].start_time == 0.62
    assert chunks[0].end_time == 3.96
    assert chunks[0].text == "First segment"
    assert "[time:" not in chunks[0].text
```

### Unit Test: Metadata Flags
```python
def test_metadata_flags_set_correctly():
    """Test has_timestamps flag set when chunks have timestamps"""
    doc = ParsedDocument(
        text_chunks=[
            TextChunk(..., start_time=1.0, end_time=2.0),
            TextChunk(..., start_time=2.0, end_time=3.0),
        ],
        metadata={"format_type": "audio"}
    )

    # After processing
    assert doc.metadata["has_timestamps"] == True
    assert doc.metadata["has_word_timestamps"] == True
    assert "vtt_path" in doc.metadata
    assert doc.metadata["vtt_available"] == True
```

---

## Success Criteria

### Implementation Success
- [ ] Timestamp extraction called during chunk creation
- [ ] Metadata flags set correctly before VTT generation
- [ ] VTT generator receives chunks with populated timestamps
- [ ] VTT file created at `data/vtt/{doc_id}.vtt`
- [ ] Logging present at all integration points

### Validation Success
- [ ] Audio file with timestamps generates VTT file
- [ ] Audio file without timestamps skips VTT generation
- [ ] Non-audio documents unaffected
- [ ] VTT file valid (passes validate_vtt check)
- [ ] Performance overhead <10%

### Integration Success
- [ ] Existing VTT generator code unchanged (no modifications needed)
- [ ] Processor.py changes minimal (metadata flags only)
- [ ] Backward compatible (documents without timestamps work)

---

## Dependencies

**Depends On**:
- IC-001 (TextChunk Timestamp Contract) - extraction function

**Consumed By**:
- IC-003 (Metadata Flags Contract) - flags usage
- IC-004 (API Response Contract) - chunks with timestamps
- Backend Implementation Agent (Wave 2)

**External**:
- Existing `vtt_generator.py` (no changes needed)
- Existing `processor.py` (minimal changes)

---

## Review Checklist

- [x] Integration points clearly identified
- [x] Code changes minimal and surgical
- [x] Error handling comprehensive
- [x] Logging requirements specified
- [x] Performance impact assessed
- [x] Test scenarios provided
- [x] Success criteria measurable
- [x] Backward compatibility preserved

---

**Contract Status**: ✅ Ready for Implementation
