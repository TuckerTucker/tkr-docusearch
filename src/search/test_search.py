"""
Comprehensive unit tests for search module.

Tests cover:
- Query processing and validation
- Two-stage search pipeline
- Result merging and ranking
- Mock implementations
- Error handling
- Performance targets

Usage:
    pytest src/search/test_search.py -v
    pytest src/search/test_search.py::TestSearchEngine -v
"""

import pytest
import numpy as np
import time
from typing import Dict, Any

from .search_engine import SearchEngine, SearchError, RetrievalError
from .query_processor import QueryProcessor, QueryProcessingError
from .result_ranker import ResultRanker
from .mocks import MockEmbeddingEngine, MockStorageClient


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_embedding_engine():
    """Create mock embedding engine."""
    return MockEmbeddingEngine(simulate_latency=False)


@pytest.fixture
def mock_storage_client():
    """Create mock storage client."""
    return MockStorageClient(simulate_latency=False)


@pytest.fixture
def search_engine(mock_storage_client, mock_embedding_engine):
    """Create search engine with mocks."""
    return SearchEngine(
        storage_client=mock_storage_client,
        embedding_engine=mock_embedding_engine,
        default_n_results=10,
        default_candidates=100
    )


@pytest.fixture
def query_processor(mock_embedding_engine):
    """Create query processor."""
    return QueryProcessor(mock_embedding_engine)


@pytest.fixture
def result_ranker():
    """Create result ranker."""
    return ResultRanker(score_normalization="min_max")


# ============================================================================
# Test MockEmbeddingEngine
# ============================================================================

