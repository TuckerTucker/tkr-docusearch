"""
Tests for search/validate_search.py module.

Tests cover:
- Basic search functionality
- Different search modes (hybrid, visual_only, text_only)
- Metadata filtering
- Two-stage pipeline (with/without reranking)
- Statistics tracking
- Mock contract compliance
"""

import numpy as np
import pytest

from search.validate_search import (
    test_basic_search,
    test_filters,
    test_mock_contracts,
    test_search_modes,
    test_statistics,
    test_two_stage_pipeline,
)


class TestBasicSearch:
    """Test basic search functionality."""

    def test_basic_search_executes_successfully(self):
        """Test that basic search runs without errors."""
        result = test_basic_search()
        assert result is True

    def test_basic_search_returns_results(self):
        """Test that basic search returns expected data."""
        # Import here to avoid module-level dependencies
        from search import SearchEngine
        from search.mocks import MockEmbeddingEngine, MockStorageClient

        storage = MockStorageClient(simulate_latency=False)
        embedding = MockEmbeddingEngine(simulate_latency=False)
        engine = SearchEngine(storage, embedding)

        response = engine.search(
            query="quarterly revenue growth",
            n_results=10,
            search_mode="hybrid",
            enable_reranking=True,
        )

        # Validate response structure
        assert "results" in response
        assert "total_time_ms" in response
        assert "stage1_time_ms" in response
        assert "stage2_time_ms" in response
        assert isinstance(response["results"], list)
        assert len(response["results"]) <= 10


class TestSearchModes:
    """Test different search modes."""

    def test_search_modes_executes_successfully(self):
        """Test that search modes test runs without errors."""
        result = test_search_modes()
        assert result is True

    def test_visual_only_mode(self):
        """Test visual-only search mode."""
        from search import SearchEngine
        from search.mocks import MockEmbeddingEngine, MockStorageClient

        storage = MockStorageClient(simulate_latency=False)
        embedding = MockEmbeddingEngine(simulate_latency=False)
        engine = SearchEngine(storage, embedding)

        response = engine.search(query="chart", search_mode="visual_only")

        # All results should be visual type
        assert all(r["type"] == "visual" for r in response["results"])

    def test_text_only_mode(self):
        """Test text-only search mode."""
        from search import SearchEngine
        from search.mocks import MockEmbeddingEngine, MockStorageClient

        storage = MockStorageClient(simulate_latency=False)
        embedding = MockEmbeddingEngine(simulate_latency=False)
        engine = SearchEngine(storage, embedding)

        response = engine.search(query="contract", search_mode="text_only")

        # All results should be text type
        assert all(r["type"] == "text" for r in response["results"])

    def test_hybrid_mode(self):
        """Test hybrid search mode."""
        from search import SearchEngine
        from search.mocks import MockEmbeddingEngine, MockStorageClient

        storage = MockStorageClient(simulate_latency=False)
        embedding = MockEmbeddingEngine(simulate_latency=False)
        engine = SearchEngine(storage, embedding)

        response = engine.search(query="revenue", search_mode="hybrid")

        # Should return results (may be mixed types)
        assert "results" in response
        assert isinstance(response["results"], list)

    def test_invalid_search_mode_raises_error(self):
        """Test that invalid search mode raises appropriate error."""
        from search import SearchEngine
        from search.mocks import MockEmbeddingEngine, MockStorageClient

        storage = MockStorageClient(simulate_latency=False)
        embedding = MockEmbeddingEngine(simulate_latency=False)
        engine = SearchEngine(storage, embedding)

        with pytest.raises(ValueError):
            engine.search(query="test", search_mode="invalid_mode")


class TestFilters:
    """Test metadata filtering."""

    def test_filters_executes_successfully(self):
        """Test that filters test runs without errors."""
        result = test_filters()
        assert result is True

    def test_filename_filter(self):
        """Test filtering by filename."""
        from search import SearchEngine
        from search.mocks import MockEmbeddingEngine, MockStorageClient

        storage = MockStorageClient(simulate_latency=False)
        embedding = MockEmbeddingEngine(simulate_latency=False)
        engine = SearchEngine(storage, embedding)

        response = engine.search(query="test", filters={"filename": "Q3-2023-Earnings.pdf"})

        # All results should match the filter
        if response["results"]:
            assert all(r["filename"] == "Q3-2023-Earnings.pdf" for r in response["results"])


class TestMockContracts:
    """Test mock implementations match contracts."""

    def test_mock_contracts_executes_successfully(self):
        """Test that mock contracts test runs without errors."""
        result = test_mock_contracts()
        assert result is True

    def test_mock_embedding_engine_contract(self):
        """Test MockEmbeddingEngine matches embedding interface."""
        from search.mocks import MockEmbeddingEngine

        embedding = MockEmbeddingEngine()
        query_result = embedding.embed_query("test query")

        # Validate contract compliance
        assert "embeddings" in query_result
        assert "cls_token" in query_result
        assert "seq_length" in query_result
        assert query_result["embeddings"].shape[1] == 768

    def test_mock_storage_client_contract(self):
        """Test MockStorageClient matches storage interface."""
        from search.mocks import MockStorageClient

        storage = MockStorageClient()
        query_emb = np.random.randn(768).astype(np.float32)

        visual_results = storage.search_visual(query_emb, n_results=10)

        # Validate contract compliance
        assert isinstance(visual_results, list)
        assert all("id" in r for r in visual_results)
        assert all("score" in r for r in visual_results)
        assert all("metadata" in r for r in visual_results)


