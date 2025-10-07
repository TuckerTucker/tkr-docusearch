# Storage Module

ChromaDB storage layer for DocuSearch MVP with multi-vector embedding support.

## Overview

The storage module provides a complete ChromaDB integration for storing and retrieving multi-vector embeddings from the ColPali model. It implements a two-stage retrieval strategy:

1. **Stage 1**: Fast approximate search using CLS tokens (representative vectors)
2. **Stage 2**: Precise late-interaction re-ranking using full multi-vector sequences

## Features

- ✅ Multi-vector storage with compression (4x size reduction)
- ✅ CLS token-based indexing for fast retrieval
- ✅ Dual collection architecture (visual + text)
- ✅ Comprehensive error handling
- ✅ Collection lifecycle management
- ✅ Health checks and validation
- ✅ >90% test coverage

## Architecture

### Collections

1. **visual_collection**: Stores page-level visual embeddings
2. **text_collection**: Stores chunk-level text embeddings

### Storage Format

Each embedding is stored with:

- **Representative Vector** (ChromaDB embedding field)
  - CLS token (first token) from multi-vector sequence
  - Shape: (768,)
  - Used for fast HNSW-based retrieval

- **Full Sequence** (ChromaDB metadata field)
  - Complete multi-vector sequence
  - Compressed with gzip + base64 encoding
  - Shape: (seq_length, 768)
  - Used for precise re-ranking

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install individually
pip install chromadb numpy pytest pytest-cov
```

## Usage

### Basic Storage

```python
from src.storage import ChromaClient
import numpy as np

# Initialize client
client = ChromaClient(host="chromadb", port=8000)

# Store visual embedding
visual_embeddings = np.random.randn(100, 768).astype(np.float32)
embedding_id = client.add_visual_embedding(
    doc_id="doc123",
    page=1,
    full_embeddings=visual_embeddings,
    metadata={
        "filename": "report.pdf",
        "source_path": "/data/report.pdf",
        "file_size": 1024000
    }
)
# Returns: "doc123-page001"

# Store text embedding
text_embeddings = np.random.randn(64, 768).astype(np.float32)
embedding_id = client.add_text_embedding(
    doc_id="doc123",
    chunk_id=0,
    full_embeddings=text_embeddings,
    metadata={
        "filename": "report.pdf",
        "page": 1,
        "source_path": "/data/report.pdf",
        "text_preview": "This is the first chunk...",
        "word_count": 150
    }
)
# Returns: "doc123-chunk0000"
```

### Search Operations

```python
# Stage 1: Fast retrieval using CLS tokens
query_cls = np.random.randn(768).astype(np.float32)

candidates = client.search_visual(
    query_embedding=query_cls,
    n_results=100,
    filters={"filename": "report.pdf"}  # Optional
)

# Returns list of:
# {
#     "id": "doc123-page001",
#     "score": 0.85,  # Cosine similarity
#     "metadata": {...},
#     "representative_vector": [...]
# }

# Stage 2: Get full embeddings for re-ranking
for candidate in candidates[:20]:  # Top-20
    full_embeddings = client.get_full_embeddings(
        embedding_id=candidate['id'],
        collection="visual"
    )
    # Shape: (seq_length, 768)
    # Use for late interaction scoring
```

### Document Management

```python
# Delete document (all embeddings)
visual_count, text_count = client.delete_document("doc123")
print(f"Deleted {visual_count} visual, {text_count} text embeddings")

# Get collection statistics
stats = client.get_collection_stats()
print(stats)
# {
#     "visual_count": 100,
#     "text_count": 300,
#     "total_documents": 10,
#     "storage_size_mb": 40.5
# }
```

### Collection Management

```python
from src.storage import CollectionManager

manager = CollectionManager(client)

# Validate collection health
report = manager.validate_collections()
print(report['status'])  # "healthy", "degraded", or "unhealthy"

# Get document list
documents = manager.get_document_list(limit=10)
for doc in documents:
    print(f"{doc['filename']}: {doc['visual_pages']} pages, {doc['text_chunks']} chunks")

# Find orphaned embeddings (invalid metadata)
orphans = manager.get_orphaned_embeddings()
print(f"Found {orphans['count']} orphaned embeddings")

