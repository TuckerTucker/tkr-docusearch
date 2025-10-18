# ChromaDB Enhanced Metadata Schema

**Version**: 1.0
**Last Updated**: 2025-10-17
**Status**: SPECIFICATION

---

## Overview

This specification defines the enhanced metadata schema for storing document structure and chunk context in ChromaDB collections. Enhanced mode enables bidirectional highlighting by storing bounding boxes, section paths, and structural relationships.

---

## 1. Visual Collection Enhanced Schema

### Base Metadata (Current)
```python
{
    "doc_id": str,
    "filename": str,
    "page": int,
    "source_path": str,
    "image_path": str,  # e.g., "data/page_images/abc123/page001.png"
    "thumb_path": str,  # e.g., "data/page_images/abc123/page001_thumb.jpg"
    "format": str,
    "mimetype": str,
    "timestamp": str (ISO),
    # ... other existing fields
}
```

### Enhanced Metadata (NEW)
```python
{
    # All base metadata fields above, PLUS:

    "has_structure": bool,  # Quick filter for structure availability

    # Structure summary (for quick queries)
    "num_headings": int,
    "num_tables": int,
    "num_pictures": int,
    "max_heading_depth": int,

    # Compressed structure data (gzipped JSON string)
    "structure": str,  # Base64-encoded gzip of DocumentStructure.to_dict()

    # Coordinate system metadata
    "image_width": int,  # Original image width in pixels
    "image_height": int,  # Original image height in pixels
}
```

### DocumentStructure Compressed Format

**Before Compression** (Python dict):
```python
{
    "headings": [
        {
            "text": "Introduction",
            "level": "SECTION_HEADER",
            "page": 1,
            "section_path": "1. Introduction",
            "bbox": [100.0, 200.0, 400.0, 250.0]
        }
    ],
    "tables": [
        {
            "page": 2,
            "caption": "Results Summary",
            "rows": 10,
            "cols": 5,
            "has_header": true,
            "table_id": "table-0",
            "bbox": [150.0, 300.0, 500.0, 600.0]
        }
    ],
    "pictures": [
        {
            "page": 3,
            "type": "chart",
            "caption": "Figure 1: Sales Trend",
            "confidence": 0.95,
            "picture_id": "picture-0",
            "bbox": [200.0, 400.0, 600.0, 700.0]
        }
    ],
    "code_blocks": [],
    "formulas": [],
    "summary": {
        "total_sections": 5,
        "max_depth": 3,
        "has_toc": false
    }
}
```

**After Compression**:
```python
import gzip
import base64
import json

structure_dict = DocumentStructure.to_dict()
json_str = json.dumps(structure_dict, separators=(',', ':'))  # Compact JSON
compressed = gzip.compress(json_str.encode('utf-8'))
stored_value = base64.b64encode(compressed).decode('ascii')
```

**Decompression** (for API retrieval):
```python
import gzip
import base64
import json

compressed = base64.b64decode(stored_value.encode('ascii'))
json_str = gzip.decompress(compressed).decode('utf-8')
structure_dict = json.loads(json_str)
structure = DocumentStructure.from_dict(structure_dict)
```

