# IC-003: Metadata Flags Contract

**Version**: 1.0
**Status**: ✅ Approved
**Author**: Backend Specification Agent
**Reviewers**: Backend Implementation Agent, Frontend Specification Agent
**Date**: 2025-10-16

---

## Overview

Defines metadata flags used to indicate timestamp presence and VTT file availability. These flags flow through the processing pipeline to the API and inform frontend behavior.

---

## Metadata Flags Specification

### Flag 1: `has_timestamps`

**Type**: `bool`
**Purpose**: Indicates if document has segment-level timestamps
**Set By**: Document processor after chunk creation
**Used By**: API response, frontend logic

**Rules**:
- `True` if **any** chunk has both `start_time` and `end_time` populated
- `False` if all chunks have `None` timestamps
- Applies to all document types (audio, PDF, etc.)

**Example**:
```python
# At least one chunk has timestamps
chunks = [
    TextChunk(..., start_time=1.0, end_time=2.0),  # Has timestamps
    TextChunk(..., start_time=None, end_time=None), # No timestamps
]
# Result: has_timestamps = True

# No chunks have timestamps
chunks = [
    TextChunk(..., start_time=None, end_time=None),
    TextChunk(..., start_time=None, end_time=None),
]
# Result: has_timestamps = False
```

---

### Flag 2: `has_word_timestamps`

**Type**: `bool`
**Purpose**: Indicates if audio has word-level timestamps (triggers VTT generation)
**Set By**: Document processor (only for audio files)
**Used By**: VTT generation trigger condition

**Rules**:
- Only set for `format_type == "audio"`
- Set to `True` if audio file has `has_timestamps == True`
- Not set for non-audio documents
- This is the **trigger** for VTT generation

**Note**: Name is legacy - actually represents segment-level timestamps, not word-level. Name kept for backward compatibility with existing VTT generator code.

**Example**:
```python
# Audio file with timestamps
if metadata["format_type"] == "audio" and has_timestamps:
    metadata["has_word_timestamps"] = True
    # This triggers VTT generation

# Non-audio document (even if has timestamps from extraction)
if metadata["format_type"] != "audio":
    # has_word_timestamps not set
    # VTT generation not triggered
```

---

### Flag 3: `vtt_available`

**Type**: `bool`
**Purpose**: Indicates if VTT file successfully generated
**Set By**: VTT generation code in processor.py
**Used By**: API response, frontend VTT track loading

**Rules**:
- `True` if VTT file successfully created
- `False` if VTT generation failed or skipped
- Only `True` when `vtt_path` also set

**Example**:
```python
try:
    vtt_content = generate_vtt(chunks, filename)
    vtt_path = save_vtt(doc_id, vtt_content)
    metadata["vtt_available"] = True
    metadata["vtt_path"] = str(vtt_path)
except Exception as e:
    logger.warning(f"VTT generation failed: {e}")
    metadata["vtt_available"] = False
    # vtt_path not set
```

---

### Flag 4: `vtt_path`

**Type**: `Optional[str]`
**Purpose**: Filesystem path to VTT file
**Set By**: VTT generation code in processor.py
**Used By**: API VTT endpoint to locate file

**Rules**:
- Set only if VTT file successfully created
- Path format: `"data/vtt/{doc_id}.vtt"`
- Not set if VTT generation fails or skips

**Example**:
```python
vtt_path = save_vtt(doc_id, vtt_content)
# Returns: Path("data/vtt/5e57bdeb-f37b-43e3-80ca-63bacaebeaab.vtt")
metadata["vtt_path"] = str(vtt_path)
# Stored as: "data/vtt/5e57bdeb-f37b-43e3-80ca-63bacaebeaab.vtt"
```

---

## Metadata Flow Through System

### Stage 1: Document Parsing
```python
# Initial metadata from docling
metadata = {
    "filename": "Myth 1.mp3",
    "format_type": "audio",
    # has_timestamps not yet set
}
```

### Stage 2: Chunk Creation
```python
# After chunks created with timestamps extracted
chunks = [
    TextChunk(..., start_time=0.62, end_time=3.96),
    TextChunk(..., start_time=5.92, end_time=12.04),
]

# Check for timestamps
has_timestamps = any(
    c.start_time is not None and c.end_time is not None
    for c in chunks
)
# Result: has_timestamps = True

# Update metadata
metadata["has_timestamps"] = has_timestamps
# Result: metadata["has_timestamps"] = True
```

