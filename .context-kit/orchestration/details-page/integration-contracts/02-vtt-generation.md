# Integration Contract: VTT Generation

**Contract ID**: IC-002
**Provider**: vtt-agent (Wave 1)
**Consumers**: api-agent (Wave 2), audio-agent (Wave 3)
**Status**: SPECIFIED

---

## VTT File Specification

### WebVTT Format

**Standard**: [W3C WebVTT Specification](https://www.w3.org/TR/webvtt1/)

**File Structure**:
```
WEBVTT

00:00:10.500 --> 00:00:15.750
This is the first chunk of transcribed text.

00:00:15.750 --> 00:00:20.120
This is the second chunk.

00:00:20.120 --> 00:00:25.000
This is the third chunk of text.
```

---

## Module Interface

### File: `src/processing/vtt_generator.py`

```python
from typing import List, Optional
from pathlib import Path
from .types import TextChunk


def generate_vtt(chunks: List[TextChunk], filename: str) -> str:
    """
    Generate WebVTT content from text chunks with timestamps.

    Args:
        chunks: List of TextChunk objects with start_time/end_time
        filename: Original filename (for metadata comment)

    Returns:
        Complete VTT file content as string

    Raises:
        ValueError: If chunks have no timestamps
        VTTGenerationError: If VTT generation fails

    Example:
        >>> chunks = [
        ...     TextChunk(..., start_time=0.0, end_time=5.5, text="Hello"),
        ...     TextChunk(..., start_time=5.5, end_time=10.0, text="World"),
        ... ]
        >>> vtt = generate_vtt(chunks, "test.mp3")
        >>> print(vtt[:6])
        WEBVTT
    """
    pass


def save_vtt(doc_id: str, vtt_content: str, output_dir: Path = None) -> Path:
    """
    Save VTT content to filesystem.

    Args:
        doc_id: Document identifier (SHA-256 hash)
        vtt_content: Complete VTT file content
        output_dir: Optional output directory (default: data/vtt/)

    Returns:
        Path to saved VTT file

    Raises:
        IOError: If file write fails

    Example:
        >>> vtt = generate_vtt(chunks, "test.mp3")
        >>> path = save_vtt("abc123...", vtt)
        >>> print(path)
        data/vtt/abc123.vtt
    """
    pass


def format_timestamp(seconds: float) -> str:
    """
    Format seconds as VTT timestamp.

    Args:
        seconds: Time in seconds (float)

    Returns:
        VTT timestamp string (HH:MM:SS.mmm)

    Example:
        >>> format_timestamp(65.500)
        '00:01:05.500'
        >>> format_timestamp(3725.123)
        '01:02:05.123'
    """
    pass


def validate_vtt(vtt_content: str) -> bool:
    """
    Validate VTT content format.

    Args:
        vtt_content: VTT file content

    Returns:
        True if valid VTT format, False otherwise

    Checks:
        - Starts with "WEBVTT"
        - Has valid timestamp format
        - Cues are properly formatted
    """
    pass
```

---

## VTT Generation Algorithm

### Step-by-Step Process

```python
def generate_vtt(chunks: List[TextChunk], filename: str) -> str:
    """
    Implementation specification.
    """
    # 1. Header
    vtt_lines = ["WEBVTT"]
    vtt_lines.append("")  # Blank line required

    # 2. Optional metadata comment
    vtt_lines.append(f"NOTE Generated from {filename}")
    vtt_lines.append("")

    # 3. Filter chunks with timestamps
    timestamped_chunks = [c for c in chunks
                         if c.start_time is not None and c.end_time is not None]

    if not timestamped_chunks:
        raise ValueError(f"No chunks with timestamps in {filename}")

    # 4. Generate cues
    for i, chunk in enumerate(timestamped_chunks, start=1):
        # Cue identifier (optional but recommended)
        vtt_lines.append(str(i))

        # Cue timings
        start = format_timestamp(chunk.start_time)
        end = format_timestamp(chunk.end_time)
        vtt_lines.append(f"{start} --> {end}")

        # Cue text (can be multi-line)
        text = chunk.text.strip()
        vtt_lines.append(text)

        # Blank line between cues
        vtt_lines.append("")

    return "\n".join(vtt_lines)
```

### Timestamp Formatting

```python
def format_timestamp(seconds: float) -> str:
    """
    Convert seconds to HH:MM:SS.mmm format.
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60

    # Format: HH:MM:SS.mmm
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
```

**Examples**:
- `0.0` → `00:00:00.000`
- `65.5` → `00:01:05.500`
- `3725.123` → `01:02:05.123`

---

## File Storage Specification

### Directory Structure

```
data/
└── vtt/
    ├── {doc_id_1}.vtt
    ├── {doc_id_2}.vtt
    └── {doc_id_3}.vtt
```

### Storage Logic

```python
def save_vtt(doc_id: str, vtt_content: str, output_dir: Path = None) -> Path:
    """
    Implementation specification.
    """
    # 1. Determine output directory
    if output_dir is None:
        output_dir = Path("data/vtt")

    # 2. Create directory if doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # 3. Generate filename
    filename = f"{doc_id}.vtt"
    output_path = output_dir / filename

    # 4. Write file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(vtt_content)

    # 5. Return path
    return output_path
```

---

## Integration into Processing Pipeline

### Modification: `src/processing/processor.py`

**Location**: After chunking, before storage

```python
# In DocumentProcessor.process_document()

# ... existing chunking code ...

# NEW: Generate VTT if audio with timestamps
if is_audio and any(chunk.start_time is not None for chunk in text_chunks):
    from .vtt_generator import generate_vtt, save_vtt

    try:
        vtt_content = generate_vtt(text_chunks, filename)
        vtt_path = save_vtt(doc_id, vtt_content)

        # Store VTT path in metadata
        doc_metadata["vtt_path"] = str(vtt_path)
        doc_metadata["vtt_available"] = True

        logger.info(f"Generated VTT: {vtt_path}")
    except Exception as e:
        logger.warning(f"VTT generation failed: {e}")
        doc_metadata["vtt_available"] = False

# ... continue with storage ...
```

---

## Validation & Testing

### Unit Tests

**File**: `src/processing/test_vtt_generator.py`

```python
import pytest
from src.processing.vtt_generator import generate_vtt, format_timestamp, validate_vtt
from src.processing.types import TextChunk


def test_format_timestamp():
    """Test timestamp formatting."""
    assert format_timestamp(0.0) == "00:00:00.000"
    assert format_timestamp(65.5) == "00:01:05.500"
    assert format_timestamp(3725.123) == "01:02:05.123"


def test_generate_vtt_basic():
    """Test basic VTT generation."""
    chunks = [
        TextChunk(
            chunk_id="test-0001",
            page_num=1,
            text="First chunk",
            start_offset=0,
            end_offset=11,
            word_count=2,
            start_time=0.0,
            end_time=5.0
        ),
        TextChunk(
            chunk_id="test-0002",
            page_num=1,
            text="Second chunk",
            start_offset=11,
            end_offset=23,
            word_count=2,
            start_time=5.0,
            end_time=10.0
        ),
    ]

    vtt = generate_vtt(chunks, "test.mp3")

    assert vtt.startswith("WEBVTT")
    assert "00:00:00.000 --> 00:00:05.000" in vtt
    assert "First chunk" in vtt
    assert "00:00:05.000 --> 00:00:10.000" in vtt
    assert "Second chunk" in vtt


def test_generate_vtt_no_timestamps():
    """Test VTT generation fails without timestamps."""
    chunks = [
        TextChunk(
            chunk_id="test-0001",
            page_num=1,
            text="No timestamps",
            start_offset=0,
            end_offset=13,
            word_count=2,
            start_time=None,
            end_time=None
        ),
    ]

    with pytest.raises(ValueError, match="No chunks with timestamps"):
        generate_vtt(chunks, "test.mp3")


def test_validate_vtt():
    """Test VTT validation."""
    valid_vtt = """WEBVTT

00:00:00.000 --> 00:00:05.000
Test content
"""

    assert validate_vtt(valid_vtt) == True
    assert validate_vtt("Not VTT") == False
    assert validate_vtt("") == False
```

### Integration Test

```python
def test_vtt_integration():
    """Test full VTT generation pipeline."""
    from src.processing.docling_parser import DoclingParser
    from src.processing.vtt_generator import generate_vtt, save_vtt

    # Parse audio file
    parser = DoclingParser()
    pages, metadata, doc = parser.parse_document("test_audio.mp3")

    # Chunk document
    chunks = parser.chunk_document(doc, pages, "test-doc-123")

    # Generate VTT
    vtt = generate_vtt(chunks, "test_audio.mp3")

    # Validate format
    assert vtt.startswith("WEBVTT")
    assert validate_vtt(vtt)

    # Save to file
    path = save_vtt("test-doc-123", vtt)
    assert path.exists()

    # Verify file content
    with open(path, 'r') as f:
        content = f.read()
    assert content == vtt
```

---

## Error Handling

### Exception Hierarchy

```python
class VTTGenerationError(Exception):
    """Base exception for VTT generation errors."""
    pass


class InvalidTimestampError(VTTGenerationError):
    """Raised when timestamp format is invalid."""
    pass


class EmptyChunkError(VTTGenerationError):
    """Raised when no chunks with timestamps available."""
    pass
```

### Error Scenarios

| Scenario | Exception | Recovery |
|----------|-----------|----------|
| No timestamps | `ValueError` | Skip VTT generation, set `vtt_available=False` |
| Invalid timestamp format | `InvalidTimestampError` | Skip cue, log warning |
| File write fails | `IOError` | Log error, continue processing |
| VTT validation fails | `VTTGenerationError` | Don't save file, log error |

---

## Acceptance Criteria

- [ ] `generate_vtt()` function implemented
- [ ] `save_vtt()` function implemented
- [ ] `format_timestamp()` utility working
- [ ] `validate_vtt()` validation working
- [ ] VTT generation integrated into processor pipeline
- [ ] VTT files saved to `data/vtt/` directory
- [ ] Unit tests pass (100% coverage)
- [ ] Integration test with real audio passes
- [ ] Error handling for all failure modes
- [ ] VTT files validate in browser HTML5 player

---

## Hand-off to Consumers

### For api-agent (Wave 2)

```python
# VTT files will be located at:
vtt_path = Path(f"data/vtt/{doc_id}.vtt")

# Check if VTT exists:
if vtt_path.exists():
    # Serve via endpoint: GET /documents/{doc_id}/vtt
    return FileResponse(vtt_path, media_type="text/vtt")
else:
    raise HTTPException(404, "VTT file not found")
```

### For audio-agent (Wave 3)

```html
<!-- Use VTT in HTML5 audio element -->
<audio id="audio-player" controls>
  <source src="/uploads/{filename}" type="audio/mpeg">
  <track kind="captions"
         src="/documents/{doc_id}/vtt"
         srclang="en"
         label="English"
         default>
</audio>
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-14 | Initial specification |
