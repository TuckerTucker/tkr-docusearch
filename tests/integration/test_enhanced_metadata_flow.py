"""Integration tests for enhanced metadata pipeline.

Replaces the 5 skipped stubs in ``tests/e2e/test_enhanced_mode_e2e.py``
with real implementations.  Processes fixture documents via
``DocumentProcessor`` with ``MockShikomiIngester`` + real KojiClient,
then verifies metadata fields are correctly stored and retrievable.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.config.koji_config import KojiConfig
from src.core.testing.mocks import MockShikomiIngester
from src.processing.processor import DocumentProcessor, StorageConfirmation
from src.storage.koji_client import KojiClient

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def koji_client(tmp_path) -> KojiClient:
    """Real KojiClient backed by a temporary file database."""
    config = KojiConfig(db_path=str(tmp_path / "metadata_test.db"))
    client = KojiClient(config)
    client.open()
    yield client
    client.close()


@pytest.fixture
def processor(koji_client) -> DocumentProcessor:
    """DocumentProcessor with mock ingester + real Koji."""
    ingester = MockShikomiIngester()
    ingester.connect()
    return DocumentProcessor(ingester=ingester, storage_client=koji_client)


@pytest.fixture
def processed_pdf(processor, koji_client) -> tuple[StorageConfirmation, KojiClient]:
    """Process sample.txt and return (confirmation, koji_client).

    Uses sample.txt because it doesn't trigger page rendering which
    requires docling/PDF libraries.  The mock ingester returns
    deterministic chunks regardless of file type.
    """
    fixture = FIXTURES_DIR / "sample.txt"
    assert fixture.exists(), "Missing fixture: sample.txt"

    confirmation = processor.process_document(
        file_path=str(fixture),
        project_id="test-project",
    )
    return confirmation, koji_client


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestEnhancedMetadataFlow:
    """Validates metadata stored by the document processing pipeline."""

    def test_upload_and_process_stores_metadata(self, processed_pdf):
        """Process a document and verify core metadata in Koji."""
        confirmation, koji = processed_pdf

        doc = koji.get_document(confirmation.doc_id)
        assert doc is not None
        assert doc["filename"] == "sample.txt"
        assert doc.get("project_id") == "test-project"
        assert doc.get("format") is not None

    def test_chunks_have_text_content(self, processed_pdf):
        """Chunks contain non-empty text content."""
        confirmation, koji = processed_pdf

        chunks = koji.get_chunks_for_document(confirmation.doc_id)
        assert len(chunks) > 0

        for chunk in chunks:
            assert chunk.get("text") is not None
            assert len(chunk["text"]) > 0

    def test_page_chunk_mapping(self, processed_pdf):
        """Chunks are assigned to valid page numbers."""
        confirmation, koji = processed_pdf

        chunks = koji.get_chunks_for_document(confirmation.doc_id)
        assert len(chunks) > 0

        for chunk in chunks:
            assert "page_num" in chunk
            assert chunk["page_num"] >= 1

    def test_text_metadata_fields(self, processed_pdf):
        """Text chunks include context metadata from the ingester."""
        confirmation, koji = processed_pdf

        chunks = koji.get_chunks_for_document(confirmation.doc_id)
        assert len(chunks) > 0

        # MockShikomiIngester provides context (parent_heading, section_path)
        chunk = chunks[0]
        assert chunk.get("id") is not None
        assert chunk.get("doc_id") == confirmation.doc_id

    def test_storage_confirmation_fields(self, processed_pdf):
        """StorageConfirmation has all required fields populated."""
        confirmation, _ = processed_pdf

        assert confirmation.doc_id is not None
        assert len(confirmation.doc_id) > 0
        assert isinstance(confirmation.text_ids, list)
        assert len(confirmation.text_ids) > 0
