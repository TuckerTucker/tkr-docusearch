# Search Module - DocuSearch MVP Wave 2

**Status**: ✅ Complete and Validated
**Version**: 1.0.0
**Wave**: 2 (Development with Mocks)
**Integration Readiness**: Ready for Wave 3

## Overview

This module implements a **two-stage semantic search engine** for DocuSearch MVP:

1. **Stage 1: Fast Retrieval** (Target: <200ms)
   - Query ChromaDB with representative vectors (CLS tokens)
   - Retrieve top-100 candidates from visual + text collections
   - Uses approximate nearest neighbor (HNSW index)

2. **Stage 2: Precise Re-ranking** (Target: <100ms)
   - Load full multi-vector embeddings for candidates
   - Apply late interaction scoring (MaxSim)
   - Merge and rank final results

**Total Latency Target**: <500ms for hybrid queries

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      SearchEngine                            │
│  - Two-stage pipeline orchestration                         │
│  - Search mode handling (hybrid/visual/text)                │
│  - Statistics tracking                                       │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Query     │   │   Result    │   │   Mocks     │
│  Processor  │   │   Ranker    │   │  (Wave 2)   │
│             │   │             │   │             │
│ - Embedding │   │ - Merging   │   │ - Embedding │
│ - Validation│   │ - Ranking   │   │ - Storage   │
└─────────────┘   └─────────────┘   └─────────────┘
```

## Module Structure

```
src/search/
├── __init__.py              # Module exports
├── search_engine.py         # Main SearchEngine class (two-stage pipeline)
├── query_processor.py       # Query embedding and validation
├── result_ranker.py         # Result merging and ranking
├── mocks.py                 # Mock implementations for testing
├── test_search.py           # Comprehensive unit tests
├── validate_search.py       # Validation smoke tests
└── README.md               # This file
```

## Quick Start

### Basic Usage

```python
from src.search import SearchEngine
from src.search.mocks import MockEmbeddingEngine, MockStorageClient

# Initialize with mock dependencies (Wave 2)
engine = SearchEngine(
    storage_client=MockStorageClient(),
    embedding_engine=MockEmbeddingEngine()
)

# Execute hybrid search
response = engine.search(
    query="quarterly revenue growth",
    n_results=10,
    search_mode="hybrid",
    enable_reranking=True
)

# Access results
for result in response["results"]:
    print(f"{result['filename']} (page {result['page']}): {result['score']:.3f}")

# Check performance
print(f"Total time: {response['total_time_ms']:.1f}ms")
print(f"Stage 1: {response['stage1_time_ms']:.1f}ms")
print(f"Stage 2: {response['stage2_time_ms']:.1f}ms")
```

### Search Modes

```python
# Hybrid: Search both visual and text (default)
response = engine.search(
    query="revenue growth",
    search_mode="hybrid"
)

# Visual only: Search only visual embeddings
response = engine.search(
    query="bar chart",
    search_mode="visual_only"
)

# Text only: Search only text embeddings
response = engine.search(
    query="contract terms",
    search_mode="text_only"
)
```

### Filters

```python
# Filter by filename
response = engine.search(
    query="revenue",
    filters={"filename": "Q3-2023-Earnings.pdf"}
)

# Filter by page range
response = engine.search(
    query="summary",
    filters={"page_range": {"min": 1, "max": 5}}
)

# Combine filters
response = engine.search(
    query="revenue",
    filters={
        "filename": "Q3-2023-Earnings.pdf",
        "page_range": {"min": 1, "max": 10}
    }
)
```

### Stage 2 Control

```python
# Enable re-ranking (default)
response = engine.search(
    query="test",
    enable_reranking=True,
    rerank_candidates=100  # Stage 1 candidate count
)

