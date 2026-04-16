"""
Unit tests for KojiClient.

Tests cover:
- Connection lifecycle (open, close)
- Document CRUD (create, get, update, delete)
- Page and chunk operations
- Relationship operations
- Multi-vector packing/unpacking
- Health check
- Raw SQL queries
- Validation and error handling
"""

import pytest

from tkr_docusearch.config.koji_config import KojiConfig
from tkr_docusearch.storage.koji_client import (
    KojiClient,
    KojiConnectionError,
    KojiDuplicateError,
    pack_multivec,
    unpack_multivec,
)


@pytest.fixture
def config(tmp_path):
    """Create a KojiConfig pointing to a temporary database."""
    return KojiConfig(db_path=str(tmp_path / "test.db"))


@pytest.fixture
def client(config):
    """Create and open a KojiClient with a temporary database."""
    c = KojiClient(config)
    c.open()
    yield c
    c.close()


class TestLifecycle:
    """Test connection lifecycle."""

    def test_open_close(self, config):
        """Open, verify tables exist, close, verify closed."""
        c = KojiClient(config)
        c.open()

        health = c.health_check()
        assert health["connected"] is True
        assert "documents" in health["tables"]
        assert "pages" in health["tables"]
        assert "chunks" in health["tables"]
        assert "doc_relations" in health["tables"]

        c.close()

        health = c.health_check()
        assert health["connected"] is False

    def test_open_idempotent(self, config):
        """Calling open() twice is a no-op."""
        c = KojiClient(config)
        c.open()
        c.open()  # Should not raise
        c.close()

    def test_close_when_not_open(self, config):
        """Closing an unopened client is safe."""
        c = KojiClient(config)
        c.close()  # Should not raise

    def test_require_open(self, config):
        """Operations on a closed client raise KojiConnectionError."""
        c = KojiClient(config)
        with pytest.raises(KojiConnectionError):
            c.query("SELECT 1")


