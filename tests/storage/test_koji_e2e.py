"""End-to-end tests for KojiClient document lifecycle.

Tests exercise full workflows spanning multiple operations to verify
that the Koji 0.2.0 API integration works correctly across create,
update, delete, and graph operations.
"""

import pytest

from tkr_docusearch.config.koji_config import KojiConfig
from tkr_docusearch.storage.koji_client import KojiClient


@pytest.fixture
def config(tmp_path):
    """Create a KojiConfig pointing to a temporary database."""
    return KojiConfig(db_path=str(tmp_path / "test_e2e.db"))


@pytest.fixture
def client(config):
    """Create and open a KojiClient with a temporary database."""
    c = KojiClient(config)
    c.open()
    yield c
    c.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pages(doc_id: str, count: int) -> list[dict]:
    """Generate page dicts for a document.

    Args:
        doc_id: Document identifier.
        count: Number of pages to generate.

    Returns:
        List of page dictionaries with id, doc_id, and page_num.
    """
    return [
        {
            "id": f"{doc_id}-page{i + 1:03d}",
            "doc_id": doc_id,
            "page_num": i + 1,
        }
        for i in range(count)
    ]


def _make_chunks(doc_id: str, count: int, page_num: int = 1) -> list[dict]:
    """Generate chunk dicts for a document.

    Args:
        doc_id: Document identifier.
        count: Number of chunks to generate.
        page_num: Page number to assign to all chunks.

    Returns:
        List of chunk dictionaries with id, doc_id, page_num, and text.
    """
    return [
        {
            "id": f"{doc_id}-chunk{i + 1:04d}",
            "doc_id": doc_id,
            "page_num": page_num,
            "text": f"Chunk {i + 1} text for {doc_id}",
        }
        for i in range(count)
    ]


# ---------------------------------------------------------------------------
# TestDocumentLifecycle
# ---------------------------------------------------------------------------

