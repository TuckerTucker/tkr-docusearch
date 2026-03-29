"""Integration tests for graph API endpoints.

Tests the /api/graph/* endpoints using FastAPI TestClient with a real
Koji database (file-based via tmp_path).

Covers all 8 graph endpoints:
    - GET /api/graph/overview
    - GET /api/graph/neighborhood/{doc_id}
    - GET /api/graph/path
    - GET /api/graph/communities
    - GET /api/graph/importance
    - GET /api/graph/similar/{doc_id}
    - GET /api/graph/edges
    - GET /api/graph/reading-order
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tkr_docusearch.config.koji_config import KojiConfig
from tkr_docusearch.storage.koji_client import KojiClient
from tkr_docusearch.api.routes.graph import router, set_storage_client


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def koji_client(tmp_path):
    """Create and open a KojiClient with a temporary file-based database."""
    config = KojiConfig(db_path=str(tmp_path / "test.db"))
    client = KojiClient(config)
    client.open()
    yield client
    client.close()


@pytest.fixture
def test_client(koji_client):
    """Create a FastAPI TestClient wired to the graph router.

    Injects the real KojiClient via ``set_storage_client`` and
    cleans up the global after the test.
    """
    app = FastAPI()
    app.include_router(router)
    set_storage_client(koji_client)
    yield TestClient(app)
    set_storage_client(None)


# ---------------------------------------------------------------------------
# Test data helpers
# ---------------------------------------------------------------------------


def _seed_graph(client: KojiClient) -> None:
    """Create 4 documents with relations forming a chain + cluster.

    Graph topology::

        doc-A --references--> doc-B --references--> doc-C
        doc-A <--similar_to--> doc-D  (bidirectional)
    """
    for name in ["doc-A", "doc-B", "doc-C", "doc-D"]:
        client.create_document(
            doc_id=name,
            filename=f"{name}.pdf",
            format="pdf",
        )
    # Chain: A -> B -> C
    client.create_relation("doc-A", "doc-B", "references")
    client.create_relation("doc-B", "doc-C", "references")
    # Cluster: A <-> D (bidirectional similarity)
    client.create_relation(
        "doc-A", "doc-D", "similar_to", metadata={"score": 0.85}
    )
    client.create_relation(
        "doc-D", "doc-A", "similar_to", metadata={"score": 0.85}
    )


def _seed_disconnected_groups(client: KojiClient) -> None:
    """Create two disconnected groups of documents.

    Group 1: g1-A -> g1-B -> g1-C
    Group 2: g2-X -> g2-Y
    """
    for name in ["g1-A", "g1-B", "g1-C"]:
        client.create_document(
            doc_id=name, filename=f"{name}.pdf", format="pdf"
        )
    for name in ["g2-X", "g2-Y"]:
        client.create_document(
            doc_id=name, filename=f"{name}.pdf", format="pdf"
        )
    client.create_relation("g1-A", "g1-B", "references")
    client.create_relation("g1-B", "g1-C", "references")
    client.create_relation("g2-X", "g2-Y", "references")


# ---------------------------------------------------------------------------
# GET /api/graph/overview
# ---------------------------------------------------------------------------


class TestOverview:
    """Tests for the graph overview endpoint."""

    def test_overview_returns_nodes_and_edges(self, koji_client, test_client):
        """Seeded graph returns correct node list and edge counts."""
        _seed_graph(koji_client)

        resp = test_client.get("/api/graph/overview")
        assert resp.status_code == 200

        data = resp.json()
        assert data["node_count"] == 4

        doc_ids = {n["doc_id"] for n in data["nodes"]}
        assert doc_ids == {"doc-A", "doc-B", "doc-C", "doc-D"}

        # 2 references + 2 similar_to = 4 total edges
        assert data["total_edges"] == 4
        assert "references" in data["edge_counts"]
        assert "similar_to" in data["edge_counts"]
        assert data["edge_counts"]["references"] == 2
        assert data["edge_counts"]["similar_to"] == 2

    def test_overview_empty_db(self, test_client):
        """Empty database returns zeroed summary."""
        resp = test_client.get("/api/graph/overview")
        assert resp.status_code == 200

        data = resp.json()
        assert data["nodes"] == []
        assert data["node_count"] == 0
        assert data["edge_counts"] == {}
        assert data["total_edges"] == 0


# ---------------------------------------------------------------------------
# GET /api/graph/neighborhood/{doc_id}
# ---------------------------------------------------------------------------


class TestNeighborhood:
    """Tests for the graph neighborhood endpoint."""

    def test_neighborhood_returns_subgraph(self, koji_client, test_client):
        """Center node + direct neighbors are returned with edges."""
        _seed_graph(koji_client)

        resp = test_client.get("/api/graph/neighborhood/doc-A")
        assert resp.status_code == 200

        data = resp.json()
        assert data["center"] == "doc-A"
        assert data["depth"] == 1

        node_ids = {n["doc_id"] for n in data["nodes"]}
        # doc-A is the center; outgoing references -> doc-B, similar_to -> doc-D
        # doc-D has incoming similar_to -> doc-A, so doc-D is a neighbor
        assert "doc-A" in node_ids
        assert len(data["edges"]) > 0

    def test_neighborhood_depth_filtering(self, koji_client, test_client):
        """Depth 1 returns fewer nodes than depth 2."""
        _seed_graph(koji_client)

        resp_d1 = test_client.get("/api/graph/neighborhood/doc-A?depth=1")
        assert resp_d1.status_code == 200
        ids_d1 = {n["doc_id"] for n in resp_d1.json()["nodes"]}

        resp_d2 = test_client.get("/api/graph/neighborhood/doc-A?depth=2")
        assert resp_d2.status_code == 200
        ids_d2 = {n["doc_id"] for n in resp_d2.json()["nodes"]}

        # Depth 2 should reach at least one more node than depth 1
        assert len(ids_d2) >= len(ids_d1)
        # At depth 2, doc-C should be reachable via A->B->C
        assert "doc-C" in ids_d2

    def test_neighborhood_not_found(self, test_client):
        """Non-existent doc_id returns 404."""
        resp = test_client.get("/api/graph/neighborhood/nonexistent")
        assert resp.status_code == 404

    def test_neighborhood_edge_type_filter(self, koji_client, test_client):
        """Filtering by edge_types restricts which edges appear."""
        _seed_graph(koji_client)

        resp = test_client.get(
            "/api/graph/neighborhood/doc-A?edge_types=similar_to"
        )
        assert resp.status_code == 200

        data = resp.json()
        # All returned edges should be similar_to only
        for edge in data["edges"]:
            assert edge["relation_type"] == "similar_to"


# ---------------------------------------------------------------------------
# GET /api/graph/path
# ---------------------------------------------------------------------------


class TestPath:
    """Tests for the shortest path endpoint."""

    def test_path_connected(self, koji_client, test_client):
        """Connected documents return a valid path."""
        _seed_graph(koji_client)

        resp = test_client.get(
            "/api/graph/path?source=doc-A&target=doc-C"
        )
        assert resp.status_code == 200

        data = resp.json()
        assert data["source"] == "doc-A"
        assert data["target"] == "doc-C"
        assert data["connected"] is True
        assert len(data["path"]) == 2  # A->B, B->C
        assert data["path"][0]["from"] == "doc-A"
        assert data["path"][0]["to"] == "doc-B"
        assert data["path"][1]["from"] == "doc-B"
        assert data["path"][1]["to"] == "doc-C"

    def test_path_not_connected(self, koji_client, test_client):
        """Disconnected documents return connected=False, empty path."""
        _seed_disconnected_groups(koji_client)

        resp = test_client.get(
            "/api/graph/path?source=g1-A&target=g2-X"
        )
        assert resp.status_code == 200

        data = resp.json()
        assert data["connected"] is False
        assert data["path"] == []
        assert data["distance"] is None

    def test_path_source_not_found(self, koji_client, test_client):
        """Non-existent source document returns 404."""
        _seed_graph(koji_client)

        resp = test_client.get(
            "/api/graph/path?source=nonexistent&target=doc-A"
        )
        assert resp.status_code == 404

    def test_path_target_not_found(self, koji_client, test_client):
        """Non-existent target document returns 404."""
        _seed_graph(koji_client)

        resp = test_client.get(
            "/api/graph/path?source=doc-A&target=nonexistent"
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/graph/communities
# ---------------------------------------------------------------------------


class TestCommunities:
    """Tests for the communities endpoint."""

    def test_communities_returns_clusters(self, koji_client, test_client):
        """Disconnected groups produce distinct communities."""
        _seed_disconnected_groups(koji_client)

        resp = test_client.get("/api/graph/communities")
        assert resp.status_code == 200

        data = resp.json()
        assert data["total"] >= 1
        assert len(data["communities"]) == data["total"]

        # Each community should have members with doc_id, filename, format
        for community in data["communities"]:
            assert "community_id" in community
            assert community["size"] > 0
            assert len(community["members"]) == community["size"]
            for member in community["members"]:
                assert "doc_id" in member
                assert "filename" in member

    def test_communities_empty(self, test_client):
        """Empty database returns empty communities list."""
        resp = test_client.get("/api/graph/communities")
        assert resp.status_code == 200

        data = resp.json()
        assert data["communities"] == []
        assert data["total"] == 0


# ---------------------------------------------------------------------------
# GET /api/graph/importance
# ---------------------------------------------------------------------------


class TestImportance:
    """Tests for the importance (PageRank) endpoint."""

    def test_importance_returns_ranked(self, koji_client, test_client):
        """Seeded graph returns documents sorted by PageRank score."""
        _seed_graph(koji_client)

        resp = test_client.get("/api/graph/importance")
        assert resp.status_code == 200

        data = resp.json()
        assert data["total"] > 0

        docs = data["documents"]
        assert len(docs) > 0

        # Verify descending score order
        scores = [d["pagerank_score"] for d in docs]
        assert scores == sorted(scores, reverse=True)

        # Each document should have required fields
        for doc in docs:
            assert "doc_id" in doc
            assert "filename" in doc
            assert "pagerank_score" in doc

    def test_importance_empty(self, test_client):
        """Empty database returns empty documents list."""
        resp = test_client.get("/api/graph/importance")
        assert resp.status_code == 200

        data = resp.json()
        assert data["documents"] == []
        assert data["total"] == 0

    def test_importance_limit(self, koji_client, test_client):
        """Limit parameter restricts the number of results."""
        _seed_graph(koji_client)

        resp = test_client.get("/api/graph/importance?limit=2")
        assert resp.status_code == 200

        data = resp.json()
        assert data["total"] <= 2


# ---------------------------------------------------------------------------
# GET /api/graph/similar/{doc_id}
# ---------------------------------------------------------------------------


class TestSimilar:
    """Tests for the similarity neighbors endpoint."""

    def test_similar_returns_neighbors(self, koji_client, test_client):
        """Document with similar_to edges returns scored results."""
        _seed_graph(koji_client)

        resp = test_client.get("/api/graph/similar/doc-A")
        assert resp.status_code == 200

        data = resp.json()
        assert data["doc_id"] == "doc-A"
        assert data["total"] > 0

        # doc-D has bidirectional similar_to with doc-A
        neighbor_ids = {r["doc_id"] for r in data["similar"]}
        assert "doc-D" in neighbor_ids

        # Check scores are present
        for result in data["similar"]:
            assert "similarity_score" in result
            assert result["similarity_score"] > 0

    def test_similar_not_found(self, test_client):
        """Non-existent document returns 404."""
        resp = test_client.get("/api/graph/similar/nonexistent")
        assert resp.status_code == 404

    def test_similar_no_edges(self, koji_client, test_client):
        """Document with no similar_to edges returns empty list."""
        _seed_graph(koji_client)

        # doc-C has no similar_to edges (only incoming references from doc-B)
        resp = test_client.get("/api/graph/similar/doc-C")
        assert resp.status_code == 200

        data = resp.json()
        assert data["doc_id"] == "doc-C"
        assert data["similar"] == []
        assert data["total"] == 0


# ---------------------------------------------------------------------------
# GET /api/graph/edges
# ---------------------------------------------------------------------------


class TestEdges:
    """Tests for the edges query endpoint."""

    def test_edges_all(self, koji_client, test_client):
        """All edges are returned when no filters are applied."""
        _seed_graph(koji_client)

        resp = test_client.get("/api/graph/edges")
        assert resp.status_code == 200

        data = resp.json()
        # 2 references + 2 similar_to = 4 total
        assert data["total"] == 4

        for edge in data["edges"]:
            assert "src_doc_id" in edge
            assert "dst_doc_id" in edge
            assert "relation_type" in edge

    def test_edges_filter_by_type(self, koji_client, test_client):
        """Filtering by edge_type returns only matching edges."""
        _seed_graph(koji_client)

        resp = test_client.get("/api/graph/edges?edge_type=similar_to")
        assert resp.status_code == 200

        data = resp.json()
        assert data["total"] == 2
        for edge in data["edges"]:
            assert edge["relation_type"] == "similar_to"

    def test_edges_filter_by_doc(self, koji_client, test_client):
        """Filtering by doc_id returns only edges involving that document."""
        _seed_graph(koji_client)

        resp = test_client.get("/api/graph/edges?doc_id=doc-A")
        assert resp.status_code == 200

        data = resp.json()
        assert data["total"] > 0
        for edge in data["edges"]:
            assert (
                edge["src_doc_id"] == "doc-A"
                or edge["dst_doc_id"] == "doc-A"
            )

    def test_edges_filter_by_type_and_doc(self, koji_client, test_client):
        """Combining doc_id and edge_type narrows results."""
        _seed_graph(koji_client)

        resp = test_client.get(
            "/api/graph/edges?doc_id=doc-A&edge_type=references"
        )
        assert resp.status_code == 200

        data = resp.json()
        for edge in data["edges"]:
            assert edge["relation_type"] == "references"
            assert (
                edge["src_doc_id"] == "doc-A"
                or edge["dst_doc_id"] == "doc-A"
            )

    def test_edges_empty_db(self, test_client):
        """Empty database returns zero edges."""
        resp = test_client.get("/api/graph/edges")
        assert resp.status_code == 200

        data = resp.json()
        assert data["edges"] == []
        assert data["total"] == 0


# ---------------------------------------------------------------------------
# GET /api/graph/reading-order
# ---------------------------------------------------------------------------


class TestReadingOrder:
    """Tests for the reading-order endpoint."""

    def test_reading_order_dag(self, koji_client, test_client):
        """Acyclic graph uses topological sort, preserving dependency order."""
        # Create a simple DAG: A -> B -> C
        for name in ["ro-A", "ro-B", "ro-C"]:
            koji_client.create_document(
                doc_id=name, filename=f"{name}.pdf", format="pdf"
            )
        koji_client.create_relation("ro-A", "ro-B", "references")
        koji_client.create_relation("ro-B", "ro-C", "references")

        resp = test_client.get("/api/graph/reading-order")
        assert resp.status_code == 200

        data = resp.json()
        assert data["method"] == "topological"
        assert data["total"] == 3

        order_ids = [d["doc_id"] for d in data["order"]]
        # A must come before B, B must come before C
        assert order_ids.index("ro-A") < order_ids.index("ro-B")
        assert order_ids.index("ro-B") < order_ids.index("ro-C")

        # Verify position numbering starts at 1
        positions = [d["position"] for d in data["order"]]
        assert positions == [1, 2, 3]

    def test_reading_order_with_cycle(self, koji_client, test_client):
        """Cyclic graph falls back to pagerank-based ordering."""
        # Create a cycle: A -> B -> C -> A
        for name in ["cy-A", "cy-B", "cy-C"]:
            koji_client.create_document(
                doc_id=name, filename=f"{name}.pdf", format="pdf"
            )
        koji_client.create_relation("cy-A", "cy-B", "references")
        koji_client.create_relation("cy-B", "cy-C", "references")
        koji_client.create_relation("cy-C", "cy-A", "references")

        resp = test_client.get("/api/graph/reading-order")
        assert resp.status_code == 200

        data = resp.json()
        assert data["method"] == "pagerank"
        assert data["total"] == 3

        # All 3 documents should appear in the order
        order_ids = {d["doc_id"] for d in data["order"]}
        assert order_ids == {"cy-A", "cy-B", "cy-C"}

    def test_reading_order_empty(self, test_client):
        """Empty database returns empty order.

        On an empty graph, graph_has_cycle returns False and
        graph_topological_sort returns an empty list.
        """
        resp = test_client.get("/api/graph/reading-order")
        assert resp.status_code == 200

        data = resp.json()
        assert data["order"] == []
        assert data["total"] == 0


# ---------------------------------------------------------------------------
# Edge cases and error handling
# ---------------------------------------------------------------------------


class TestStorageUnavailable:
    """Tests for when the storage client is not initialized."""

    def test_overview_503_without_storage(self):
        """Endpoints return 503 when storage client is not set."""
        app = FastAPI()
        app.include_router(router)
        set_storage_client(None)
        client = TestClient(app)

        resp = client.get("/api/graph/overview")
        assert resp.status_code == 503

    def test_neighborhood_503_without_storage(self):
        """Neighborhood returns 503 when storage client is not set."""
        app = FastAPI()
        app.include_router(router)
        set_storage_client(None)
        client = TestClient(app)

        resp = client.get("/api/graph/neighborhood/doc-A")
        assert resp.status_code == 503
