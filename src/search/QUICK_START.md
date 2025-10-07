# Search Module - Quick Start Guide

## Installation (Wave 2 - Mocks Only)

No dependencies needed! Pure Python with NumPy.

```bash
# Validate installation
python3 src/search/validate_search.py
```

## Basic Usage

```python
from src.search import SearchEngine
from src.search.mocks import MockEmbeddingEngine, MockStorageClient

# Initialize
engine = SearchEngine(
    storage_client=MockStorageClient(),
    embedding_engine=MockEmbeddingEngine()
)

# Search
response = engine.search(
    query="quarterly revenue growth",
    n_results=10
)

# Results
for r in response["results"]:
    print(f"{r['filename']} p.{r['page']}: {r['score']:.3f}")
```

## Search Modes

```python
# Hybrid (default)
engine.search(query="revenue", search_mode="hybrid")

# Visual only
engine.search(query="chart", search_mode="visual_only")

# Text only
engine.search(query="contract", search_mode="text_only")
```

## Filtering

```python
# By filename
engine.search(
    query="revenue",
    filters={"filename": "Q3-2023-Earnings.pdf"}
)

# By page range
engine.search(
    query="summary",
    filters={"page_range": {"min": 1, "max": 5}}
)
```

## Control Re-ranking

```python
# With Stage 2 (default)
engine.search(query="test", enable_reranking=True)

# Without Stage 2 (faster)
engine.search(query="test", enable_reranking=False)
```

## Response Format

```python
{
    "results": [
        {
            "id": "doc1-page003",
            "doc_id": "doc1",
            "type": "text",
            "score": 0.94,
            "filename": "Q3-2023-Earnings.pdf",
            "page": 3,
            "text_preview": "Revenue growth...",
            # ... more fields
        }
    ],
    "total_time_ms": 13.5,
    "stage1_time_ms": 1.6,
    "stage2_time_ms": 11.5,
    # ... more metadata
}
```

## Statistics

```python
# Get performance stats
stats = engine.get_search_stats()
print(f"Total queries: {stats['total_queries']}")
print(f"Avg time: {stats['avg_total_ms']:.1f}ms")
```

## Testing

```bash
# Validation
python3 src/search/validate_search.py

# Unit tests (requires pytest)
pytest src/search/test_search.py -v
```

## Error Handling

```python
from src.search import SearchError

try:
    response = engine.search(query="")
except ValueError as e:
    print(f"Invalid query: {e}")
except SearchError as e:
    print(f"Search failed: {e}")
```

## Mock Data

MockStorageClient provides:
- 5 documents (Q3-2023-Earnings.pdf, Product-Roadmap.pdf, etc.)
- 15 visual embeddings (3 pages per doc)
- 50 text embeddings (10 chunks per doc)

## Performance

Wave 2 (Mocks): ~15-25ms total
Wave 3 (Real): ~200-300ms expected

## Documentation

- Full API: `src/search/README.md`
- Summary: `SEARCH_AGENT_SUMMARY.md`
- Contracts: `.context-kit/orchestration/docusearch-mvp/integration-contracts/`

## Wave 3 Migration

Just swap dependencies:

```python
# Wave 2
from src.search.mocks import MockEmbeddingEngine, MockStorageClient

# Wave 3
from src.embedding import ColPaliEngine
from src.storage import ChromaClient
```

No code changes needed!