# Cleanup orphans (requires confirmation)
report = manager.cleanup_orphaned_embeddings(confirm=True)
print(f"Deleted {report['total_deleted']} orphaned embeddings")

# Reset collection (requires confirmation)
report = manager.reset_collection("visual", confirm=True)
print(f"Reset complete: {report['items_deleted']} items deleted")

# Export metadata for backup
export = manager.export_collection_metadata(collection="all")
# Save to file for backup/analysis
```

## Error Handling

The module defines custom exceptions for different error scenarios:

```python
from src.storage import (
    StorageError,                 # Base exception
    ChromaDBConnectionError,      # Connection failures
    EmbeddingValidationError,     # Invalid embedding shape/dtype
    MetadataCompressionError,     # Compression failures
    DocumentNotFoundError,        # Missing documents
)

try:
    client = ChromaClient(host="invalid", port=9999)
except ChromaDBConnectionError as e:
    print(f"Connection failed: {e}")

try:
    # Invalid shape (must be 2D with dim=768)
    bad_embedding = np.random.randn(768)  # 1D
    client.add_visual_embedding(
        doc_id="test",
        page=1,
        full_embeddings=bad_embedding,
        metadata={...}
    )
except EmbeddingValidationError as e:
    print(f"Validation failed: {e}")

try:
    # Get non-existent embedding
    full_emb = client.get_full_embeddings("nonexistent", "visual")
except DocumentNotFoundError as e:
    print(f"Not found: {e}")
```

## Compression

The module uses gzip + base64 compression to fit large multi-vector embeddings in ChromaDB metadata fields (2MB limit):

```python
from src.storage import compress_embeddings, decompress_embeddings

# Compress
embeddings = np.random.randn(100, 768).astype(np.float32)
compressed = compress_embeddings(embeddings)
# Size: ~307KB -> ~77KB (4x reduction)

# Decompress
restored = decompress_embeddings(compressed, shape=(100, 768))
# Exact match within float32 precision
np.allclose(embeddings, restored)  # True
```

Utility functions:

```python
from src.storage import estimate_compressed_size, compression_ratio

size_bytes = estimate_compressed_size(embeddings)
ratio = compression_ratio(embeddings)
print(f"Compression: {ratio:.1f}x ({size_bytes} bytes)")
```

## Testing

Run the comprehensive test suite:

```bash
# All tests with coverage
pytest src/storage/test_storage.py -v --cov=src/storage --cov-report=html

# Specific test class
pytest src/storage/test_storage.py::TestChromaClientInit -v

# Run with detailed output
pytest src/storage/test_storage.py -vv -s
```

Test coverage areas:
- ✅ Collection initialization (3 tests)
- ✅ Embedding storage (6 tests)
- ✅ Search operations (4 tests)
- ✅ Full embedding retrieval (3 tests)
- ✅ Document deletion (2 tests)
- ✅ Collection statistics (1 test)
- ✅ Collection management (8 tests)
- ✅ Compression utilities (5 tests)
- ✅ Integration scenarios (2 tests)

## API Reference

### ChromaClient

```python
class ChromaClient:
    def __init__(
        self,
        host: str = "chromadb",
        port: int = 8000,
        visual_collection: str = "visual_collection",
        text_collection: str = "text_collection"
    )

    def add_visual_embedding(
        self,
        doc_id: str,
        page: int,
        full_embeddings: np.ndarray,
        metadata: Dict[str, Any]
    ) -> str

    def add_text_embedding(
        self,
        doc_id: str,
        chunk_id: int,
        full_embeddings: np.ndarray,
        metadata: Dict[str, Any]
    ) -> str

    def search_visual(
        self,
        query_embedding: np.ndarray,
        n_results: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]

    def search_text(
        self,
        query_embedding: np.ndarray,
        n_results: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]

    def get_full_embeddings(
        self,
        embedding_id: str,
        collection: str = "visual"
    ) -> np.ndarray

    def delete_document(
        self,
        doc_id: str
    ) -> Tuple[int, int]

    def get_collection_stats(self) -> Dict[str, Any]
