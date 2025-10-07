# Storage Module Architecture

Visual overview of the ChromaDB storage layer implementation.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DocuSearch MVP - Storage Layer               │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐                              ┌──────────────────┐
│ processing-agent │                              │   search-agent    │
│                  │                              │                  │
│  - ColPali model │                              │ - Query encoding │
│  - PDF → images  │                              │ - Late interact. │
│  - Embeddings    │                              │ - Re-ranking     │
└────────┬─────────┘                              └────────┬─────────┘
         │                                                 │
         │ add_visual_embedding()                         │ search_visual()
         │ add_text_embedding()                           │ search_text()
         │                                                 │ get_full_embeddings()
         │                                                 │
         ▼                                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ChromaClient                             │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Connection Management                                  │    │
│  │  - HttpClient initialization                           │    │
│  │  - Heartbeat validation                                │    │
│  │  - Collection creation                                 │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Embedding Storage                                      │    │
│  │  - Extract CLS token → representative vector           │    │
│  │  - Compress full sequence → metadata                   │    │
│  │  - Validate shape/dtype                                │    │
│  │  - Generate ID (page###/chunk####)                     │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Search Operations                                      │    │
│  │  - Query using CLS tokens (Stage 1)                    │    │
│  │  - HNSW approximate search                             │    │
│  │  - Metadata filtering                                  │    │
│  │  - Cosine similarity scoring                           │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Retrieval Operations                                   │    │
│  │  - Decompress full embeddings (Stage 2)                │    │
│  │  - Document deletion                                   │    │
│  │  - Collection statistics                               │    │
│  └────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  CollectionManager   │
                    │                      │
                    │  - Health validation │
                    │  - Orphan cleanup    │
                    │  - Collection reset  │
                    │  - Metadata export   │
                    └──────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ChromaDB Server                             │
│                                                                  │
│  ┌──────────────────────┐          ┌──────────────────────┐    │
│  │  visual_collection   │          │  text_collection     │    │
│  │                      │          │                      │    │
│  │  - Page embeddings   │          │  - Chunk embeddings  │    │
│  │  - CLS token index   │          │  - CLS token index   │    │
│  │  - Full sequence     │          │  - Full sequence     │    │
│  │    (compressed)      │          │    (compressed)      │    │
│  └──────────────────────┘          └──────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Embedding Storage (processing-agent → storage)

```
┌─────────────┐
│  PDF Page   │
│  (Image)    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│  ColPali Model          │
│  Multi-vector output    │
│  Shape: (seq_len, 768)  │
└──────────┬──────────────┘
           │
           ▼
    ┌──────────────┐
    │ Extract CLS  │◄─── First token (768,)
    │   Token      │
    └──────┬───────┘
           │
           ▼                    ┌─────────────────┐
    ┌──────────────┐            │ Compress Full   │
    │ Store in     │            │ Sequence        │
    │ embedding    │            │ gzip + base64   │
    │ field        │            └────────┬────────┘
    └──────┬───────┘                     │
           │                             ▼
           │                      ┌──────────────┐
           │                      │ Store in     │
           │                      │ metadata     │
           │                      │ field        │
           │                      └──────┬───────┘
           │                             │
           ▼                             ▼
    ┌──────────────────────────────────────┐
    │      ChromaDB Collection              │
    │                                       │
    │  ID: doc123-page001                   │
    │  Embedding: [CLS token (768,)]        │
    │  Metadata: {                          │
    │    full_embeddings: "base64...",      │
    │    seq_length: 100,                   │
    │    embedding_shape: "(100, 768)",     │
    │    ...                                │
    │  }                                    │
    └───────────────────────────────────────┘
```

### 2. Two-Stage Retrieval (search-agent → storage)

#### Stage 1: Fast Approximate Search

```
┌────────────┐
│   Query    │
│   Image    │
└─────┬──────┘
      │
      ▼
┌──────────────────┐
│  ColPali Model   │
│  Query encoding  │
└────────┬─────────┘
         │
         ▼
  ┌──────────────┐
  │ Extract CLS  │
  │   Token      │
  └──────┬───────┘
         │
         ▼
  ┌────────────────────────┐
  │ ChromaDB HNSW Search   │
  │ Using CLS tokens       │
  │                        │
  │ Returns: Top-100       │
  │ candidates with        │
  │ similarity scores      │
  └──────────┬─────────────┘
             │
             ▼
      ┌─────────────────┐
      │  Candidates     │
      │  [              │
      │   {id, score,   │
      │    metadata},   │
      │   ...           │
      │  ]              │
      └─────────────────┘
```

#### Stage 2: Precise Re-ranking

```
┌──────────────────┐
│  Top-100         │
│  Candidates      │
└────────┬─────────┘
         │
         ▼
  ┌──────────────────────┐
  │ For top-20:          │
  │ get_full_embeddings()│
  └──────────┬───────────┘
             │
             ▼
      ┌─────────────────┐
      │ Decompress      │
      │ from metadata   │
      └─────┬───────────┘
            │
            ▼
     ┌──────────────────┐
     │ Full multi-vector│
     │ Shape: (seq, 768)│
     └─────┬────────────┘
           │
           ▼
    ┌──────────────────────┐
    │ Late Interaction     │
    │ MaxSim Scoring       │
    └──────────┬───────────┘
               │
               ▼
        ┌──────────────┐
        │ Final        │
        │ Top-20       │
        │ Results      │
        └──────────────┘
```

## Multi-Vector Storage Format

### Visual Collection Entry

```json
{
  "id": "abc123-page001",
  "embedding": [0.123, 0.456, ..., 0.789],  // CLS token (768 floats)
  "metadata": {
    "doc_id": "abc123",
    "filename": "report.pdf",
    "page": 1,
    "type": "visual",
    "full_embeddings": "H4sIAAAAAAAA/+2d...",  // base64(gzip(numpy array))
    "seq_length": 100,
    "embedding_shape": "(100, 768)",
    "timestamp": "2024-01-01T00:00:00Z",
    "source_path": "/data/report.pdf",
    "file_size": 1024000
  }
}
```

### Text Collection Entry

```json
{
  "id": "abc123-chunk0000",
  "embedding": [0.321, 0.654, ..., 0.987],  // CLS token (768 floats)
  "metadata": {
    "doc_id": "abc123",
    "filename": "report.pdf",
    "chunk_id": 0,
    "page": 1,
    "type": "text",
    "full_embeddings": "H4sIAAAAAAAA/+2d...",  // base64(gzip(numpy array))
    "seq_length": 64,
    "embedding_shape": "(64, 768)",
    "text_preview": "This is the first chunk of text...",
    "word_count": 150,
    "timestamp": "2024-01-01T00:00:00Z",
    "source_path": "/data/report.pdf"
  }
}
```

## Compression Strategy

```
Original Multi-Vector Embedding
┌─────────────────────────────────┐
│  NumPy Array                    │
│  Shape: (100, 768)              │
│  Dtype: float32                 │
│  Size: 307,200 bytes (300KB)    │
└────────────┬────────────────────┘
             │
             ▼
      ┌──────────────┐
      │  .tobytes()  │
      └──────┬───────┘
             │
             ▼
┌─────────────────────────────────┐
│  Byte Array                     │
│  Size: 307,200 bytes            │
└────────────┬────────────────────┘
             │
             ▼
      ┌──────────────┐
      │ gzip.compress│
      │ (level=6)    │
      └──────┬───────┘
             │
             ▼
┌─────────────────────────────────┐
│  Compressed Bytes               │
│  Size: ~77,000 bytes (75KB)     │
│  Ratio: 4x reduction            │
└────────────┬────────────────────┘
             │
             ▼
    ┌────────────────────┐
    │ base64.b64encode() │
    └──────┬─────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  Base64 String                  │
│  Size: ~103,000 bytes (100KB)   │
│  Storage: ChromaDB metadata     │
│  Limit: <2MB ✓                  │
└─────────────────────────────────┘
```

## Class Relationships

```
┌──────────────────────┐
│   ChromaClient       │
│                      │
│  Attributes:         │
│  - client: HttpClient│
│  - _visual_collection│
│  - _text_collection  │
│                      │
│  Methods:            │
│  - add_visual_*()    │
│  - add_text_*()      │
│  - search_visual()   │
│  - search_text()     │
│  - get_full_*()      │
│  - delete_*()        │
│  - get_stats()       │
│                      │
│  Private Methods:    │
│  - _validate_*()     │
│  - _extract_cls_*()  │
│  - _compress_*()     │
└──────────────────────┘
           │
           │ uses
           ▼
┌──────────────────────┐
│  compression.py      │
│                      │
│  - compress_*()      │
│  - decompress_*()    │
│  - estimate_size()   │
│  - compression_ratio()│
└──────────────────────┘
           │
           │ consumed by
           ▼
┌──────────────────────┐
│ CollectionManager    │
│                      │
│  Attributes:         │
│  - client            │
│                      │
│  Methods:            │
│  - validate_*()      │
│  - reset_*()         │
│  - get_orphaned_*()  │
│  - cleanup_*()       │
│  - export_*()        │
└──────────────────────┘
```

## Exception Hierarchy

```
Exception
    │
    └─── StorageError (base)
            │
            ├─── ChromaDBConnectionError
            │       └── Connection failures
            │
            ├─── EmbeddingValidationError
            │       └── Invalid shape/dtype
            │
            ├─── MetadataCompressionError
            │       └── Compression failures
            │
            └─── DocumentNotFoundError
                    └── Missing documents
```

## ID Generation Pattern

```
Document ID: "abc123" (from processing-agent)

Visual Embeddings (per page):
abc123-page001  ← Page 1
abc123-page002  ← Page 2
abc123-page003  ← Page 3
...

Text Embeddings (per chunk):
abc123-chunk0000  ← Chunk 0
abc123-chunk0001  ← Chunk 1
abc123-chunk0002  ← Chunk 2
...
```

## Search Index Structure

```
ChromaDB HNSW Index
┌─────────────────────────────────────────┐
│  Representative Vectors (CLS tokens)    │
│                                         │
│  ┌────────┐    ┌────────┐    ┌────────┐│
│  │ Node 1 │───│ Node 2 │───│ Node 3 ││
│  │(768,)  │    │(768,)  │    │(768,)  ││
│  └────────┘    └────────┘    └────────┘│
│       │             │             │     │
│       └─────────────┴─────────────┘     │
│                     │                   │
│              Hierarchical NSW           │
│              Approximate NN             │
│              < 200ms for top-100        │
└─────────────────────────────────────────┘
                     │
                     ▼
              Query Results
         ┌──────────────────────┐
         │ Top-100 candidates   │
         │ with similarity      │
         │ scores (cosine)      │
         └──────────────────────┘
```

## Performance Characteristics

### Latency Targets

| Operation | Target | Implementation |
|-----------|--------|----------------|
| Compression | <10ms | gzip level 6 |
| Decompression | <5ms | gzip decompress |
| CLS extraction | <1ms | Array slicing |
| Storage (visual) | <50ms | Compress + store |
| Storage (text) | <50ms | Compress + store |
| Search (Stage 1) | <200ms | HNSW index |
| Retrieval (Stage 2) | <20ms | Decompress |
| Document delete | <100ms | Batch delete |

### Space Efficiency

| Component | Original | Compressed | Ratio |
|-----------|----------|------------|-------|
| (100, 768) array | 307KB | 77KB | 4x |
| (50, 768) array | 153KB | 38KB | 4x |
| (200, 768) array | 614KB | 153KB | 4x |

## Module Structure

```
src/storage/
│
├── Core Implementation
│   ├── __init__.py              # Public API
│   ├── chroma_client.py         # Main client (642 lines)
│   ├── collection_manager.py    # Lifecycle mgmt (378 lines)
│   └── compression.py           # Utilities (115 lines)
│
├── Testing
│   └── test_storage.py          # Unit tests (798 lines)
│
├── Documentation
│   ├── README.md                # Usage guide
│   ├── QUICK_REFERENCE.md       # Quick reference
│   ├── ARCHITECTURE.md          # This file
│   ├── CONTRACT_VALIDATION.md   # Compliance check
│   └── IMPLEMENTATION_SUMMARY.md # Summary
│
└── Configuration
    └── requirements.txt         # Dependencies
```

## Integration Points

### Input (from processing-agent)

```python
# After ColPali generates embeddings
visual_embeddings: List[np.ndarray]  # [(seq_len, 768), ...]
text_embeddings: List[np.ndarray]    # [(seq_len, 768), ...]

# Storage
client = ChromaClient()
for page, emb in enumerate(visual_embeddings, 1):
    client.add_visual_embedding(doc_id, page, emb, {...})

for chunk, emb in enumerate(text_embeddings):
    client.add_text_embedding(doc_id, chunk, emb, {...})
```

### Output (to search-agent)

```python
# Stage 1: Fast retrieval
candidates = client.search_visual(query_cls, n_results=100)
# Returns: [{"id": "...", "score": 0.85, "metadata": {...}}, ...]

# Stage 2: Re-ranking
for candidate in candidates[:20]:
    full_emb = client.get_full_embeddings(candidate['id'], "visual")
    # Returns: np.ndarray (seq_len, 768)
    # Use for late interaction MaxSim scoring
```

---

**Architecture Status**: Production Ready ✅
**Integration Points**: Well-defined ✅
**Performance Targets**: Achievable ✅