class TestDocumentLifecycle:
    """Full lifecycle tests for document create, update, and delete."""

    def test_create_update_delete_lifecycle(self, client):
        """Create a doc with metadata, update fields, verify, delete, confirm gone."""
        # Create
        client.create_document(
            doc_id="doc-lifecycle-01",
            filename="report.pdf",
            format="pdf",
            num_pages=10,
            metadata={"author": "Alice", "department": "Engineering"},
        )

        doc = client.get_document("doc-lifecycle-01")
        assert doc is not None, "Document should exist after creation"
        assert doc["filename"] == "report.pdf"
        assert doc["num_pages"] == 10
        assert doc["metadata"]["author"] == "Alice"

        # Update filename and num_pages
        client.update_document(
            "doc-lifecycle-01",
            filename="report-v2.pdf",
            num_pages=12,
        )

        doc = client.get_document("doc-lifecycle-01")
        assert doc["filename"] == "report-v2.pdf", (
            "Filename should reflect updated value"
        )
        assert doc["num_pages"] == 12, "num_pages should reflect updated value"

        # Delete
        client.delete_document("doc-lifecycle-01")

        assert client.get_document("doc-lifecycle-01") is None, (
            "Document should be gone after deletion"
        )

    def test_multi_document_isolation(self, client):
        """Create 3 docs with children, delete the middle one, verify isolation."""
        doc_ids = ["doc-iso-A", "doc-iso-B", "doc-iso-C"]

        for doc_id in doc_ids:
            client.create_document(
                doc_id=doc_id,
                filename=f"{doc_id}.pdf",
                format="pdf",
            )
            client.insert_pages(_make_pages(doc_id, count=2))
            client.insert_chunks(_make_chunks(doc_id, count=3))

        # Verify all exist
        for doc_id in doc_ids:
            assert client.get_document(doc_id) is not None
            assert len(client.get_pages_for_document(doc_id)) == 2
            assert len(client.get_chunks_for_document(doc_id)) == 3

        # Delete the middle document
        client.delete_document("doc-iso-B")

        # Middle doc and its children are gone
        assert client.get_document("doc-iso-B") is None, (
            "Deleted document should be gone"
        )
        assert len(client.get_pages_for_document("doc-iso-B")) == 0, (
            "Deleted document's pages should be gone"
        )
        assert len(client.get_chunks_for_document("doc-iso-B")) == 0, (
            "Deleted document's chunks should be gone"
        )

        # Remaining docs and ALL their children are intact
        for doc_id in ["doc-iso-A", "doc-iso-C"]:
            assert client.get_document(doc_id) is not None, (
                f"{doc_id} should survive deletion of doc-iso-B"
            )
            assert len(client.get_pages_for_document(doc_id)) == 2, (
                f"{doc_id} should still have 2 pages"
            )
            assert len(client.get_chunks_for_document(doc_id)) == 3, (
                f"{doc_id} should still have 3 chunks"
            )

    def test_update_then_delete_with_children(self, client):
        """Create doc with pages, chunks, and relation. Update, then delete."""
        # Create two docs: one will be the target, one the related
        client.create_document(
            doc_id="doc-upd-del",
            filename="main.pdf",
            format="pdf",
            num_pages=3,
        )
        client.create_document(
            doc_id="doc-upd-del-related",
            filename="related.pdf",
            format="pdf",
        )

        client.insert_pages(_make_pages("doc-upd-del", count=3))
        client.insert_chunks(_make_chunks("doc-upd-del", count=5))

        client.create_relation(
            src_doc_id="doc-upd-del",
            dst_doc_id="doc-upd-del-related",
            relation_type="references",
        )

        # Update a field on the document
        client.update_document("doc-upd-del", filename="main-revised.pdf")

        # After update: children and relation survived
        doc = client.get_document("doc-upd-del")
        assert doc["filename"] == "main-revised.pdf"
        assert len(client.get_pages_for_document("doc-upd-del")) == 3, (
            "Pages should survive document update"
        )
        assert len(client.get_chunks_for_document("doc-upd-del")) == 5, (
            "Chunks should survive document update"
        )
        relations = client.get_relations("doc-upd-del", direction="outgoing")
        assert len(relations) == 1, "Relation should survive document update"

        # Delete the document
        client.delete_document("doc-upd-del")

        # After delete: everything is gone
        assert client.get_document("doc-upd-del") is None
        assert len(client.get_pages_for_document("doc-upd-del")) == 0, (
            "Pages should be cascade-deleted"
        )
        assert len(client.get_chunks_for_document("doc-upd-del")) == 0, (
            "Chunks should be cascade-deleted"
        )
        # Outgoing relations from deleted doc should be gone
        outgoing = client.get_relations(
            "doc-upd-del-related", direction="incoming"
        )
        assert len(outgoing) == 0, (
            "Incoming relations pointing to deleted doc should be gone"
        )

    def test_reinsert_after_delete(self, client):
        """Create doc, delete it, re-create with same ID, verify clean slate."""
        # First version: doc with pages and chunks
        client.create_document(
            doc_id="doc-reinsert",
            filename="v1.pdf",
            format="pdf",
        )
        client.insert_pages(_make_pages("doc-reinsert", count=4))
        client.insert_chunks(_make_chunks("doc-reinsert", count=6))

        # Delete
        client.delete_document("doc-reinsert")

        # Re-create with same doc_id
        client.create_document(
            doc_id="doc-reinsert",
            filename="v2.pdf",
            format="pdf",
        )

        # Verify clean state: new doc exists, no leftover children
        doc = client.get_document("doc-reinsert")
        assert doc is not None, "Re-inserted document should exist"
        assert doc["filename"] == "v2.pdf", (
            "Re-inserted document should have the new filename"
        )
        assert len(client.get_pages_for_document("doc-reinsert")) == 0, (
            "Re-inserted document should have no leftover pages"
        )
        assert len(client.get_chunks_for_document("doc-reinsert")) == 0, (
            "Re-inserted document should have no leftover chunks"
        )


# ---------------------------------------------------------------------------
# TestRelationLifecycle
# ---------------------------------------------------------------------------

