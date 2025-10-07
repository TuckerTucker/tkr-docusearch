# Storage Module - Quick Reference

One-page reference for DocuSearch storage operations.

## Import

```python
from src.storage import ChromaClient, CollectionManager
```

## Initialize

```python
# Basic
client = ChromaClient()

# Custom
client = ChromaClient(
    host="chromadb",
    port=8000,
    visual_collection="visual_collection",
    text_collection="text_collection"
)
```

## Store Embeddings

### Visual (Page-Level)

```python
embedding_id = client.add_visual_embedding(
    doc_id="abc123",
    page=1,  # 1-indexed
    full_embeddings=np.ndarray(shape=(seq_len, 768)),
    metadata={
        "filename": "report.pdf",
        "source_path": "/data/report.pdf",
        "file_size": 1024000
    }
)
# Returns: "abc123-page001"
```

### Text (Chunk-Level)

```python
embedding_id = client.add_text_embedding(
    doc_id="abc123",
    chunk_id=0,  # 0-indexed
    full_embeddings=np.ndarray(shape=(seq_len, 768)),
    metadata={
        "filename": "report.pdf",
        "page": 1,
        "source_path": "/data/report.pdf",
        "text_preview": "First 200 chars...",
        "word_count": 150
    }
)
# Returns: "abc123-chunk0000"
```

## Search

### Stage 1: Fast Retrieval

```python
# Visual search
candidates = client.search_visual(
    query_embedding=np.ndarray(shape=(768,)),  # CLS token
    n_results=100,
    filters={"filename": "report.pdf"}  # Optional
)

# Text search
candidates = client.search_text(
    query_embedding=np.ndarray(shape=(768,)),
    n_results=100
)

# Result format:
# [
#     {
#         "id": "abc123-page001",
#         "score": 0.85,  # 0-1
#         "metadata": {...},
#         "representative_vector": [...]
#     },
#     ...
# ]
```

### Stage 2: Re-ranking

```python
for candidate in candidates[:20]:  # Top-20
    full_embeddings = client.get_full_embeddings(
        embedding_id=candidate['id'],
        collection="visual"  # or "text"
    )
    # Returns: np.ndarray(shape=(seq_len, 768))
    # Use for late interaction scoring
```

## Delete

```python
visual_count, text_count = client.delete_document("abc123")
# Deletes all embeddings for doc
```

## Statistics

```python
stats = client.get_collection_stats()
# {
#     "visual_count": 100,
#     "text_count": 300,
#     "total_documents": 10,
#     "storage_size_mb": 40.5
# }
```

## Collection Management

```python
manager = CollectionManager(client)

# Health check
report = manager.validate_collections()
# {"status": "healthy|degraded|unhealthy", ...}

# List documents
docs = manager.get_document_list(limit=10)
# [{"doc_id": "...", "filename": "...", ...}, ...]

# Find orphans
orphans = manager.get_orphaned_embeddings()
# {"visual_orphans": [...], "text_orphans": [...], "count": N}

# Cleanup (REQUIRES CONFIRMATION)
report = manager.cleanup_orphaned_embeddings(confirm=True)

# Reset (REQUIRES CONFIRMATION)
report = manager.reset_collection("visual", confirm=True)

# Export metadata
export = manager.export_collection_metadata(collection="all")
```

## Error Handling

```python
from src.storage import (
    StorageError,
    ChromaDBConnectionError,
    EmbeddingValidationError,
    MetadataCompressionError,
    DocumentNotFoundError,
)

try:
    client = ChromaClient(host="chromadb", port=8000)
except ChromaDBConnectionError:
    # Handle connection failure
    pass

try:
    client.add_visual_embedding(...)
except EmbeddingValidationError:
    # Handle invalid shape/dtype
    pass
except MetadataCompressionError:
    # Handle compression failure
    pass

try:
    full_emb = client.get_full_embeddings("id", "visual")
except DocumentNotFoundError:
    # Handle missing document
    pass
```

## Validation Rules

- **Shape**: Must be `(seq_length, 768)` where `seq_length > 0`
- **Dtype**: Must be float (float32, float16, or float64)
- **Size**: Compressed must be <2MB
- **Required metadata**: filename, source_path, doc_id, type, timestamp

## Environment Variables

```bash
export CHROMA_HOST=chromadb
export CHROMA_PORT=8001
export VISUAL_COLLECTION=visual_collection
export TEXT_COLLECTION=text_collection
```

## Common Patterns

### Full Document Storage

```python
doc_id = "abc123"

# Visual embeddings (per page)
for page_num, emb in enumerate(visual_embeddings, 1):
    client.add_visual_embedding(doc_id, page_num, emb, {...})

# Text embeddings (per chunk)
for chunk_id, emb in enumerate(text_embeddings):
    client.add_text_embedding(doc_id, chunk_id, emb, {...})
```

### Hybrid Search

```python
# Search both collections
visual_results = client.search_visual(query, n_results=50)
text_results = client.search_text(query, n_results=50)

# Combine and re-rank
all_candidates = visual_results + text_results
top_candidates = sorted(all_candidates, key=lambda x: x['score'], reverse=True)[:20]

# Get full embeddings for top candidates
for candidate in top_candidates:
    col = "visual" if "page" in candidate['id'] else "text"
    full_emb = client.get_full_embeddings(candidate['id'], col)
    # Re-rank with late interaction
```

### Filtered Search

```python
# By filename
results = client.search_visual(
    query,
    filters={"filename": "report.pdf"}
)

# By doc_id
results = client.search_visual(
    query,
    filters={"doc_id": "abc123"}
)

# By type (automatically filtered by collection)
results = client.search_visual(query)  # Only visual
results = client.search_text(query)    # Only text
```

## Testing

```bash
# Run all tests
pytest src/storage/test_storage.py -v

# With coverage
pytest src/storage/test_storage.py -v --cov=src/storage

# Specific test
pytest src/storage/test_storage.py::TestCompression -v
```

## Troubleshooting

### Connection Failed
```python
# Check ChromaDB is running
docker ps | grep chroma

# Test connection
from src.storage import ChromaClient
try:
    client = ChromaClient(host="chromadb", port=8000)
    print("✅ Connected")
except Exception as e:
    print(f"❌ Failed: {e}")
```

### Invalid Shape
```python
# Ensure 2D array
if len(embeddings.shape) == 1:
    embeddings = embeddings.reshape(1, -1)

# Check dimension
assert embeddings.shape[1] == 768, f"Expected dim=768, got {embeddings.shape[1]}"
```

### Compression Too Large
```python
from src.storage import estimate_compressed_size

size_mb = estimate_compressed_size(embeddings) / (1024 * 1024)
if size_mb > 2.0:
    # Reduce sequence length or split into multiple entries
    pass
```

## Performance Tips

1. **Batch operations**: Store multiple embeddings in sequence
2. **Use filters**: Narrow search space with metadata filters
3. **Limit results**: Request only needed candidates (e.g., n_results=100)
4. **Cache clients**: Reuse ChromaClient instance across operations

## Files

- `chroma_client.py` - Main client
- `collection_manager.py` - Lifecycle management
- `compression.py` - Compression utilities
- `test_storage.py` - Unit tests
- `README.md` - Full documentation

---

**Quick Start**: `from src.storage import ChromaClient; client = ChromaClient()`
