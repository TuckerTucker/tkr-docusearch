"""End-to-end tests for the document processing pipeline.

Exercises the full pipeline: Docling parsing -> mock embeddings -> real Koji
storage. Uses real fixture files (PDF, DOCX, MD, CSV, PNG) with
MockEmbeddingModel (no GPU) and a real KojiClient backed by tmp_path.

Tests verify that documents, pages, and chunks are correctly stored in Koji
and that StorageConfirmation fields are populated accurately.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.processing.processor import DocumentProcessor
from src.storage.koji_client import unpack_multivec


class TestPipelineEndToEnd:
    """End-to-end pipeline tests with real parsing + mock embeddings + real Koji."""

    # ------------------------------------------------------------------
    # 1. PDF document record
    # ------------------------------------------------------------------

    def test_pdf_stores_document(self, make_processor, koji_storage, sample_pdf):
        """Process sample.pdf and verify the document record in Koji."""
        processor = make_processor(storage=koji_storage)
        confirmation = processor.process_document(str(sample_pdf))

        doc = koji_storage.get_document(confirmation.doc_id)
        assert doc is not None, "Document record should exist in Koji"
        assert doc["filename"] == "sample.pdf"
        assert doc["format"] == "pdf"
        assert doc["created_at"] is not None

    # ------------------------------------------------------------------
    # 2. PDF page records
    # ------------------------------------------------------------------

    def test_pdf_stores_pages(self, make_processor, koji_storage, sample_pdf):
        """Process sample.pdf and verify page records with embeddings."""
        processor = make_processor(storage=koji_storage)
        confirmation = processor.process_document(str(sample_pdf))

        pages = koji_storage.get_pages_for_document(confirmation.doc_id)
        assert len(pages) > 0, "PDF should produce at least one page"

        page_nums = [p["page_num"] for p in pages]
        assert page_nums == sorted(page_nums), "Pages should be ordered by page_num"

        for page in pages:
            assert page["embedding"] is not None, (
                f"Page {page['page_num']} should have an embedding blob"
            )

    # ------------------------------------------------------------------
    # 3. PDF chunk records
    # ------------------------------------------------------------------

    def test_pdf_stores_chunks(self, make_processor, koji_storage, sample_pdf):
        """Process sample.pdf and verify chunk records with text."""
        processor = make_processor(storage=koji_storage)
        confirmation = processor.process_document(str(sample_pdf))

        chunks = koji_storage.get_chunks_for_document(confirmation.doc_id)
        assert len(chunks) > 0, "PDF should produce at least one text chunk"

        for chunk in chunks:
            assert chunk["doc_id"] == confirmation.doc_id
            assert chunk["text"] is not None and len(chunk["text"].strip()) > 0, (
                "Each chunk should have non-empty text"
            )

    # ------------------------------------------------------------------
    # 4. DOCX text-only
    # ------------------------------------------------------------------

    def test_docx_text_only(self, make_processor, koji_storage, sample_docx):
        """Process sample.docx and verify text-only storage (no visual pages)."""
        processor = make_processor(storage=koji_storage)
        confirmation = processor.process_document(str(sample_docx))

        doc = koji_storage.get_document(confirmation.doc_id)
        assert doc is not None

        chunks = koji_storage.get_chunks_for_document(confirmation.doc_id)
        assert len(chunks) > 0, "DOCX should produce text chunks"

        pages = koji_storage.get_pages_for_document(confirmation.doc_id)
        assert len(pages) == 0, (
            "Text-only format should produce no visual page records"
        )

    # ------------------------------------------------------------------
    # 5. Markdown text-only
    # ------------------------------------------------------------------

    def test_md_text_only(self, make_processor, koji_storage, sample_md):
        """Process sample.md and verify text-only storage (no visual pages)."""
        processor = make_processor(storage=koji_storage)
        confirmation = processor.process_document(str(sample_md))

        doc = koji_storage.get_document(confirmation.doc_id)
        assert doc is not None

        chunks = koji_storage.get_chunks_for_document(confirmation.doc_id)
        assert len(chunks) > 0, "Markdown should produce text chunks"

        pages = koji_storage.get_pages_for_document(confirmation.doc_id)
        assert len(pages) == 0, (
            "Text-only format should produce no visual page records"
        )

    # ------------------------------------------------------------------
    # 6. CSV text-only
    # ------------------------------------------------------------------

    def test_csv_text_only(self, make_processor, koji_storage, sample_csv):
        """Process sample.csv and verify chunks from tabular content."""
        processor = make_processor(storage=koji_storage)
        confirmation = processor.process_document(str(sample_csv))

        doc = koji_storage.get_document(confirmation.doc_id)
        assert doc is not None

        chunks = koji_storage.get_chunks_for_document(confirmation.doc_id)
        assert len(chunks) > 0, "CSV should produce text chunks from tabular data"

        pages = koji_storage.get_pages_for_document(confirmation.doc_id)
        assert len(pages) == 0, (
            "Text-only format should produce no visual page records"
        )

    # ------------------------------------------------------------------
    # 7. Image single page
    # ------------------------------------------------------------------

    def test_image_single_page(self, make_processor, koji_storage, sample_png):
        """Process sample.png and verify exactly 1 page record."""
        processor = make_processor(storage=koji_storage)
        confirmation = processor.process_document(str(sample_png))

        pages = koji_storage.get_pages_for_document(confirmation.doc_id)
        assert len(pages) == 1, "PNG should produce exactly one page record"

        page = pages[0]
        assert page["page_num"] == 1
        assert page["embedding"] is not None

    # ------------------------------------------------------------------
    # 8. version_of relation across shared base filename
    # ------------------------------------------------------------------

    def test_creates_version_of_relation(
        self, make_processor, koji_storage, sample_pdf, sample_docx
    ):
        """Process sample.pdf and sample.docx into the same Koji.

        Relation detection (version_of) is handled inside shikomi's
        real Ingester.  The MockShikomiIngester returns empty relations,
        so this test verifies that the relation storage path works when
        relations are provided, rather than asserting automatic detection.
        """
        from src.core.testing.mocks import MockShikomiIngester

        # Build a mock ingester whose second call returns a version_of relation
        ingester = MockShikomiIngester()
        ingester.connect()
        processor = DocumentProcessor(ingester=ingester, storage_client=koji_storage)

        conf_pdf = processor.process_document(str(sample_pdf))

        # Manually inject a relation into the second ingest result
        import hashlib
        docx_hash = hashlib.sha256(str(sample_docx).encode()).hexdigest()
        from shikomi import IngestResult
        second_result = ingester.process(str(sample_docx))
        second_result.relations = [{
            "src_doc_id": second_result.content_hash,
            "dst_doc_id": conf_pdf.doc_id,
            "relation_type": "version_of",
        }]
        ingester._result = second_result

        conf_docx = processor.process_document(str(sample_docx))

        # Reset so other tests aren't affected
        ingester._result = None

        # Check relations from either direction
        relations_pdf = koji_storage.get_relations(
            conf_pdf.doc_id, relation_type="version_of"
        )
        relations_docx = koji_storage.get_relations(
            conf_docx.doc_id, relation_type="version_of"
        )

        all_relations = relations_pdf + relations_docx
        assert len(all_relations) >= 1, (
            "Should have at least one version_of relation after explicit injection"
        )

    # ------------------------------------------------------------------
    # 9. StorageConfirmation fields
    # ------------------------------------------------------------------

    def test_storage_confirmation_fields(
        self, make_processor, koji_storage, sample_pdf
    ):
        """Verify StorageConfirmation has all expected fields populated."""
        processor = make_processor(storage=koji_storage)
        confirmation = processor.process_document(str(sample_pdf))

        assert confirmation.doc_id, "doc_id should be non-empty"
        assert isinstance(confirmation.text_ids, list), "text_ids should be a list"
        assert len(confirmation.text_ids) > 0, "PDF should have text_ids"
        assert confirmation.total_size_bytes > 0, "total_size_bytes should be > 0"
        assert confirmation.timestamp, "timestamp should be non-empty"

    # ------------------------------------------------------------------
    # 10. Embedding blob validity via unpack_multivec
    # ------------------------------------------------------------------

    def test_embedding_blobs_valid(self, make_processor, koji_storage, sample_pdf):
        """Process sample.pdf, read a chunk embedding, and verify via unpack_multivec."""
        processor = make_processor(storage=koji_storage)
        confirmation = processor.process_document(str(sample_pdf))

        chunks = koji_storage.get_chunks_for_document(confirmation.doc_id)
        assert len(chunks) > 0, "Need at least one chunk to test embedding blob"

        # Find a chunk with an embedding blob
        chunk_with_embedding = None
        for chunk in chunks:
            if chunk.get("embedding") is not None:
                chunk_with_embedding = chunk
                break

        assert chunk_with_embedding is not None, (
            "At least one chunk should have an embedding blob"
        )

        vectors = unpack_multivec(chunk_with_embedding["embedding"])
        assert isinstance(vectors, list), "unpack_multivec should return a list"
        assert len(vectors) > 0, "Should have at least one token vector"

        for vec in vectors:
            assert isinstance(vec, list), "Each token vector should be a list"
            assert len(vec) > 0, "Token vectors should be non-empty"
            assert all(
                isinstance(v, float) for v in vec
            ), "Vector values should be floats"
