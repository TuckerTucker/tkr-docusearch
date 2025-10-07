"""
Search module for DocuSearch MVP.

This module implements a two-stage semantic search engine:
- Stage 1: Fast retrieval with representative vectors (HNSW index)
- Stage 2: Late interaction re-ranking with MaxSim scoring

Components:
- SearchEngine: Main search orchestrator
- QueryProcessor: Query embedding and validation
- ResultRanker: Result merging and ranking
- Mock implementations: For Wave 2 testing

Usage:
    >>> from src.search import SearchEngine
    >>> from src.search.mocks import MockEmbeddingEngine, MockStorageClient
    >>>
    >>> # Initialize with mock dependencies
    >>> engine = SearchEngine(
    ...     storage_client=MockStorageClient(),
    ...     embedding_engine=MockEmbeddingEngine()
    ... )
    >>>
    >>> # Execute hybrid search
    >>> response = engine.search(
    ...     query="quarterly revenue growth",
    ...     n_results=10,
    ...     search_mode="hybrid",
    ...     enable_reranking=True
    ... )
    >>>
    >>> print(f"Found {len(response['results'])} results")
    >>> print(f"Total time: {response['total_time_ms']:.1f}ms")

Performance Targets:
- Stage 1 retrieval: <200ms
- Stage 2 re-ranking: <100ms
- Total hybrid search: <500ms
"""

from .search_engine import SearchEngine, SearchError, RetrievalError, RerankingError
from .query_processor import QueryProcessor, QueryProcessingError
from .result_ranker import ResultRanker

__all__ = [
    # Main classes
    'SearchEngine',
    'QueryProcessor',
    'ResultRanker',

    # Exceptions
    'SearchError',
    'RetrievalError',
    'RerankingError',
    'QueryProcessingError',
]

__version__ = '1.0.0'
__author__ = 'DocuSearch Team'