```

### CollectionManager

```python
class CollectionManager:
    def __init__(self, client: ChromaClient)

    def validate_collections(self) -> Dict[str, Any]

    def reset_collection(
        self,
        collection: str,
        confirm: bool = False
    ) -> Dict[str, Any]

    def get_document_list(
        self,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]

    def get_orphaned_embeddings(self) -> Dict[str, List[str]]

    def cleanup_orphaned_embeddings(
        self,
        confirm: bool = False
    ) -> Dict[str, Any]

    def export_collection_metadata(
        self,
        collection: str = "all"
    ) -> Dict[str, List[Dict[str, Any]]]
```

## Configuration

### Environment Variables

```bash
# ChromaDB connection
export CHROMA_HOST=chromadb
export CHROMA_PORT=8001

# Collection names
export VISUAL_COLLECTION=visual_collection
export TEXT_COLLECTION=text_collection

# Batch operations
export CHROMA_BATCH_SIZE=100

# Persistence
export CHROMA_DATA=/chroma/chroma
```

### Docker Integration

```yaml
# docker-compose.yml
services:
  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - chroma_data:/chroma/chroma
    environment:
      - IS_PERSISTENT=TRUE
```

## Performance

Target latencies (actual performance depends on deployment):

| Operation | Target | Notes |
|-----------|--------|-------|
| add_visual_embedding | <50ms | Includes compression |
| add_text_embedding | <50ms | Includes compression |
| search_visual | <200ms | Top-100 retrieval |
| search_text | <200ms | Top-100 retrieval |
| get_full_embeddings | <20ms | Decompression only |
| delete_document | <100ms | Batch delete |

## Files

```
src/storage/
├── __init__.py              # Module exports
├── chroma_client.py         # Main ChromaClient class
├── collection_manager.py    # Collection lifecycle management
├── compression.py           # Compression utilities
├── test_storage.py          # Unit tests
├── requirements.txt         # Dependencies
├── README.md               # This file
└── CONTRACT_VALIDATION.md  # Contract compliance
```

## Integration

### With processing-agent

```python
# After generating embeddings with ColPali
from src.storage import ChromaClient

client = ChromaClient()

# Store page embeddings
for page_num, page_emb in enumerate(visual_embeddings, 1):
    client.add_visual_embedding(
        doc_id=doc_id,
        page=page_num,
        full_embeddings=page_emb,
        metadata={...}
    )

# Store chunk embeddings
for chunk_id, chunk_emb in enumerate(text_embeddings):
    client.add_text_embedding(
        doc_id=doc_id,
        chunk_id=chunk_id,
        full_embeddings=chunk_emb,
        metadata={...}
    )
```

### With search-agent

```python
# Two-stage retrieval
from src.storage import ChromaClient

client = ChromaClient()

# Stage 1: Fast retrieval
candidates = client.search_visual(query_cls, n_results=100)

# Stage 2: Re-ranking
for candidate in candidates[:20]:
    full_emb = client.get_full_embeddings(
        candidate['id'],
        collection="visual"
    )
    # Compute late interaction score
```

## Troubleshooting

### Connection Issues

```python
# Test ChromaDB connection
from src.storage import ChromaClient

try:
    client = ChromaClient(host="chromadb", port=8000)
    print("✅ Connection successful")
except ChromaDBConnectionError as e:
    print(f"❌ Connection failed: {e}")
    # Check: Is ChromaDB running? Correct host/port?
```

### Validation Errors

```python
# Check embedding shape
embeddings = np.random.randn(100, 768).astype(np.float32)
print(f"Shape: {embeddings.shape}")  # Must be (seq_length, 768)
print(f"Dtype: {embeddings.dtype}")  # Must be float type

# Ensure 2D array
if len(embeddings.shape) == 1:
    embeddings = embeddings.reshape(1, -1)
```

### Compression Limits

```python
from src.storage import estimate_compressed_size

size_mb = estimate_compressed_size(embeddings) / (1024 * 1024)
if size_mb > 2.0:
    print(f"⚠️ Compressed size ({size_mb:.2f}MB) exceeds 2MB limit")
    # Consider: Reduce sequence length or split into multiple entries
```

## License

Part of DocuSearch MVP - Internal use only

## Support

For issues or questions, contact the storage-agent team.
