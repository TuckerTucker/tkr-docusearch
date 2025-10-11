# Parser Markdown Extraction Interface Contract

**Provider**: parser-agent (docling_parser module)
**Consumers**: storage-client-agent
**File**: `src/processing/docling_parser.py`

## Interface Specification

### Modified Return Value: _parse_with_docling()

**Purpose**: Extract full markdown from Docling document and include in metadata.

**Current Signature** (unchanged):
```python
def _parse_with_docling(
    self,
    file_path: str,
    config: Optional[EnhancedModeConfig] = None
) -> tuple:
    """Parse document using Docling.

    Returns:
        Tuple of (pages, metadata, docling_document)
    """
```

**Modified Metadata Contract**:

The `metadata` dict returned MUST include these additional fields:

```python
metadata = {
    # ... existing fields ...
    "full_markdown": str,        # Full document as markdown (uncompressed)
    "markdown_length": int,      # Character count for monitoring
    "markdown_extracted": bool,  # True if extraction succeeded
    "markdown_error": Optional[str]  # Error message if extraction failed
}
```

## Contract Requirements

### For All Document Types:
1. **Markdown extraction MUST be attempted** for all formats that Docling supports
2. **Extraction MUST happen** after successful Docling conversion (after line 482)
3. **Failures MUST NOT block** document processing:
   - Set `markdown_extracted: False`
   - Set `markdown_error: str` with error message
   - Continue with document processing
4. **Empty documents MUST return** empty string, not None

### Extraction Logic:
```python
# After: doc = result.document (line 488)
try:
    markdown = doc.export_to_markdown()
    metadata["full_markdown"] = markdown
    metadata["markdown_length"] = len(markdown)
    metadata["markdown_extracted"] = True
    metadata["markdown_error"] = None
    logger.info(f"Extracted markdown: {len(markdown)} chars")
except Exception as e:
    logger.warning(f"Markdown extraction failed: {e}")
    metadata["full_markdown"] = ""
    metadata["markdown_length"] = 0
    metadata["markdown_extracted"] = False
    metadata["markdown_error"] = str(e)
```

### Field Specifications:

**full_markdown** (str):
- Contains complete document as markdown
- Includes all headings, paragraphs, tables, lists
- Uses Docling's markdown export format
- May be empty string (valid for image-only docs)
- MUST NOT be None

**markdown_length** (int):
- Character count of full_markdown
- Used for monitoring and size validation
- 0 for empty documents
- Must match `len(metadata["full_markdown"])`

**markdown_extracted** (bool):
- `True`: Extraction succeeded
- `False`: Extraction failed (see markdown_error)

**markdown_error** (Optional[str]):
- `None` if extraction succeeded
- Error message string if extraction failed
- Should be concise but informative

## Data Flow

```
Docling parse → doc.export_to_markdown() →
metadata["full_markdown"] →
processor.py (_store_embeddings) →
ChromaClient (compression happens here) →
ChromaDB storage
```

## Format-Specific Behavior

### PDF/DOCX/PPTX:
- Full markdown with structure preserved
- Tables rendered as markdown tables
- Headings with proper hierarchy

### Images (PNG/JPG):
- OCR text if available
- May be minimal/empty

### Audio (MP3/WAV - after ASR implementation):
- Transcript as markdown
- May include timestamps as markdown comments

### Text-only (MD/HTML):
- Parsed and re-exported markdown
- Should match input closely

## Error Handling Contract

### Non-Blocking Errors:
Parser MUST continue processing if markdown extraction fails:
- Log warning (not error)
- Set markdown_extracted = False
- Set markdown_error with reason
- Continue with pages/chunks processing

### Blocking Errors:
Only Docling parsing failures should block (existing behavior)

## Performance Contract

- Markdown extraction overhead: <100ms per document
- No impact on page/chunk processing
- Lazy evaluation: only call export_to_markdown() once

## Testing Contract

Parser agent MUST implement:
- Unit test: PDF with markdown extraction
- Unit test: DOCX with markdown extraction
- Unit test: Image-only document (empty markdown)
- Unit test: Markdown extraction failure handling
- Integration test: metadata flows to storage

## Validation Checklist

- [ ] Markdown extraction added after doc parsing
- [ ] All 4 metadata fields included
- [ ] Error handling is non-blocking
- [ ] Empty documents handled correctly
- [ ] Extraction logged appropriately
- [ ] Tests cover success and failure cases
- [ ] No breaking changes to existing functionality

## Integration Notes

**Storage Client Agent**: Will receive metadata dict with markdown fields
**Compression Agent**: Will compress markdown before storage
**No changes needed**: processor.py passes metadata through unchanged
