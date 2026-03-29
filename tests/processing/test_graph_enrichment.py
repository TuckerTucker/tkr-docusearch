"""Tests for GraphEnrichmentService.

Validates the batch graph enrichment pipeline using MockKojiClient.
Since MockKojiClient raises KojiQueryError for raw SQL queries,
steps that depend on query() (compute_similar_to, compute_same_topic)
return 0 gracefully because the service catches KojiQueryError
in its internal helpers.
"""

import json

import pytest

from src.config.graph_config import GraphEnrichmentConfig
from src.core.testing.mocks import MockKojiClient
from src.processing.graph_enrichment import GraphEnrichmentService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_client():
    """Create and open a MockKojiClient."""
    client = MockKojiClient()
    client.open()
    return client


@pytest.fixture
def config():
    """Create a GraphEnrichmentConfig with explicit thresholds."""
    return GraphEnrichmentConfig(
        similarity_threshold=0.7,
        similarity_top_k=3,
        same_topic_jaccard_threshold=0.5,
        max_community_full_connect=20,
        enrichment_interval_seconds=3600,
    )


@pytest.fixture
def service(mock_client, config):
    """Create a GraphEnrichmentService backed by MockKojiClient."""
    return GraphEnrichmentService(
        storage_client=mock_client,
        config=config,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_cluster(client, doc_pairs):
    """Create documents and bidirectional relations for a list of pairs.

    Args:
        client: MockKojiClient instance.
        doc_pairs: List of (src_id, dst_id, relation_type) tuples.
            Documents are auto-created if they don't already exist.
    """
    seen = set()
    for src, dst, rel_type in doc_pairs:
        for doc_id in (src, dst):
            if doc_id not in seen:
                if client.get_document(doc_id) is None:
                    client.create_document(
                        doc_id=doc_id,
                        filename=f"{doc_id}.pdf",
                        format="pdf",
                    )
                seen.add(doc_id)
        client.create_relation(src, dst, rel_type)
        client.create_relation(dst, src, rel_type)


# ===========================================================================
# TestComputeOverlapsTopic
# ===========================================================================


class TestComputeOverlapsTopic:
    """Tests for compute_overlaps_topic (label propagation community edges)."""

    def test_overlaps_topic_creates_edges(self, mock_client, service):
        """Documents in the same community receive overlaps_topic edges.

        Creates two disconnected clusters (A<->B, C<->D). Label propagation
        assigns each cluster a separate community. overlaps_topic edges are
        created within each cluster but not across clusters.
        """
        _create_cluster(mock_client, [
            ("doc-a", "doc-b", "references"),
            ("doc-c", "doc-d", "references"),
        ])

        created = service.compute_overlaps_topic()

        # Each cluster of 2 produces 2 directed edges (A->B, B->A)
        # Two clusters -> 4 total edges
        assert created == 4

        # Verify edges are overlaps_topic type
        rels_a = mock_client.get_relations("doc-a", relation_type="overlaps_topic")
        assert len(rels_a) >= 1
        targets_a = {r["dst_doc_id"] for r in rels_a if r["src_doc_id"] == "doc-a"}
        assert "doc-b" in targets_a

        rels_c = mock_client.get_relations("doc-c", relation_type="overlaps_topic")
        assert len(rels_c) >= 1
        targets_c = {r["dst_doc_id"] for r in rels_c if r["src_doc_id"] == "doc-c"}
        assert "doc-d" in targets_c

        # No cross-cluster edge
        all_targets_a = {
            r["dst_doc_id"]
            for r in mock_client.get_relations("doc-a", relation_type="overlaps_topic")
            if r["src_doc_id"] == "doc-a"
        }
        assert "doc-c" not in all_targets_a
        assert "doc-d" not in all_targets_a

    def test_overlaps_topic_empty_graph(self, mock_client, service):
        """Empty graph returns 0 and does not crash."""
        created = service.compute_overlaps_topic()

        assert created == 0


# ===========================================================================
# TestComputeNodeProperties
# ===========================================================================


class TestComputeNodeProperties:
    """Tests for compute_node_properties (PageRank, community, hub score)."""

    def test_node_properties_stores_in_metadata(self, mock_client, service):
        """Graph analytics are written into each document's metadata["graph"].

        Creates a 3-node chain (A->B->C) and verifies that after running
        compute_node_properties, every document has graph metadata with
        expected keys.
        """
        for doc_id in ("doc-a", "doc-b", "doc-c"):
            mock_client.create_document(
                doc_id=doc_id,
                filename=f"{doc_id}.pdf",
                format="pdf",
            )
        mock_client.create_relation("doc-a", "doc-b", "references")
        mock_client.create_relation("doc-b", "doc-c", "references")

        updated = service.compute_node_properties()

        assert updated == 3

        expected_keys = {"pagerank_score", "community_id", "hub_score", "enriched_at"}
        for doc_id in ("doc-a", "doc-b", "doc-c"):
            doc = mock_client.get_document(doc_id)
            assert doc is not None, f"Document {doc_id} not found"

            metadata = doc.get("metadata")
            assert metadata is not None, f"No metadata on {doc_id}"

            # metadata may be dict or JSON string depending on update path
            if isinstance(metadata, str):
                metadata = json.loads(metadata)

            graph = metadata.get("graph")
            assert graph is not None, f"No graph key in metadata for {doc_id}"
            assert set(graph.keys()) == expected_keys

            assert isinstance(graph["pagerank_score"], float)
            assert isinstance(graph["hub_score"], int)
            assert graph["enriched_at"] is not None

    def test_node_properties_empty_db(self, mock_client, service):
        """Empty database returns 0 and does not crash."""
        updated = service.compute_node_properties()

        assert updated == 0


# ===========================================================================
# TestDeleteRelationsByType
# ===========================================================================


class TestDeleteRelationsByType:
    """Tests for idempotent delete-then-recreate pattern."""

    def test_idempotent_rerun(self, mock_client, service):
        """Running compute_overlaps_topic twice produces the same edge count.

        The service deletes all overlaps_topic edges before recreating,
        so a second run yields identical results.
        """
        _create_cluster(mock_client, [
            ("doc-a", "doc-b", "references"),
            ("doc-c", "doc-d", "references"),
        ])

        first_count = service.compute_overlaps_topic()
        second_count = service.compute_overlaps_topic()

        assert first_count == second_count

        # Verify no duplicate edges exist
        overlaps = [
            r for r in mock_client._relations
            if r["relation_type"] == "overlaps_topic"
        ]
        # 2 clusters * 2 directed edges each = 4
        assert len(overlaps) == 4


# ===========================================================================
# TestRunFullEnrichment
# ===========================================================================


class TestRunFullEnrichment:
    """Tests for run_full_enrichment orchestration."""

    def test_full_enrichment_returns_summary(self, mock_client, service):
        """Full enrichment completes and returns a summary dict.

        All four steps complete without errors on MockKojiClient.
        Steps using raw SQL (similar_to, same_topic) return 0 because
        KojiQueryError is caught internally, not propagated.
        """
        _create_cluster(mock_client, [
            ("doc-a", "doc-b", "references"),
        ])

        result = service.run_full_enrichment()

        # Required keys are present
        assert "similar_to" in result
        assert "same_topic" in result
        assert "overlaps_topic" in result
        assert "node_properties" in result
        assert "total_ms" in result
        assert "errors" in result

        # total_ms is a positive number
        assert isinstance(result["total_ms"], float)
        assert result["total_ms"] >= 0

        # No step should have errored (KojiQueryError is caught internally)
        assert result["errors"] == {}

        # SQL-dependent steps return 0 on mock
        assert result["similar_to"] == 0
        assert result["same_topic"] == 0

        # Graph-native steps produce real results
        assert result["overlaps_topic"] >= 0
        assert result["node_properties"] >= 0

    def test_full_enrichment_empty_db(self, mock_client, service):
        """Full enrichment on an empty database completes without error."""
        result = service.run_full_enrichment()

        assert isinstance(result, dict)
        assert "total_ms" in result
        assert result["errors"] == {}
        assert result["similar_to"] == 0
        assert result["same_topic"] == 0
        assert result["overlaps_topic"] == 0
        assert result["node_properties"] == 0


# ===========================================================================
# TestComputeSimilarTo
# ===========================================================================


class TestComputeSimilarTo:
    """Tests for compute_similar_to (embedding similarity edges)."""

    def test_similar_to_returns_zero_on_mock(self, mock_client, service):
        """MockKojiClient raises KojiQueryError for raw SQL.

        compute_similar_to calls _fetch_all_doc_ids which uses query().
        KojiQueryError is caught internally, returning an empty doc list,
        so the method returns 0 without crashing.
        """
        mock_client.create_document(
            doc_id="doc-a", filename="a.pdf", format="pdf",
        )

        result = service.compute_similar_to()

        assert result == 0


# ===========================================================================
# TestComputeSameTopic
# ===========================================================================


class TestComputeSameTopic:
    """Tests for compute_same_topic (heading Jaccard edges)."""

    def test_same_topic_returns_zero_on_mock(self, mock_client, service):
        """MockKojiClient raises KojiQueryError for raw SQL.

        compute_same_topic calls _build_doc_heading_sets which uses query().
        KojiQueryError is caught internally, returning an empty heading map,
        so the method returns 0 without crashing.
        """
        mock_client.create_document(
            doc_id="doc-a", filename="a.pdf", format="pdf",
        )
        mock_client.create_document(
            doc_id="doc-b", filename="b.pdf", format="pdf",
        )

        result = service.compute_same_topic()

        assert result == 0