class TestDocumentCRUD:
    """Test document operations."""

    def test_create_document(self, client):
        """Create a document and verify retrieval."""
        client.create_document(
            doc_id="doc-test-1234",
            filename="test.pdf",
            format="pdf",
            num_pages=5,
        )

        doc = client.get_document("doc-test-1234")
        assert doc is not None
        assert doc["doc_id"] == "doc-test-1234"
        assert doc["filename"] == "test.pdf"
        assert doc["format"] == "pdf"
        assert doc["num_pages"] == 5
        assert doc["created_at"] is not None

    def test_create_document_duplicate(self, client):
        """Verify KojiDuplicateError on duplicate doc_id."""
        client.create_document(
            doc_id="doc-test-1234",
            filename="test.pdf",
            format="pdf",
        )

        with pytest.raises(KojiDuplicateError):
            client.create_document(
                doc_id="doc-test-1234",
                filename="other.pdf",
                format="pdf",
            )

    def test_get_document_not_found(self, client):
        """Verify returns None for non-existent document."""
        result = client.get_document("nonexistent-doc")
        assert result is None

    def test_get_document_markdown(self, client):
        """Verify convenience method for markdown retrieval."""
        client.create_document(
            doc_id="doc-test-1234",
            filename="test.md",
            format="md",
            markdown="# Hello\n\nWorld",
        )

        md = client.get_document_markdown("doc-test-1234")
        assert md == "# Hello\n\nWorld"

    def test_get_document_markdown_not_found(self, client):
        """Verify returns None for non-existent document."""
        result = client.get_document_markdown("nonexistent-doc")
        assert result is None

    def test_update_document(self, client):
        """Create, update fields, verify changed."""
        client.create_document(
            doc_id="doc-test-1234",
            filename="test.pdf",
            format="pdf",
            num_pages=5,
        )

        client.update_document("doc-test-1234", num_pages=10, filename="updated.pdf")

        doc = client.get_document("doc-test-1234")
        assert doc["num_pages"] == 10
        assert doc["filename"] == "updated.pdf"

    def test_update_document_invalid_field(self, client):
        """Verify ValueError for invalid field names."""
        client.create_document(
            doc_id="doc-test-1234",
            filename="test.pdf",
            format="pdf",
        )

        with pytest.raises(ValueError, match="Invalid document fields"):
            client.update_document("doc-test-1234", nonexistent_field="value")

    def test_update_document_no_fields(self, client):
        """Verify ValueError when no fields provided."""
        with pytest.raises(ValueError, match="No fields to update"):
            client.update_document("doc-test-1234")

    def test_list_documents(self, client):
        """Create multiple, list, verify."""
        for i in range(3):
            client.create_document(
                doc_id=f"doc-test-{i:04d}",
                filename=f"test{i}.pdf",
                format="pdf",
            )

        docs = client.list_documents()
        assert len(docs) == 3

    def test_list_documents_with_format_filter(self, client):
        """Verify format filter works."""
        client.create_document(doc_id="doc-test-0001", filename="a.pdf", format="pdf")
        client.create_document(doc_id="doc-test-0002", filename="b.md", format="md")
        client.create_document(doc_id="doc-test-0003", filename="c.pdf", format="pdf")

        pdfs = client.list_documents(format="pdf")
        assert len(pdfs) == 2

        mds = client.list_documents(format="md")
        assert len(mds) == 1

    def test_list_documents_pagination(self, client):
        """Verify limit and offset work."""
        for i in range(5):
            client.create_document(
                doc_id=f"doc-test-{i:04d}",
                filename=f"test{i}.pdf",
                format="pdf",
            )

        page1 = client.list_documents(limit=2, offset=0)
        assert len(page1) == 2

        page2 = client.list_documents(limit=2, offset=2)
        assert len(page2) == 2

    def test_delete_document_cascade(self, client):
        """Create doc + pages + chunks, delete doc, verify all gone."""
        client.create_document(
            doc_id="doc-test-1234",
            filename="test.pdf",
            format="pdf",
        )

        client.insert_pages([
            {"id": "doc-test-1234-page001", "doc_id": "doc-test-1234", "page_num": 1},
            {"id": "doc-test-1234-page002", "doc_id": "doc-test-1234", "page_num": 2},
        ])

        client.insert_chunks([
            {
                "id": "doc-test-1234-chunk0001",
                "doc_id": "doc-test-1234",
                "page_num": 1,
                "text": "Hello world",
            },
        ])

        # Verify data exists
        assert client.get_document("doc-test-1234") is not None
        assert len(client.get_pages_for_document("doc-test-1234")) == 2
        assert len(client.get_chunks_for_document("doc-test-1234")) == 1

        # Delete
        client.delete_document("doc-test-1234")

        # Verify all gone
        assert client.get_document("doc-test-1234") is None
        assert len(client.get_pages_for_document("doc-test-1234")) == 0
        assert len(client.get_chunks_for_document("doc-test-1234")) == 0

    def test_delete_document_idempotent(self, client):
        """Deleting a non-existent document should not raise."""
        client.delete_document("nonexistent-doc")  # Should not raise

    def test_create_document_with_metadata(self, client):
        """Verify metadata dict is stored and retrieved as JSON."""
        client.create_document(
            doc_id="doc-test-1234",
            filename="test.pdf",
            format="pdf",
            metadata={"author": "Test", "tags": ["a", "b"]},
        )

        doc = client.get_document("doc-test-1234")
        assert doc["metadata"] == {"author": "Test", "tags": ["a", "b"]}

    def test_create_document_with_enrichment(self, client):
        """VLM enrichment dict round-trips through the enrichment column."""
        enrichment = {
            "summary": "Q3 revenue report.",
            "key_points": ["Revenue up 12%"],
            "document_type": "report",
            "topics": ["finance"],
            "entities": [{"name": "Acme", "type": "company"}],
        }
        client.create_document(
            doc_id="doc-enrich-0001",
            filename="r.pdf",
            format="pdf",
            enrichment=enrichment,
        )

        doc = client.get_document("doc-enrich-0001")
        assert doc["enrichment"] == enrichment

    def test_create_document_enrichment_absent_yields_null(self, client):
        """Creating a document without enrichment stores NULL."""
        client.create_document(
            doc_id="doc-no-enrich",
            filename="plain.pdf",
            format="pdf",
        )
        doc = client.get_document("doc-no-enrich")
        # Deserialized: absent JSON stays as None / falsy, not parsed.
        assert not doc.get("enrichment")