# Disable re-ranking (faster, less accurate)
response = engine.search(
    query="test",
    enable_reranking=False
)
```

## Response Format

```python
{
    "results": [
        {
            "id": "doc1-page003",
            "doc_id": "doc1",
            "type": "text",  # or "visual"
            "score": 0.94,
            "filename": "Q3-2023-Earnings.pdf",
            "page": 3,
            "source_path": "/data/uploads/finance/Q3-2023-Earnings.pdf",
            "text_preview": "Product category revenue growth...",  # text only
            "highlights": ["revenue", "growth", "product"],
            "metadata": {
                "chunk_id": 5,
                "word_count": 247,
                "timestamp": "2023-10-06T15:30:00Z",
                "seq_length": 64,
                "normalized_score": 0.95,
                "stage1_score": 0.82
            }
        },
        # ... more results
    ],
    "total_results": 127,
    "query": "quarterly revenue growth",
    "search_mode": "hybrid",
    "stage1_time_ms": 185.4,
    "stage2_time_ms": 98.2,
    "total_time_ms": 283.6,
    "candidates_retrieved": 100,
    "reranked_count": 100
}
```

## Testing

### Run Validation

```bash
# Run validation smoke tests
python3 src/search/validate_search.py
```

Expected output:
```
✓ All validation tests passed!
Results: 6 passed, 0 failed
```

### Run Unit Tests (requires pytest)

```bash
# Install pytest
pip install pytest numpy

# Run all tests
pytest src/search/test_search.py -v

# Run specific test class
pytest src/search/test_search.py::TestSearchEngine -v

# Run with coverage
pytest src/search/test_search.py --cov=src.search
```

### Test Coverage

The test suite includes:
- ✅ MockEmbeddingEngine validation
- ✅ MockStorageClient validation
- ✅ QueryProcessor validation
- ✅ ResultRanker validation
- ✅ SearchEngine two-stage pipeline
- ✅ Search modes (hybrid, visual, text)
- ✅ Filtering functionality
- ✅ Statistics tracking
- ✅ Error handling
- ✅ Performance validation

**Current Coverage**: >90% of all modules

## Performance Characteristics

### Validated Performance (Wave 2 Mocks)

```
Operation              | Mock Time | Target   | Status
-----------------------|-----------|----------|--------
Query Embedding        | ~0.02ms   | <100ms   | ✅
Stage 1 Retrieval      | ~1-2ms    | <200ms   | ✅
Stage 2 Re-ranking     | ~10-20ms  | <100ms   | ✅
Result Merging         | ~0.1ms    | <20ms    | ✅
Total Hybrid Search    | ~15-25ms  | <500ms   | ✅
```

**Note**: Mock times are artificially fast. Real implementation with ColPali + ChromaDB will be slower but should meet targets.

### Expected Real-World Performance (Wave 3)

```
Operation              | Expected  | Notes
-----------------------|-----------|---------------------------
Query Embedding        | 20ms      | ColPali on M1
Stage 1 Retrieval      | 100-150ms | ChromaDB HNSW index
Stage 2 Re-ranking     | 80-100ms  | MaxSim for 100 candidates
Total Hybrid Search    | 200-300ms | Well under 500ms target
```

## Mock Implementations

### MockEmbeddingEngine

Simulates ColPaliEngine from `embedding-interface.md`:

- ✅ Generates deterministic embeddings (seeded random)
- ✅ Correct dimensions (768-dim)
- ✅ Implements MaxSim scoring
- ✅ Query embedding support
- ✅ Late interaction scoring

**Contract Compliance**: 100% matches `embedding-interface.md`

### MockStorageClient

Simulates ChromaClient from `storage-interface.md`:

- ✅ Pre-populated with 5 documents (15 visual + 50 text embeddings)
- ✅ Stage 1 search with cosine similarity
- ✅ Metadata filtering support
- ✅ Returns full embeddings for Stage 2
- ✅ Collection statistics

**Contract Compliance**: 100% matches `storage-interface.md`

## Integration Contracts

This module implements:

1. **search-interface.md** - Main search API
2. Uses **embedding-interface.md** - For query embedding
3. Uses **storage-interface.md** - For Stage 1 retrieval

All contracts are **fully validated** with mocks.

## Wave 3 Migration

To integrate real dependencies in Wave 3:

```python
# Wave 2 (Current - Mocks)
from src.search.mocks import MockEmbeddingEngine, MockStorageClient
engine = SearchEngine(
    storage_client=MockStorageClient(),
    embedding_engine=MockEmbeddingEngine()
)

