# Search Interface Contract

**Owner**: search-agent
**Consumers**: ui-agent
**Purpose**: Define two-stage search API for hybrid visual + text semantic search

---

## Search Architecture

### Two-Stage Pipeline

**Stage 1: Fast Retrieval** (200ms)
- Query ChromaDB with representative vectors (CLS tokens)
- Retrieve top-100 candidates from each collection (visual + text)
- Uses approximate nearest neighbor (HNSW index)

**Stage 2: Precise Re-ranking** (100ms)
- Load full multi-vector embeddings for top candidates
- Apply late interaction scoring (MaxSim)
- Merge and rank final results

**Total Latency Target**: <500ms for hybrid queries

---

## Data Structures

### Query Request

```python
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime

class SearchQuery(TypedDict):
    """Search query request."""
    query: str                           # Natural language query
    n_results: int                       # Number of results to return (default: 10)
    search_mode: Literal[                # Search mode
        "hybrid",                        # Both visual + text (default)
        "visual_only",                   # Visual embeddings only
        "text_only"                      # Text embeddings only
    ]
    filters: Optional[Dict[str, Any]]    # Metadata filters
    enable_reranking: bool               # Enable Stage 2 (default: True)
    rerank_candidates: int               # Candidates for Stage 2 (default: 100)

# Example
{
    "query": "quarterly revenue growth by product category",
    "n_results": 10,
    "search_mode": "hybrid",
    "filters": {
        "filename": "Q3-2023-Earnings.pdf",  # Optional: filter by document
        "date_range": {                       # Optional: filter by upload date
            "start": "2023-01-01",
            "end": "2023-12-31"
        }
    },
    "enable_reranking": True,
    "rerank_candidates": 100
}
```

### Search Result

```python
class SearchResult(TypedDict):
    """Single search result."""
    id: str                              # Embedding ID (e.g., "doc123-page002")
    doc_id: str                          # Document identifier
    type: Literal["visual", "text"]      # Result type
    score: float                         # Relevance score (0-1, higher = better)
    filename: str                        # Source filename
    page: int                            # Page number (1-indexed)
    source_path: str                     # Full path to source file
    thumbnail_url: Optional[str]         # URL to page thumbnail (visual only)
    text_preview: Optional[str]          # Text snippet (text only)
    highlights: List[str]                # Matching terms or phrases
    metadata: Dict[str, Any]             # Additional metadata

# Example
{
    "id": "a1b2c3d4-page003",
    "doc_id": "a1b2c3d4",
    "type": "text",
    "score": 0.94,
    "filename": "Q3-2023-Earnings.pdf",
    "page": 3,
    "source_path": "/data/uploads/finance/Q3-2023-Earnings.pdf",
    "thumbnail_url": "/api/thumbnail/a1b2c3d4-page003",
    "text_preview": "Product category revenue growth: Software products increased 24% year-over-year...",
    "highlights": ["revenue", "growth", "product category"],
    "metadata": {
        "chunk_id": 5,
        "word_count": 247,
        "timestamp": "2023-10-06T15:30:00Z"
    }
}
```

### Search Response

```python
class SearchResponse(TypedDict):
    """Complete search response."""
    results: List[SearchResult]          # Ranked results
    total_results: int                   # Total matching documents
    query: str                           # Original query
    search_mode: str                     # Mode used
    stage1_time_ms: float                # Stage 1 latency
    stage2_time_ms: float                # Stage 2 latency (if enabled)
    total_time_ms: float                 # Total search time
    candidates_retrieved: int            # Stage 1 candidates
    reranked_count: int                  # Stage 2 count (if enabled)

# Example
{
    "results": [...],  # List of SearchResult
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

---

## API Interface

### SearchEngine Class

```python
from typing import List, Dict, Any, Optional

