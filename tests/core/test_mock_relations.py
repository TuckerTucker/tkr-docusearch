"""Tests for MockKojiClient relation methods.

Validates that the mock mirrors the real KojiClient relation behavior,
enabling reliable unit tests for all graph-dependent code.
"""

import pytest

from src.core.testing.mocks import MockKojiClient
from src.storage.koji_client import KojiDuplicateError


@pytest.fixture
def client():
    """Create and open a MockKojiClient."""
    c = MockKojiClient()
    c.open()
    return c


def _create_two_docs(client: MockKojiClient) -> None:
    """Helper: create two test documents."""
    client.create_document(doc_id="doc-A", filename="a.pdf", format="pdf")
    client.create_document(doc_id="doc-B", filename="b.pdf", format="pdf")


class TestMockRelations:
    """Verify MockKojiClient relation CRUD mirrors real KojiClient."""

    def test_create_relation(self, client):
        """Create a relation and retrieve it."""
        _create_two_docs(client)

        client.create_relation(
            src_doc_id="doc-A",
            dst_doc_id="doc-B",
            relation_type="references",
        )

        relations = client.get_relations("doc-A", direction="outgoing")
        assert len(relations) == 1
        assert relations[0]["dst_doc_id"] == "doc-B"
        assert relations[0]["relation_type"] == "references"

    def test_create_relation_missing_doc(self, client):
        """ValueError when a referenced document does not exist."""
        client.create_document(doc_id="doc-A", filename="a.pdf", format="pdf")

        with pytest.raises(ValueError, match="not found"):
            client.create_relation(
                src_doc_id="doc-A",
                dst_doc_id="nonexistent",
                relation_type="references",
            )

    def test_create_relation_duplicate(self, client):
        """KojiDuplicateError on duplicate relation."""
        _create_two_docs(client)

        client.create_relation(
            src_doc_id="doc-A",
            dst_doc_id="doc-B",
            relation_type="references",
        )

        with pytest.raises(KojiDuplicateError):
            client.create_relation(
                src_doc_id="doc-A",
                dst_doc_id="doc-B",
                relation_type="references",
            )

    def test_get_relations_directions(self, client):
        """Test outgoing, incoming, and both directions."""
        _create_two_docs(client)

        client.create_relation(
            src_doc_id="doc-A",
            dst_doc_id="doc-B",
            relation_type="references",
        )

        outgoing = client.get_relations("doc-A", direction="outgoing")
        assert len(outgoing) == 1

        incoming = client.get_relations("doc-A", direction="incoming")
        assert len(incoming) == 0

        incoming_b = client.get_relations("doc-B", direction="incoming")
        assert len(incoming_b) == 1

        both_b = client.get_relations("doc-B", direction="both")
        assert len(both_b) == 1

    def test_delete_relation(self, client):
        """Create then delete a relation."""
        _create_two_docs(client)

        client.create_relation(
            src_doc_id="doc-A",
            dst_doc_id="doc-B",
            relation_type="references",
        )

        client.delete_relation(
            src_doc_id="doc-A",
            dst_doc_id="doc-B",
            relation_type="references",
        )

        relations = client.get_relations("doc-A")
        assert len(relations) == 0

    def test_get_related_documents_recursive(self, client):
        """BFS traversal across a 3-doc chain."""
        client.create_document(doc_id="doc-A", filename="a.pdf", format="pdf")
        client.create_document(doc_id="doc-B", filename="b.pdf", format="pdf")
        client.create_document(doc_id="doc-C", filename="c.pdf", format="pdf")

        client.create_relation(
            src_doc_id="doc-A",
            dst_doc_id="doc-B",
            relation_type="references",
        )
        client.create_relation(
            src_doc_id="doc-B",
            dst_doc_id="doc-C",
            relation_type="related",
        )

        related = client.get_related_documents("doc-A", max_depth=3)
        doc_ids = [r["doc_id"] for r in related]
        assert "doc-B" in doc_ids
        assert "doc-C" in doc_ids

        depths = {r["doc_id"]: r["depth"] for r in related}
        assert depths["doc-B"] == 1
        assert depths["doc-C"] == 2

        # Depth-limited
        shallow = client.get_related_documents("doc-A", max_depth=1)
        assert len(shallow) == 1
        assert shallow[0]["doc_id"] == "doc-B"

    def test_delete_document_cascades_relations(self, client):
        """Deleting a document removes all its relations."""
        _create_two_docs(client)

        client.create_relation(
            src_doc_id="doc-A",
            dst_doc_id="doc-B",
            relation_type="references",
        )

        client.delete_document("doc-A")

        # Relation should be gone from both sides
        relations_b = client.get_relations("doc-B", direction="incoming")
        assert len(relations_b) == 0
