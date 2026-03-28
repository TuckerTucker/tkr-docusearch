"""Tests for PageRank blending in search results."""

import pytest

from src.core.testing.mocks import MockKojiClient
from src.search.koji_search import KojiSearch


@pytest.fixture
def search():
    """Create a minimal KojiSearch with a mock client."""
    mock_koji = MockKojiClient()
    mock_koji.open()
    ks = object.__new__(KojiSearch)
    ks._koji = mock_koji
    ks._shikomi = None
    ks._query_times = []
    return ks


class TestApplyPageRankBoost:
    """Test _apply_pagerank_boost method."""

    def test_pagerank_reorders_results(self, search):
        """High PageRank doc with lower search score gets boosted up."""
        results = [
            {"doc_id": "doc-A", "score": 0.9, "metadata": {}},
            {"doc_id": "doc-B", "score": 0.85, "metadata": {}},
        ]
        pagerank_scores = {
            "doc-A": 0.1,   # Low importance
            "doc-B": 0.9,   # High importance
        }

        boosted = search._apply_pagerank_boost(results, pagerank_scores, weight=0.3)

        # doc-B: 0.7*0.85 + 0.3*1.0 = 0.895
        # doc-A: 0.7*0.9 + 0.3*0.111 = 0.663
        assert boosted[0]["doc_id"] == "doc-B"

    def test_pagerank_empty_scores(self, search):
        """Empty PageRank scores leaves results unchanged."""
        results = [
            {"doc_id": "doc-A", "score": 0.9, "metadata": {}},
        ]

        boosted = search._apply_pagerank_boost(results, {})
        assert boosted[0]["score"] == 0.9

    def test_pagerank_empty_results(self, search):
        """Empty results list returns empty."""
        boosted = search._apply_pagerank_boost([], {"doc-A": 0.5})
        assert boosted == []

    def test_pagerank_metadata_set(self, search):
        """PageRank score stored in result metadata."""
        results = [
            {"doc_id": "doc-A", "score": 0.8, "metadata": {}},
        ]
        pagerank_scores = {"doc-A": 0.42}

        search._apply_pagerank_boost(results, pagerank_scores)
        assert results[0]["metadata"]["pagerank"] == 0.42