class TestPageOperations:
    """Test page operations."""

    def test_insert_pages(self, client):
        """Insert pages and verify retrieval."""
        client.create_document(
            doc_id="doc-test-1234", filename="test.pdf", format="pdf"
        )

        client.insert_pages([
            {"id": "doc-test-1234-page001", "doc_id": "doc-test-1234", "page_num": 1},
            {"id": "doc-test-1234-page002", "doc_id": "doc-test-1234", "page_num": 2},
        ])

        pages = client.get_pages_for_document("doc-test-1234")
        assert len(pages) == 2
        assert pages[0]["page_num"] == 1
        assert pages[1]["page_num"] == 2

    def test_get_page(self, client):
        """Verify get_page(page_id) returns single page."""
        client.create_document(
            doc_id="doc-test-1234", filename="test.pdf", format="pdf"
        )

        client.insert_pages([
            {
                "id": "doc-test-1234-page001",
                "doc_id": "doc-test-1234",
                "page_num": 1,
                "structure": {"headings": [{"text": "Title", "level": "TITLE"}]},
            },
        ])

        page = client.get_page("doc-test-1234-page001")
        assert page is not None
        assert page["doc_id"] == "doc-test-1234"
        assert page["page_num"] == 1
        assert isinstance(page["structure"], dict)
        assert page["structure"]["headings"][0]["text"] == "Title"

    def test_get_page_not_found(self, client):
        """Verify returns None for non-existent page."""
        result = client.get_page("nonexistent-page")
        assert result is None

    def test_insert_pages_validation(self, client):
        """Missing required fields raises ValueError."""
        with pytest.raises(ValueError, match="require"):
            client.insert_pages([{"doc_id": "doc-test-1234", "page_num": 1}])

    def test_insert_pages_empty(self, client):
        """Inserting empty list is a no-op."""
        client.insert_pages([])  # Should not raise

    def test_page_enrichment_round_trip(self, client):
        """Per-page enrichment dict survives insert -> get."""
        client.create_document(
            doc_id="doc-enrich-page", filename="p.pdf", format="pdf",
        )
        page_enrichment = {
            "figures": [
                {
                    "figure_id": "fig-1",
                    "description": "Bar chart",
                    "classification": "chart",
                },
            ],
        }
        client.insert_pages([
            {
                "id": "doc-enrich-page-page001",
                "doc_id": "doc-enrich-page",
                "page_num": 1,
                "enrichment": page_enrichment,
            },
        ])

        pages = client.get_pages_for_document("doc-enrich-page")
        assert pages[0]["enrichment"] == page_enrichment
        single = client.get_page("doc-enrich-page-page001")
        assert single["enrichment"] == page_enrichment


class TestChunkOperations:
    """Test chunk operations."""

    def test_insert_chunks(self, client):
        """Insert chunks and verify retrieval."""
        client.create_document(
            doc_id="doc-test-1234", filename="test.pdf", format="pdf"
        )

        client.insert_chunks([
            {
                "id": "doc-test-1234-chunk0001",
                "doc_id": "doc-test-1234",
                "page_num": 1,
                "text": "First chunk",
                "word_count": 2,
            },
            {
                "id": "doc-test-1234-chunk0002",
                "doc_id": "doc-test-1234",
                "page_num": 1,
                "text": "Second chunk",
                "word_count": 2,
            },
        ])

        chunks = client.get_chunks_for_document("doc-test-1234")
        assert len(chunks) == 2
        assert chunks[0]["text"] == "First chunk"

    def test_get_chunk(self, client):
        """Verify get_chunk(chunk_id) returns single chunk."""
        client.create_document(
            doc_id="doc-test-1234", filename="test.pdf", format="pdf"
        )

        client.insert_chunks([
            {
                "id": "doc-test-1234-chunk0001",
                "doc_id": "doc-test-1234",
                "page_num": 1,
                "text": "Test chunk text",
                "context": {"parent_heading": "Introduction"},
            },
        ])

        chunk = client.get_chunk("doc-test-1234-chunk0001")
        assert chunk is not None
        assert chunk["text"] == "Test chunk text"
        assert isinstance(chunk["context"], dict)
        assert chunk["context"]["parent_heading"] == "Introduction"

    def test_get_chunk_not_found(self, client):
        """Verify returns None for non-existent chunk."""
        result = client.get_chunk("nonexistent-chunk")
        assert result is None

    def test_insert_chunks_validation(self, client):
        """Missing required fields raises ValueError."""
        with pytest.raises(ValueError, match="require"):
            client.insert_chunks([{"doc_id": "doc-test-1234", "page_num": 1}])

    def test_chunk_enrichment_round_trip(self, client):
        """Per-chunk enrichment (figure captions on a chunk) round-trips."""
        client.create_document(
            doc_id="doc-enrich-chunk", filename="c.pdf", format="pdf",
        )
        chunk_enrichment = {
            "figures": [
                {
                    "figure_id": "fig-7",
                    "description": "Flow diagram",
                    "classification": "diagram",
                },
            ],
        }
        client.insert_chunks([
            {
                "id": "doc-enrich-chunk-c1",
                "doc_id": "doc-enrich-chunk",
                "page_num": 2,
                "text": "References figure 7.",
                "enrichment": chunk_enrichment,
            },
        ])

        chunks = client.get_chunks_for_document("doc-enrich-chunk")
        assert chunks[0]["enrichment"] == chunk_enrichment
        single = client.get_chunk("doc-enrich-chunk-c1")
        assert single["enrichment"] == chunk_enrichment

    def test_synthetic_enrichment_chunk(self, client):
        """Synthetic enrichment chunk stores source metadata in enrichment."""
        client.create_document(
            doc_id="doc-syn", filename="s.pdf", format="pdf",
        )
        client.insert_chunks([
            {
                "id": "doc-syn:enrichment-summary",
                "doc_id": "doc-syn",
                "page_num": 1,
                "text": "Document-level summary text.",
                "enrichment": {
                    "source": "document_summary",
                    "document_type": "report",
                },
            },
        ])

        chunk = client.get_chunk("doc-syn:enrichment-summary")
        assert chunk["enrichment"]["source"] == "document_summary"
        assert chunk["enrichment"]["document_type"] == "report"


