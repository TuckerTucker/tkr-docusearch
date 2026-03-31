"""Integration tests for graph API flows with richer topologies.

Extends the basic endpoint coverage in ``test_graph_endpoints.py`` with
scenarios that exercise multi-hop paths, disconnected components,
community detection across varied topologies, and importance ranking
with asymmetric connectivity.

Each test seeds a 5-document graph with explicit relations, then
asserts against the actual response shapes returned by the graph router.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tkr_docusearch.api.routes.graph import router, set_storage_client
from tkr_docusearch.config.koji_config import KojiConfig
from tkr_docusearch.storage.koji_client import KojiClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def koji_client(tmp_path):
    """Create and open a KojiClient with a temporary file-based database."""
    config = KojiConfig(db_path=str(tmp_path / "test_flows.db"))
    client = KojiClient(config)
    client.open()
    yield client
    client.close()


@pytest.fixture
def test_client(koji_client: KojiClient):
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
# Seed helpers
# ---------------------------------------------------------------------------


def _seed_rich_graph(client: KojiClient) -> None:
    """Create 5 documents with explicit relations forming a rich topology.

    Graph topology::

        doc-A --references--> doc-B --references--> doc-C
        doc-A <--similar_to--> doc-D  (bidirectional, score=0.9)
        doc-E  (isolated — no relations)

    This gives us a chain (A -> B -> C), a similarity cluster (A <-> D),
    and an isolated node (E) for testing connectivity and community
    separation.
    """
    docs = [
        ("doc-A", "intro.pdf", "pdf"),
        ("doc-B", "methods.pdf", "pdf"),
        ("doc-C", "results.pdf", "pdf"),
        ("doc-D", "related.pdf", "pdf"),
        ("doc-E", "appendix.pdf", "pdf"),
    ]
    for doc_id, filename, fmt in docs:
        client.create_document(doc_id=doc_id, filename=filename, format=fmt)

    # Chain: A -> B -> C
    client.create_relation("doc-A", "doc-B", "references")
    client.create_relation("doc-B", "doc-C", "references")

    # Cluster: A <-> D (bidirectional similarity)
    client.create_relation(
        "doc-A", "doc-D", "similar_to", metadata={"score": 0.9}
    )
    client.create_relation(
        "doc-D", "doc-A", "similar_to", metadata={"score": 0.9}
    )

    # doc-E intentionally has no relations


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGraphAPIFlows:
    """Integration tests covering richer graph topologies.

    These extend the basic endpoint tests to verify correct behavior
    with multi-hop paths, disconnected nodes, community separation,
    and relative importance ordering.
    """

    def test_overview_with_seeded_graph(
        self,
        koji_client: KojiClient,
        test_client: TestClient,
    ) -> None:
        """Seed 5 docs + relations, verify overview counts are correct.

        Expects 5 nodes, 2 ``references`` edges, 2 ``similar_to`` edges,
        and 4 total edges.
        """
        _seed_rich_graph(koji_client)

        resp = test_client.get("/api/graph/overview")
        assert resp.status_code == 200

        data = resp.json()
        assert data["node_count"] == 5

        node_ids = {n["doc_id"] for n in data["nodes"]}
        assert node_ids == {"doc-A", "doc-B", "doc-C", "doc-D", "doc-E"}

        assert data["total_edges"] == 4
        assert data["edge_counts"].get("references") == 2
        assert data["edge_counts"].get("similar_to") == 2

    def test_path_between_connected_docs(
        self,
        koji_client: KojiClient,
        test_client: TestClient,
    ) -> None:
        """Shortest path A -> B -> C yields two hops with correct steps.

        The path endpoint returns a list of ``{from, to, relation_type}``
        steps. For A to C, the chain is A->B then B->C.
        """
        _seed_rich_graph(koji_client)

        resp = test_client.get("/api/graph/path?source=doc-A&target=doc-C")
        assert resp.status_code == 200

        data = resp.json()
        assert data["source"] == "doc-A"
        assert data["target"] == "doc-C"
        assert data["connected"] is True
        assert data["distance"] is not None

        path = data["path"]
        assert len(path) == 2

        assert path[0]["from"] == "doc-A"
        assert path[0]["to"] == "doc-B"
        assert path[0]["relation_type"] == "references"

        assert path[1]["from"] == "doc-B"
        assert path[1]["to"] == "doc-C"
        assert path[1]["relation_type"] == "references"

    def test_path_between_disconnected_docs(
        self,
        koji_client: KojiClient,
        test_client: TestClient,
    ) -> None:
        """Isolated doc-E has no path from doc-A.

        The path endpoint returns ``connected=False`` and an empty path
        list when no route exists.
        """
        _seed_rich_graph(koji_client)

        resp = test_client.get("/api/graph/path?source=doc-A&target=doc-E")
        assert resp.status_code == 200

        data = resp.json()
        assert data["connected"] is False
        assert data["path"] == []
        assert data["distance"] is None

    def test_communities_reflect_topology(
        self,
        koji_client: KojiClient,
        test_client: TestClient,
    ) -> None:
        """Community detection groups connected documents together.

        Label propagation operates on edge-connected nodes only.
        Isolated doc-E (no edges) is excluded from the algorithm output.
        The connected cluster (A, B, C, D) should appear in at least
        one community.
        """
        _seed_rich_graph(koji_client)

        resp = test_client.get("/api/graph/communities")
        assert resp.status_code == 200

        data = resp.json()
        assert data["total"] >= 1

        # Collect all member doc_ids across communities
        communities = data["communities"]
        all_member_ids: set[str] = set()
        for c in communities:
            members = {m["doc_id"] for m in c["members"]}
            all_member_ids.update(members)

        # Connected documents (A, B, C, D) must appear
        connected_ids = {"doc-A", "doc-B", "doc-C", "doc-D"}
        assert connected_ids.issubset(all_member_ids)

        # Isolated doc-E has no edges, so label propagation excludes it
        assert "doc-E" not in all_member_ids

    def test_importance_ranking_order(
        self,
        koji_client: KojiClient,
        test_client: TestClient,
    ) -> None:
        """Most-connected node ranks highest in PageRank importance.

        doc-A has the most edges (outgoing: references B, similar_to D;
        incoming: similar_to from D) so it should appear at or near the
        top. doc-E (isolated) should rank lowest.
        """
        _seed_rich_graph(koji_client)

        resp = test_client.get("/api/graph/importance")
        assert resp.status_code == 200

        data = resp.json()
        assert data["total"] > 0

        documents = data["documents"]

        # Scores are in descending order
        scores = [d["pagerank_score"] for d in documents]
        assert scores == sorted(scores, reverse=True)

        doc_ids = [d["doc_id"] for d in documents]

        # doc-E is isolated and should rank below all connected nodes
        if "doc-E" in doc_ids:
            e_idx = doc_ids.index("doc-E")
            # At least A, B, C, D should rank above E
            connected_ids = {"doc-A", "doc-B", "doc-C", "doc-D"}
            for did in connected_ids:
                if did in doc_ids:
                    assert doc_ids.index(did) < e_idx, (
                        f"{did} should rank higher than isolated doc-E"
                    )

    def test_reading_order_returns_all_documents(
        self,
        koji_client: KojiClient,
        test_client: TestClient,
    ) -> None:
        """Reading order includes edge-connected documents with sequential positions.

        Graph algorithms (topological sort / pagerank) only include nodes
        that participate in edges. Isolated doc-E has no edges and is
        excluded. The 4 connected documents (A, B, C, D) should appear
        with 1-based sequential positions.
        """
        _seed_rich_graph(koji_client)

        resp = test_client.get("/api/graph/reading-order")
        assert resp.status_code == 200

        data = resp.json()
        assert data["method"] in ("topological", "pagerank")
        assert data["total"] == 4

        order = data["order"]
        order_ids = {d["doc_id"] for d in order}
        assert order_ids == {"doc-A", "doc-B", "doc-C", "doc-D"}

        # Isolated doc-E is excluded from graph algorithm output
        assert "doc-E" not in order_ids

        # Positions are 1-based and sequential
        positions = [d["position"] for d in order]
        assert positions == list(range(1, 5))

        # Each entry carries filename and format
        for entry in order:
            assert entry["filename"] is not None
            assert entry["format"] == "pdf"