### Stage 3: VTT Trigger Flag
```python
# Set VTT trigger for audio files
if metadata["format_type"] == "audio" and has_timestamps:
    metadata["has_word_timestamps"] = True

# Result: metadata["has_word_timestamps"] = True
```

### Stage 4: VTT Generation
```python
# Triggered by has_word_timestamps flag
if metadata.get("has_word_timestamps") and chunks:
    vtt_content = generate_vtt(chunks, filename)
    vtt_path = save_vtt(doc_id, vtt_content)

    metadata["vtt_path"] = str(vtt_path)
    metadata["vtt_available"] = True

# Result:
# metadata["vtt_path"] = "data/vtt/{doc_id}.vtt"
# metadata["vtt_available"] = True
```

### Stage 5: Storage in ChromaDB
```python
# Metadata stored with chunks in ChromaDB
chroma_client.add_text_embedding(
    doc_id=doc_id,
    chunk_id=chunk.chunk_id,
    embedding=embedding,
    metadata={
        "filename": "Myth 1.mp3",
        "format_type": "audio",
        "has_timestamps": True,
        "has_word_timestamps": True,
        "vtt_available": True,
        "vtt_path": "data/vtt/{doc_id}.vtt",
        # ... other metadata
    }
)
```

### Stage 6: API Response
```python
# GET /documents/{doc_id}
{
    "doc_id": "5e57bdeb-f37b-43e3-80ca-63bacaebeaab",
    "filename": "Myth 1.mp3",
    "metadata": {
        "has_timestamps": true,
        "vtt_available": true,
        "format_type": "audio"
        // vtt_path internal, not exposed to API
    },
    "chunks": [
        {
            "chunk_id": "chunk_...",
            "text_content": "Myth 1. Ideas come in a flash.",
            "start_time": 0.62,
            "end_time": 3.96
        }
    ]
}
```

---

## Decision Matrix

### When to Set Each Flag

| Scenario | has_timestamps | has_word_timestamps | vtt_available |
|----------|----------------|---------------------|---------------|
| Audio with valid timestamps | `True` | `True` | `True` |
| Audio without timestamps | `False` | Not set | `False` |
| Audio with malformed timestamps | `False` | Not set | `False` |
| PDF with no timestamps | `False` | Not set | `False` |
| PDF with timestamps (rare) | `True` | Not set | `False` |
| VTT generation fails | `True` | `True` | `False` |

---

## Code Location for Changes

### File: `src/processing/processor.py`

**Current Code** (Lines ~280-340):
```python
# Stage 3: Embedding generation
logger.info(f"Stage 3: Generating embeddings for {filename}")

# ... embedding code ...

# Stage 3.5: VTT Generation (audio with timestamps only)
if parsed_doc.metadata.get("has_word_timestamps") and parsed_doc.text_chunks:
    # VTT generation code (already exists)
```

**Required Addition** (Insert BEFORE Stage 3.5):
```python
# Stage 3: Embedding generation
logger.info(f"Stage 3: Generating embeddings for {filename}")

# ... existing embedding code ...

# NEW: Check for timestamps and set metadata flags
if parsed_doc.text_chunks:
    has_timestamps = any(
        chunk.start_time is not None and chunk.end_time is not None
        for chunk in parsed_doc.text_chunks
    )
    parsed_doc.metadata["has_timestamps"] = has_timestamps

    # For audio files with timestamps, set VTT trigger
    if parsed_doc.metadata.get("format_type") == "audio" and has_timestamps:
        parsed_doc.metadata["has_word_timestamps"] = True

    timestamp_count = sum(
        1 for c in parsed_doc.text_chunks
        if c.start_time is not None
    )
    logger.info(
        f"Document has timestamps: {has_timestamps} "
        f"({timestamp_count}/{len(parsed_doc.text_chunks)} chunks)"
    )
else:
    parsed_doc.metadata["has_timestamps"] = False

# Stage 3.5: VTT Generation (existing code continues)
if parsed_doc.metadata.get("has_word_timestamps") and parsed_doc.text_chunks:
    # ... existing VTT generation code ...
```

---

## Error Handling