class TestRelations:
    """Test document relationship operations."""

    def _create_two_docs(self, client):
        """Helper to create two test documents."""
        client.create_document(doc_id="doc-test-0001", filename="a.pdf", format="pdf")
        client.create_document(doc_id="doc-test-0002", filename="b.pdf", format="pdf")

    def test_create_relation(self, client):
        """Create two docs, add relation, verify."""
        self._create_two_docs(client)

        client.create_relation(
            src_doc_id="doc-test-0001",
            dst_doc_id="doc-test-0002",
            relation_type="references",
        )

        relations = client.get_relations("doc-test-0001", direction="outgoing")
        assert len(relations) == 1
        assert relations[0]["dst_doc_id"] == "doc-test-0002"
        assert relations[0]["relation_type"] == "references"

    def test_create_relation_duplicate(self, client):
        """Verify KojiDuplicateError on duplicate relation."""
        self._create_two_docs(client)

        client.create_relation(
            src_doc_id="doc-test-0001",
            dst_doc_id="doc-test-0002",
            relation_type="references",
        )

        with pytest.raises(KojiDuplicateError):
            client.create_relation(
                src_doc_id="doc-test-0001",
                dst_doc_id="doc-test-0002",
                relation_type="references",
            )

    def test_create_relation_missing_doc(self, client):
        """Verify ValueError when document doesn't exist."""
        client.create_document(doc_id="doc-test-0001", filename="a.pdf", format="pdf")

        with pytest.raises(ValueError, match="not found"):
            client.create_relation(
                src_doc_id="doc-test-0001",
                dst_doc_id="nonexistent-doc",
                relation_type="references",
            )

    def test_delete_relation(self, client):
        """Create + delete relation, verify gone."""
        self._create_two_docs(client)

        client.create_relation(
            src_doc_id="doc-test-0001",
            dst_doc_id="doc-test-0002",
            relation_type="references",
        )

        client.delete_relation(
            src_doc_id="doc-test-0001",
            dst_doc_id="doc-test-0002",
            relation_type="references",
        )

        relations = client.get_relations("doc-test-0001")
        assert len(relations) == 0

    def test_get_relations_both_directions(self, client):
        """Verify both incoming and outgoing relations are returned."""
        self._create_two_docs(client)

        client.create_relation(
            src_doc_id="doc-test-0001",
            dst_doc_id="doc-test-0002",
            relation_type="references",
        )

        # From doc-test-0002's perspective, it has an incoming relation
        incoming = client.get_relations("doc-test-0002", direction="incoming")
        assert len(incoming) == 1

        both = client.get_relations("doc-test-0002", direction="both")
        assert len(both) == 1

    def test_create_relation_with_metadata(self, client):
        """Verify relation metadata is stored."""
        self._create_two_docs(client)

        client.create_relation(
            src_doc_id="doc-test-0001",
            dst_doc_id="doc-test-0002",
            relation_type="cites",
            metadata={"page": 5, "context": "see also"},
        )

        relations = client.get_relations("doc-test-0001", direction="outgoing")
        assert relations[0]["metadata"] == {"page": 5, "context": "see also"}

    def test_get_related_documents_recursive(self, client):
        """Verify recursive graph traversal via get_related_documents."""
        client.create_document(doc_id="doc-test-A", filename="a.pdf", format="pdf")
        client.create_document(doc_id="doc-test-B", filename="b.pdf", format="pdf")
        client.create_document(doc_id="doc-test-C", filename="c.pdf", format="pdf")

        client.create_relation(
            src_doc_id="doc-test-A",
            dst_doc_id="doc-test-B",
            relation_type="references",
        )
        client.create_relation(
            src_doc_id="doc-test-B",
            dst_doc_id="doc-test-C",
            relation_type="related",
        )

        # Full depth: both B and C reachable
        related = client.get_related_documents("doc-test-A", max_depth=3)
        doc_ids = [r["doc_id"] for r in related]
        assert "doc-test-B" in doc_ids
        assert "doc-test-C" in doc_ids

        depths = {r["doc_id"]: r["depth"] for r in related}
        assert depths["doc-test-B"] == 1
        assert depths["doc-test-C"] == 2

        # Depth 1: only B reachable
        shallow = client.get_related_documents("doc-test-A", max_depth=1)
        shallow_ids = [r["doc_id"] for r in shallow]
        assert "doc-test-B" in shallow_ids
        assert "doc-test-C" not in shallow_ids