class SearchEngine:
    """Two-stage semantic search engine."""

    def __init__(
        self,
        storage_client,      # ChromaClient instance
        embedding_engine,    # ColPaliEngine instance
        default_n_results: int = 10,
        default_candidates: int = 100
    ):
        """
        Initialize search engine.

        Args:
            storage_client: ChromaDB client for retrieval
            embedding_engine: ColPali engine for query embedding and scoring
            default_n_results: Default number of results to return
            default_candidates: Default Stage 1 candidates
        """
        pass

    def search(
        self,
        query: str,
        n_results: int = None,
        search_mode: str = "hybrid",
        filters: Optional[Dict[str, Any]] = None,
        enable_reranking: bool = True,
        rerank_candidates: int = None
    ) -> SearchResponse:
        """
        Execute two-stage semantic search.

        Args:
            query: Natural language search query
            n_results: Number of final results (default: self.default_n_results)
            search_mode: "hybrid", "visual_only", or "text_only"
            filters: Metadata filters (e.g., {"filename": "report.pdf"})
            enable_reranking: Enable Stage 2 late interaction (default: True)
            rerank_candidates: Stage 1 candidates (default: self.default_candidates)

        Returns:
            SearchResponse with ranked results and timing info

        Raises:
            ValueError: If query is empty or invalid
            SearchError: If search execution fails

        Workflow:
            1. Embed query with ColPali engine
            2. Stage 1: Retrieve top candidates from ChromaDB
            3. (Optional) Stage 2: Re-rank with late interaction
            4. Merge visual + text results
            5. Return top-n ranked results
        """
        pass

    def _stage1_retrieval(
        self,
        query_embedding: np.ndarray,
        search_mode: str,
        filters: Optional[Dict[str, Any]],
        n_candidates: int
    ) -> List[Dict[str, Any]]:
        """
        Stage 1: Fast approximate retrieval using representative vectors.

        Args:
            query_embedding: Query embedding (CLS token), shape (768,)
            search_mode: "hybrid", "visual_only", or "text_only"
            filters: Metadata filters
            n_candidates: Number of candidates to retrieve

        Returns:
            List of candidates with metadata and representative vectors

        Performance Target: <200ms
        """
        pass

    def _stage2_reranking(
        self,
        query_embeddings: np.ndarray,
        candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Stage 2: Precise re-ranking using late interaction.

        Args:
            query_embeddings: Full multi-vector query, shape (seq_length, 768)
            candidates: Stage 1 candidates with full embeddings in metadata

        Returns:
            Candidates with updated scores (MaxSim)

        Performance Target: <100ms for 100 candidates
        """
        pass

    def _merge_results(
        self,
        visual_results: List[Dict[str, Any]],
        text_results: List[Dict[str, Any]],
        n_results: int
    ) -> List[SearchResult]:
        """
        Merge and rank visual + text results.

        Args:
            visual_results: Ranked visual results
            text_results: Ranked text results
            n_results: Final result count

        Returns:
            Merged and ranked results

        Algorithm:
            1. Normalize scores to [0, 1] within each collection
            2. Merge by score (interleave visual and text)
            3. Deduplicate by doc_id (keep highest scoring per document)
            4. Return top-n results
        """
        pass

    def _format_result(
        self,
        candidate: Dict[str, Any]
    ) -> SearchResult:
        """
        Format candidate into SearchResult structure.

        Args:
            candidate: Raw candidate from ChromaDB

        Returns:
            Formatted SearchResult with all required fields
        """
        pass

    def get_search_stats(self) -> Dict[str, Any]:
        """
        Get search performance statistics.

        Returns:
            {
                "total_queries": int,
                "avg_stage1_ms": float,
                "avg_stage2_ms": float,
                "avg_total_ms": float,
                "cache_hit_rate": float
            }
        """
        pass
```

---

## Search Modes

### Hybrid (Default)

Searches both visual and text collections:

```python
# Query both collections
visual_candidates = storage.search_visual(query_emb, n=100)
text_candidates = storage.search_text(query_emb, n=100)

# Re-rank both with late interaction
visual_reranked = rerank(query_full, visual_candidates)
text_reranked = rerank(query_full, text_candidates)

# Merge and return top-10
results = merge(visual_reranked, text_reranked, n=10)
```

**Use Cases**:
- "Find charts showing revenue growth" (visual + text keywords)
- "Quarterly earnings reports" (broad semantic search)
- Default for most queries

### Visual Only

Searches only visual collection:

```python
# Query visual collection only
visual_candidates = storage.search_visual(query_emb, n=100)
visual_reranked = rerank(query_full, visual_candidates)
results = format(visual_reranked[:10])
```

**Use Cases**:
- "Show me bar charts" (visual structure search)
- "Find pages with diagrams" (visual content)
- Image-focused searches

### Text Only

Searches only text collection:

```python
# Query text collection only
text_candidates = storage.search_text(query_emb, n=100)
text_reranked = rerank(query_full, text_candidates)
results = format(text_reranked[:10])
```

**Use Cases**:
- "Find exact quote: 'termination clause'" (precise text match)
- "Search for contract sections" (text-heavy documents)
- Keyword-focused searches

---

## Filtering

### Supported Filters

```python
# Filter by filename
filters = {"filename": "Q3-2023-Earnings.pdf"}

# Filter by document ID
filters = {"doc_id": "a1b2c3d4"}

# Filter by date range
filters = {
    "date_range": {
        "start": "2023-01-01",
        "end": "2023-12-31"
    }
}

# Filter by page range
filters = {
    "page_range": {
        "min": 1,
        "max": 10
    }
}

# Combine multiple filters
filters = {
    "filename": "Q3-2023-Earnings.pdf",
    "page_range": {"min": 1, "max": 5}
}
```

### Filter Application

Filters are applied at Stage 1 (ChromaDB query) for efficiency:

```python
# ChromaDB where clause
where_clause = {
    "filename": {"$eq": "Q3-2023-Earnings.pdf"},
    "page": {"$gte": 1, "$lte": 5}
}

candidates = collection.query(
    query_embeddings=query_emb,
    n_results=100,
    where=where_clause
)
```

---

## Result Ranking

### Scoring Algorithm

**Stage 1 Scores** (Cosine Similarity):
- Range: 0 to 1
- Computed by ChromaDB using representative vectors
- Fast but approximate

**Stage 2 Scores** (MaxSim):
- Range: 0 to 1 (normalized)
- Computed by ColPali late interaction
- Precise token-level matching

### Score Normalization

```python
def normalize_scores(results: List[Dict]) -> List[Dict]:
    """
    Normalize scores to [0, 1] range within collection.

    This ensures fair comparison between visual and text results.
    """
    scores = [r["score"] for r in results]
    min_score = min(scores)
    max_score = max(scores)

    for result in results:
        # Min-max normalization
        result["normalized_score"] = (
            (result["score"] - min_score) / (max_score - min_score)
            if max_score > min_score else 0.5
        )

    return results
```

### Merging Strategy

```python
def merge_visual_text_results(
    visual: List[SearchResult],
    text: List[SearchResult],
    n_results: int
) -> List[SearchResult]:
    """
    Merge visual and text results by score.

    Strategy:
    1. Normalize scores within each collection
    2. Combine lists and sort by normalized_score (descending)
    3. Deduplicate: Keep highest score per doc_id
    4. Return top-n results
    """
    # Normalize
    visual = normalize_scores(visual)
    text = normalize_scores(text)

    # Combine and sort
    combined = visual + text
    combined.sort(key=lambda x: x["normalized_score"], reverse=True)

    # Deduplicate by doc_id (keep first occurrence = highest score)
    seen_docs = set()
    deduplicated = []
    for result in combined:
        if result["doc_id"] not in seen_docs:
            deduplicated.append(result)
            seen_docs.add(result["doc_id"])

    return deduplicated[:n_results]
```

---

## Performance Targets

| Operation | Target Latency | Measurement |
|-----------|----------------|-------------|
| **Stage 1 Retrieval** | <200ms | p95 for 10k documents |
| **Stage 2 Re-ranking** | <100ms | 100 candidates |
| **Total Hybrid Search** | <500ms | End-to-end |
| **Visual Only Search** | <300ms | Faster (single collection) |
| **Text Only Search** | <300ms | Faster (single collection) |

### Latency Breakdown

```
Hybrid Search (300ms total):
  - Query embedding:        20ms
  - Stage 1 visual:        100ms
  - Stage 1 text:          100ms  (parallel)
  - Stage 2 re-ranking:    100ms
  - Result merging:         20ms
  - Formatting:             10ms
```

---

## Error Handling

### Exception Types

```python
class SearchError(Exception):
    """Base exception for search operations."""
    pass

class QueryEmbeddingError(SearchError):
    """Failed to embed query."""
    pass

class RetrievalError(SearchError):
    """Stage 1 retrieval failed."""
    pass

class RerankingError(SearchError):
    """Stage 2 re-ranking failed."""
    pass

class ResultFormattingError(SearchError):
    """Failed to format results."""
    pass
```

### Fallback Strategies

1. **Stage 2 Failure** → Return Stage 1 results without re-ranking
   ```python
   try:
       reranked = stage2_reranking(candidates)
   except RerankingError:
       logger.warning("Stage 2 failed, returning Stage 1 results")
       reranked = candidates
   ```

2. **Empty Results** → Return empty list with status message
   ```python
   if len(results) == 0:
       return {
           "results": [],
           "message": "No matching documents found",
           "suggestions": ["Try different keywords", "Check filters"]
       }
   ```

3. **Timeout** → Return partial results
   ```python
   # Set timeout for Stage 2
   with timeout(seconds=5):
       reranked = stage2_reranking(candidates)
   ```

---

## Unit Test Requirements

search-agent must provide unit tests covering:

1. **Query Embedding**
   - Embed query successfully
   - Handle empty query gracefully
   - Long query is auto-truncated

2. **Stage 1 Retrieval**
   - Retrieve top-k candidates from each collection
   - Apply filters correctly
   - Handle collection mode (hybrid, visual_only, text_only)

3. **Stage 2 Re-ranking**
   - Re-rank candidates with late interaction
   - Scores updated correctly (higher than Stage 1 avg)
   - Handle edge cases (single candidate, 1000 candidates)

4. **Result Merging**
   - Merge visual + text results correctly
   - Deduplicate by doc_id
   - Normalize scores before merging

5. **End-to-End**
   - Hybrid search returns top-10 results
   - Total latency <500ms
   - Results sorted by score (descending)

---

## Integration Test Requirements

ui-agent must validate:

1. **Search Quality**
   - Query "revenue growth" returns relevant pages
   - Top-3 results match expected documents
   - Visual queries return pages with charts/images

2. **Filtering**
   - Filter by filename works correctly
   - Date range filter returns correct subset
   - Multiple filters combine with AND logic

3. **Performance**
   - p95 latency <500ms under load (10 queries/min)
   - Memory usage stable (<1GB for search engine)

4. **Error Handling**
   - Empty query returns error message
   - No results returns empty list with suggestions
   - ChromaDB connection failure handled gracefully

---

## Optimization Notes

### Caching

Implement query caching for frequent searches:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def search_cached(query: str, n_results: int) -> SearchResponse:
    """Cache search results for repeated queries."""
    return self.search(query, n_results)
```

### Parallel Processing

Stage 1 retrieval can run in parallel:

```python
import asyncio

async def stage1_parallel():
    visual_task = asyncio.create_task(search_visual())
    text_task = asyncio.create_task(search_text())
    visual_results, text_results = await asyncio.gather(visual_task, text_task)
```

### Early Stopping

For Stage 2, stop re-ranking if score threshold met:

```python
# Re-rank until we have 10 high-confidence results
reranked = []
for candidate in candidates:
    score = maxsim(query, candidate)
    if score > 0.9:  # High confidence
        reranked.append(candidate)
        if len(reranked) >= n_results:
            break  # Early stop
```

---

## Future Enhancements (Post-MVP)

1. **Semantic Query Expansion**: Expand query with synonyms
2. **User Feedback Loop**: Learn from click-through rates
3. **Multi-Query Fusion**: Combine multiple query variants
4. **Personalization**: Rank based on user preferences
5. **Faceted Search**: Group results by category/date

Current version: **1.0** (two-stage hybrid search)