class TestRelationLifecycle:
    """Tests for relationship operations across the full lifecycle."""

    def _create_chain(self, client, ids: list[str]):
        """Create a linear chain of documents with relations: A -> B -> C ...

        Args:
            client: KojiClient instance.
            ids: Ordered list of doc_ids to chain together.
        """
        for doc_id in ids:
            client.create_document(
                doc_id=doc_id,
                filename=f"{doc_id}.pdf",
                format="pdf",
            )
        for i in range(len(ids) - 1):
            client.create_relation(
                src_doc_id=ids[i],
                dst_doc_id=ids[i + 1],
                relation_type="references",
            )

    def test_relation_survives_document_update(self, client):
        """Create 2 docs with a relation. Update doc1. Verify relation intact."""
        client.create_document(
            doc_id="doc-rel-surv-A",
            filename="a.pdf",
            format="pdf",
        )
        client.create_document(
            doc_id="doc-rel-surv-B",
            filename="b.pdf",
            format="pdf",
        )

        client.create_relation(
            src_doc_id="doc-rel-surv-A",
            dst_doc_id="doc-rel-surv-B",
            relation_type="cites",
        )

        # Update doc A
        client.update_document("doc-rel-surv-A", filename="a-updated.pdf")

        # Relation should still exist
        relations = client.get_relations(
            "doc-rel-surv-A", direction="outgoing"
        )
        assert len(relations) == 1, "Relation should survive document update"
        assert relations[0]["dst_doc_id"] == "doc-rel-surv-B"
        assert relations[0]["relation_type"] == "cites"

    def test_bidirectional_relation_cleanup(self, client):
        """Create A <-> B bidirectional relations. Delete A. Verify cleanup."""
        client.create_document(
            doc_id="doc-bidir-A", filename="a.pdf", format="pdf"
        )
        client.create_document(
            doc_id="doc-bidir-B", filename="b.pdf", format="pdf"
        )

        # A -> B
        client.create_relation(
            src_doc_id="doc-bidir-A",
            dst_doc_id="doc-bidir-B",
            relation_type="references",
        )
        # B -> A
        client.create_relation(
            src_doc_id="doc-bidir-B",
            dst_doc_id="doc-bidir-A",
            relation_type="references",
        )

        # Delete doc A
        client.delete_document("doc-bidir-A")

        # Both relations should be gone (A->B via src cascade, B->A via dst cascade)
        all_relations_for_b = client.get_relations(
            "doc-bidir-B", direction="both"
        )
        assert len(all_relations_for_b) == 0, (
            "Both directions of relation should be cleaned up on delete"
        )

        # Doc B should survive
        assert client.get_document("doc-bidir-B") is not None, (
            "Non-deleted document should survive"
        )

    def test_relation_chain_traversal_after_updates(self, client):
        """Create A->B->C chain, update B, verify traversal still works."""
        self._create_chain(
            client, ["doc-chain-A", "doc-chain-B", "doc-chain-C"]
        )

        # Update B's filename
        client.update_document("doc-chain-B", filename="b-updated.pdf")

        # Traversal from A should still find B and C at correct depths
        related = client.get_related_documents("doc-chain-A", max_depth=2)
        doc_ids = [r["doc_id"] for r in related]
        assert "doc-chain-B" in doc_ids, "B should be reachable from A"
        assert "doc-chain-C" in doc_ids, "C should be reachable from A"

        depths = {r["doc_id"]: r["depth"] for r in related}
        assert depths["doc-chain-B"] == 1, "B should be at depth 1"
        assert depths["doc-chain-C"] == 2, "C should be at depth 2"

        # Verify B has the updated filename in the traversal result
        b_result = next(r for r in related if r["doc_id"] == "doc-chain-B")
        assert b_result["filename"] == "b-updated.pdf", (
            "Updated filename should appear in traversal results"
        )

    def test_delete_middle_of_chain(self, client):
        """Create A->B->C chain. Delete B. Verify A and C survive, no path."""
        self._create_chain(
            client, ["doc-mid-A", "doc-mid-B", "doc-mid-C"]
        )

        # Delete the middle node
        client.delete_document("doc-mid-B")

        # A and C survive
        assert client.get_document("doc-mid-A") is not None, (
            "A should survive deletion of B"
        )
        assert client.get_document("doc-mid-C") is not None, (
            "C should survive deletion of B"
        )

        # B is gone
        assert client.get_document("doc-mid-B") is None, "B should be deleted"

        # A's relation to B is gone (src_doc_id cascade or manual cleanup)
        a_outgoing = client.get_relations("doc-mid-A", direction="outgoing")
        assert len(a_outgoing) == 0, (
            "A's outgoing relation to deleted B should be gone"
        )

        # B's relation to C is gone (B was deleted, relation was src_doc_id cascade)
        c_incoming = client.get_relations("doc-mid-C", direction="incoming")
        assert len(c_incoming) == 0, (
            "C's incoming relation from deleted B should be gone"
        )

        # Graph traversal from A returns empty
        related = client.get_related_documents("doc-mid-A", max_depth=3)
        assert len(related) == 0, (
            "No documents should be reachable from A after B is deleted"
        )


