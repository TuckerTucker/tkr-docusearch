# Metadata Storage Contract

**Contract ID**: STORE-001
**Version**: 1.0
**Status**: Specification
**Owner**: metadata-agent
**Consumers**: All agents (storage consumer)

## Purpose

Define ChromaDB metadata schema for storing enhanced document structure and chunk context, including size limits, compression strategies, and query patterns.

## Metadata Schema

### Visual Collection Metadata

```python
# Per-embedding metadata in visual collection

{
    # Core identification (existing)
    "doc_id": str,           # Document UUID
    "filename": str,         # Original filename
    "page": int,             # Page number (1-indexed)

    # Document structure (new)
    "structure": {
        "headings": [...],    # From DocumentStructure
        "tables": [...],      # From DocumentStructure
        "pictures": [...],    # From DocumentStructure
        "code_blocks": [...], # From DocumentStructure (optional)
        "formulas": [...]     # From DocumentStructure (optional)
    },

    # Page-specific context (new)
    "page_context": {
        "headings_on_page": List[str],  # Headings visible on this page
        "table_count": int,              # Tables on this page
        "picture_count": int,            # Pictures on this page
        "element_types": List[str]       # Element types present
    }
}
```

### Text Collection Metadata

```python
# Per-chunk metadata in text collection

{
    # Core identification (existing)
    "doc_id": str,           # Document UUID
    "chunk_id": str,         # Unique chunk identifier
    "filename": str,         # Original filename
    "page": int,             # Primary page number

    # Chunk info (existing)
    "word_count": int,       # Words in chunk
    "start_offset": int,     # Character offset
    "end_offset": int,       # Character offset

    # Chunk context (new)
    "context": {
        "parent_heading": str | None,       # Immediate parent heading
        "parent_heading_level": int | None, # 0=title, 1=section, etc.
        "section_path": str,                # Full heading path
        "element_type": str,                # text, list_item, table_cell, etc.
        "related_tables": List[str],        # Referenced table IDs
        "related_pictures": List[str],      # Referenced picture IDs
        "page_nums": List[int],             # Pages spanned
        "is_page_boundary": bool            # Crosses page boundary
    }
}
```

## Storage Operations

### Add Visual Embedding (Enhanced)

```python
def add_visual_embedding(
    self,
    embedding: np.ndarray,
    doc_id: str,
    filename: str,
    page_num: int,
    structure: DocumentStructure,  # New parameter
    page_context: dict  # New parameter
) -> str:
    """
    Add visual embedding with enhanced metadata.

    Args:
        embedding: Visual embedding array (1031, 128) compressed to (128,)
        doc_id: Document UUID
        filename: Original filename
        page_num: Page number
        structure: Document structure metadata
        page_context: Page-specific context

    Returns:
        Embedding ID

    Raises:
        StorageError: If storage fails
        MetadataTooLargeError: If metadata exceeds size limit
    """
    # Prepare metadata
    metadata = {
        "doc_id": doc_id,
        "filename": filename,
        "page": page_num,
        "structure": compress_structure(structure.to_dict()),  # Compress
        "page_context": page_context
    }

    # Validate size
    metadata_size = estimate_metadata_size(metadata)
    if metadata_size > MAX_METADATA_SIZE_KB * 1024:
        raise MetadataTooLargeError(
            f"Metadata size {metadata_size/1024:.1f}KB exceeds limit "
            f"{MAX_METADATA_SIZE_KB}KB"
        )

    # Compress full embedding sequence for metadata
    full_embedding_compressed = compress_embedding_sequence(embedding)

    metadata["_embedding_full"] = full_embedding_compressed

    # Add to ChromaDB
    embedding_id = f"{doc_id}-visual-p{page_num}"

    self.chroma_collection_visual.add(
        ids=[embedding_id],
        embeddings=[embedding[:128]],  # CLS token for retrieval
        metadatas=[metadata]
    )

    return embedding_id
```