**Size Limits**:
- Uncompressed structure: <200 KB
- Compressed structure: Typically 10-30 KB (10:1 compression ratio)
- ChromaDB metadata limit: 50 KB per field (we're well within)

---

## 2. Text Collection Enhanced Schema

### Base Metadata (Current)
```python
{
    "doc_id": str,
    "chunk_id": str,  # e.g., "abc123-chunk0012"
    "page": int,
    "filename": str,
    "text_preview": str,  # First 200 chars
    "full_text": str,     # Complete chunk text
    "word_count": int,
    "source_path": str,
    "timestamp": str (ISO),
    # ... other existing fields
}
```

### Enhanced Metadata (NEW)
```python
{
    # All base metadata fields above, PLUS:

    "has_context": bool,  # Quick filter for context availability

    # Chunk context fields (flat for ChromaDB filtering)
    "parent_heading": str | null,
    "parent_heading_level": int | null,  # 0=TITLE, 1=SECTION, 2=SUB_SECTION, 3=PARAGRAPH
    "section_path": str,  # e.g., "Introduction > Background > Methods"
    "element_type": str,  # text|list_item|table_cell|caption|code|formula
    "is_page_boundary": bool,

    # Related elements (for cross-referencing)
    "related_tables": str,  # JSON array as string: '["table-0", "table-1"]'
    "related_pictures": str,  # JSON array as string: '["picture-0"]'

    # Chunk bounding box (if available from smart chunking)
    "bbox": str | null,  # JSON array as string: '[100.0, 200.0, 400.0, 250.0]'

    # Page range (for multi-page chunks)
    "page_nums": str,  # JSON array as string: '[1, 2]'
}
```

### ChunkContext Storage Format

**Why Flat Fields?**
ChromaDB only supports flat metadata (strings, numbers, booleans), not nested objects. We store:
- Simple fields directly: `parent_heading`, `section_path`, `element_type`
- Arrays as JSON strings: `related_tables`, `bbox`, `page_nums`

**Example**:
```python
# Input: ChunkContext object
chunk_context = ChunkContext(
    parent_heading="Methods",
    parent_heading_level=1,
    section_path="Introduction > Methods",
    element_type="text",
    related_tables=["table-0", "table-1"],
    related_pictures=["picture-0"],
    page_nums=[2, 3],
    is_page_boundary=True
)

# Stored in ChromaDB as:
{
    "has_context": True,
    "parent_heading": "Methods",
    "parent_heading_level": 1,
    "section_path": "Introduction > Methods",
    "element_type": "text",
    "is_page_boundary": True,
    "related_tables": '["table-0", "table-1"]',  # JSON string
    "related_pictures": '["picture-0"]',
    "bbox": '[150.0, 300.0, 500.0, 400.0]',  # JSON string
    "page_nums": '[2, 3]'  # JSON string
}
```

**Retrieval**:
```python
import json

# Parse JSON fields back to Python objects
related_tables = json.loads(metadata["related_tables"])  # ["table-0", "table-1"]
bbox = json.loads(metadata["bbox"]) if metadata["bbox"] else None
page_nums = json.loads(metadata["page_nums"])
```

---

## 3. Page→Chunk Mapping Index

**Problem**: Need efficient query: "Get all chunks for page N of doc X"

**Solution**: Create queryable mapping in text collection metadata.

**Implementation**:
```python
# When storing text chunk, include page number in metadata
{
    "doc_id": "abc123",
    "chunk_id": "abc123-chunk0012",
    "page": 5,  # PRIMARY PAGE where chunk starts
    "page_nums": '[5, 6]',  # All pages chunk spans
    ...
}
```

**Query**:
```python
# Get all chunks on page 5 of doc abc123
chunks = text_collection.get(
    where={
        "$and": [
            {"doc_id": {"$eq": "abc123"}},
            {"page": {"$eq": 5}}
        ]
    },
    include=["metadatas"]
)
```

**Note**: This returns chunks that START on page 5. For chunks spanning multiple pages, check `page_nums` field.

---

## 4. Heading→Chunk Association

**Problem**: Connect headings in structure to text chunks

**Solution**: Store chunk IDs with headings in DocumentStructure

**Enhanced Heading Format**:
```python
{
    "text": "Introduction",
    "level": "SECTION_HEADER",
    "page": 1,
    "section_path": "1. Introduction",
    "bbox": [100.0, 200.0, 400.0, 250.0],
    "chunk_ids": ["abc123-chunk0003", "abc123-chunk0004"]  # NEW
}
```

**How to Populate**:
1. During text chunking, when a chunk has `parent_heading="Introduction"`
2. Find matching heading in DocumentStructure
3. Add chunk_id to heading's `chunk_ids` list
4. Store updated structure in visual metadata

**Usage**:
```javascript
// Frontend: User clicks heading in structure
const heading = structure.headings[0];
const chunkIds = heading.chunk_ids;

// Scroll to first chunk under this heading
scrollToChunk(chunkIds[0]);
```

---

## 5. Validation Rules

### Visual Collection
```python
def validate_enhanced_visual_metadata(metadata):
    assert "has_structure" in metadata, "Missing has_structure field"
    assert isinstance(metadata["has_structure"], bool)

    if metadata["has_structure"]:
        assert "structure" in metadata, "has_structure=True but no structure field"
        assert "num_headings" in metadata
        assert "num_tables" in metadata
        assert "num_pictures" in metadata
        assert "max_heading_depth" in metadata
        assert "image_width" in metadata
        assert "image_height" in metadata

        # Validate compressed structure
        structure = decompress_structure(metadata["structure"])
        assert isinstance(structure, dict)
        assert "headings" in structure
        assert "summary" in structure
```

### Text Collection
```python
def validate_enhanced_text_metadata(metadata):
    assert "has_context" in metadata, "Missing has_context field"
    assert isinstance(metadata["has_context"], bool)

    if metadata["has_context"]:
        assert "element_type" in metadata
        assert metadata["element_type"] in [
            "text", "list_item", "table_cell",
            "caption", "code", "formula"
        ]

        # Validate JSON fields
        if metadata.get("related_tables"):
            related = json.loads(metadata["related_tables"])
            assert isinstance(related, list)

        if metadata.get("bbox"):
            bbox = json.loads(metadata["bbox"])
            assert isinstance(bbox, list)
            assert len(bbox) == 4
            assert bbox[0] < bbox[2]  # x1 < x2
            assert bbox[1] < bbox[3]  # y1 < y2
```

---

## 6. Migration Strategy

### Option A: Reprocess All Documents
```python
# scripts/migrate_enhanced_mode.py --reprocess-all
for doc in get_all_documents():
    # Delete old embeddings
    delete_document(doc.doc_id)

    # Reprocess with enhanced mode
    process_document(doc.path, enhanced_mode=True)
```

**Pros**: Clean, consistent metadata
**Cons**: Slow, resource-intensive

### Option B: Lazy Migration
```python
# On document access, check if enhanced
def get_document_structure(doc_id, page):
    metadata = visual_collection.get(doc_id, page)

    if not metadata.get("has_structure"):
        # Trigger background reprocessing
        queue_reprocess(doc_id, enhanced_mode=True)

        # Return empty structure for now
        return {"has_structure": False}

    return decompress_structure(metadata["structure"])
```

**Pros**: Fast, on-demand
**Cons**: Inconsistent state during migration

### Option C: Flag Legacy Documents
```python
# Add metadata field to distinguish
{
    "metadata_version": "v2.0-enhanced",  # or "v1.0-legacy"
    "has_structure": False,  # Legacy docs explicitly marked
    ...
}
```

**Pros**: Clear distinction, gradual migration
**Cons**: Permanent legacy flag

**Recommendation**: Option C (Flag Legacy) + Option B (Lazy Migration)

---

## 7. Compression Performance

**Benchmark** (typical PDF page structure):
```
Uncompressed JSON: 45 KB
Compressed (gzip): 4.2 KB (10.7:1 ratio)
Base64 overhead: 5.6 KB (33% encoding overhead)

Total stored: 5.6 KB per page
Decompression time: <1ms
```

**Why Compression?**
- ChromaDB has 50 KB metadata limit per field
- Structure can be large for complex documents
- Compression achieves 10:1 ratio typically
- Decompression is fast (<1ms)

---

## 8. Query Optimization

### Efficient Structure Retrieval
```python
# BAD: Decompress structure for every search result
for result in search_results:
    structure = decompress_structure(result["metadata"]["structure"])
    # Process structure...

# GOOD: Only decompress when needed
for result in search_results:
    if result["metadata"]["has_structure"]:
        # Only fetch if user requests structure
        pass
```

### Efficient Chunk Lookup
```python
# BAD: Scan all chunks to find page chunks
all_chunks = text_collection.get(where={"doc_id": "abc123"})
page_chunks = [c for c in all_chunks if c["page"] == 5]

# GOOD: Use indexed query
page_chunks = text_collection.get(
    where={"$and": [{"doc_id": "abc123"}, {"page": 5}]}
)
```

---

## 9. Comprehensive Validation Rules

### Visual Collection Validation

```python
def validate_enhanced_visual_metadata(metadata: dict) -> tuple[bool, list[str]]:
    """Validate enhanced visual collection metadata.

    Args:
        metadata: Metadata dictionary to validate

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Required base fields
    required_fields = ["doc_id", "filename", "page", "source_path",
                       "image_path", "thumb_path", "format", "mimetype", "timestamp"]
    for field in required_fields:
        if field not in metadata:
            errors.append(f"MISSING_FIELD: Required field '{field}' not found")

    # Required enhanced fields
    if "has_structure" not in metadata:
        errors.append("MISSING_FIELD: Required field 'has_structure' not found")
    elif not isinstance(metadata["has_structure"], bool):
        errors.append("INVALID_TYPE: 'has_structure' must be boolean")

    # If has_structure=True, validate structure fields
    if metadata.get("has_structure"):
        # Check summary fields
        summary_fields = ["num_headings", "num_tables", "num_pictures", "max_heading_depth"]
        for field in summary_fields:
            if field not in metadata:
                errors.append(f"MISSING_FIELD: Required field '{field}' not found when has_structure=True")
            elif not isinstance(metadata[field], int):
                errors.append(f"INVALID_TYPE: '{field}' must be integer")
            elif metadata[field] < 0:
                errors.append(f"INVALID_VALUE: '{field}' must be non-negative")

        # Check coordinate system
        if "image_width" not in metadata:
            errors.append("MISSING_FIELD: Required field 'image_width' not found")
        elif not isinstance(metadata["image_width"], int) or metadata["image_width"] <= 0:
            errors.append("INVALID_VALUE: 'image_width' must be positive integer")

        if "image_height" not in metadata:
            errors.append("MISSING_FIELD: Required field 'image_height' not found")
        elif not isinstance(metadata["image_height"], int) or metadata["image_height"] <= 0:
            errors.append("INVALID_VALUE: 'image_height' must be positive integer")

        # Check compressed structure
        if "structure" not in metadata:
            errors.append("MISSING_FIELD: Required field 'structure' not found when has_structure=True")
        else:
            try:
                # Attempt to decompress
                import base64
                import gzip
                import json

                compressed = base64.b64decode(metadata["structure"].encode("ascii"))
                json_str = gzip.decompress(compressed).decode("utf-8")
                structure_dict = json.loads(json_str)

                # Validate structure format
                required_structure_keys = ["headings", "tables", "pictures", "summary"]
                for key in required_structure_keys:
                    if key not in structure_dict:
                        errors.append(f"INVALID_STRUCTURE: Missing key '{key}' in decompressed structure")

                # Validate summary counts match
                if "summary" in structure_dict:
                    if structure_dict["summary"].get("total_sections", 0) != metadata.get("num_headings", -1):
                        errors.append("INCONSISTENT_DATA: num_headings doesn't match structure summary")

                # Validate bbox coordinates within image bounds
                for heading in structure_dict.get("headings", []):
                    if heading.get("bbox"):
                        bbox = heading["bbox"]
                        if len(bbox) != 4:
                            errors.append("INVALID_BBOX: Heading bbox must have 4 coordinates")
                        elif bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
                            errors.append("INVALID_BBOX: Heading bbox coordinates invalid (x1>=x2 or y1>=y2)")
                        elif bbox[2] > metadata.get("image_width", float("inf")):
                            errors.append("BBOX_OUT_OF_BOUNDS: Heading bbox exceeds image width")
                        elif bbox[3] > metadata.get("image_height", float("inf")):
                            errors.append("BBOX_OUT_OF_BOUNDS: Heading bbox exceeds image height")

            except base64.binascii.Error:
                errors.append("CORRUPTED_DATA: 'structure' field is not valid base64")
            except gzip.BadGzipFile:
                errors.append("CORRUPTED_DATA: 'structure' field is not valid gzip")
            except json.JSONDecodeError:
                errors.append("CORRUPTED_DATA: Decompressed structure is not valid JSON")
            except Exception as e:
                errors.append(f"DECOMPRESSION_ERROR: Failed to decompress structure: {e}")

    return (len(errors) == 0, errors)
```

### Text Collection Validation

```python
def validate_enhanced_text_metadata(metadata: dict) -> tuple[bool, list[str]]:
    """Validate enhanced text collection metadata.

    Args:
        metadata: Metadata dictionary to validate

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Required base fields
    required_fields = ["doc_id", "chunk_id", "page", "filename",
                       "text_preview", "full_text", "word_count", "timestamp"]
    for field in required_fields:
        if field not in metadata:
            errors.append(f"MISSING_FIELD: Required field '{field}' not found")

    # Required enhanced fields
    if "has_context" not in metadata:
        errors.append("MISSING_FIELD: Required field 'has_context' not found")
    elif not isinstance(metadata["has_context"], bool):
        errors.append("INVALID_TYPE: 'has_context' must be boolean")

    # If has_context=True, validate context fields
    if metadata.get("has_context"):
        # Validate element_type
        if "element_type" not in metadata:
            errors.append("MISSING_FIELD: Required field 'element_type' not found when has_context=True")
        else:
            valid_types = ["text", "list_item", "table_cell", "caption", "code", "formula"]
            if metadata["element_type"] not in valid_types:
                errors.append(f"INVALID_VALUE: 'element_type' must be one of {valid_types}")

        # Validate parent_heading_level
        if "parent_heading_level" in metadata and metadata["parent_heading_level"] is not None:
            level = metadata["parent_heading_level"]
            if not isinstance(level, int):
                errors.append("INVALID_TYPE: 'parent_heading_level' must be integer or null")
            elif level < 0 or level > 10:
                errors.append("INVALID_VALUE: 'parent_heading_level' must be between 0-10")

        # Validate section_path length
        if "section_path" in metadata:
            if len(metadata["section_path"]) > 500:
                errors.append("INVALID_VALUE: 'section_path' exceeds 500 character limit")

        # Validate JSON array fields
        json_fields = {
            "related_tables": "array of table IDs",
            "related_pictures": "array of picture IDs",
            "page_nums": "array of page numbers",
            "bbox": "array of 4 coordinates"
        }

        for field, description in json_fields.items():
            if field in metadata and metadata[field] is not None:
                try:
                    parsed = json.loads(metadata[field])

                    if not isinstance(parsed, list):
                        errors.append(f"INVALID_JSON: '{field}' must be JSON array ({description})")

                    # Field-specific validation
                    if field == "bbox" and len(parsed) != 4:
                        errors.append("INVALID_BBOX: bbox must have exactly 4 coordinates")
                    elif field == "bbox" and len(parsed) == 4:
                        if parsed[0] >= parsed[2] or parsed[1] >= parsed[3]:
                            errors.append("INVALID_BBOX: bbox coordinates invalid (x1>=x2 or y1>=y2)")

                    if field == "page_nums":
                        if not all(isinstance(p, int) and p > 0 for p in parsed):
                            errors.append("INVALID_VALUE: All page_nums must be positive integers")

                except json.JSONDecodeError:
                    errors.append(f"INVALID_JSON: '{field}' is not valid JSON")

    # Validate page number consistency
    if "page" in metadata:
        if not isinstance(metadata["page"], int) or metadata["page"] < 1:
            errors.append("INVALID_VALUE: 'page' must be positive integer")

        # Check page_nums contains page
        if "page_nums" in metadata and metadata["page_nums"]:
            try:
                page_nums = json.loads(metadata["page_nums"])
                if metadata["page"] not in page_nums:
                    errors.append("INCONSISTENT_DATA: 'page' not found in 'page_nums' array")
            except:
                pass  # Already caught by JSON validation above

    return (len(errors) == 0, errors)
```

### Error Message Reference

| Error Code | Description | Resolution |
|------------|-------------|------------|
| `MISSING_FIELD` | Required field not present in metadata | Add missing field with appropriate value |
| `INVALID_TYPE` | Field has wrong data type | Convert to correct type (bool, int, str) |
| `INVALID_VALUE` | Field value out of valid range | Correct value to be within constraints |
| `INVALID_STRUCTURE` | Decompressed structure missing required keys | Fix DocumentStructure.to_dict() output |
| `INCONSISTENT_DATA` | Summary counts don't match actual data | Recalculate summary statistics |
| `INVALID_BBOX` | Bounding box coordinates invalid | Check bbox format [x1, y1, x2, y2] with x1<x2, y1<y2 |
| `BBOX_OUT_OF_BOUNDS` | Bbox coordinates exceed image dimensions | Validate bbox against image_width/height |
| `CORRUPTED_DATA` | Compressed data cannot be decoded | Recompress using proper encoding |
| `DECOMPRESSION_ERROR` | Unknown error during decompression | Check compression implementation |
| `INVALID_JSON` | JSON string field is malformed | Validate JSON before storing |

---

## 10. Schema Version Compatibility

### Current Version: v1.0

**Compatibility Rules**:
- Storage layer MUST validate metadata version before processing
- Legacy documents (no `has_structure` field) are implicitly version v0.0
- Version v1.0 is backwards compatible with v0.0 (base fields unchanged)
- Future versions must maintain backwards compatibility or provide migration

**Version Detection**:
```python
def detect_metadata_version(metadata: dict) -> str:
    """Detect metadata schema version.

    Args:
        metadata: Metadata dictionary

    Returns:
        Version string (e.g., "v1.0", "v0.0")
    """
    # Check for explicit version field (future-proofing)
    if "metadata_version" in metadata:
        return metadata["metadata_version"]

    # Check for v1.0 enhanced fields
    if "has_structure" in metadata or "has_context" in metadata:
        return "v1.0"

    # Legacy format
    return "v0.0"
```

**Migration Path**:
```python
def migrate_metadata_to_v1(metadata: dict) -> dict:
    """Migrate legacy metadata to v1.0 format.

    Args:
        metadata: Legacy metadata dict

    Returns:
        Enhanced metadata dict
    """
    # Add version flag
    metadata["metadata_version"] = "v1.0"

    # Visual collection: Add structure fields
    if "image_path" in metadata:  # Visual collection indicator
        metadata["has_structure"] = False  # Legacy docs have no structure
        metadata["num_headings"] = 0
        metadata["num_tables"] = 0
        metadata["num_pictures"] = 0
        metadata["max_heading_depth"] = 0

    # Text collection: Add context fields
    if "chunk_id" in metadata:  # Text collection indicator
        metadata["has_context"] = False  # Legacy docs have no context

    return metadata
```

---

## 11. Testing Requirements

### Unit Tests
- [ ] Compression/decompression roundtrip preserves data
- [ ] Validation rules catch all invalid scenarios
- [ ] JSON field parsing handles malformed data gracefully
- [ ] Bbox validation catches invalid coordinates
- [ ] Error messages are clear and actionable
- [ ] Schema version detection works correctly
- [ ] Migration from v0.0 to v1.0 adds all required fields

### Integration Tests
- [ ] Store and retrieve enhanced visual metadata
- [ ] Store and retrieve enhanced text metadata
- [ ] Page→chunk query returns correct results
- [ ] Heading→chunk associations work bidirectionally
- [ ] Validation errors prevent invalid data storage
- [ ] Large documents (100+ pages) handle compression correctly
- [ ] Metadata size stays within ChromaDB limits

### Performance Tests
- [ ] Compression time <10ms per structure
- [ ] Decompression time <1ms per structure
- [ ] Metadata size <50KB per document (target <30KB)
- [ ] Query performance <100ms for page→chunk lookup
- [ ] Validation overhead <5ms per document

### Edge Cases
- [ ] Empty structure (no headings/tables/pictures)
- [ ] Very large tables (1000+ rows)
- [ ] Deeply nested headings (10+ levels)
- [ ] Multi-page chunks (5+ pages)
- [ ] Chunks with many related elements (10+ tables/pictures)
- [ ] Special characters in section paths (>, |, /, etc.)
- [ ] Missing bbox information (null handling)
- [ ] Zero-length chunks (empty paragraphs)

---

## 12. Implementation Recommendations for Wave 2

### Storage Agent Priority Tasks
1. **Implement validation functions** (highest priority)
   - Start with `validate_enhanced_visual_metadata()`
   - Then `validate_enhanced_text_metadata()`
   - Test with sample metadata from `sample-metadata-*.json`

2. **Add compression helpers** (use existing utilities)
   - Use `src/storage/compression.py::compress_structure_metadata()`
   - Test compression ratios on realistic documents

3. **Extend ChromaClient methods**
   - Add `add_enhanced_visual_embedding()` method
   - Add `add_enhanced_text_embedding()` method
   - Both should validate before storing

4. **Create migration utility**
   - Implement `detect_metadata_version()` and `migrate_metadata_to_v1()`
   - Add `--dry-run` flag for testing
   - Log all migrations for auditability

### API Agent Priority Tasks
1. **Add structure retrieval endpoint** (deferred to Wave 3)
   - `GET /api/documents/{doc_id}/pages/{page}/structure`
   - Returns decompressed DocumentStructure
   - Include caching to avoid repeated decompression

2. **Add chunk context endpoint** (deferred to Wave 3)
   - `GET /api/documents/{doc_id}/chunks/{chunk_id}/context`
   - Returns parsed ChunkContext with related elements

3. **Enhance search results** (deferred to Wave 3)
   - Include `has_structure` and `has_context` flags in results
   - Allow filtering by element_type or parent_heading

### Performance Optimizations
- **Lazy loading**: Only decompress structure when explicitly requested
- **Caching**: Cache decompressed structures for active documents
- **Batch validation**: Validate multiple documents in parallel
- **Index optimization**: Ensure page and parent_heading fields are indexed

### Common Pitfalls to Avoid
- ❌ Don't decompress structure for every search result
- ❌ Don't forget to validate JSON arrays before parsing
- ❌ Don't store Python objects directly (use JSON strings for arrays)
- ❌ Don't skip size validation (enforce 50KB ChromaDB limit)
- ❌ Don't hardcode coordinate systems (always use image_width/height)

### Testing Strategy
1. **Start with sample metadata**: Use provided JSON files for initial tests
2. **Generate synthetic data**: Create test documents with various structures
3. **Test edge cases**: Empty structures, large structures, malformed data
4. **Performance benchmarks**: Measure compression, validation, query times
5. **Integration tests**: End-to-end workflow from upload to bidirectional highlighting

---

## Version History

**v1.1** (2025-10-17):
- Added comprehensive validation functions with error codes
- Added schema version compatibility and migration strategy
- Added detailed error message reference
- Added Wave 2 implementation recommendations
- Added common pitfalls and testing strategy
- Created sample metadata files for reference

**v1.0** (2025-10-17):
- Initial specification
- Enhanced visual schema with compressed structure
- Enhanced text schema with flat chunk context
- Page→chunk mapping via page field
- Heading→chunk association via chunk_ids
- Validation rules defined
- Migration strategies outlined
