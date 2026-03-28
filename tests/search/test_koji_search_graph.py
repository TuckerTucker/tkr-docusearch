"""Tests for graph-based score boosting in KojiSearch.

Validates that ``_boost_related_results`` correctly boosts scores for
documents that share graph relations with other results, and that
``_collect_result_relationships`` returns the correct edge set.

Uses ``MockKojiClient`` so no real Koji database is required.
"""

from __future__ import annotations

import pytest

from src.core.testing.mocks import MockKojiClient
from src.search.koji_search import KojiSearch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_search(koji: MockKojiClient) -> KojiSearch:
    """Construct a KojiSearch with a MockKojiClient and a dummy shikomi.

    The shikomi client is unused by the methods under test, so ``None``
    is safe here.
    """
    return KojiSearch(koji_client=koji, shikomi_client=None)


def _make_result(doc_id: str, score: float) -> dict:
    """Build a minimal search result dict."""
    return {
        "doc_id": doc_id,
        "chunk_id": None,
        "page_num": 1,
        "score": score,
        "text": "",
        "metadata": {
            "filename": f"{doc_id}.pdf",
            "format": "pdf",
            "source": "text",
        },
    }


def _setup_three_docs_with_relation(
    koji: MockKojiClient,
) -> None:
    """Create three documents; A and B are related, C is isolated."""
    koji.open()
    koji.create_document(doc_id="doc-A", filename="a.pdf", format="pdf")
    koji.create_document(doc_id="doc-B", filename="b.pdf", format="pdf")
    koji.create_document(doc_id="doc-C", filename="c.pdf", format="pdf")

    koji.create_relation(
        src_doc_id="doc-A",
        dst_doc_id="doc-B",
        relation_type="references",
    )


# ---------------------------------------------------------------------------
# Tests — _boost_related_results
# ---------------------------------------------------------------------------


class TestBoostRelatedResults:
    """Verify graph-based score boosting logic."""

    def test_boost_related_basic(self) -> None:
        """Related docs get boosted scores; results are re-sorted."""
        koji = MockKojiClient()
        _setup_three_docs_with_relation(koji)
        search = _make_search(koji)

        results = [
            _make_result("doc-C", 0.90),  # highest initial, no relations
            _make_result("doc-A", 0.80),  # related to B
            _make_result("doc-B", 0.70),  # related to A
        ]

        boosted = search._boost_related_results(results, boost_factor=0.05)

        # A and B each have 1 neighbor in the set -> +0.05
        boost_a = next(
            r["metadata"]["graph_boost"] for r in boosted if r["doc_id"] == "doc-A"
        )
        boost_b = next(
            r["metadata"]["graph_boost"] for r in boosted if r["doc_id"] == "doc-B"
        )
        boost_c = next(
            r["metadata"]["graph_boost"] for r in boosted if r["doc_id"] == "doc-C"
        )
        assert boost_a == pytest.approx(0.05)
        assert boost_b == pytest.approx(0.05)
        assert boost_c == pytest.approx(0.0)

        score_a = next(r["score"] for r in boosted if r["doc_id"] == "doc-A")
        score_b = next(r["score"] for r in boosted if r["doc_id"] == "doc-B")
        score_c = next(r["score"] for r in boosted if r["doc_id"] == "doc-C")

        assert score_a == pytest.approx(0.85)  # 0.80 + 0.05
        assert score_b == pytest.approx(0.75)  # 0.70 + 0.05
        assert score_c == pytest.approx(0.90)  # unchanged

        # C (0.90) > A (0.85) > B (0.75)
        assert boosted[0]["doc_id"] == "doc-C"
        assert boosted[1]["doc_id"] == "doc-A"
        assert boosted[2]["doc_id"] == "doc-B"

    def test_boost_reorders_results(self) -> None:
        """Boost can change result ordering when scores are close."""
        koji = MockKojiClient()
        _setup_three_docs_with_relation(koji)
        search = _make_search(koji)

        results = [
            _make_result("doc-C", 0.82),  # highest initial, no relations
            _make_result("doc-A", 0.80),  # related to B -> 0.85
            _make_result("doc-B", 0.70),  # related to A -> 0.75
        ]

        boosted = search._boost_related_results(results, boost_factor=0.05)

        # A (0.85) should now outrank C (0.82)
        assert boosted[0]["doc_id"] == "doc-A"
        assert boosted[1]["doc_id"] == "doc-C"
        assert boosted[2]["doc_id"] == "doc-B"

    def test_boost_no_relations(self) -> None:
        """With no relations, scores remain unchanged."""
        koji = MockKojiClient()
        koji.open()
        koji.create_document(doc_id="doc-X", filename="x.pdf", format="pdf")
        koji.create_document(doc_id="doc-Y", filename="y.pdf", format="pdf")
        search = _make_search(koji)

        results = [
            _make_result("doc-X", 0.90),
            _make_result("doc-Y", 0.80),
        ]

        boosted = search._boost_related_results(results, boost_factor=0.05)

        assert boosted[0]["score"] == pytest.approx(0.90)
        assert boosted[1]["score"] == pytest.approx(0.80)
        assert boosted[0]["metadata"]["graph_boost"] == pytest.approx(0.0)
        assert boosted[1]["metadata"]["graph_boost"] == pytest.approx(0.0)

    def test_boost_empty_results(self) -> None:
        """Empty results list returns immediately without error."""
        koji = MockKojiClient()
        koji.open()
        search = _make_search(koji)

        boosted = search._boost_related_results([])
        assert boosted == []

    def test_boost_capped_at_one(self) -> None:
        """Score never exceeds 1.0 even with large boost."""
        koji = MockKojiClient()
        _setup_three_docs_with_relation(koji)
        search = _make_search(koji)

        results = [
            _make_result("doc-A", 0.99),
            _make_result("doc-B", 0.98),
        ]

        boosted = search._boost_related_results(results, boost_factor=0.10)

        for r in boosted:
            assert r["score"] <= 1.0


