# Storage Markdown Handling Interface Contract

**Provider**: storage-client-agent (ChromaClient)
**Consumers**: search-agent (future), ui-agent (future)
**File**: `src/storage/chroma_client.py`

## Interface Specification

### Modified: add_visual_embedding()

**Purpose**: Store visual embeddings with compressed markdown in metadata.

**Current Signature** (unchanged):
```python
def add_visual_embedding(
    self,
    doc_id: str,
    page: int,
    full_embeddings: np.ndarray,
    metadata: Dict[str, Any]
) -> str:
```

**Metadata Processing Contract**:

When `metadata` contains `full_markdown` field:
1. Check if markdown is large (>1KB threshold)
2. If large: compress using `compress_markdown()`
3. Store compressed version in metadata
4. Add metadata flag indicating compression

```python
# Inside add_visual_embedding(), before storing
if "full_markdown" in metadata and metadata.get("markdown_extracted"):
    markdown = metadata["full_markdown"]

    if len(markdown) > 1024:  # 1KB threshold
        # Compress and replace
        compressed = compress_markdown(markdown)
        metadata["full_markdown_compressed"] = compressed
        metadata["markdown_compression"] = "gzip+base64"
        del metadata["full_markdown"]  # Remove uncompressed
        logger.debug(f"Compressed markdown: {len(markdown)} → {len(compressed)} chars")
    else:
        # Small markdown, store uncompressed
        metadata["markdown_compression"] = "none"
```

### Modified: add_text_embedding()

**Same contract as add_visual_embedding()** for markdown handling.

### New Method: get_document_markdown()

**Purpose**: Retrieve full markdown for a document, handling decompression automatically.

**Signature**:
```python
def get_document_markdown(self, doc_id: str) -> Optional[str]:
    """Retrieve full markdown for a document.

    Args:
        doc_id: Document identifier

    Returns:
        Full markdown text, or None if not available

    Raises:
        DocumentNotFoundError: If doc_id doesn't exist
        DecompressionError: If markdown data corrupted
    """
```

**Implementation Contract**:
```python
def get_document_markdown(self, doc_id: str) -> Optional[str]:
    # Query any embedding for this doc_id (visual or text)
    results = self._visual_collection.get(
        where={"doc_id": doc_id},
        limit=1,
        include=["metadatas"]
    )

    if not results['ids']:
        # Try text collection
        results = self._text_collection.get(
            where={"doc_id": doc_id},
            limit=1,
            include=["metadatas"]
        )

    if not results['ids']:
        raise DocumentNotFoundError(f"Document {doc_id} not found")

    metadata = results['metadatas'][0]

    # Check if markdown extraction succeeded
    if not metadata.get("markdown_extracted"):
        logger.info(f"Markdown not available for {doc_id}")
        return None

    # Handle compressed markdown
    if "full_markdown_compressed" in metadata:
        compressed = metadata["full_markdown_compressed"]
        return decompress_markdown(compressed)

    # Handle uncompressed markdown
    if "full_markdown" in metadata:
        return metadata["full_markdown"]

    return None
```

## Contract Requirements

### Compression Thresholds:
- Markdown >1KB → compress
- Markdown ≤1KB → store uncompressed
- Always set `markdown_compression` flag

### Metadata Fields Added:

**full_markdown_compressed** (str, optional):
- Base64-encoded gzip-compressed markdown
- Only present if compression was applied
- Mutually exclusive with full_markdown

**markdown_compression** (str):
- "none": Uncompressed (small markdown)
- "gzip+base64": Compressed with gzip
- Used to determine decompression method

### Backward Compatibility:
- Documents without markdown fields → get_document_markdown() returns None
- No errors for missing markdown
- Graceful degradation

## Data Flow

```
Incoming metadata with full_markdown →
Check size (>1KB?) →
If yes: compress + store compressed version →
If no: store uncompressed →
Add compression flag →
Store in ChromaDB
```

## Error Handling Contract

### Non-Critical Errors:
- Compression fails → log warning, store uncompressed
- Decompression fails → log error, return None
- Missing markdown → return None (not an error)

### Critical Errors:
- Document not found → raise DocumentNotFoundError
- Corrupted compressed data → raise DecompressionError

## Performance Contract

- Compression overhead per document: <100ms
- Decompression on retrieval: <50ms
- No impact on search performance (markdown not indexed)
- Metadata size increase: minimal due to compression

## Size Management Contract

### Metadata Size Limits:
- Current limit: 50KB per embedding
- Compressed markdown: typically 10-30KB for large docs
- If compressed markdown >40KB: log warning but allow
- If total metadata >100KB: consider raising limit

### Monitoring:
- Log compression ratio for large documents
- Track total metadata sizes
- Alert if many documents exceed thresholds

## Testing Contract

Storage client agent MUST implement:
- Unit test: store small markdown (no compression)
- Unit test: store large markdown (with compression)
- Unit test: retrieve compressed markdown
- Unit test: retrieve uncompressed markdown
- Unit test: missing markdown returns None
- Unit test: corrupted compressed markdown raises error
- Integration test: round-trip through storage

## Validation Checklist

- [ ] Compression logic added to add_visual_embedding()
- [ ] Compression logic added to add_text_embedding()
- [ ] get_document_markdown() method implemented
- [ ] Compression threshold (1KB) configurable
- [ ] All metadata fields correctly set
- [ ] Error handling for missing/corrupted markdown
- [ ] Backward compatibility maintained
- [ ] Tests cover all scenarios
- [ ] Logging added for monitoring
- [ ] Documentation updated

## Integration Notes

**Parser Agent**: Provides uncompressed markdown in metadata
**Compression Agent**: Provides compress/decompress functions
**Search Agent** (future): Can call get_document_markdown() for results
**No breaking changes**: Existing embeddings work unchanged