class TestMultivec:
    """Test multi-vector packing/unpacking."""

    def test_pack_unpack_multivec(self):
        """Round-trip binary packing."""
        original = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        packed = pack_multivec(original)

        assert isinstance(packed, bytes)
        assert len(packed) == 8 + 2 * 3 * 4  # header + data

        unpacked = unpack_multivec(packed)
        assert len(unpacked) == 2
        assert len(unpacked[0]) == 3

        for orig_vec, unpacked_vec in zip(original, unpacked):
            for o, u in zip(orig_vec, unpacked_vec):
                assert abs(o - u) < 1e-6

    def test_pack_unpack_single_vector(self):
        """Single vector round-trip."""
        original = [[0.1, 0.2, 0.3, 0.4]]
        packed = pack_multivec(original)
        unpacked = unpack_multivec(packed)

        assert len(unpacked) == 1
        assert len(unpacked[0]) == 4


class TestHealthCheck:
    """Test health check."""

    def test_health_check_connected(self, client):
        """Verify health response structure when connected."""
        health = client.health_check()
        assert health["connected"] is True
        assert health["db_path"] is not None
        assert isinstance(health["tables"], list)
        assert len(health["tables"]) >= 4

    def test_health_check_disconnected(self, config):
        """Verify health response when not connected."""
        c = KojiClient(config)
        health = c.health_check()
        assert health["connected"] is False


class TestRawSQL:
    """Test raw SQL query."""

    def test_query_raw_sql(self, client):
        """Verify raw SQL works."""
        client.create_document(
            doc_id="doc-test-1234", filename="test.pdf", format="pdf"
        )

        result = client.query("SELECT COUNT(*) AS n FROM documents")
        assert result.num_rows == 1
        assert result.column("n")[0].as_py() == 1


