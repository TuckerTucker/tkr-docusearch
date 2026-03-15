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