class TestMockEmbeddingEngine:
    """Test mock embedding engine implementation."""

    def test_initialization(self, mock_embedding_engine):
        """Test engine initializes correctly."""
        assert mock_embedding_engine.is_loaded
        assert mock_embedding_engine.embedding_dim == 768
        assert mock_embedding_engine.model_name == "nomic-ai/colnomic-embed-multimodal-7b"

    def test_embed_query_success(self, mock_embedding_engine):
        """Test query embedding generation."""
        result = mock_embedding_engine.embed_query("quarterly revenue growth")

        assert "embeddings" in result
        assert "cls_token" in result
        assert "seq_length" in result
        assert result["input_type"] == "text"

        # Check shapes
        embeddings = result["embeddings"]
        assert embeddings.ndim == 2
        assert embeddings.shape[1] == 768
        assert embeddings.shape[0] == result["seq_length"]

        cls_token = result["cls_token"]
        assert cls_token.shape == (768,)

    def test_embed_query_empty(self, mock_embedding_engine):
        """Test empty query raises error."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            mock_embedding_engine.embed_query("")

    def test_embed_query_reproducible(self, mock_embedding_engine):
        """Test query embedding is reproducible."""
        query = "test query"
        result1 = mock_embedding_engine.embed_query(query)
        result2 = mock_embedding_engine.embed_query(query)

        np.testing.assert_array_almost_equal(
            result1["embeddings"],
            result2["embeddings"]
        )

    def test_score_multi_vector(self, mock_embedding_engine):
        """Test late interaction scoring."""
        query_emb = np.random.randn(10, 768).astype(np.float32)
        doc_emb1 = np.random.randn(100, 768).astype(np.float32)
        doc_emb2 = np.random.randn(80, 768).astype(np.float32)

        result = mock_embedding_engine.score_multi_vector(
            query_embeddings=query_emb,
            document_embeddings=[doc_emb1, doc_emb2]
        )

        assert "scores" in result
        assert len(result["scores"]) == 2
        assert all(0 <= s <= 1 for s in result["scores"])
        assert result["num_candidates"] == 2

    def test_score_multi_vector_invalid_shape(self, mock_embedding_engine):
        """Test invalid embedding shapes raise errors."""
        query_emb = np.random.randn(10, 768).astype(np.float32)
        doc_emb_wrong = np.random.randn(100, 512).astype(np.float32)  # Wrong dim

        with pytest.raises(ValueError, match="must have shape"):
            mock_embedding_engine.score_multi_vector(
                query_embeddings=query_emb,
                document_embeddings=[doc_emb_wrong]
            )

    def test_get_model_info(self, mock_embedding_engine):
        """Test model info returns correct data."""
        info = mock_embedding_engine.get_model_info()

        assert info["is_loaded"]
        assert info["is_mock"]
        assert info["model_name"] == "nomic-ai/colnomic-embed-multimodal-7b"


# ============================================================================
# Test MockStorageClient
# ============================================================================

class TestMockStorageClient:
    """Test mock storage client implementation."""

    def test_initialization(self, mock_storage_client):
        """Test client initializes with data."""
        stats = mock_storage_client.get_collection_stats()

        assert stats["visual_count"] > 0
        assert stats["text_count"] > 0
        assert stats["total_documents"] > 0
        assert stats["is_mock"]

    def test_search_visual(self, mock_storage_client):
        """Test visual collection search."""
        query_emb = np.random.randn(768).astype(np.float32)

        results = mock_storage_client.search_visual(
            query_embedding=query_emb,
            n_results=10
        )

        assert len(results) <= 10
        assert all("id" in r for r in results)
        assert all("score" in r for r in results)
        assert all("metadata" in r for r in results)
        assert all(r["metadata"]["type"] == "visual" for r in results)

    def test_search_text(self, mock_storage_client):
        """Test text collection search."""
        query_emb = np.random.randn(768).astype(np.float32)

        results = mock_storage_client.search_text(
            query_embedding=query_emb,
            n_results=10
        )

        assert len(results) <= 10
        assert all(r["metadata"]["type"] == "text" for r in results)

    def test_search_with_filters(self, mock_storage_client):
        """Test search with metadata filters."""
        query_emb = np.random.randn(768).astype(np.float32)

        # Filter by filename
        results = mock_storage_client.search_visual(
            query_embedding=query_emb,
            n_results=10,
            filters={"filename": "Q3-2023-Earnings.pdf"}
        )

        assert all(
            r["metadata"]["filename"] == "Q3-2023-Earnings.pdf"
            for r in results
        )

    def test_search_invalid_shape(self, mock_storage_client):
        """Test invalid query shape raises error."""
        query_emb = np.random.randn(512).astype(np.float32)  # Wrong dim

        with pytest.raises(ValueError, match="must have shape"):
            mock_storage_client.search_visual(query_embedding=query_emb)


# ============================================================================
# Test QueryProcessor
# ============================================================================

class TestQueryProcessor:
    """Test query processing module."""

    def test_process_query_success(self, query_processor):
        """Test successful query processing."""
        result = query_processor.process_query("revenue growth analysis")

        assert "query" in result
        assert "processed_query" in result
        assert "embeddings" in result
        assert "cls_token" in result
        assert "seq_length" in result

        assert result["embeddings"].shape[1] == 768
        assert result["cls_token"].shape == (768,)

    def test_process_query_empty(self, query_processor):
        """Test empty query raises error."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            query_processor.process_query("")

    def test_process_query_whitespace(self, query_processor):
        """Test whitespace-only query raises error."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            query_processor.process_query("   ")

    def test_process_query_long(self, query_processor):
        """Test long query is truncated."""
        long_query = " ".join(["word"] * 200)
        result = query_processor.process_query(long_query)

        processed_words = result["processed_query"].split()
        assert len(processed_words) <= query_processor.max_query_length

    def test_validate_embedding(self, query_processor):
        """Test embedding validation."""
        valid_emb = np.random.randn(10, 768).astype(np.float32)
        assert query_processor.validate_embedding(valid_emb)

        # Invalid shape
        with pytest.raises(ValueError, match="must be 2D"):
            query_processor.validate_embedding(np.random.randn(768))

        # Wrong dimension
        with pytest.raises(ValueError, match="must have dimension"):
            query_processor.validate_embedding(np.random.randn(10, 512))


# ============================================================================
# Test ResultRanker
# ============================================================================

class TestResultRanker:
    """Test result ranking module."""

    def test_merge_results_hybrid(self, result_ranker):
        """Test merging visual and text results."""
        visual_results = [
            {"id": "v1", "score": 0.9, "metadata": {"doc_id": "doc1", "type": "visual"}},
            {"id": "v2", "score": 0.7, "metadata": {"doc_id": "doc2", "type": "visual"}},
        ]
        text_results = [
            {"id": "t1", "score": 0.8, "metadata": {"doc_id": "doc1", "type": "text"}},
            {"id": "t2", "score": 0.6, "metadata": {"doc_id": "doc3", "type": "text"}},
        ]

        merged = result_ranker.merge_results(
            visual_results=visual_results,
            text_results=text_results,
            n_results=10
        )

        assert len(merged) > 0
        # Check results are sorted by normalized score
        scores = [r.get("normalized_score", r["score"]) for r in merged]
        assert scores == sorted(scores, reverse=True)

    def test_merge_results_deduplication(self, result_ranker):
        """Test deduplication by doc_id."""
        visual_results = [
            {"id": "v1", "score": 0.9, "metadata": {"doc_id": "doc1", "type": "visual"}},
        ]
        text_results = [
            {"id": "t1", "score": 0.8, "metadata": {"doc_id": "doc1", "type": "text"}},
        ]

        merged = result_ranker.merge_results(
            visual_results=visual_results,
            text_results=text_results,
            n_results=10,
            deduplicate=True
        )

        # Should keep only highest scoring result per doc
        assert len(merged) == 1
        assert merged[0]["id"] == "v1"  # Higher score

    def test_rank_by_late_interaction(self, result_ranker):
        """Test re-ranking with late interaction scores."""
        candidates = [
            {"id": "c1", "score": 0.7, "metadata": {}},
            {"id": "c2", "score": 0.8, "metadata": {}},
            {"id": "c3", "score": 0.6, "metadata": {}},
        ]
        new_scores = [0.95, 0.85, 0.90]

        reranked = result_ranker.rank_by_late_interaction(
            candidates=candidates,
            late_interaction_scores=new_scores
        )

        # Check re-ranking
        assert reranked[0]["id"] == "c1"  # Now highest
        assert reranked[1]["id"] == "c3"  # Now second
        assert reranked[2]["id"] == "c2"  # Now third

        # Check stage1_score preserved
        assert reranked[0]["stage1_score"] == 0.7

    def test_format_search_result(self, result_ranker):
        """Test result formatting."""
        candidate = {
            "id": "doc1-page001",
            "score": 0.95,
            "metadata": {
                "doc_id": "doc1",
                "type": "visual",
                "filename": "test.pdf",
                "page": 1,
                "source_path": "/data/test.pdf",
                "timestamp": "2023-10-06T15:30:00Z"
            }
        }

        result = result_ranker.format_search_result(candidate)

        assert result["id"] == "doc1-page001"
        assert result["doc_id"] == "doc1"
        assert result["type"] == "visual"
        assert result["score"] == 0.95
        assert result["filename"] == "test.pdf"
        assert result["thumbnail_url"] == "/api/thumbnail/doc1-page001"


# ============================================================================
# Test SearchEngine
# ============================================================================

class TestSearchEngine:
    """Test main search engine."""

    def test_initialization(self, search_engine):
        """Test engine initializes correctly."""
        assert search_engine.default_n_results == 10
        assert search_engine.default_candidates == 100

    def test_search_hybrid_success(self, search_engine):
        """Test successful hybrid search."""
        response = search_engine.search(
            query="quarterly revenue growth",
            n_results=10,
            search_mode="hybrid",
            enable_reranking=True
        )

        assert "results" in response
        assert "total_results" in response
        assert "query" in response
        assert "search_mode" in response
        assert "stage1_time_ms" in response
        assert "stage2_time_ms" in response
        assert "total_time_ms" in response

        assert response["search_mode"] == "hybrid"
        assert len(response["results"]) <= 10

    def test_search_visual_only(self, search_engine):
        """Test visual-only search mode."""
        response = search_engine.search(
            query="bar chart",
            n_results=5,
            search_mode="visual_only"
        )

        assert response["search_mode"] == "visual_only"
        assert len(response["results"]) <= 5
        assert all(r["type"] == "visual" for r in response["results"])

    def test_search_text_only(self, search_engine):
        """Test text-only search mode."""
        response = search_engine.search(
            query="contract terms",
            n_results=5,
            search_mode="text_only"
        )

        assert response["search_mode"] == "text_only"
        assert len(response["results"]) <= 5
        assert all(r["type"] == "text" for r in response["results"])

    def test_search_with_filters(self, search_engine):
        """Test search with metadata filters."""
        response = search_engine.search(
            query="revenue",
            n_results=10,
            filters={"filename": "Q3-2023-Earnings.pdf"}
        )

        assert all(
            r["filename"] == "Q3-2023-Earnings.pdf"
            for r in response["results"]
        )

    def test_search_without_reranking(self, search_engine):
        """Test search without Stage 2 re-ranking."""
        response = search_engine.search(
            query="test",
            enable_reranking=False
        )

        assert response["stage2_time_ms"] == 0.0
        assert response["reranked_count"] == 0

    def test_search_invalid_query(self, search_engine):
        """Test empty query raises error."""
        with pytest.raises(ValueError):
            search_engine.search(query="")

    def test_search_invalid_mode(self, search_engine):
        """Test invalid search mode raises error."""
        with pytest.raises(ValueError, match="search_mode must be"):
            search_engine.search(query="test", search_mode="invalid")

    def test_search_results_sorted(self, search_engine):
        """Test results are sorted by score."""
        response = search_engine.search(
            query="revenue growth",
            n_results=10
        )

        scores = [r["score"] for r in response["results"]]
        assert scores == sorted(scores, reverse=True)

    def test_search_stats(self, search_engine):
        """Test statistics tracking."""
        # Execute some searches
        for _ in range(5):
            search_engine.search(query="test", n_results=5)

        stats = search_engine.get_search_stats()

        assert stats["total_queries"] == 5
        assert stats["avg_stage1_ms"] >= 0
        assert stats["avg_stage2_ms"] >= 0
        assert stats["avg_total_ms"] >= 0
        assert stats["p95_total_ms"] >= 0


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Test performance targets."""

    def test_stage1_latency(self, search_engine):
        """Test Stage 1 retrieval meets latency target (<200ms)."""
        response = search_engine.search(
            query="test query",
            enable_reranking=False
        )

        # Note: Mock has simulate_latency=False, so this tests algorithm only
        # Real implementation should meet <200ms target
        assert response["stage1_time_ms"] < 500  # Generous for mock

    def test_stage2_latency(self, search_engine):
        """Test Stage 2 re-ranking meets latency target (<100ms)."""
        response = search_engine.search(
            query="test query",
            enable_reranking=True,
            rerank_candidates=50  # Smaller batch for faster test
        )

        # Real implementation should meet <100ms for 100 candidates
        assert response["stage2_time_ms"] < 500  # Generous for mock

    def test_total_latency_hybrid(self, search_engine):
        """Test total hybrid search meets latency target (<500ms)."""
        response = search_engine.search(
            query="test query",
            search_mode="hybrid",
            enable_reranking=True
        )

        # Real implementation should meet <500ms target
        assert response["total_time_ms"] < 1000  # Generous for mock


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for end-to-end workflows."""

    def test_end_to_end_search(self, search_engine):
        """Test complete search workflow."""
        # Execute search
        response = search_engine.search(
            query="quarterly revenue growth by product category",
            n_results=10,
            search_mode="hybrid",
            filters={"filename": "Q3-2023-Earnings.pdf"},
            enable_reranking=True
        )

        # Validate response structure
        assert response["query"] == "quarterly revenue growth by product category"
        assert len(response["results"]) <= 10
        assert response["search_mode"] == "hybrid"

        # Validate result structure
        for result in response["results"]:
            assert "id" in result
            assert "doc_id" in result
            assert "type" in result
            assert "score" in result
            assert "filename" in result
            assert "page" in result

        # Check performance
        assert response["total_time_ms"] > 0
        assert response["stage1_time_ms"] > 0
        if response["reranked_count"] > 0:
            assert response["stage2_time_ms"] > 0

    def test_multiple_searches(self, search_engine):
        """Test multiple consecutive searches."""
        queries = [
            "revenue growth",
            "product categories",
            "financial metrics",
            "quarterly earnings"
        ]

        for query in queries:
            response = search_engine.search(query=query, n_results=5)
            assert len(response["results"]) <= 5
            assert response["total_time_ms"] > 0

        # Check statistics
        stats = search_engine.get_search_stats()
        assert stats["total_queries"] == len(queries)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
