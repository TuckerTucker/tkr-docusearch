"""Tests for graph-aware context builder enrichment and clustering.

Validates that ``ContextBuilder._enrich_with_relations`` populates graph
fields on ``SourceDocument`` instances and that ``_cluster_sources`` groups
related documents into contiguous clusters ordered by relevance.
"""

import pytest

from src.core.testing.mocks import MockKojiClient
from src.research.context_builder import ContextBuilder, SourceDocument


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_source(doc_id: str, score: float = 0.8, filename: str = "doc.pdf") -> SourceDocument:
    """Create a minimal SourceDocument for testing."""
    return SourceDocument(
        doc_id=doc_id,
        filename=filename,
        page=1,
        extension="pdf",
        relevance_score=score,
    )


def _setup_client_with_docs(*doc_ids: str) -> MockKojiClient:
    """Create a MockKojiClient pre-populated with documents."""
    client = MockKojiClient()
    client.open()
    for doc_id in doc_ids:
        client.create_document(doc_id, f"{doc_id}.pdf", "pdf")
    return client


def _make_builder(storage_client: MockKojiClient) -> ContextBuilder:
    """Create a ContextBuilder with a mock search engine and storage client."""

    class _StubSearchEngine:
        """Minimal stub — graph tests never call search."""

        def search(self, **kwargs):
            return {"results": []}

    return ContextBuilder(
        search_engine=_StubSearchEngine(),
        storage_client=storage_client,
    )


# ---------------------------------------------------------------------------
# Tests: _enrich_with_relations
# ---------------------------------------------------------------------------


class TestEnrichWithRelations:
    """Tests for ContextBuilder._enrich_with_relations."""

    def test_enrich_populates_related_fields(self) -> None:
        """related_doc_ids and relationship_types are populated from relations."""
        client = _setup_client_with_docs("doc-a", "doc-b")
        client.create_relation("doc-a", "doc-b", "references")

        builder = _make_builder(client)
        sources = [_make_source("doc-a", score=0.9), _make_source("doc-b", score=0.7)]

        result = builder._enrich_with_relations(sources)

        # doc-a should list doc-b as related
        source_a = next(s for s in result if s.doc_id == "doc-a")
        assert "doc-b" in source_a.related_doc_ids
        assert "references" in source_a.relationship_types

    def test_bidirectional_relations(self) -> None:
        """Both directions of a relation are captured when direction='both'."""
        client = _setup_client_with_docs("doc-a", "doc-b")
        client.create_relation("doc-a", "doc-b", "references")

        builder = _make_builder(client)
        sources = [_make_source("doc-a", score=0.9), _make_source("doc-b", score=0.8)]

        result = builder._enrich_with_relations(sources)

        source_b = next(s for s in result if s.doc_id == "doc-b")
        assert "doc-a" in source_b.related_doc_ids

    def test_only_top_5_enriched(self) -> None:
        """Only the top-5 sources by relevance score get relations fetched."""
        doc_ids = [f"doc-{i}" for i in range(7)]
        client = _setup_client_with_docs(*doc_ids)
        # Relate all docs to doc-0
        for doc_id in doc_ids[1:]:
            client.create_relation("doc-0", doc_id, "references")

        builder = _make_builder(client)
        sources = [_make_source(d, score=0.9 - i * 0.1) for i, d in enumerate(doc_ids)]

        result = builder._enrich_with_relations(sources)

        # doc-5 (score 0.4) and doc-6 (score 0.3) are outside top-5 and have
        # no outgoing relations of their own, so they should not be enriched.
        source_5 = next(s for s in result if s.doc_id == "doc-5")
        source_6 = next(s for s in result if s.doc_id == "doc-6")
        assert source_5.related_doc_ids == []
        assert source_6.related_doc_ids == []


# ---------------------------------------------------------------------------
# Tests: supplementary sources
# ---------------------------------------------------------------------------


class TestSupplementarySources:
    """Tests for supplementary source addition via graph neighbors."""

    def test_supplementary_source_added(self) -> None:
        """A graph neighbor not in the initial sources is added as supplementary."""
        client = _setup_client_with_docs("doc-a", "doc-b", "doc-c")
        client.create_relation("doc-a", "doc-c", "references")

        builder = _make_builder(client)
        sources = [_make_source("doc-a", score=0.9), _make_source("doc-b", score=0.7)]

        result = builder._enrich_with_relations(sources)

        result_ids = [s.doc_id for s in result]
        assert "doc-c" in result_ids

        # Supplementary score should be penalized (0.3 * parent)
        source_c = next(s for s in result if s.doc_id == "doc-c")
        assert source_c.relevance_score == pytest.approx(0.3 * 0.9)

    def test_supplementary_respects_max(self) -> None:
        """At most max_supplementary neighbors are added."""
        neighbor_ids = [f"neighbor-{i}" for i in range(5)]
        all_ids = ["doc-a"] + neighbor_ids
        client = _setup_client_with_docs(*all_ids)
        for nid in neighbor_ids:
            client.create_relation("doc-a", nid, "references")

        builder = _make_builder(client)
        sources = [_make_source("doc-a", score=0.9)]

        result = builder._enrich_with_relations(sources, max_supplementary=2)

        # Original (1) + supplementary (capped at 2)
        assert len(result) == 3

    def test_no_duplicate_supplementary(self) -> None:
        """A doc already in sources is not added again as supplementary."""
        client = _setup_client_with_docs("doc-a", "doc-b")
        client.create_relation("doc-a", "doc-b", "references")

        builder = _make_builder(client)
        sources = [_make_source("doc-a", score=0.9), _make_source("doc-b", score=0.7)]

        result = builder._enrich_with_relations(sources)

        doc_b_count = sum(1 for s in result if s.doc_id == "doc-b")
        assert doc_b_count == 1


