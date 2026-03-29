"""Integration tests for DocumentProcessor with real Koji storage."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import numpy as np
import pytest

from shikomi import IngestResult
from shikomi.types import MultiVectorEmbedding, TextChunk

from src.config.koji_config import KojiConfig
from src.core.testing.mocks import MockKojiClient
from src.processing.processor import (
    DocumentProcessor,
    ProcessingStatus,
    StorageConfirmation,
)
from src.processing.shikomi_ingester import ShikomiIngester
from src.storage.koji_client import KojiClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_embedding(num_tokens: int = 10, dim: int = 128) -> MultiVectorEmbedding:
    """Create a deterministic MultiVectorEmbedding."""
    data = np.random.randn(num_tokens, dim).astype(np.float32)
    return MultiVectorEmbedding(num_tokens=num_tokens, dim=dim, data=data)


def _make_ingest_result(
    chunk_count: int = 3,
    content_hash: str = "testhash123",
    vtt_content: str | None = None,
    markdown_content: str | None = "# Document\n\nSample text.",
) -> IngestResult:
    """Build a realistic IngestResult with the given number of chunks."""
    chunks = []
    text_embeddings = []

    for i in range(chunk_count):
        chunks.append(
            TextChunk(
                id=f"chunk-{i:03d}",
                content=f"This is test chunk number {i} with enough words to be meaningful.",
                source_path="/tmp/test.pdf",
                start_char=i * 100,
                end_char=(i + 1) * 100,
                page=1,
            ),
        )
        text_embeddings.append(_make_embedding())

    return IngestResult(
        chunks=chunks,
        text_embeddings=text_embeddings,
        content_hash=content_hash,
        markdown_content=markdown_content,
        metadata={"title": "Test Document", "author": "Test Author"},
        source_path="/tmp/test.pdf",
        source_type="pdf",
        chunk_count=chunk_count,
        vtt_content=vtt_content,
    )


def _make_mock_ingester(
    ingest_result: IngestResult | None = None,
) -> ShikomiIngester:
    """Create a mock ShikomiIngester that returns the given IngestResult.

    The returned object is a MagicMock with spec=ShikomiIngester, so
    isinstance checks and attribute access work as expected by
    DocumentProcessor.
    """
    if ingest_result is None:
        ingest_result = _make_ingest_result()

    mock = MagicMock(spec=ShikomiIngester)
    mock.process.return_value = ingest_result
    mock._run_async = MagicMock(side_effect=lambda coro: None)
    mock.engine = MagicMock()
    return mock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def koji_storage(tmp_path: Path) -> KojiClient:
    """Real KojiClient backed by a temporary file database."""
    config = KojiConfig(db_path=str(tmp_path / "integration_test.db"))
    client = KojiClient(config)
    client.open()
    yield client
    client.close()


@pytest.fixture
def sample_file(tmp_path: Path) -> Path:
    """Create a minimal text file to act as a processing target."""
    fp = tmp_path / "sample.txt"
    fp.write_text("Sample document content for testing.", encoding="utf-8")
    return fp


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


class TestProcessorIntegration:
    """Integration tests exercising DocumentProcessor with real Koji storage."""

    def test_process_stores_document_in_koji(
        self, koji_storage: KojiClient, sample_file: Path,
    ) -> None:
        """Processing stores a document record retrievable from Koji."""
        expected_hash = "storedhash001"
        result = _make_ingest_result(
            chunk_count=2, content_hash=expected_hash,
        )
        mock_ingester = _make_mock_ingester(result)

        processor = DocumentProcessor(
            ingester=mock_ingester, storage_client=koji_storage,
        )

        processor.process_document(
            file_path=str(sample_file), project_id="test-proj",
        )

        doc = koji_storage.get_document(expected_hash)
        assert doc is not None
        assert doc["doc_id"] == expected_hash
        assert doc["project_id"] == "test-proj"

    def test_process_stores_chunks_with_correct_fields(
        self, koji_storage: KojiClient, sample_file: Path,
    ) -> None:
        """Stored chunks have populated text, page_num, embedding, word_count."""
        result = _make_ingest_result(chunk_count=2, content_hash="chunkhash01")
        mock_ingester = _make_mock_ingester(result)

        processor = DocumentProcessor(
            ingester=mock_ingester, storage_client=koji_storage,
        )
        processor.process_document(file_path=str(sample_file))

        chunks = koji_storage.get_chunks_for_document("chunkhash01")
        assert len(chunks) == 2

        for chunk in chunks:
            assert chunk["text"] is not None
            assert len(chunk["text"]) > 0
            assert chunk["page_num"] == 1
            assert chunk["embedding"] is not None
            assert isinstance(chunk["embedding"], bytes)
            assert len(chunk["embedding"]) > 0
            assert chunk["word_count"] > 0

    def test_process_returns_storage_confirmation(
        self, koji_storage: KojiClient, sample_file: Path,
    ) -> None:
        """process_document returns a StorageConfirmation with expected fields."""
        result = _make_ingest_result(chunk_count=4, content_hash="confirmhash")
        mock_ingester = _make_mock_ingester(result)

        processor = DocumentProcessor(
            ingester=mock_ingester, storage_client=koji_storage,
        )
        confirmation = processor.process_document(file_path=str(sample_file))

        assert isinstance(confirmation, StorageConfirmation)
        assert confirmation.doc_id == "confirmhash"
        assert isinstance(confirmation.text_ids, list)
        assert len(confirmation.text_ids) == 4
        assert confirmation.total_size_bytes > 0

    def test_process_status_callbacks_fired(
        self, koji_storage: KojiClient, sample_file: Path,
    ) -> None:
        """Status callback receives parsing, storing, and completed statuses."""
        result = _make_ingest_result(content_hash="statushash01")
        mock_ingester = _make_mock_ingester(result)

        processor = DocumentProcessor(
            ingester=mock_ingester, storage_client=koji_storage,
        )

        captured: list[ProcessingStatus] = []

        def _callback(status: ProcessingStatus) -> None:
            captured.append(status)

        processor.process_document(
            file_path=str(sample_file), status_callback=_callback,
        )

        status_names = [s.status for s in captured]

        # The pipeline emits at least parsing, storing, and completed stages
        assert "parsing" in status_names or "pending" in status_names
        assert "storing" in status_names
        assert "completed" in status_names

    def test_process_with_vtt_saves_file(
        self, koji_storage: KojiClient, sample_file: Path, tmp_path: Path,
    ) -> None:
        """When IngestResult has vtt_content, a VTT file is written to disk."""
        vtt_text = "WEBVTT\n\n00:00:00.000 --> 00:00:05.000\nHello world"
        result = _make_ingest_result(
            content_hash="vtthash01", vtt_content=vtt_text,
        )
        mock_ingester = _make_mock_ingester(result)

        processor = DocumentProcessor(
            ingester=mock_ingester, storage_client=koji_storage,
        )

        # Use tmp_path as the working directory so VTT is written there
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            processor.process_document(file_path=str(sample_file))
        finally:
            os.chdir(original_cwd)

        vtt_path = tmp_path / "data" / "vtt" / "vtthash01.vtt"
        assert vtt_path.exists()
        assert vtt_path.read_text(encoding="utf-8") == vtt_text


class TestProcessorWithMockStorage:
    """Lightweight tests using MockKojiClient for fast feedback."""

    def test_process_with_mock_storage(self) -> None:
        """End-to-end with MockKojiClient confirms the pipeline wiring."""
        storage = MockKojiClient()
        storage.open()

        result = _make_ingest_result(chunk_count=2, content_hash="mockhash")
        mock_ingester = _make_mock_ingester(result)

        processor = DocumentProcessor(
            ingester=mock_ingester, storage_client=storage,
        )

        # Create a temporary file for processing
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False,
        ) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            confirmation = processor.process_document(file_path=temp_path)

            assert confirmation.doc_id == "mockhash"
            assert len(confirmation.text_ids) == 2

            doc = storage.get_document("mockhash")
            assert doc is not None
            assert doc["filename"] == os.path.basename(temp_path)

            chunks = storage.get_chunks_for_document("mockhash")
            assert len(chunks) == 2
        finally:
            os.unlink(temp_path)