# ---------------------------------------------------------------------------
# Tests — _collect_result_relationships
# ---------------------------------------------------------------------------


class TestCollectResultRelationships:
    """Verify relationship edge collection between result documents."""

    def test_collects_edges_between_results(self) -> None:
        """Edges are returned when both endpoints are in the result set."""
        koji = MockKojiClient()
        _setup_three_docs_with_relation(koji)
        search = _make_search(koji)

        results = [
            _make_result("doc-A", 0.90),
            _make_result("doc-B", 0.80),
            _make_result("doc-C", 0.70),
        ]

        edges = search._collect_result_relationships(results)

        assert len(edges) == 1
        assert edges[0]["src_doc_id"] == "doc-A"
        assert edges[0]["dst_doc_id"] == "doc-B"
        assert edges[0]["relation_type"] == "references"

    def test_no_edges_when_unrelated(self) -> None:
        """No edges when result documents have no relations."""
        koji = MockKojiClient()
        koji.open()
        koji.create_document(doc_id="doc-X", filename="x.pdf", format="pdf")
        koji.create_document(doc_id="doc-Y", filename="y.pdf", format="pdf")
        search = _make_search(koji)

        results = [
            _make_result("doc-X", 0.90),
            _make_result("doc-Y", 0.80),
        ]

        edges = search._collect_result_relationships(results)
        assert edges == []

    def test_no_edges_for_empty_results(self) -> None:
        """Empty result set produces no edges."""
        koji = MockKojiClient()
        koji.open()
        search = _make_search(koji)

        edges = search._collect_result_relationships([])
        assert edges == []

    def test_edges_excluded_when_one_endpoint_missing(self) -> None:
        """Edge not returned if one endpoint is outside the result set."""
        koji = MockKojiClient()
        _setup_three_docs_with_relation(koji)
        search = _make_search(koji)

        # Only doc-A in results; doc-B is missing
        results = [
            _make_result("doc-A", 0.90),
            _make_result("doc-C", 0.70),
        ]

        edges = search._collect_result_relationships(results)
        assert edges == []
