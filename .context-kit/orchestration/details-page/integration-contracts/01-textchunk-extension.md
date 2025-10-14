# Integration Contract: TextChunk Extension

**Contract ID**: IC-001
**Provider**: data-layer-agent (Wave 1)
**Consumers**: vtt-agent (Wave 1), api-agent (Wave 2), accordion-agent (Wave 3)
**Status**: SPECIFIED

---

## Data Structure Specification

### Extended TextChunk Dataclass

**File**: `src/processing/types.py`

```python
@dataclass
class TextChunk:
    """Represents a text chunk from a document.

    Attributes:
        chunk_id: Unique chunk identifier
        page_num: Source page number
        text: Chunk text content
        start_offset: Character offset in page
        end_offset: Character offset in page
        word_count: Approximate word count
        context: Optional chunk context metadata (enhanced mode)
        start_time: Optional start time in seconds (audio only)
        end_time: Optional end time in seconds (audio only)
    """

    chunk_id: str
    page_num: int
    text: str
    start_offset: int
    end_offset: int
    word_count: int
    context: Optional[ChunkContext] = None

    # NEW FIELDS (Wave 1)
    start_time: Optional[float] = None  # Seconds from start (audio only)
    end_time: Optional[float] = None    # Seconds from start (audio only)
```

---

## Field Specifications

### `start_time` (float, optional)

**Purpose**: Timestamp in seconds when this text chunk begins in audio

**Constraints**:
- Must be `>= 0.0`
- Must be `< end_time` (if both present)
- Precision: 3 decimal places (milliseconds)
- Only present for audio files with word-level timestamps

**Examples**:
```python
chunk.start_time = 10.500  # 10.5 seconds
chunk.start_time = 0.0     # Start of audio
chunk.start_time = None    # Non-audio document
```

### `end_time` (float, optional)

**Purpose**: Timestamp in seconds when this text chunk ends in audio

**Constraints**:
- Must be `> start_time` (if both present)
- Must be `<= total_audio_duration`
- Precision: 3 decimal places (milliseconds)
- Only present for audio files with word-level timestamps

**Examples**:
```python
chunk.end_time = 15.750    # 15.75 seconds
chunk.end_time = 180.0     # 3 minutes
chunk.end_time = None      # Non-audio document
```

---

## Timestamp Extraction Logic

### Source Data

Timestamps come from Docling's provenance data:

```python
# Docling structure (discovered during parsing)
doc.texts[i].prov[j].start_time  # Word-level start time
doc.texts[i].prov[j].end_time    # Word-level end time
```

### Aggregation Algorithm

**Chunk-Level Timestamps** = aggregate from word-level timestamps

```python
def compute_chunk_timestamps(chunk_words: List[str],
                            doc_prov: List[ProvenanceItem]) -> Tuple[float, float]:
    """
    Compute chunk timestamps from word-level provenance.

    Args:
        chunk_words: Words in this chunk
        doc_prov: Provenance items from Docling

    Returns:
        (start_time, end_time) tuple

    Algorithm:
        1. Find provenance items matching chunk words
        2. start_time = MIN(prov[i].start_time)
        3. end_time = MAX(prov[i].end_time)
    """
    timestamps = []
    for prov in doc_prov:
        if prov.text in chunk_words:
            timestamps.append((prov.start_time, prov.end_time))

    if not timestamps:
        return (None, None)

    start_time = min(t[0] for t in timestamps)
    end_time = max(t[1] for t in timestamps)

    return (round(start_time, 3), round(end_time, 3))
```

---

## ChromaDB Storage Specification

### Metadata Fields

When storing chunks with timestamps, include these metadata fields:

```python
metadata = {
    # Existing fields
    "filename": str,
    "chunk_id": int,
    "page": int,
    "text_preview": str,
    "word_count": int,
    "source_path": str,
    "doc_id": str,

    # NEW FIELDS (Wave 1)
    "start_time": float or None,   # Seconds (3 decimals)
    "end_time": float or None,     # Seconds (3 decimals)
    "has_timestamps": bool,        # Quick check flag
}
```

### Storage Logic

