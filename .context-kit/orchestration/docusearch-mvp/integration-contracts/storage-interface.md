# Storage Interface Contract

**Owner**: storage-agent
**Consumers**: processing-agent, search-agent
**Purpose**: Define ChromaDB client interface for multi-vector embedding storage and retrieval

---

## ChromaDB Collection Schema

### Collections

Two collections are maintained:

1. **`visual_collection`** - Stores page-level visual embeddings
2. **`text_collection`** - Stores chunk-level text embeddings

### Multi-Vector Storage Format

Each document (page or chunk) is stored with:

1. **Representative Vector** (ChromaDB embedding field)
   - Type: `List[float]`
   - Shape: `(768,)`
   - Source: CLS token (first token) from multi-vector sequence
   - Purpose: Fast approximate search using ChromaDB's HNSW index

2. **Full Multi-Vector Sequence** (ChromaDB metadata field)
   - Type: `str` (base64-encoded numpy array)
   - Original shape: `(seq_length, 768)` where seq_length varies
   - Compression: gzip before base64 encoding (4x size reduction)
   - Purpose: Precise late interaction re-ranking

---

## Data Structures

### Metadata Schema

```python
# Visual collection metadata
{
    "filename": str,                    # "Q3-2023-Earnings.pdf"
    "page": int,                        # 1-indexed page number
    "doc_id": str,                      # Unique document identifier
    "type": "visual",                   # Literal type indicator
    "full_embeddings": str,             # base64(gzip(numpy_array))
    "seq_length": int,                  # Number of tokens (avg: 100)
    "embedding_shape": str,             # "(100, 768)" for validation
    "timestamp": str,                   # ISO 8601 upload time
    "source_path": str,                 # "/data/uploads/finance/Q3-2023-Earnings.pdf"
    "file_size": int,                   # Bytes
}

# Text collection metadata
{
    "filename": str,                    # Same as visual
    "chunk_id": int,                    # 0-indexed chunk number
    "page": int,                        # Source page number
    "doc_id": str,                      # Same as visual (links collections)
    "type": "text",                     # Literal type indicator
    "full_embeddings": str,             # base64(gzip(numpy_array))
    "seq_length": int,                  # Number of tokens (avg: 64)
    "embedding_shape": str,             # "(64, 768)" for validation
    "text_preview": str,                # First 200 chars of chunk
    "word_count": int,                  # Chunk word count
    "timestamp": str,                   # ISO 8601 upload time
    "source_path": str,                 # Same as visual
}
```

### ID Generation

IDs follow consistent format for traceability:

```python
# Visual embeddings
visual_id = f"{doc_id}-page{page:03d}"
# Example: "a1b2c3d4-page001"

# Text embeddings
text_id = f"{doc_id}-chunk{chunk_id:04d}"
# Example: "a1b2c3d4-chunk0000"
```

---

## API Interface

### ChromaClient Class

```python
from typing import List, Dict, Any, Tuple
import numpy as np

class ChromaClient:
    """ChromaDB client wrapper with multi-vector storage support."""

    def __init__(
        self,
        host: str = "chromadb",
        port: int = 8000,
        visual_collection: str = "visual_collection",
        text_collection: str = "text_collection"
    ):
        """
        Initialize ChromaDB client and create collections if needed.

        Args:
            host: ChromaDB server host
            port: ChromaDB server port
            visual_collection: Name of visual embeddings collection
            text_collection: Name of text embeddings collection
        """
        pass

    def add_visual_embedding(
        self,
        doc_id: str,
        page: int,
        full_embeddings: np.ndarray,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Store visual embedding for a document page.

        Args:
            doc_id: Unique document identifier
            page: Page number (1-indexed)
            full_embeddings: Multi-vector sequence, shape (seq_length, 768)
            metadata: Additional metadata (filename, source_path, etc.)

        Returns:
            Embedding ID: "{doc_id}-page{page:03d}"

        Raises:
            ValueError: If embedding shape is invalid
            ChromaDBError: If storage fails
        """
        pass

    def add_text_embedding(
        self,
        doc_id: str,
        chunk_id: int,
        full_embeddings: np.ndarray,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Store text embedding for a document chunk.

        Args:
            doc_id: Unique document identifier (same as visual)
            chunk_id: Chunk number (0-indexed)
            full_embeddings: Multi-vector sequence, shape (seq_length, 768)
            metadata: Additional metadata (text_preview, word_count, etc.)

        Returns:
            Embedding ID: "{doc_id}-chunk{chunk_id:04d}"

        Raises:
            ValueError: If embedding shape is invalid
            ChromaDBError: If storage fails
        """
        pass

    def search_visual(
        self,
        query_embedding: np.ndarray,
        n_results: int = 100,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Stage 1 search: Fast retrieval using representative vectors.

        Args:
            query_embedding: Query embedding CLS token, shape (768,)
            n_results: Number of candidates to retrieve
            filters: Optional metadata filters (e.g., {"filename": "report.pdf"})

        Returns:
            List of candidates with:
            {
                "id": str,
                "score": float,              # Cosine similarity (0-1)
                "metadata": Dict[str, Any],  # Includes full_embeddings
                "representative_vector": List[float]
            }

        Raises:
            ChromaDBError: If query fails
        """
        pass

    def search_text(
        self,
        query_embedding: np.ndarray,
        n_results: int = 100,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Stage 1 search: Fast retrieval using representative vectors.

        Same interface as search_visual but queries text_collection.
        """
        pass

    def get_full_embeddings(
        self,
        embedding_id: str,
        collection: str = "visual"
    ) -> np.ndarray:
        """
        Retrieve full multi-vector sequence for re-ranking.

        Args:
            embedding_id: ID returned from search
            collection: "visual" or "text"

        Returns:
            Decompressed numpy array, shape (seq_length, 768)

        Raises:
            ValueError: If embedding_id not found
            DecompressionError: If metadata corrupted
        """
        pass

    def delete_document(
        self,
        doc_id: str
    ) -> Tuple[int, int]:
        """
        Delete all embeddings for a document.

        Args:
            doc_id: Document identifier

        Returns:
            Tuple of (visual_count, text_count) deleted
        """
        pass

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics.

        Returns:
            {
                "visual_count": int,
                "text_count": int,
                "total_documents": int,  # Unique doc_ids
                "storage_size_mb": float
            }
        """
        pass
```