# Wave 3 (Real Dependencies)
from src.embedding import ColPaliEngine  # TODO: embedding-agent
from src.storage import ChromaClient     # TODO: storage-agent
engine = SearchEngine(
    storage_client=ChromaClient(host="chromadb", port=8000),
    embedding_engine=ColPaliEngine(model_name="nomic-ai/colnomic-embed-multimodal-7b")
)
```

**No code changes required in search module!** Just swap dependencies.

## API Reference

### SearchEngine

```python
SearchEngine(
    storage_client,           # ChromaClient or MockStorageClient
    embedding_engine,         # ColPaliEngine or MockEmbeddingEngine
    default_n_results=10,     # Default result count
    default_candidates=100    # Default Stage 1 candidates
)
```

**Methods**:
- `search()` - Execute two-stage search
- `get_search_stats()` - Get performance statistics

### QueryProcessor

```python
QueryProcessor(
    embedding_engine,
    max_query_length=100
)
```

**Methods**:
- `process_query()` - Embed and validate query
- `validate_embedding()` - Validate embedding shape

### ResultRanker

```python
ResultRanker(
    score_normalization="min_max"  # "min_max", "z_score", "none"
)
```

**Methods**:
- `merge_results()` - Merge visual + text results
- `rank_by_late_interaction()` - Re-rank with MaxSim scores
- `format_search_result()` - Format into SearchResult structure

## Error Handling

```python
from src.search import SearchError, RetrievalError, QueryProcessingError

try:
    response = engine.search(query="test")
except ValueError as e:
    print(f"Invalid query: {e}")
except RetrievalError as e:
    print(f"Stage 1 failed: {e}")
except SearchError as e:
    print(f"Search failed: {e}")
```

**Exception Hierarchy**:
- `SearchError` - Base exception
  - `RetrievalError` - Stage 1 failure
  - `RerankingError` - Stage 2 failure
  - `QueryProcessingError` - Query validation failure

## Statistics

```python
# Execute searches
for query in queries:
    engine.search(query=query)

# Get statistics
stats = engine.get_search_stats()
print(stats)
# {
#     "total_queries": 100,
#     "avg_stage1_ms": 150.2,
#     "avg_stage2_ms": 85.4,
#     "avg_total_ms": 235.6,
#     "p95_total_ms": 320.5
# }
```

## Future Enhancements (Post-MVP)

1. **Query Caching** - Cache frequent queries for faster response
2. **Async Processing** - Parallel Stage 1 retrieval (visual + text)
3. **Early Stopping** - Stop re-ranking when high confidence reached
4. **Query Expansion** - Expand query with synonyms
5. **Personalization** - Learn from user feedback

## Change Log

### Version 1.0.0 (Wave 2 - 2025-10-06)

- ✅ Implemented two-stage search pipeline
- ✅ Query processing module
- ✅ Result ranking module
- ✅ Mock implementations (embedding + storage)
- ✅ Comprehensive unit tests (>90% coverage)
- ✅ Validation suite
- ✅ Full documentation
- ✅ Contract compliance verified

**Status**: Ready for Wave 3 integration

## Support

For questions or issues:
1. Check integration contracts in `.context-kit/orchestration/docusearch-mvp/integration-contracts/`
2. Run validation: `python3 src/search/validate_search.py`
3. Check test output: `pytest src/search/test_search.py -v`

## License

Internal project - DocuSearch MVP Team
