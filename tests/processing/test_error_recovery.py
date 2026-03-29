"""Tests for failure modes and graceful error handling.

Exercises error paths in the document processing pipeline to verify that
parsing failures, embedding engine errors, storage errors, and status
callback failure reporting all behave correctly.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.core.testing.mocks import MockEmbeddingModel, MockKojiClient
from src.processing.processor import (
    EmbeddingError,
    ProcessingError,
    StorageError,
)


# ============================================================================
# Failing mock subclasses
# ============================================================================


class FailingImageEngine(MockEmbeddingModel):
    """Embedding engine that raises on embed_images."""

    def embed_images(self, images, batch_size=4):
        raise RuntimeError("GPU out of memory")


class FailingTextEngine(MockEmbeddingModel):
    """Embedding engine that raises on embed_texts."""

    def embed_texts(self, texts, batch_size=8):
        raise RuntimeError("Tokenizer OOM")


class FailingInsertPagesStorage(MockKojiClient):
    """Storage client that raises on insert_pages."""

    def insert_pages(self, pages):
        raise RuntimeError("Database connection lost")


class FailingInsertChunksStorage(MockKojiClient):
    """Storage client that raises on insert_chunks."""

    def insert_chunks(self, chunks):
        raise RuntimeError("Disk quota exceeded")


# ============================================================================
# TestParsingErrors
# ============================================================================


class TestParsingErrors:
    """Verify the pipeline raises on unparseable or missing files."""

    def test_nonexistent_file(self, make_processor):
        """Processing a nonexistent path raises an exception."""
        processor = make_processor()
        with pytest.raises(Exception):
            processor.process_document("/tmp/nonexistent_file.pdf")

    def test_corrupt_file(self, make_processor, tmp_path):
        """Processing a file filled with random bytes raises an exception."""
        corrupt = tmp_path / "corrupt.pdf"
        corrupt.write_bytes(os.urandom(512))

        processor = make_processor()
        with pytest.raises(Exception):
            processor.process_document(str(corrupt))

    def test_empty_file(self, make_processor, tmp_path):
        """Processing a zero-byte file raises an exception."""
        empty = tmp_path / "empty.pdf"
        empty.write_bytes(b"")

        processor = make_processor()
        with pytest.raises(Exception):
            processor.process_document(str(empty))

    def test_wrong_extension(self, make_processor, tmp_path):
        """Processing a plaintext file disguised as .pdf raises an exception."""
        wrong = tmp_path / "not_a_pdf.pdf"
        wrong.write_text("Hello, I am not a PDF at all.", encoding="utf-8")

        processor = make_processor()
        with pytest.raises(Exception):
            processor.process_document(str(wrong))


# ============================================================================
# TestEmbeddingErrors
# ============================================================================


class TestEmbeddingErrors:
    """Verify that embedding engine failures propagate as exceptions."""

    def test_embed_images_failure(self, make_processor, sample_pdf):
        """RuntimeError in embed_images propagates through the pipeline.

        PDF processing hits embed_images for page-level visual embeddings.
        The processor's generic except block wraps this as ProcessingError.
        """
        engine = FailingImageEngine(simulate_latency=False)
        processor = make_processor(engine=engine)

        with pytest.raises((RuntimeError, ProcessingError)):
            processor.process_document(str(sample_pdf))

    def test_embed_texts_failure(self, make_processor, sample_md):
        """RuntimeError in embed_texts propagates through the pipeline.

        Markdown processing is text-only, so it hits embed_texts
        without ever calling embed_images.
        """
        engine = FailingTextEngine(simulate_latency=False)
        processor = make_processor(engine=engine)

        with pytest.raises((RuntimeError, ProcessingError)):
            processor.process_document(str(sample_md))


# ============================================================================
# TestStorageErrors
# ============================================================================


class TestStorageErrors:
    """Verify that storage client failures propagate as exceptions."""

    def test_insert_pages_failure(self, make_processor, sample_pdf):
        """RuntimeError in insert_pages is wrapped as StorageError.

        PDF documents have visual content, so the processor calls
        insert_pages during _store_koji.
        """
        storage = FailingInsertPagesStorage()
        storage.open()
        processor = make_processor(storage=storage)

        with pytest.raises((StorageError, ProcessingError)):
            processor.process_document(str(sample_pdf))

    def test_insert_chunks_failure(self, make_processor, sample_md):
        """RuntimeError in insert_chunks is wrapped as StorageError.

        Markdown documents are text-only, so the processor calls
        insert_chunks (but not insert_pages) during _store_koji.
        """
        storage = FailingInsertChunksStorage()
        storage.open()
        processor = make_processor(storage=storage)

        with pytest.raises((StorageError, ProcessingError)):
            processor.process_document(str(sample_md))


# ============================================================================
# TestCallbackOnFailure
# ============================================================================


class TestCallbackOnFailure:
    """Verify status callbacks report failure state on processing errors."""

    def test_callback_captures_failure_status(
        self, make_processor, status_collector, tmp_path
    ):
        """Status callback receives at least one status with status='failed'.

        A corrupt file triggers a ParsingError; the processor's except
        block calls _update_failure_status before re-raising.
        """
        corrupt = tmp_path / "callback_corrupt.pdf"
        corrupt.write_bytes(os.urandom(256))

        callback, statuses = status_collector
        processor = make_processor()

        with pytest.raises(Exception):
            processor.process_document(str(corrupt), status_callback=callback)

        failed = [s for s in statuses if s.status == "failed"]
        assert len(failed) >= 1, (
            f"Expected at least one 'failed' status, got: "
            f"{[s.status for s in statuses]}"
        )

    def test_callback_captures_error_message(
        self, make_processor, status_collector, tmp_path
    ):
        """The failed status entry includes a non-empty error_message.

        Verifies the error diagnostic is propagated through the callback
        so callers can surface it to users.
        """
        corrupt = tmp_path / "callback_err_msg.pdf"
        corrupt.write_bytes(os.urandom(256))

        callback, statuses = status_collector
        processor = make_processor()

        with pytest.raises(Exception):
            processor.process_document(str(corrupt), status_callback=callback)

        failed = [s for s in statuses if s.status == "failed"]
        assert len(failed) >= 1, "Expected at least one failed status"
        assert failed[0].error_message, (
            "Failed status should contain a non-empty error_message"
        )