### Scenario 1: Empty Chunks List
```python
if not parsed_doc.text_chunks:
    parsed_doc.metadata["has_timestamps"] = False
    # Don't set has_word_timestamps
    # VTT generation skipped
```

### Scenario 2: Partial Timestamps
```python
# Some chunks have timestamps, some don't
# This is VALID - VTT generator will filter
has_timestamps = any(c.start_time is not None for c in chunks)
# Result: has_timestamps = True

# VTT generator filters out None timestamps automatically
```

### Scenario 3: VTT Generation Exception
```python
try:
    vtt_content = generate_vtt(chunks, filename)
    vtt_path = save_vtt(doc_id, vtt_content)
    metadata["vtt_available"] = True
    metadata["vtt_path"] = str(vtt_path)
except Exception as e:
    logger.warning(f"VTT generation failed: {e}")
    metadata["vtt_available"] = False
    # vtt_path not set
    # Processing continues (non-fatal)
```

---

## Logging Requirements

```python
# After setting has_timestamps
logger.info(
    f"Document has timestamps: {has_timestamps} "
    f"({timestamp_count}/{total_chunks} chunks)"
)

# When setting VTT trigger
if metadata.get("has_word_timestamps"):
    logger.info(f"Audio file with timestamps detected, VTT generation enabled")

# VTT generation success
logger.info(f"Generated VTT: {vtt_path}")
metadata["vtt_available"] = True

# VTT generation failure
logger.warning(f"VTT generation failed: {e}")
metadata["vtt_available"] = False
```

---

## Testing

### Test 1: Audio with Timestamps
```python
def test_audio_with_timestamps_sets_flags():
    chunks = [
        TextChunk(..., start_time=1.0, end_time=2.0),
        TextChunk(..., start_time=2.0, end_time=3.0),
    ]
    metadata = {"format_type": "audio"}

    # Process
    set_timestamp_flags(chunks, metadata)

    assert metadata["has_timestamps"] == True
    assert metadata["has_word_timestamps"] == True
    # vtt_available set by VTT generator
```

### Test 2: Audio without Timestamps
```python
def test_audio_without_timestamps():
    chunks = [
        TextChunk(..., start_time=None, end_time=None),
    ]
    metadata = {"format_type": "audio"}

    set_timestamp_flags(chunks, metadata)

    assert metadata["has_timestamps"] == False
    assert "has_word_timestamps" not in metadata
```

### Test 3: Non-Audio with Timestamps
```python
def test_pdf_with_timestamps():
    chunks = [
        TextChunk(..., start_time=1.0, end_time=2.0),
    ]
    metadata = {"format_type": "pdf"}

    set_timestamp_flags(chunks, metadata)

    assert metadata["has_timestamps"] == True
    assert "has_word_timestamps" not in metadata  # VTT not triggered
```

### Test 4: Empty Chunks
```python
def test_empty_chunks():
    chunks = []
    metadata = {}

    set_timestamp_flags(chunks, metadata)

    assert metadata["has_timestamps"] == False
    assert "has_word_timestamps" not in metadata
```

---

## Success Criteria

### Implementation Success
- [ ] `has_timestamps` set correctly for all document types
- [ ] `has_word_timestamps` set only for audio with timestamps
- [ ] `vtt_available` set based on VTT generation result
- [ ] `vtt_path` set when VTT file created
- [ ] Flags stored in ChromaDB metadata
- [ ] Flags accessible via API

### Validation Success
- [ ] Audio with timestamps: all flags set correctly
- [ ] Audio without timestamps: flags indicate no VTT
- [ ] Non-audio documents: appropriate flags only
- [ ] VTT generation failures handled gracefully

---

## Dependencies

**Depends On**:
- IC-001 (TextChunk Timestamp Contract) - chunk fields
- IC-002 (VTT Pipeline Contract) - integration flow

**Consumed By**:
- IC-004 (API Response Contract) - flags in response
- Backend Implementation Agent (Wave 2)
- Frontend Implementation Agent (Wave 2) - conditional logic

---

## Review Checklist

- [x] All flags clearly defined
- [x] Decision matrix comprehensive
- [x] Code location specified
- [x] Error handling covered
- [x] Test scenarios provided
- [x] Flow through system documented
- [x] Backward compatibility preserved

---

**Contract Status**: ✅ Ready for Implementation