### Add Text Embedding (Enhanced)

```python
def add_text_embedding(
    self,
    embedding: np.ndarray,
    chunk: TextChunk  # Now includes context
) -> str:
    """
    Add text embedding with enhanced chunk metadata.

    Args:
        embedding: Text embedding array (30, 128) compressed to (128,)
        chunk: Enhanced TextChunk with context

    Returns:
        Embedding ID

    Raises:
        StorageError: If storage fails
    """
    # Prepare metadata
    metadata = {
        "doc_id": chunk.chunk_id.split("-chunk")[0],  # Extract doc_id
        "chunk_id": chunk.chunk_id,
        "filename": "",  # Set by caller if available
        "page": chunk.page_num,
        "word_count": chunk.word_count,
        "start_offset": chunk.start_offset,
        "end_offset": chunk.end_offset
    }

    # Add context if present
    if chunk.context:
        metadata["context"] = compress_context(chunk.context.to_dict())

    # Compress full embedding sequence
    full_embedding_compressed = compress_embedding_sequence(embedding)
    metadata["_embedding_full"] = full_embedding_compressed

    # Add to ChromaDB
    self.chroma_collection_text.add(
        ids=[chunk.chunk_id],
        embeddings=[embedding[:128]],  # CLS token for retrieval
        metadatas=[metadata]
    )

    return chunk.chunk_id
```

## Compression Strategies

### Structure Compression

```python
import gzip
import json
import base64

def compress_structure(structure_dict: dict) -> str:
    """Compress document structure for storage."""
    # Convert to JSON
    json_bytes = json.dumps(structure_dict, separators=(',', ':')).encode('utf-8')

    # Gzip compress
    compressed = gzip.compress(json_bytes, compresslevel=9)

    # Base64 encode for storage as string
    encoded = base64.b64encode(compressed).decode('ascii')

    return encoded

def decompress_structure(compressed_str: str) -> dict:
    """Decompress document structure from storage."""
    # Base64 decode
    compressed = base64.b64decode(compressed_str.encode('ascii'))

    # Gzip decompress
    json_bytes = gzip.decompress(compressed)

    # Parse JSON
    structure_dict = json.loads(json_bytes.decode('utf-8'))

    return structure_dict
```

### Context Compression

```python
def compress_context(context_dict: dict) -> dict:
    """Compress chunk context (minimal compression needed)."""
    # Context is already small, just remove None values
    return {k: v for k, v in context_dict.items() if v is not None}

def decompress_context(context_dict: dict) -> dict:
    """Decompress chunk context (just add defaults)."""
    defaults = {
        "parent_heading": None,
        "parent_heading_level": None,
        "section_path": "",
        "element_type": "text",
        "related_tables": [],
        "related_pictures": [],
        "page_nums": [],
        "is_page_boundary": False
    }
    return {**defaults, **context_dict}
```

## Size Limits

### Configuration

```python
# Metadata size limits (per embedding)
MAX_METADATA_SIZE_KB = 50  # ChromaDB recommended limit

# Component size targets
TARGET_STRUCTURE_SIZE_KB = 20   # Compressed structure
TARGET_CONTEXT_SIZE_KB = 2      # Chunk context
TARGET_EMBEDDING_SIZE_KB = 20   # Compressed full embedding
OVERHEAD_SIZE_KB = 8            # Other metadata fields

# Total: ~50KB per embedding
```

### Size Estimation

```python
def estimate_metadata_size(metadata: dict) -> int:
    """Estimate serialized metadata size in bytes."""
    import json
    serialized = json.dumps(metadata, default=str)
    return len(serialized.encode('utf-8'))

def validate_metadata_size(metadata: dict, max_size_kb: int = 50) -> None:
    """Validate metadata size within limits."""
    size_bytes = estimate_metadata_size(metadata)
    size_kb = size_bytes / 1024

    if size_kb > max_size_kb:
        raise MetadataTooLargeError(
            f"Metadata size {size_kb:.1f}KB exceeds limit {max_size_kb}KB"
        )
```

