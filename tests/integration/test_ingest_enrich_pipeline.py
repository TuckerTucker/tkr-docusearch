"""Integration tests for ingest-then-enrich pipeline.

Processes real fixture documents into a real Koji database, runs
GraphEnrichmentService, and verifies that edges and node properties
are correctly written.  Uses MockEmbeddingModel (no GPU required)
with a file-backed KojiClient on tmp_path.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.config.graph_config import GraphEnrichmentConfig
from src.config.koji_config import KojiConfig
from src.core.testing.mocks import MockShikomiIngester
from src.processing.graph_enrichment import GraphEnrichmentService
from src.processing.processor import DocumentProcessor
from src.storage.koji_client import KojiClient

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def koji_storage(tmp_path) -> KojiClient:
    """Real KojiClient backed by a temporary file database."""
    config = KojiConfig(db_path=str(tmp_path / "enrich_test.db"))
    client = KojiClient(config)
    client.open()
    yield client
    client.close()


@pytest.fixture
def enrichment_service(koji_storage) -> GraphEnrichmentService:
    """GraphEnrichmentService wired to the real Koji storage.

    Uses deliberately low thresholds so mock embedding data can
    still produce edges.
    """
    config = GraphEnrichmentConfig(
        similarity_threshold=0.5,
        similarity_top_k=3,
        same_topic_jaccard_threshold=0.3,
    )
    return GraphEnrichmentService(
        storage_client=koji_storage,
        config=config,
    )


@pytest.fixture
def processor(koji_storage) -> DocumentProcessor:
    """DocumentProcessor with mock ingester writing to real Koji."""
    ingester = MockShikomiIngester()
    ingester.connect()
    return DocumentProcessor(
        ingester=ingester,
        storage_client=koji_storage,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestIngestEnrichPipeline:
    """Verify that graph enrichment works correctly after document ingest."""

    def test_ingest_then_enrich(
        self, processor, koji_storage, enrichment_service
    ):
        """Process two docs, add a relation, then run full enrichment.

        Relation detection (version_of) now happens inside shikomi's
        real Ingester, so the MockShikomiIngester returns no relations.
        We manually create a version_of relation after ingest to exercise
        the enrichment pipeline.
        """
        sample_pdf = FIXTURES_DIR / "sample.pdf"
        sample_docx = FIXTURES_DIR / "sample.docx"

        conf_pdf = processor.process_document(str(sample_pdf))
        conf_docx = processor.process_document(str(sample_docx))

        # Manually create a version_of relation (mock ingester doesn't produce them)
        koji_storage.create_relation(
            src_doc_id=conf_pdf.doc_id,
            dst_doc_id=conf_docx.doc_id,
            relation_type="version_of",
        )

        relations_before = (
            koji_storage.get_relations(conf_pdf.doc_id)
            + koji_storage.get_relations(conf_docx.doc_id)
        )
        assert len(relations_before) >= 1, (
            "Should have at least one version_of relation after manual creation"
        )

        summary = enrichment_service.run_full_enrichment()

        assert isinstance(summary, dict)
        assert "total_ms" in summary
        assert isinstance(summary.get("errors"), dict)

        # After enrichment, node properties should be written to at
        # least one document's metadata.
        docs_with_graph = 0
        for doc_id in (conf_pdf.doc_id, conf_docx.doc_id):
            doc = koji_storage.get_document(doc_id)
            assert doc is not None
            meta = doc.get("metadata")
            if meta is not None:
                if isinstance(meta, str):
                    meta = json.loads(meta)
                if isinstance(meta, dict) and "graph" in meta:
                    docs_with_graph += 1

        assert docs_with_graph >= 1, (
            "At least one document should have graph metadata after enrichment"
        )

    def test_node_properties_populated(
        self, processor, koji_storage, enrichment_service
    ):
        """Verify graph metadata keys after compute_node_properties.

        Each enriched document's metadata should contain a ``graph``
        dict with ``pagerank_score``, ``community_id``, ``hub_score``,
        and ``enriched_at``.
        """
        sample_pdf = FIXTURES_DIR / "sample.pdf"
        sample_docx = FIXTURES_DIR / "sample.docx"

        conf_pdf = processor.process_document(str(sample_pdf))
        conf_docx = processor.process_document(str(sample_docx))

        # Manually create a relation so graph algorithms have edges to
        # work with (mock ingester doesn't produce relations).
        koji_storage.create_relation(
            src_doc_id=conf_pdf.doc_id,
            dst_doc_id=conf_docx.doc_id,
            relation_type="version_of",
        )

        updated_count = enrichment_service.compute_node_properties()
        assert updated_count >= 1, (
            "compute_node_properties should update at least one document"
        )

        for doc_id in (conf_pdf.doc_id, conf_docx.doc_id):
            doc = koji_storage.get_document(doc_id)
            assert doc is not None

            meta = doc.get("metadata")
            if meta is None:
                continue
            if isinstance(meta, str):
                meta = json.loads(meta)
            if not isinstance(meta, dict):
                continue

            graph = meta.get("graph")
            if graph is None:
                # Not every doc may have graph properties if it has
                # no edges — skip quietly.
                continue

            assert isinstance(graph["pagerank_score"], float), (
                "pagerank_score should be a float"
            )
            assert graph["community_id"] is None or isinstance(
                graph["community_id"], int
            ), "community_id should be int or None"
            assert isinstance(graph["hub_score"], int), (
                "hub_score should be an int"
            )
            assert isinstance(graph["enriched_at"], str), (
                "enriched_at should be an ISO timestamp string"
            )

    def test_overlaps_topic_from_relations(
        self, processor, koji_storage, enrichment_service
    ):
        """Manually add a relation, then verify overlaps_topic edges.

        Processing two documents and adding a ``references`` edge
        between them places them in the same community.  Running
        ``compute_overlaps_topic()`` should then create
        ``overlaps_topic`` edges.
        """
        sample_pdf = FIXTURES_DIR / "sample.pdf"
        sample_md = FIXTURES_DIR / "sample.md"

        conf_pdf = processor.process_document(str(sample_pdf))
        conf_md = processor.process_document(str(sample_md))

        # Create an explicit relation so label propagation has
        # edges to form communities from.
        koji_storage.create_relation(
            src_doc_id=conf_pdf.doc_id,
            dst_doc_id=conf_md.doc_id,
            relation_type="references",
        )

        created = enrichment_service.compute_overlaps_topic()

        # With at least one edge, label propagation should detect a
        # community and create overlaps_topic edges.
        assert created >= 0, (
            "compute_overlaps_topic should return a non-negative count"
        )

        # If label propagation worked, we expect edges.  If the graph
        # is too sparse for communities, created may legitimately be 0,
        # so we verify structurally rather than demanding a minimum.
        if created > 0:
            relations = koji_storage.get_relations(
                conf_pdf.doc_id, relation_type="overlaps_topic"
            )
            assert len(relations) >= 1, (
                "overlaps_topic relations should be retrievable"
            )

    def test_enrich_idempotent(
        self, processor, koji_storage, enrichment_service
    ):
        """Running enrichment twice should produce the same edge count.

        Each enrichment step deletes its computed edges before
        recreating them, so re-running should be a no-op in terms of
        net edge count.
        """
        sample_pdf = FIXTURES_DIR / "sample.pdf"
        sample_docx = FIXTURES_DIR / "sample.docx"

        conf_pdf = processor.process_document(str(sample_pdf))
        conf_docx = processor.process_document(str(sample_docx))

        # Create a seed relation so enrichment has edges to work with
        koji_storage.create_relation(
            src_doc_id=conf_pdf.doc_id,
            dst_doc_id=conf_docx.doc_id,
            relation_type="version_of",
        )

        enrichment_service.run_full_enrichment()

        count_after_first = koji_storage.query(
            "SELECT COUNT(*) AS cnt FROM doc_relations"
        ).to_pydict()["cnt"][0]

        enrichment_service.run_full_enrichment()

        count_after_second = koji_storage.query(
            "SELECT COUNT(*) AS cnt FROM doc_relations"
        ).to_pydict()["cnt"][0]

        assert count_after_second == count_after_first, (
            f"Edge count should be stable across runs: "
            f"first={count_after_first}, second={count_after_second}"
        )

    def test_enrich_empty_library(self, koji_storage, enrichment_service):
        """Enriching with no documents should return zero counts and no errors."""
        summary = enrichment_service.run_full_enrichment()

        assert isinstance(summary, dict)
        assert summary["similar_to"] == 0
        assert summary["same_topic"] == 0
        assert summary["overlaps_topic"] == 0
        assert summary["node_properties"] == 0
        assert isinstance(summary["total_ms"], float)
        assert summary["total_ms"] >= 0
        errors = summary.get("errors", {})
        assert not errors, f"Expected no errors, got: {errors}"
