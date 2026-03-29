"""Tests verifying multi-document isolation in a shared Koji database.

Processes multiple fixture files (PDF, DOCX, MD, CSV, PNG) into the
same KojiClient instance and asserts that each document's data remains
isolated: unique IDs, no cross-contamination in pages/chunks, and
deletion of one document does not affect others.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src.processing.processor import StorageConfirmation


@pytest.fixture
def five_docs(
    make_processor,
    koji_storage,
    sample_pdf,
    sample_docx,
    sample_md,
    sample_csv,
    sample_png,
):
    """Process up to 5 fixture files into the same Koji instance.

    Returns:
        Tuple of (confirmations list, koji_storage client).
        Skips if fewer than 2 files could be processed.
    """
    processor = make_processor(storage=koji_storage)
    confirmations: list[StorageConfirmation] = []

    for path in [sample_pdf, sample_docx, sample_md, sample_csv, sample_png]:
        if not path.exists():
            continue
        conf = processor.process_document(str(path))
        confirmations.append(conf)

    if len(confirmations) < 2:
        pytest.skip(
            f"Only {len(confirmations)} fixture files could be processed; "
            "need at least 2 for isolation tests"
        )

    return confirmations, koji_storage


class TestMultiDocumentIsolation:
    """Verify that processing multiple documents into one Koji DB
    produces correct, isolated results with no cross-contamination."""

    # ------------------------------------------------------------------
    # 1. All documents produce distinct doc_ids
    # ------------------------------------------------------------------

    def test_unique_doc_ids(self, five_docs):
        """All processed documents must have unique doc_ids."""
        confirmations, _ = five_docs

        doc_ids = [c.doc_id for c in confirmations]
        assert len(set(doc_ids)) == len(doc_ids), (
            f"Expected {len(doc_ids)} unique doc_ids, "
            f"got {len(set(doc_ids))}. Duplicates: "
            f"{[d for d in doc_ids if doc_ids.count(d) > 1]}"
        )

    # ------------------------------------------------------------------
    # 2. Pages belong exclusively to their parent document
    # ------------------------------------------------------------------

    def test_pages_exclusive_to_document(self, five_docs):
        """For each document, every page record references only that doc_id."""
        confirmations, storage = five_docs

        for conf in confirmations:
            pages = storage.get_pages_for_document(conf.doc_id)
            for page in pages:
                assert page["doc_id"] == conf.doc_id, (
                    f"Page {page.get('id', '?')} has doc_id "
                    f"'{page['doc_id']}' but was retrieved for "
                    f"doc_id '{conf.doc_id}'"
                )

    # ------------------------------------------------------------------
    # 3. Chunks belong exclusively to their parent document
    # ------------------------------------------------------------------

    def test_chunks_exclusive_to_document(self, five_docs):
        """For each document, every chunk record references only that doc_id."""
        confirmations, storage = five_docs

        for conf in confirmations:
            chunks = storage.get_chunks_for_document(conf.doc_id)
            for chunk in chunks:
                assert chunk["doc_id"] == conf.doc_id, (
                    f"Chunk {chunk.get('id', '?')} has doc_id "
                    f"'{chunk['doc_id']}' but was retrieved for "
                    f"doc_id '{conf.doc_id}'"
                )

    # ------------------------------------------------------------------
    # 4. All chunk IDs across all documents are globally unique
    # ------------------------------------------------------------------

    def test_chunk_ids_globally_unique(self, five_docs):
        """Chunk IDs must be unique across all documents in the database."""
        confirmations, storage = five_docs

        all_chunk_ids: list[str] = []
        for conf in confirmations:
            chunks = storage.get_chunks_for_document(conf.doc_id)
            all_chunk_ids.extend(c["id"] for c in chunks)

        assert len(all_chunk_ids) > 0, (
            "Expected at least one chunk across all documents"
        )
        assert len(set(all_chunk_ids)) == len(all_chunk_ids), (
            f"Duplicate chunk IDs found. Total: {len(all_chunk_ids)}, "
            f"Unique: {len(set(all_chunk_ids))}"
        )

    # ------------------------------------------------------------------
    # 5. Deleting one document preserves all others completely
    # ------------------------------------------------------------------

    def test_delete_one_preserves_others(self, five_docs):
        """Delete one document and verify the remaining documents retain
        their complete data (document record, page count, chunk count)."""
        confirmations, storage = five_docs

        # Snapshot pre-deletion counts for every document.
        pre_counts: dict[str, dict[str, int]] = {}
        for conf in confirmations:
            pages = storage.get_pages_for_document(conf.doc_id)
            chunks = storage.get_chunks_for_document(conf.doc_id)
            pre_counts[conf.doc_id] = {
                "pages": len(pages),
                "chunks": len(chunks),
            }

        # Delete the first document.
        deleted_id = confirmations[0].doc_id
        storage.delete_document(deleted_id)

        # Verify the deleted document is gone.
        assert storage.get_document(deleted_id) is None, (
            f"Document '{deleted_id}' should not exist after deletion"
        )

        # Verify every surviving document is intact.
        for conf in confirmations[1:]:
            doc = storage.get_document(conf.doc_id)
            assert doc is not None, (
                f"Surviving document '{conf.doc_id}' should still exist"
            )

            pages = storage.get_pages_for_document(conf.doc_id)
            chunks = storage.get_chunks_for_document(conf.doc_id)

            expected = pre_counts[conf.doc_id]
            assert len(pages) == expected["pages"], (
                f"Document '{conf.doc_id}' had {expected['pages']} pages "
                f"before deletion but now has {len(pages)}"
            )
            assert len(chunks) == expected["chunks"], (
                f"Document '{conf.doc_id}' had {expected['chunks']} chunks "
                f"before deletion but now has {len(chunks)}"
            )