```python
# In processor.py, when adding text embeddings
for chunk in text_chunks:
    metadata = {
        # ... existing fields
        "start_time": chunk.start_time,
        "end_time": chunk.end_time,
        "has_timestamps": chunk.start_time is not None,
    }

    storage_client.add_text_embedding(
        doc_id=doc_id,
        chunk_id=chunk_id,
        full_embeddings=embedding,
        metadata=metadata
    )
```

---

## Validation Tests

### Unit Test Requirements

**File**: `src/processing/test_types.py`

```python
def test_textchunk_with_timestamps():
    """Test TextChunk with audio timestamps."""
    chunk = TextChunk(
        chunk_id="test-chunk-0001",
        page_num=1,
        text="Hello world",
        start_offset=0,
        end_offset=11,
        word_count=2,
        context=None,
        start_time=10.500,
        end_time=12.750
    )

    assert chunk.start_time == 10.500
    assert chunk.end_time == 12.750
    assert chunk.end_time > chunk.start_time


def test_textchunk_without_timestamps():
    """Test TextChunk for non-audio documents."""
    chunk = TextChunk(
        chunk_id="test-chunk-0001",
        page_num=1,
        text="Hello world",
        start_offset=0,
        end_offset=11,
        word_count=2,
        context=None
    )

    assert chunk.start_time is None
    assert chunk.end_time is None
```

---

## Integration Test

### End-to-End Validation

```python
def test_audio_processing_with_timestamps():
    """Test full audio processing pipeline with timestamps."""
    from src.processing.docling_parser import DoclingParser
    from src.processing.processor import DocumentProcessor

    # Parse audio file with word timestamps
    parser = DoclingParser()
    pages, metadata, doc = parser.parse_document("test_audio.mp3")

    # Verify metadata indicates timestamps
    assert metadata["has_word_timestamps"] == True

    # Chunk the document
    chunks = parser.chunk_document(doc, pages, "test-doc-123")

    # Verify at least some chunks have timestamps
    chunks_with_timestamps = [c for c in chunks if c.start_time is not None]
    assert len(chunks_with_timestamps) > 0

    # Verify timestamp ordering
    for chunk in chunks_with_timestamps:
        assert chunk.end_time > chunk.start_time
        assert chunk.start_time >= 0.0
```

---

## Backward Compatibility

### Existing Documents

**Existing chunks without timestamps** (processed before Wave 1):
- `start_time = None`
- `end_time = None`
- `has_timestamps = False`

No migration required - timestamps are optional fields.

### Non-Audio Documents

**PDFs, DOCX, images, etc.**:
- `start_time = None`
- `end_time = None`
- `has_timestamps = False`

No impact on existing functionality.

---

## Acceptance Criteria

- [ ] `TextChunk` dataclass extended with `start_time`/`end_time` fields
- [ ] Fields are optional (default `None`)
- [ ] Timestamp extraction logic implemented for audio files
- [ ] Timestamps stored in ChromaDB metadata
- [ ] Unit tests pass
- [ ] Integration test with real audio file passes
- [ ] Backward compatibility maintained
- [ ] No breaking changes to existing code

---

## Hand-off to Consumers

### For vtt-agent (Wave 1)
```python
# You will receive chunks with timestamps like this:
chunk = TextChunk(
    chunk_id="abc123-chunk0001",
    text="This is the transcribed text",
    start_time=10.500,
    end_time=15.750,
    # ... other fields
)

# Use these to generate VTT cues:
# 00:00:10.500 --> 00:00:15.750
# This is the transcribed text
```

### For api-agent (Wave 2)
```python
# Query ChromaDB to get chunks with timestamps:
text_data = client._text_collection.get(where={"doc_id": doc_id})

for metadata in text_data['metadatas']:
    chunk_info = {
        "chunk_id": metadata["chunk_id"],
        "text_content": metadata["text_preview"],
        "start_time": metadata.get("start_time"),  # May be None
        "end_time": metadata.get("end_time"),      # May be None
    }
```

### For accordion-agent (Wave 3)
```javascript
// API will return chunks with timestamps:
{
  "chunks": [
    {
      "chunk_id": "chunk_0001",
      "text_content": "...",
      "start_time": 10.5,    // Seconds, may be null
      "end_time": 15.75      // Seconds, may be null
    }
  ]
}

// Use to display time ranges in accordion titles:
// "Chunk 1 (00:10 - 00:15)"
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-14 | Initial specification |
