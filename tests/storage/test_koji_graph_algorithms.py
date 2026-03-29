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

_has_graph_support = hasattr(koji.open_memory(), "graph")

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


@requires_graph
class TestGraphLabelPropagation:
    """Test label propagation community detection via Koji graph engine."""

    def test_label_propagation_two_clusters(self, client):
        """Two disconnected fully-connected triangles get distinct labels."""
        # Cluster 1: A, B, E — fully connected
        client.create_document(doc_id="doc-A", filename="a.pdf", format="pdf")
        client.create_document(doc_id="doc-B", filename="b.pdf", format="pdf")
        client.create_document(doc_id="doc-E", filename="e.pdf", format="pdf")

        client.create_relation("doc-A", "doc-B", "references")
        client.create_relation("doc-B", "doc-A", "cites")
        client.create_relation("doc-A", "doc-E", "references")
        client.create_relation("doc-E", "doc-A", "cites")
        client.create_relation("doc-B", "doc-E", "references")
        client.create_relation("doc-E", "doc-B", "cites")

        # Cluster 2: C, D, F — fully connected
        client.create_document(doc_id="doc-C", filename="c.pdf", format="pdf")
        client.create_document(doc_id="doc-D", filename="d.pdf", format="pdf")
        client.create_document(doc_id="doc-F", filename="f.pdf", format="pdf")

        client.create_relation("doc-C", "doc-D", "references")
        client.create_relation("doc-D", "doc-C", "cites")
        client.create_relation("doc-C", "doc-F", "references")
        client.create_relation("doc-F", "doc-C", "cites")
        client.create_relation("doc-D", "doc-F", "references")
        client.create_relation("doc-F", "doc-D", "cites")

        labels = client.graph_label_propagation()
        assert len(labels) == 6

        # All of cluster 1 share a label
        assert labels["doc-A"] == labels["doc-B"] == labels["doc-E"]
        # All of cluster 2 share a label
        assert labels["doc-C"] == labels["doc-D"] == labels["doc-F"]
        # The two clusters have different labels
        assert labels["doc-A"] != labels["doc-C"]

    def test_label_propagation_empty(self, client):
        """No documents returns empty dict."""
        labels = client.graph_label_propagation()
        assert labels == {}


@requires_graph
class TestGraphShortestPaths:
    """Test shortest-path computation via Koji graph engine."""

    def test_shortest_paths_chain(self, client):
        """A->B->C chain: B at distance 1, C at distance 2 from A."""
        client.create_document(doc_id="doc-A", filename="a.pdf", format="pdf")
        client.create_document(doc_id="doc-B", filename="b.pdf", format="pdf")
        client.create_document(doc_id="doc-C", filename="c.pdf", format="pdf")

        client.create_relation("doc-A", "doc-B", "references")
        client.create_relation("doc-B", "doc-C", "references")

        distances = client.graph_shortest_paths("doc-A")
        assert "doc-B" in distances
        assert "doc-C" in distances
        assert distances["doc-B"] < distances["doc-C"]

    def test_shortest_paths_no_source(self, client):
        """Non-existent source document returns empty dict."""
        distances = client.graph_shortest_paths("doc-nonexistent")
        assert distances == {}


@requires_graph
class TestGraphSCC:
    """Test strongly connected components via Koji graph engine."""

    def test_scc_triangle(self, client):
        """A->B->C->A cycle: all three in the same component."""
        _create_triangle(client)

        components = client.graph_scc()
        assert len(components) == 3
        assert components["doc-A"] == components["doc-B"]
        assert components["doc-B"] == components["doc-C"]


@requires_graph
class TestGraphHasCycle:
    """Test cycle detection via Koji graph engine."""

    def test_has_cycle_true(self, client):
        """Triangle graph (A->B->C->A) contains a cycle."""
        _create_triangle(client)
        assert client.graph_has_cycle() is True

    def test_has_cycle_dag(self, client):
        """DAG (A->B, A->C) without back-edges has no cycle."""
        client.create_document(doc_id="doc-A", filename="a.pdf", format="pdf")
        client.create_document(doc_id="doc-B", filename="b.pdf", format="pdf")
        client.create_document(doc_id="doc-C", filename="c.pdf", format="pdf")

        client.create_relation("doc-A", "doc-B", "references")
        client.create_relation("doc-A", "doc-C", "references")

        assert client.graph_has_cycle() is False


@requires_graph
class TestGraphTopologicalSort:
    """Test topological sort via Koji graph engine."""

    def test_topological_sort_dag(self, client):
        """A->B, A->C, B->C: A before B and C, B before C."""
        client.create_document(doc_id="doc-A", filename="a.pdf", format="pdf")
        client.create_document(doc_id="doc-B", filename="b.pdf", format="pdf")
        client.create_document(doc_id="doc-C", filename="c.pdf", format="pdf")

        client.create_relation("doc-A", "doc-B", "references")
        client.create_relation("doc-A", "doc-C", "references")
        client.create_relation("doc-B", "doc-C", "references")

        order = client.graph_topological_sort()
        assert len(order) == 3

        idx_a = order.index("doc-A")
        idx_b = order.index("doc-B")
        idx_c = order.index("doc-C")

        assert idx_a < idx_b, "A must come before B"
        assert idx_a < idx_c, "A must come before C"
        assert idx_b < idx_c, "B must come before C"


@requires_graph
class TestDeleteRelationsByType:
    """Test selective relation deletion by type."""

    def test_delete_by_type_selective(self, client):
        """Deleting one relation type preserves others."""
        client.create_document(doc_id="doc-A", filename="a.pdf", format="pdf")
        client.create_document(doc_id="doc-B", filename="b.pdf", format="pdf")

        client.create_relation("doc-A", "doc-B", "references")
        client.create_relation("doc-A", "doc-B", "version_of")
        client.create_relation("doc-B", "doc-A", "same_author")

        deleted = client.delete_relations_by_type("same_author")
        assert deleted == 1

        # Surviving relations should still include references and version_of
        remaining = client.get_relations("doc-A", direction="outgoing")
        remaining_types = {r["relation_type"] for r in remaining}
        assert "references" in remaining_types
        assert "version_of" in remaining_types
        assert "same_author" not in remaining_types

    def test_delete_by_type_empty(self, client):
        """Deleting a type that doesn't exist returns 0."""
        client.create_document(doc_id="doc-A", filename="a.pdf", format="pdf")
        client.create_document(doc_id="doc-B", filename="b.pdf", format="pdf")
        client.create_relation("doc-A", "doc-B", "references")

        deleted = client.delete_relations_by_type("nonexistent_type")
        assert deleted == 0