## Query Patterns

### Structure-Aware Search

```python
def search_by_document_type(
    self,
    query_embedding: np.ndarray,
    document_types: List[str],  # e.g., ["has_tables", "has_code"]
    n_results: int = 10
) -> dict:
    """
    Search with document structure filters.

    Args:
        query_embedding: Query embedding vector
        document_types: Required structure types
        n_results: Number of results

    Returns:
        Search results filtered by document type
    """
    # Query ChromaDB with where filter
    where_filter = {"$and": []}

    if "has_tables" in document_types:
        where_filter["$and"].append({"structure.tables": {"$ne": []}})

    if "has_code" in document_types:
        where_filter["$and"].append({"structure.code_blocks": {"$ne": []}})

    results = self.chroma_collection_visual.query(
        query_embeddings=[query_embedding[:128]],
        n_results=n_results,
        where=where_filter if where_filter["$and"] else None
    )

    return results
```

### Context-Aware Text Search

```python
def search_by_section(
    self,
    query_embedding: np.ndarray,
    section_keywords: List[str],  # e.g., ["introduction", "methods"]
    n_results: int = 10
) -> dict:
    """
    Search text chunks filtered by section.

    Args:
        query_embedding: Query embedding vector
        section_keywords: Keywords to match in section_path
        n_results: Number of results

    Returns:
        Search results filtered by section
    """
    # Query ChromaDB with where filter
    where_filters = []

    for keyword in section_keywords:
        where_filters.append({
            "context.section_path": {"$contains": keyword}
        })

    where_filter = {"$or": where_filters} if len(where_filters) > 1 else where_filters[0]

    results = self.chroma_collection_text.query(
        query_embeddings=[query_embedding[:128]],
        n_results=n_results,
        where=where_filter
    )

    return results
```

## Backward Compatibility

### Handling Legacy Metadata

```python
def normalize_metadata(metadata: dict) -> dict:
    """Normalize metadata to handle both old and new formats."""
    # Check if new format (has structure or context)
    has_structure = "structure" in metadata
    has_context = "context" in metadata

    if not has_structure and not has_context:
        # Legacy format - add empty placeholders
        metadata = metadata.copy()
        if "page" in metadata:  # Visual metadata
            metadata["structure"] = compress_structure({
                "headings": [],
                "tables": [],
                "pictures": [],
                "code_blocks": [],
                "formulas": []
            })
            metadata["page_context"] = {
                "headings_on_page": [],
                "table_count": 0,
                "picture_count": 0,
                "element_types": ["text"]
            }
        else:  # Text metadata
            metadata["context"] = compress_context({
                "parent_heading": None,
                "section_path": "",
                "element_type": "text"
            })

    return metadata
```

## Testing Contract

### Storage Tests Required
- ✅ Enhanced metadata stores successfully
- ✅ Metadata retrieval works correctly
- ✅ Compression/decompression round-trips correctly
- ✅ Size validation catches oversized metadata
- ✅ Query filters work with new fields
- ✅ Legacy metadata still works

### Performance Tests Required
- ✅ Storage time increase <10%
- ✅ Retrieval time unchanged
- ✅ Compression achieves >3x ratio
- ✅ Metadata size within limits

## Error Handling

### Custom Exceptions

```python
class MetadataTooLargeError(StorageError):
    """Raised when metadata exceeds size limit."""
    pass

class CompressionError(StorageError):
    """Raised when compression/decompression fails."""
    pass

class InvalidMetadataError(StorageError):
    """Raised when metadata format is invalid."""
    pass
```

## File Locations

- `src/storage/metadata_schema.py` - Schema definitions
- `src/storage/chroma_client.py` - Storage operations
- `src/storage/compression.py` - Compression utilities

## Version History

- **1.0** (2025-10-07): Initial specification
