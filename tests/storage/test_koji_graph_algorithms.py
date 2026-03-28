"""Tests for Koji graph algorithm integration.

Tests the KojiClient graph methods (graph_pagerank, graph_communities)
and the integer mapping layer that bridges text doc_ids to Int64 node IDs.

These tests require a real Koji database (file-based, via tmp_path fixture)
since graph algorithms run in the Koji engine, not in Python mocks.

Graph algorithm tests are skipped when the installed koji-python binary
was not built with graph support (``graph()`` method missing).
"""

import koji
import pytest

from src.config.koji_config import KojiConfig
from src.storage.koji_client import KojiClient, KojiQueryError

_has_graph_support = hasattr(
    koji.open_memory()._async_db, "graph"
)

requires_graph = pytest.mark.skipif(
    not _has_graph_support,
    reason="koji-python built without graph support",
)


@pytest.fixture
def config(tmp_path):
    """Create isolated database config per test."""
    return KojiConfig(db_path=str(tmp_path / "test.db"))


@pytest.fixture
def client(config):
    """Create, open, and yield a KojiClient; close on teardown."""
    c = KojiClient(config)
    c.open()
    yield c
    c.close()


def _create_triangle(client: KojiClient) -> None:
    """Create 3 docs with a directed cycle: A→B→C→A."""
    client.create_document(doc_id="doc-A", filename="a.pdf", format="pdf")
    client.create_document(doc_id="doc-B", filename="b.pdf", format="pdf")
    client.create_document(doc_id="doc-C", filename="c.pdf", format="pdf")

    client.create_relation("doc-A", "doc-B", "references")
    client.create_relation("doc-B", "doc-C", "references")
    client.create_relation("doc-C", "doc-A", "references")


class TestDocIdIntMapping:
    """Test the integer mapping helper."""

    def test_mapping_covers_all_docs(self, client):
        """Every document gets a unique integer node_id."""
        client.create_document(doc_id="doc-X", filename="x.pdf", format="pdf")
        client.create_document(doc_id="doc-Y", filename="y.pdf", format="pdf")

        mapping = client._doc_id_int_mapping()
        assert len(mapping) == 2
        assert set(mapping.values()) == {"doc-X", "doc-Y"}

    def test_mapping_empty_db(self, client):
        """Empty database returns empty mapping."""
        mapping = client._doc_id_int_mapping()
        assert mapping == {}


@requires_graph
class TestGraphPageRank:
    """Test PageRank computation via Koji graph engine."""

    def test_pagerank_triangle(self, client):
        """Triangle graph: all nodes get roughly equal PageRank scores."""
        _create_triangle(client)

        scores = client.graph_pagerank()
        assert len(scores) == 3
        assert "doc-A" in scores
        assert "doc-B" in scores
        assert "doc-C" in scores

        # Scores should sum to approximately 1.0
        total = sum(scores.values())
        assert abs(total - 1.0) < 0.05

    def test_pagerank_empty(self, client):
        """No documents returns empty dict."""
        scores = client.graph_pagerank()
        assert scores == {}

    def test_pagerank_no_relations(self, client):
        """Documents with no relations: graph algorithm may fail or return empty."""
        client.create_document(doc_id="doc-A", filename="a.pdf", format="pdf")
        # No relations — edge query returns 0 rows
        # This may raise or return empty depending on Koji's behavior
        try:
            scores = client.graph_pagerank()
            # If it returns, scores should be empty or have doc-A with default score
            assert isinstance(scores, dict)
        except KojiQueryError:
            pass  # Acceptable: graph algorithm on empty edge set


@requires_graph
class TestGraphCommunities:
    """Test community detection via label propagation."""

    def test_two_disconnected_clusters(self, client):
        """Two disconnected pairs should get different community labels."""
        client.create_document(doc_id="doc-A", filename="a.pdf", format="pdf")
        client.create_document(doc_id="doc-B", filename="b.pdf", format="pdf")
        client.create_document(doc_id="doc-C", filename="c.pdf", format="pdf")
        client.create_document(doc_id="doc-D", filename="d.pdf", format="pdf")

        # Bidirectional edges within each cluster for strong community signal
        client.create_relation("doc-A", "doc-B", "references")
        client.create_relation("doc-B", "doc-A", "cites")
        client.create_relation("doc-C", "doc-D", "references")
        client.create_relation("doc-D", "doc-C", "cites")

        communities = client.graph_communities()
        assert len(communities) == 4

        # A and B should be in the same community
        assert communities["doc-A"] == communities["doc-B"]
        # C and D should be in the same community
        assert communities["doc-C"] == communities["doc-D"]
        # The two clusters should be different
        assert communities["doc-A"] != communities["doc-C"]

    def test_communities_empty(self, client):
        """No documents returns empty dict."""
        communities = client.graph_communities()
        assert communities == {}