---

## Compression Algorithm

**Multi-Vector Compression** (used to fit in ChromaDB metadata limits)

```python
import numpy as np
import gzip
import base64

def compress_embeddings(embeddings: np.ndarray) -> str:
    """
    Compress multi-vector embeddings for metadata storage.

    Args:
        embeddings: Shape (seq_length, 768), dtype float32

    Returns:
        Base64-encoded gzipped bytes

    Example:
        Input: (100, 768) array = 307KB
        After gzip: 77KB (4x compression)
        After base64: 103KB (storage size)
    """
    bytes_array = embeddings.astype(np.float32).tobytes()
    compressed = gzip.compress(bytes_array, compresslevel=6)
    encoded = base64.b64encode(compressed).decode('utf-8')
    return encoded

def decompress_embeddings(encoded: str, shape: Tuple[int, int]) -> np.ndarray:
    """
    Decompress embeddings from metadata.

    Args:
        encoded: Base64-encoded gzipped bytes
        shape: Original array shape (seq_length, 768)

    Returns:
        Numpy array with original shape
    """
    compressed = base64.b64decode(encoded.encode('utf-8'))
    bytes_array = gzip.decompress(compressed)
    embeddings = np.frombuffer(bytes_array, dtype=np.float32)
    return embeddings.reshape(shape)
```

---

## Error Handling

### Exception Types

```python
class StorageError(Exception):
    """Base exception for storage operations."""
    pass

class ChromaDBConnectionError(StorageError):
    """Cannot connect to ChromaDB server."""
    pass

class EmbeddingValidationError(StorageError):
    """Invalid embedding shape or dtype."""
    pass

class MetadataCompressionError(StorageError):
    """Failed to compress or decompress embeddings."""
    pass

class DocumentNotFoundError(StorageError):
    """Document ID not found in collections."""
    pass
```

### Validation Rules

1. **Embedding Shape**: Must be (seq_length, 768) where seq_length > 0
2. **Dtype**: Must be float32 or float16 (converted to float32 for storage)
3. **Metadata Size**: Compressed embeddings must be <2MB (ChromaDB limit)
4. **Required Fields**: filename, doc_id, type, timestamp, source_path

---

## Performance Targets

| Operation | Target Latency | Notes |
|-----------|----------------|-------|
| `add_visual_embedding` | <50ms | Includes compression |
| `add_text_embedding` | <50ms | Includes compression |
| `search_visual` | <200ms | Top-100 retrieval |
| `search_text` | <200ms | Top-100 retrieval |
| `get_full_embeddings` | <20ms | Decompression only |
| `delete_document` | <100ms | Deletes from both collections |

**Batch Operations** (optional optimization for Wave 4):
- `add_batch_visual`: Process 10 pages in <300ms
- `add_batch_text`: Process 50 chunks in <500ms

---

## Unit Test Requirements

storage-agent must provide unit tests covering:

1. **Collection Initialization**
   - Create collections if not exist
   - Handle existing collections gracefully

2. **Embedding Storage**
   - Store visual embedding with valid metadata
   - Store text embedding with valid metadata
   - Validate embedding shape enforcement
   - Test compression/decompression round-trip

3. **Search Operations**
   - Retrieve top-k candidates with correct scores
   - Apply metadata filters correctly
   - Handle empty result sets

4. **Error Cases**
   - Invalid embedding shapes raise EmbeddingValidationError
   - Missing metadata fields raise ValidationError
   - ChromaDB connection failures raise ChromaDBConnectionError

5. **Compression**
   - Compression reduces size by 4x
   - Decompression restores original values (within float32 precision)
   - Handle edge cases (very short sequences, very long sequences)

---

## Integration Test Requirements

processing-agent and search-agent must validate:

1. **End-to-End Storage**
   - Store 10 visual + 30 text embeddings for a sample PDF
   - Verify all embeddings retrievable by doc_id
   - Check metadata accuracy

2. **Search Accuracy**
   - Query with known embedding returns correct document
   - Top-k candidates sorted by similarity score
   - Filters work correctly (e.g., filter by filename)

3. **Full Sequence Retrieval**
   - Decompress embeddings for top-100 candidates in <2s
   - Late interaction scoring uses correct embeddings

---

## Migration Notes

If storage format changes in future:

1. Add version field to metadata: `"storage_version": "1.0"`
2. Implement migration script to re-compress existing embeddings
3. Support reading old format during transition period
4. Update contract document with version history

Current version: **1.0** (initial multi-vector storage)
