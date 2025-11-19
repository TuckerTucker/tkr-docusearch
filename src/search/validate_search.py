#!/usr/bin/env python3
"""
Validation script for search module implementation.

This script performs basic smoke tests to validate the search engine
works correctly with mock dependencies.

Usage:
    python3 src/search/validate_search.py
"""

import logging
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import search components
from tkr_docusearch.search import SearchEngine
from tkr_docusearch.search.mocks import MockEmbeddingEngine, MockStorageClient


def test_basic_search():
    """Test basic search functionality."""
    logger.info("Testing basic search...")

    # Initialize components
    storage = MockStorageClient(simulate_latency=False)
    embedding = MockEmbeddingEngine(simulate_latency=False)
    engine = SearchEngine(storage, embedding)

    # Test hybrid search
    response = engine.search(
        query="quarterly revenue growth", n_results=10, search_mode="hybrid", enable_reranking=True
    )

    # Validate response
    assert "results" in response
    assert "total_time_ms" in response
    assert len(response["results"]) <= 10

    logger.info(f"✓ Hybrid search successful: {len(response['results'])} results")
    logger.info(f"  Stage 1: {response['stage1_time_ms']:.1f}ms")
    logger.info(f"  Stage 2: {response['stage2_time_ms']:.1f}ms")
    logger.info(f"  Total: {response['total_time_ms']:.1f}ms")

    return True


def test_search_modes():
    """Test different search modes."""
    logger.info("Testing search modes...")

    storage = MockStorageClient(simulate_latency=False)
    embedding = MockEmbeddingEngine(simulate_latency=False)
    engine = SearchEngine(storage, embedding)

    # Test visual only
    response = engine.search(query="chart", search_mode="visual_only")
    assert all(r["type"] == "visual" for r in response["results"])
    logger.info(f"✓ Visual-only search: {len(response['results'])} results")

    # Test text only
    response = engine.search(query="contract", search_mode="text_only")
    assert all(r["type"] == "text" for r in response["results"])
    logger.info(f"✓ Text-only search: {len(response['results'])} results")

    # Test hybrid
    response = engine.search(query="revenue", search_mode="hybrid")
    logger.info(f"✓ Hybrid search: {len(response['results'])} results")

    return True


def test_filters():
    """Test metadata filtering."""
    logger.info("Testing filters...")

    storage = MockStorageClient(simulate_latency=False)
    embedding = MockEmbeddingEngine(simulate_latency=False)
    engine = SearchEngine(storage, embedding)

    # Filter by filename
    response = engine.search(query="test", filters={"filename": "Q3-2023-Earnings.pdf"})

    if response["results"]:
        assert all(r["filename"] == "Q3-2023-Earnings.pdf" for r in response["results"])
        logger.info(f"✓ Filename filter: {len(response['results'])} results")
    else:
        logger.info("✓ Filename filter: 0 results (valid)")

    return True


def test_mock_contracts():
    """Test mock implementations match contracts."""
    logger.info("Testing contract compliance...")

    # Test MockEmbeddingEngine
    embedding = MockEmbeddingEngine()
    query_result = embedding.embed_query("test query")

    assert "embeddings" in query_result
    assert "cls_token" in query_result
    assert "seq_length" in query_result
    assert query_result["embeddings"].shape[1] == 768
    logger.info("✓ MockEmbeddingEngine matches embedding-interface.md")

    # Test MockStorageClient
    storage = MockStorageClient()
    import numpy as np

    query_emb = np.random.randn(768).astype(np.float32)

    visual_results = storage.search_visual(query_emb, n_results=10)
    assert all("id" in r for r in visual_results)
    assert all("score" in r for r in visual_results)
    assert all("metadata" in r for r in visual_results)
    logger.info("✓ MockStorageClient matches storage-interface.md")

    return True


def test_two_stage_pipeline():
    """Test two-stage search pipeline."""
    logger.info("Testing two-stage pipeline...")

    storage = MockStorageClient(simulate_latency=False)
    embedding = MockEmbeddingEngine(simulate_latency=False)
    engine = SearchEngine(storage, embedding)

    # With re-ranking
    response_with = engine.search(query="test", enable_reranking=True, rerank_candidates=50)

    assert response_with["reranked_count"] > 0
    assert response_with["stage2_time_ms"] > 0
    logger.info("✓ Stage 2 re-ranking enabled")

    # Without re-ranking
    response_without = engine.search(query="test", enable_reranking=False)

    assert response_without["reranked_count"] == 0
    assert response_without["stage2_time_ms"] == 0
    logger.info("✓ Stage 2 re-ranking disabled")

    return True


def test_statistics():
    """Test statistics tracking."""
    logger.info("Testing statistics...")

    storage = MockStorageClient(simulate_latency=False)
    embedding = MockEmbeddingEngine(simulate_latency=False)
    engine = SearchEngine(storage, embedding)

    # Execute multiple searches
    for i in range(5):
        engine.search(query=f"test query {i}", n_results=5)

    stats = engine.get_search_stats()

    assert stats["total_queries"] == 5
    assert stats["avg_total_ms"] > 0
    logger.info(f"✓ Statistics tracking: {stats['total_queries']} queries")
    logger.info(f"  Avg total: {stats['avg_total_ms']:.1f}ms")
    logger.info(f"  P95 total: {stats['p95_total_ms']:.1f}ms")

    return True


def main():
    """Run all validation tests."""
    logger.info("=" * 60)
    logger.info("Search Module Validation")
    logger.info("=" * 60)

    tests = [
        ("Basic Search", test_basic_search),
        ("Search Modes", test_search_modes),
        ("Filters", test_filters),
        ("Mock Contracts", test_mock_contracts),
        ("Two-Stage Pipeline", test_two_stage_pipeline),
        ("Statistics", test_statistics),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            logger.info(f"\n--- {test_name} ---")
            test_func()
            passed += 1
        except Exception as e:
            logger.error(f"✗ {test_name} failed: {e}")
            failed += 1

    logger.info("\n" + "=" * 60)
    logger.info(f"Results: {passed} passed, {failed} failed")
    logger.info("=" * 60)

    if failed > 0:
        sys.exit(1)
    else:
        logger.info("✓ All validation tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