# ---------------------------------------------------------------------------
# Tests: _cluster_sources
# ---------------------------------------------------------------------------


class TestClusterSources:
    """Tests for ContextBuilder._cluster_sources."""

    def test_two_pairs_get_different_clusters(self) -> None:
        """Two disjoint pairs of related docs get distinct cluster_ids."""
        client = _setup_client_with_docs("a1", "a2", "b1", "b2")
        builder = _make_builder(client)

        s_a1 = _make_source("a1", score=0.9)
        s_a2 = _make_source("a2", score=0.8)
        s_b1 = _make_source("b1", score=0.7)
        s_b2 = _make_source("b2", score=0.6)

        # Set up relationships (as _enrich_with_relations would)
        s_a1.related_doc_ids = ["a2"]
        s_a2.related_doc_ids = ["a1"]
        s_b1.related_doc_ids = ["b2"]
        s_b2.related_doc_ids = ["b1"]

        result = builder._cluster_sources([s_a1, s_a2, s_b1, s_b2])

        # Each pair should share a cluster_id
        assert result[0].cluster_id == result[1].cluster_id  # a1, a2 grouped
        assert result[2].cluster_id == result[3].cluster_id  # b1, b2 grouped
        assert result[0].cluster_id != result[2].cluster_id  # different clusters

    def test_clusters_ordered_by_max_score(self) -> None:
        """Cluster with higher max relevance score appears first."""
        client = _setup_client_with_docs("lo1", "lo2", "hi1", "hi2")
        builder = _make_builder(client)

        s_lo1 = _make_source("lo1", score=0.3)
        s_lo2 = _make_source("lo2", score=0.2)
        s_hi1 = _make_source("hi1", score=0.9)
        s_hi2 = _make_source("hi2", score=0.8)

        s_lo1.related_doc_ids = ["lo2"]
        s_lo2.related_doc_ids = ["lo1"]
        s_hi1.related_doc_ids = ["hi2"]
        s_hi2.related_doc_ids = ["hi1"]

        # Pass in low-score cluster first
        result = builder._cluster_sources([s_lo1, s_lo2, s_hi1, s_hi2])

        # High-score cluster should be reordered to front
        assert result[0].doc_id == "hi1"
        assert result[1].doc_id == "hi2"

    def test_within_cluster_sorted_by_score(self) -> None:
        """Sources within a cluster are sorted by relevance_score descending."""
        client = _setup_client_with_docs("x", "y", "z")
        builder = _make_builder(client)

        s_x = _make_source("x", score=0.5)
        s_y = _make_source("y", score=0.9)
        s_z = _make_source("z", score=0.7)

        s_x.related_doc_ids = ["y", "z"]
        s_y.related_doc_ids = ["x", "z"]
        s_z.related_doc_ids = ["x", "y"]

        result = builder._cluster_sources([s_x, s_y, s_z])

        # All three in one cluster, ordered by score
        assert [s.doc_id for s in result] == ["y", "z", "x"]


# ---------------------------------------------------------------------------
# Tests: no-relations passthrough
# ---------------------------------------------------------------------------


class TestNoRelationsPassthrough:
    """Verify graceful behavior when no relations exist."""

    def test_sources_returned_unchanged(self) -> None:
        """When no relations exist, sources come back with empty graph fields."""
        client = _setup_client_with_docs("doc-a", "doc-b")
        builder = _make_builder(client)

        sources = [_make_source("doc-a", score=0.9), _make_source("doc-b", score=0.7)]

        result = builder._enrich_with_relations(sources)

        assert len(result) == 2
        for source in result:
            assert source.related_doc_ids == []
            assert source.relationship_types == []

    def test_clustering_with_no_relations(self) -> None:
        """Each unrelated source gets its own cluster_id."""
        client = _setup_client_with_docs("doc-a", "doc-b", "doc-c")
        builder = _make_builder(client)

        sources = [
            _make_source("doc-a", score=0.9),
            _make_source("doc-b", score=0.7),
            _make_source("doc-c", score=0.5),
        ]

        result = builder._cluster_sources(sources)

        cluster_ids = {s.cluster_id for s in result}
        assert len(cluster_ids) == 3  # each source in its own cluster

    def test_order_preserved_when_no_relations(self) -> None:
        """Without relations, ordering is purely by relevance_score descending."""
        client = _setup_client_with_docs("doc-a", "doc-b", "doc-c")
        builder = _make_builder(client)

        sources = [
            _make_source("doc-c", score=0.5),
            _make_source("doc-a", score=0.9),
            _make_source("doc-b", score=0.7),
        ]

        result = builder._cluster_sources(sources)

        assert [s.doc_id for s in result] == ["doc-a", "doc-b", "doc-c"]