class TestUpdateDocumentPreservesChildren:
    """Verify that update_document() no longer destroys child data.

    Previously, update_document used a delete-reinsert workaround that
    would cascade-delete child rows (pages, chunks, relations). After
    switching to Koji's native db.update(), child data must survive.
    """

    def test_update_preserves_pages(self, client):
        """Create doc + 2 pages, update doc's num_pages, verify both pages survive."""
        client.create_document(
            doc_id="doc-upd-pages",
            filename="test.pdf",
            format="pdf",
            num_pages=2,
        )

        client.insert_pages([
            {"id": "doc-upd-pages-page001", "doc_id": "doc-upd-pages", "page_num": 1},
            {"id": "doc-upd-pages-page002", "doc_id": "doc-upd-pages", "page_num": 2},
        ])

        # Verify pages exist before update
        assert len(client.get_pages_for_document("doc-upd-pages")) == 2

        # Update a field on the parent document
        client.update_document("doc-upd-pages", num_pages=10)

        # Pages must still exist
        pages = client.get_pages_for_document("doc-upd-pages")
        assert len(pages) == 2
        page_nums = {p["page_num"] for p in pages}
        assert page_nums == {1, 2}

        # Verify the update itself took effect
        doc = client.get_document("doc-upd-pages")
        assert doc["num_pages"] == 10

    def test_update_preserves_chunks(self, client):
        """Create doc + 2 chunks, update doc's filename, verify chunks survive with correct text."""
        client.create_document(
            doc_id="doc-upd-chunks",
            filename="original.pdf",
            format="pdf",
        )

        client.insert_chunks([
            {
                "id": "doc-upd-chunks-chunk0001",
                "doc_id": "doc-upd-chunks",
                "page_num": 1,
                "text": "First chunk of text",
            },
            {
                "id": "doc-upd-chunks-chunk0002",
                "doc_id": "doc-upd-chunks",
                "page_num": 1,
                "text": "Second chunk of text",
            },
        ])

        # Verify chunks exist before update
        assert len(client.get_chunks_for_document("doc-upd-chunks")) == 2

        # Update a field on the parent document
        client.update_document("doc-upd-chunks", filename="renamed.pdf")

        # Chunks must still exist with correct text
        chunks = client.get_chunks_for_document("doc-upd-chunks")
        assert len(chunks) == 2
        texts = {c["text"] for c in chunks}
        assert texts == {"First chunk of text", "Second chunk of text"}

        # Verify the update itself took effect
        doc = client.get_document("doc-upd-chunks")
        assert doc["filename"] == "renamed.pdf"

    def test_update_preserves_relations(self, client):
        """Create 2 docs + a relation, update doc1's markdown, verify relation survives."""
        client.create_document(
            doc_id="doc-upd-rel-A",
            filename="a.pdf",
            format="pdf",
            markdown="# Original",
        )
        client.create_document(
            doc_id="doc-upd-rel-B",
            filename="b.pdf",
            format="pdf",
        )

        client.create_relation(
            src_doc_id="doc-upd-rel-A",
            dst_doc_id="doc-upd-rel-B",
            relation_type="references",
        )

        # Verify relation exists before update
        assert len(client.get_relations("doc-upd-rel-A", direction="outgoing")) == 1

        # Update a field on the source document
        client.update_document("doc-upd-rel-A", markdown="# Updated")

        # Relation must still exist
        relations = client.get_relations("doc-upd-rel-A", direction="outgoing")
        assert len(relations) == 1
        assert relations[0]["dst_doc_id"] == "doc-upd-rel-B"
        assert relations[0]["relation_type"] == "references"

        # Verify the update itself took effect
        md = client.get_document_markdown("doc-upd-rel-A")
        assert md == "# Updated"

    def test_update_preserves_all_children(self, client):
        """Create doc + pages + chunks + relation, update a field, verify ALL children survive."""
        client.create_document(
            doc_id="doc-upd-all-A",
            filename="full.pdf",
            format="pdf",
            num_pages=2,
        )
        client.create_document(
            doc_id="doc-upd-all-B",
            filename="other.pdf",
            format="pdf",
        )

        client.insert_pages([
            {"id": "doc-upd-all-A-page001", "doc_id": "doc-upd-all-A", "page_num": 1},
            {"id": "doc-upd-all-A-page002", "doc_id": "doc-upd-all-A", "page_num": 2},
        ])

        client.insert_chunks([
            {
                "id": "doc-upd-all-A-chunk0001",
                "doc_id": "doc-upd-all-A",
                "page_num": 1,
                "text": "Chunk one",
            },
            {
                "id": "doc-upd-all-A-chunk0002",
                "doc_id": "doc-upd-all-A",
                "page_num": 2,
                "text": "Chunk two",
            },
        ])

        client.create_relation(
            src_doc_id="doc-upd-all-A",
            dst_doc_id="doc-upd-all-B",
            relation_type="related",
        )

        # Verify all children exist before update
        assert len(client.get_pages_for_document("doc-upd-all-A")) == 2
        assert len(client.get_chunks_for_document("doc-upd-all-A")) == 2
        assert len(client.get_relations("doc-upd-all-A", direction="outgoing")) == 1

        # Update a field on the parent document
        client.update_document("doc-upd-all-A", num_pages=10)

        # ALL children must survive
        pages = client.get_pages_for_document("doc-upd-all-A")
        assert len(pages) == 2

        chunks = client.get_chunks_for_document("doc-upd-all-A")
        assert len(chunks) == 2
        assert {c["text"] for c in chunks} == {"Chunk one", "Chunk two"}

        relations = client.get_relations("doc-upd-all-A", direction="outgoing")
        assert len(relations) == 1
        assert relations[0]["dst_doc_id"] == "doc-upd-all-B"

        # Verify the update itself took effect
        doc = client.get_document("doc-upd-all-A")
        assert doc["num_pages"] == 10

    def test_update_metadata_as_dict(self, client):
        """Create doc, update with metadata as a dict, verify stored correctly as JSON."""
        client.create_document(
            doc_id="doc-upd-meta",
            filename="test.pdf",
            format="pdf",
        )

        new_meta = {"author": "Alice", "tags": ["science", "review"], "year": 2025}
        client.update_document("doc-upd-meta", metadata=new_meta)

        doc = client.get_document("doc-upd-meta")
        assert doc["metadata"] == new_meta
        assert doc["metadata"]["author"] == "Alice"
        assert doc["metadata"]["tags"] == ["science", "review"]
        assert doc["metadata"]["year"] == 2025

    def test_update_nonexistent_document(self, client):
        """Call update on a non-existent doc_id, verify no error is raised."""
        # Should be a no-op, not an error
        client.update_document("doc-does-not-exist", filename="phantom.pdf")

        # Document still should not exist
        assert client.get_document("doc-does-not-exist") is None


