"""Tests for RelationBuilder — automatic relation detection at ingest time."""

import pytest

from src.core.testing.mocks import MockKojiClient
from src.processing.relation_builder import RelationBuilder


@pytest.fixture
def client():
    """Create and open a MockKojiClient with pre-existing documents."""
    c = MockKojiClient()
    c.open()
    return c


@pytest.fixture
def builder(client):
    """Create a RelationBuilder backed by the mock client."""
    return RelationBuilder(storage_client=client)


class TestDetectVersionOf:
    """Tests for version_of relation detection."""

    def test_detect_version_of(self, client, builder):
        """Same base filename triggers version_of relation."""
        client.create_document(doc_id="doc-old", filename="report.pdf", format="pdf")
        client.create_document(doc_id="doc-new", filename="report.docx", format="docx")

        created = builder.build_relations(
            doc_id="doc-new", filename="report.docx", chunks=[],
        )

        assert len(created) == 1
        assert created[0]["relation_type"] == "version_of"
        assert created[0]["dst_doc_id"] == "doc-old"

    def test_detect_version_of_case_insensitive(self, client, builder):
        """Base filename comparison is case-insensitive."""
        client.create_document(doc_id="doc-old", filename="Report.PDF", format="pdf")
        client.create_document(doc_id="doc-new", filename="report.docx", format="docx")

        created = builder.build_relations(
            doc_id="doc-new", filename="report.docx", chunks=[],
        )

        assert len(created) == 1
        assert created[0]["relation_type"] == "version_of"

    def test_detect_version_of_no_match(self, client, builder):
        """Unique filename produces no version_of relations."""
        client.create_document(doc_id="doc-old", filename="budget.xlsx", format="xlsx")
        client.create_document(doc_id="doc-new", filename="report.pdf", format="pdf")

        created = builder.build_relations(
            doc_id="doc-new", filename="report.pdf", chunks=[],
        )

        version_rels = [r for r in created if r["relation_type"] == "version_of"]
        assert len(version_rels) == 0


class TestDetectReferences:
    """Tests for references relation detection."""

    def test_detect_references_found(self, client, builder):
        """Chunk text mentioning another document's filename triggers references."""
        client.create_document(doc_id="doc-budget", filename="budget.xlsx", format="xlsx")
        client.create_document(doc_id="doc-new", filename="report.pdf", format="pdf")

        chunks = [
            {"id": "doc-new-chunk0001", "text": "As detailed in budget.xlsx, costs rose 15%."},
        ]

        created = builder.build_relations(
            doc_id="doc-new", filename="report.pdf", chunks=chunks,
        )

        ref_rels = [r for r in created if r["relation_type"] == "references"]
        assert len(ref_rels) == 1
        assert ref_rels[0]["dst_doc_id"] == "doc-budget"

    def test_detect_references_no_match(self, client, builder):
        """Chunk text without known filenames produces no references."""
        client.create_document(doc_id="doc-other", filename="budget.xlsx", format="xlsx")
        client.create_document(doc_id="doc-new", filename="report.pdf", format="pdf")

        chunks = [
            {"id": "doc-new-chunk0001", "text": "Revenue increased significantly this quarter."},
        ]

        created = builder.build_relations(
            doc_id="doc-new", filename="report.pdf", chunks=chunks,
        )

        ref_rels = [r for r in created if r["relation_type"] == "references"]
        assert len(ref_rels) == 0

    def test_detect_references_deduplicates(self, client, builder):
        """Same filename in multiple chunks creates only one references relation."""
        client.create_document(doc_id="doc-budget", filename="budget.xlsx", format="xlsx")
        client.create_document(doc_id="doc-new", filename="report.pdf", format="pdf")

        chunks = [
            {"id": "doc-new-chunk0001", "text": "See budget.xlsx for details."},
            {"id": "doc-new-chunk0002", "text": "Refer to budget.xlsx again here."},
            {"id": "doc-new-chunk0003", "text": "As budget.xlsx shows clearly."},
        ]

        created = builder.build_relations(
            doc_id="doc-new", filename="report.pdf", chunks=chunks,
        )

        ref_rels = [r for r in created if r["relation_type"] == "references"]
        assert len(ref_rels) == 1


class TestBuildRelations:
    """Tests for the top-level build_relations method."""

    def test_failure_isolation(self, client):
        """create_relation failure does not propagate from build_relations."""
        client.create_document(doc_id="doc-new", filename="report.pdf", format="pdf")

        # Create a builder with a client whose create_relation always raises
        class BrokenClient:
            def list_documents(self, **kwargs):
                return [{"doc_id": "doc-old", "filename": "report.docx"}]

            def create_relation(self, **kwargs):
                raise RuntimeError("DB on fire")

        builder = RelationBuilder(storage_client=BrokenClient())
        # Should not raise
        created = builder.build_relations(
            doc_id="doc-new", filename="report.pdf", chunks=[],
        )
        assert len(created) == 0

    def test_returns_created_relations(self, client, builder):
        """Return value contains all successfully created relations."""
        client.create_document(doc_id="doc-old", filename="report.docx", format="docx")
        client.create_document(doc_id="doc-budget", filename="budget.xlsx", format="xlsx")
        client.create_document(doc_id="doc-new", filename="report.pdf", format="pdf")

        chunks = [
            {"id": "doc-new-chunk0001", "text": "Refer to budget.xlsx for numbers."},
        ]

        created = builder.build_relations(
            doc_id="doc-new", filename="report.pdf", chunks=chunks,
        )

        types = {r["relation_type"] for r in created}
        assert "version_of" in types
        assert "references" in types
        assert all("src_doc_id" in r for r in created)
        assert all("dst_doc_id" in r for r in created)