class TestTwoStagePipeline:
    """Test two-stage search pipeline."""

    def test_two_stage_pipeline_executes_successfully(self):
        """Test that two-stage pipeline test runs without errors."""
        result = test_two_stage_pipeline()
        assert result is True

    def test_reranking_enabled(self):
        """Test search with re-ranking enabled."""
        from search import SearchEngine
        from search.mocks import MockEmbeddingEngine, MockStorageClient

        storage = MockStorageClient(simulate_latency=False)
        embedding = MockEmbeddingEngine(simulate_latency=False)
        engine = SearchEngine(storage, embedding)

        response = engine.search(query="test", enable_reranking=True, rerank_candidates=50)

        # Stage 2 should have run
        assert response["reranked_count"] > 0
        assert response["stage2_time_ms"] >= 0  # Can be very small

    def test_reranking_disabled(self):
        """Test search with re-ranking disabled."""
        from search import SearchEngine
        from search.mocks import MockEmbeddingEngine, MockStorageClient

        storage = MockStorageClient(simulate_latency=False)
        embedding = MockEmbeddingEngine(simulate_latency=False)
        engine = SearchEngine(storage, embedding)

        response = engine.search(query="test", enable_reranking=False)

        # Stage 2 should not have run
        assert response["reranked_count"] == 0
        assert response["stage2_time_ms"] == 0


class TestStatistics:
    """Test statistics tracking."""

    def test_statistics_executes_successfully(self):
        """Test that statistics test runs without errors."""
        result = test_statistics()
        assert result is True

    def test_statistics_tracking(self):
        """Test that statistics are tracked correctly."""
        from search import SearchEngine
        from search.mocks import MockEmbeddingEngine, MockStorageClient

        storage = MockStorageClient(simulate_latency=False)
        embedding = MockEmbeddingEngine(simulate_latency=False)
        engine = SearchEngine(storage, embedding)

        # Execute multiple searches
        num_queries = 5
        for i in range(num_queries):
            engine.search(query=f"test query {i}", n_results=5)

        stats = engine.get_search_stats()

        # Validate statistics
        assert stats["total_queries"] == num_queries
        assert stats["avg_total_ms"] > 0
        assert stats["p95_total_ms"] >= stats["avg_total_ms"]  # P95 should be >= average

    def test_statistics_reset(self):
        """Test that statistics can be reset."""
        from search import SearchEngine
        from search.mocks import MockEmbeddingEngine, MockStorageClient

        storage = MockStorageClient(simulate_latency=False)
        embedding = MockEmbeddingEngine(simulate_latency=False)
        engine = SearchEngine(storage, embedding)

        # Execute some searches
        engine.search(query="test 1")
        engine.search(query="test 2")

        # Get initial stats
        stats_before = engine.get_search_stats()
        assert stats_before["total_queries"] == 2

        # Reset is not in the interface, so we just verify cumulative behavior
        # Execute more searches
        engine.search(query="test 3")
        stats_after = engine.get_search_stats()
        assert stats_after["total_queries"] == 3


class TestIntegration:
    """Integration tests for validate_search module."""

    def test_all_validation_tests_pass(self):
        """Test that all validation functions execute successfully."""
        assert test_basic_search() is True
        assert test_search_modes() is True
        assert test_filters() is True
        assert test_mock_contracts() is True
        assert test_two_stage_pipeline() is True
        assert test_statistics() is True

    def test_search_engine_initialization(self):
        """Test SearchEngine can be initialized."""
        from search import SearchEngine
        from search.mocks import MockEmbeddingEngine, MockStorageClient

        storage = MockStorageClient()
        embedding = MockEmbeddingEngine()
        engine = SearchEngine(storage, embedding)

        assert engine is not None

    def test_query_processing_pipeline(self):
        """Test complete query processing pipeline."""
        from search import SearchEngine
        from search.mocks import MockEmbeddingEngine, MockStorageClient

        storage = MockStorageClient(simulate_latency=False)
        embedding = MockEmbeddingEngine(simulate_latency=False)
        engine = SearchEngine(storage, embedding)

        # Process a query through the complete pipeline
        response = engine.search(
            query="Find documents about quarterly earnings",
            n_results=10,
            search_mode="hybrid",
            enable_reranking=True,
        )

        # Validate complete pipeline execution
        assert "results" in response
        assert "total_time_ms" in response
        assert "stage1_time_ms" in response
        assert "stage2_time_ms" in response
        assert "reranked_count" in response