class TestDeleteCascade:
    """Verify that delete_document cascades to all child tables correctly.

    Tests confirm that foreign-key cascade (or the manual fallback) removes
    pages, chunks, and relations for the deleted document while leaving
    other documents' children intact.
    """

    def test_delete_cascades_to_relations(self, client):
        """Create 3 docs with relations. Delete doc1. Verify doc1 relations gone, doc2-doc3 survive."""
        client.create_document(doc_id="doc-del-A", filename="a.pdf", format="pdf")
        client.create_document(doc_id="doc-del-B", filename="b.pdf", format="pdf")
        client.create_document(doc_id="doc-del-C", filename="c.pdf", format="pdf")

        # A -> B, A -> C, B -> C
        client.create_relation(
            src_doc_id="doc-del-A", dst_doc_id="doc-del-B", relation_type="references",
        )
        client.create_relation(
            src_doc_id="doc-del-A", dst_doc_id="doc-del-C", relation_type="related",
        )
        client.create_relation(
            src_doc_id="doc-del-B", dst_doc_id="doc-del-C", relation_type="cites",
        )

        # Verify all 3 relations exist
        assert len(client.get_relations("doc-del-A", direction="outgoing")) == 2
        assert len(client.get_relations("doc-del-B", direction="outgoing")) == 1

        # Delete doc A
        client.delete_document("doc-del-A")

        # A's relations must be gone (both where A is src and dst)
        assert client.get_document("doc-del-A") is None
        assert len(client.get_relations("doc-del-A", direction="both")) == 0

        # B -> C relation must survive
        relations_b = client.get_relations("doc-del-B", direction="outgoing")
        assert len(relations_b) == 1
        assert relations_b[0]["dst_doc_id"] == "doc-del-C"
        assert relations_b[0]["relation_type"] == "cites"

    def test_delete_cascade_with_all_children(self, client):
        """Create doc + pages + chunks + relations. Delete doc. Verify all 4 tables clean."""
        client.create_document(doc_id="doc-del-full", filename="full.pdf", format="pdf")
        client.create_document(doc_id="doc-del-other", filename="other.pdf", format="pdf")

        client.insert_pages([
            {"id": "doc-del-full-page001", "doc_id": "doc-del-full", "page_num": 1},
            {"id": "doc-del-full-page002", "doc_id": "doc-del-full", "page_num": 2},
        ])

        client.insert_chunks([
            {
                "id": "doc-del-full-chunk0001",
                "doc_id": "doc-del-full",
                "page_num": 1,
                "text": "To be deleted",
            },
        ])

        client.create_relation(
            src_doc_id="doc-del-full",
            dst_doc_id="doc-del-other",
            relation_type="references",
        )

        # Verify everything exists before delete
        assert client.get_document("doc-del-full") is not None
        assert len(client.get_pages_for_document("doc-del-full")) == 2
        assert len(client.get_chunks_for_document("doc-del-full")) == 1
        assert len(client.get_relations("doc-del-full", direction="outgoing")) == 1

        # Delete the document
        client.delete_document("doc-del-full")

        # All child data must be gone
        assert client.get_document("doc-del-full") is None
        assert len(client.get_pages_for_document("doc-del-full")) == 0
        assert len(client.get_chunks_for_document("doc-del-full")) == 0
        assert len(client.get_relations("doc-del-full", direction="both")) == 0

        # The other document must still exist
        assert client.get_document("doc-del-other") is not None

    def test_delete_other_documents_survive(self, client):
        """Create doc1 + doc2, both with pages and chunks. Delete doc1. Verify doc2 intact."""
        client.create_document(doc_id="doc-del-surv1", filename="one.pdf", format="pdf")
        client.create_document(doc_id="doc-del-surv2", filename="two.pdf", format="pdf")

        client.insert_pages([
            {"id": "doc-del-surv1-page001", "doc_id": "doc-del-surv1", "page_num": 1},
            {"id": "doc-del-surv2-page001", "doc_id": "doc-del-surv2", "page_num": 1},
            {"id": "doc-del-surv2-page002", "doc_id": "doc-del-surv2", "page_num": 2},
        ])

        client.insert_chunks([
            {
                "id": "doc-del-surv1-chunk0001",
                "doc_id": "doc-del-surv1",
                "page_num": 1,
                "text": "Doc one chunk",
            },
            {
                "id": "doc-del-surv2-chunk0001",
                "doc_id": "doc-del-surv2",
                "page_num": 1,
                "text": "Doc two first chunk",
            },
            {
                "id": "doc-del-surv2-chunk0002",
                "doc_id": "doc-del-surv2",
                "page_num": 2,
                "text": "Doc two second chunk",
            },
        ])

        # Delete doc1
        client.delete_document("doc-del-surv1")

        # doc1 and all its children are gone
        assert client.get_document("doc-del-surv1") is None
        assert len(client.get_pages_for_document("doc-del-surv1")) == 0
        assert len(client.get_chunks_for_document("doc-del-surv1")) == 0

        # doc2 and all its children survive untouched
        assert client.get_document("doc-del-surv2") is not None
        assert client.get_document("doc-del-surv2")["filename"] == "two.pdf"

        pages = client.get_pages_for_document("doc-del-surv2")
        assert len(pages) == 2

        chunks = client.get_chunks_for_document("doc-del-surv2")
        assert len(chunks) == 2
        assert {c["text"] for c in chunks} == {
            "Doc two first chunk",
            "Doc two second chunk",
        }


