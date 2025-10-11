# Compression Interface Contract

**Provider**: storage-agent (compression module)
**Consumers**: parser-agent, storage-client-agent
**File**: `src/storage/compression.py`

## Interface Specification

### Function: compress_markdown()

**Purpose**: Compress markdown text using gzip and encode to base64 for storage in ChromaDB metadata.

**Signature**:
```python
def compress_markdown(markdown: str) -> str:
    """Compress markdown text for efficient storage.

    Args:
        markdown: Full markdown text as string

    Returns:
        Base64-encoded gzip-compressed string

    Raises:
        CompressionError: If compression fails
    """
```

**Contract Requirements**:
- Must accept any valid UTF-8 string
- Must return valid base64 string (no newlines, padding included)
- Compression ratio should be 3-5x for typical markdown
- Must be deterministic (same input → same output)
- Maximum input size: 10MB (raise error if exceeded)
- Must handle empty string (return compressed empty string)

**Example**:
```python
markdown = "# Title\n\nContent here..."
compressed = compress_markdown(markdown)
assert isinstance(compressed, str)
assert len(compressed) < len(markdown)  # Typically
```

### Function: decompress_markdown()

**Purpose**: Decompress base64-encoded gzip markdown back to original text.

**Signature**:
```python
def decompress_markdown(compressed: str) -> str:
    """Decompress markdown text from storage format.

    Args:
        compressed: Base64-encoded gzip-compressed string

    Returns:
        Original markdown text

    Raises:
        DecompressionError: If decompression fails or data corrupted
    """
```

**Contract Requirements**:
- Must accept any base64 string produced by compress_markdown()
- Must return exact original text (round-trip fidelity)
- Must detect and report corruption (CRC check)
- Must handle malformed base64 gracefully
- Maximum output size: 10MB (raise error if exceeded)

**Round-Trip Guarantee**:
```python
original = "# Test\nContent"
compressed = compress_markdown(original)
decompressed = decompress_markdown(compressed)
assert decompressed == original  # Exact equality required
```

## Error Handling Contract

### Exception Types:
```python
class CompressionError(Exception):
    """Base exception for compression operations."""
    pass

class MarkdownTooLargeError(CompressionError):
    """Markdown exceeds size limit."""
    pass

class CorruptedDataError(CompressionError):
    """Compressed data is corrupted."""
    pass
```

### Error Scenarios:
1. Input > 10MB → `MarkdownTooLargeError` with size details
2. Invalid base64 → `CorruptedDataError` with parse error
3. Gzip decompression fails → `CorruptedDataError` with details
4. Output > 10MB → `MarkdownTooLargeError` with size details

## Performance Contract

- Compression: <100ms for 1MB markdown
- Decompression: <50ms for 1MB markdown
- Memory overhead: <2x input size during operation
- Thread-safe: Yes (no shared state)

## Testing Contract

Provider MUST implement:
- Unit test: round-trip with various sizes (1KB, 100KB, 1MB)
- Unit test: empty string handling
- Unit test: unicode/emoji handling
- Unit test: error cases (oversized, corrupted)
- Unit test: deterministic output
- Performance test: 1MB markdown <100ms

## Validation Checklist

- [ ] compress_markdown() implemented
- [ ] decompress_markdown() implemented
- [ ] Exception classes defined
- [ ] Size limits enforced
- [ ] Round-trip tests pass
- [ ] Error handling tests pass
- [ ] Performance benchmarks pass
- [ ] Documentation complete

## Integration Notes

**Storage Agent**: Will call compress_markdown() before storing in metadata
**Parser Agent**: Will receive compressed markdown from storage via decompress_markdown()
**No direct imports**: Consumers import from `src.storage.compression`