# ---------------------------------------------------------------------------
# TestBulkOperations
# ---------------------------------------------------------------------------

class TestBulkOperations:
    """Stress tests with larger data volumes."""

    def test_bulk_document_creation_and_deletion(self, client):
        """Create 20 docs with pages and chunks, delete every other, verify."""
        num_docs = 20
        pages_per_doc = 3
        chunks_per_doc = 5

        # Create all documents with children
        for i in range(num_docs):
            doc_id = f"doc-bulk-{i:04d}"
            client.create_document(
                doc_id=doc_id,
                filename=f"bulk-{i}.pdf",
                format="pdf",
                num_pages=pages_per_doc,
            )
            client.insert_pages(_make_pages(doc_id, count=pages_per_doc))
            client.insert_chunks(_make_chunks(doc_id, count=chunks_per_doc))

        # Verify all 20 exist
        all_docs = client.list_documents(limit=100)
        assert len(all_docs) == num_docs, (
            f"Expected {num_docs} documents after creation"
        )

        # Delete every other document (even indices)
        deleted_ids = set()
        surviving_ids = set()
        for i in range(num_docs):
            doc_id = f"doc-bulk-{i:04d}"
            if i % 2 == 0:
                client.delete_document(doc_id)
                deleted_ids.add(doc_id)
            else:
                surviving_ids.add(doc_id)

        # Verify 10 remain
        remaining_docs = client.list_documents(limit=100)
        assert len(remaining_docs) == 10, "10 documents should remain"

        remaining_ids = {d["doc_id"] for d in remaining_docs}
        assert remaining_ids == surviving_ids, (
            "Only odd-indexed documents should survive"
        )

        # Verify each surviving doc has correct page/chunk counts
        for doc_id in surviving_ids:
            pages = client.get_pages_for_document(doc_id)
            assert len(pages) == pages_per_doc, (
                f"{doc_id} should still have {pages_per_doc} pages"
            )
            chunks = client.get_chunks_for_document(doc_id)
            assert len(chunks) == chunks_per_doc, (
                f"{doc_id} should still have {chunks_per_doc} chunks"
            )

        # Verify deleted docs are truly gone
        for doc_id in deleted_ids:
            assert client.get_document(doc_id) is None, (
                f"{doc_id} should be deleted"
            )
            assert len(client.get_pages_for_document(doc_id)) == 0, (
                f"{doc_id} pages should be cascade-deleted"
            )
            assert len(client.get_chunks_for_document(doc_id)) == 0, (
                f"{doc_id} chunks should be cascade-deleted"
            )

    def test_concurrent_updates(self, client):
        """Update different fields 10 times in sequence, verify final state."""
        client.create_document(
            doc_id="doc-seq-updates",
            filename="original.pdf",
            format="pdf",
            num_pages=1,
            markdown="# Original",
        )

        # Alternate updates across different fields
        expected_filename = None
        expected_num_pages = None
        expected_markdown = None

        for i in range(10):
            if i % 3 == 0:
                expected_filename = f"version-{i}.pdf"
                client.update_document(
                    "doc-seq-updates", filename=expected_filename
                )
            elif i % 3 == 1:
                expected_num_pages = i * 10
                client.update_document(
                    "doc-seq-updates", num_pages=expected_num_pages
                )
            else:
                expected_markdown = f"# Version {i}"
                client.update_document(
                    "doc-seq-updates", markdown=expected_markdown
                )

        # Verify final state has all the latest values
        doc = client.get_document("doc-seq-updates")
        assert doc is not None, "Document should exist after sequential updates"
        assert doc["filename"] == expected_filename, (
            f"Filename should be '{expected_filename}', got '{doc['filename']}'"
        )
        assert doc["num_pages"] == expected_num_pages, (
            f"num_pages should be {expected_num_pages}, got {doc['num_pages']}"
        )
        assert doc["markdown"] == expected_markdown, (
            f"markdown should be '{expected_markdown}', "
            f"got '{doc['markdown']}'"
        )

        # Verify no corruption: format and doc_id unchanged
        assert doc["doc_id"] == "doc-seq-updates"
        assert doc["format"] == "pdf"
        assert doc["created_at"] is not None