class TestDeleteRelationDirect:
    """Verify the simplified delete_relation using db.delete() directly.

    Tests confirm idempotent behavior and isolation — deleting one
    relation must not affect others.
    """

    def test_delete_relation_idempotent(self, client):
        """Delete a relation that does not exist. Verify no error is raised."""
        client.create_document(doc_id="doc-delrel-A", filename="a.pdf", format="pdf")
        client.create_document(doc_id="doc-delrel-B", filename="b.pdf", format="pdf")

        # No relation exists between these two docs — should be a no-op
        client.delete_relation(
            src_doc_id="doc-delrel-A",
            dst_doc_id="doc-delrel-B",
            relation_type="references",
        )

        # Verify nothing was inadvertently created
        assert len(client.get_relations("doc-delrel-A", direction="both")) == 0

    def test_delete_relation_preserves_other_relations(self, client):
        """Create 3 relations, delete one, verify other 2 survive."""
        client.create_document(doc_id="doc-delrel-X", filename="x.pdf", format="pdf")
        client.create_document(doc_id="doc-delrel-Y", filename="y.pdf", format="pdf")
        client.create_document(doc_id="doc-delrel-Z", filename="z.pdf", format="pdf")

        # X -> Y (references), X -> Z (related), Y -> Z (cites)
        client.create_relation(
            src_doc_id="doc-delrel-X",
            dst_doc_id="doc-delrel-Y",
            relation_type="references",
        )
        client.create_relation(
            src_doc_id="doc-delrel-X",
            dst_doc_id="doc-delrel-Z",
            relation_type="related",
        )
        client.create_relation(
            src_doc_id="doc-delrel-Y",
            dst_doc_id="doc-delrel-Z",
            relation_type="cites",
        )

        # Delete only X -> Y
        client.delete_relation(
            src_doc_id="doc-delrel-X",
            dst_doc_id="doc-delrel-Y",
            relation_type="references",
        )

        # X -> Y should be gone
        x_outgoing = client.get_relations("doc-delrel-X", direction="outgoing")
        assert len(x_outgoing) == 1
        assert x_outgoing[0]["dst_doc_id"] == "doc-delrel-Z"
        assert x_outgoing[0]["relation_type"] == "related"

        # Y -> Z should survive
        y_outgoing = client.get_relations("doc-delrel-Y", direction="outgoing")
        assert len(y_outgoing) == 1
        assert y_outgoing[0]["dst_doc_id"] == "doc-delrel-Z"
        assert y_outgoing[0]["relation_type"] == "cites"
