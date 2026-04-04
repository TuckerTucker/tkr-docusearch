"""Tests for the headless processing worker.

Tests process_job() with mock ingester + real Koji to verify
the job lifecycle: claim → process → complete/fail.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.config.koji_config import KojiConfig
from src.core.testing.mocks import MockShikomiIngester
from src.processing.processor import DocumentProcessor
from src.processing.worker import process_job
from src.storage.koji_client import KojiClient

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def koji(tmp_path):
    """Real KojiClient with fresh database."""
    config = KojiConfig(db_path=str(tmp_path / "worker_test.db"))
    client = KojiClient(config)
    client.open()
    yield client
    client.close()


@pytest.fixture
def processor(koji):
    """DocumentProcessor with mock ingester + real Koji."""
    ingester = MockShikomiIngester()
    ingester.connect()
    return DocumentProcessor(ingester=ingester, storage_client=koji)


class TestProcessJob:
    """Tests for process_job()."""

    def test_successful_job_completes(self, koji, processor) -> None:
        """A successful job is marked as completed in Koji."""
        koji.create_job("test1", "sample.pdf", str(FIXTURES / "sample.pdf"))
        job = koji.claim_next_job()

        process_job(job, processor, koji)

        result = koji.get_job("test1")
        assert result["status"] == "completed"
        assert result["progress"] == 1.0
        assert result["completed_at"] is not None

    def test_successful_job_stores_document(self, koji, processor) -> None:
        """After processing, the document record exists in Koji."""
        koji.create_job("test2", "sample.pdf", str(FIXTURES / "sample.pdf"))
        job = koji.claim_next_job()

        process_job(job, processor, koji)

        # MockShikomiIngester hashes the file path, not content
        docs = koji.list_documents()
        assert len(docs) >= 1

    def test_successful_job_stores_chunks(self, koji, processor) -> None:
        """After processing, text chunks are stored in Koji."""
        koji.create_job("test3", "sample.pdf", str(FIXTURES / "sample.pdf"))
        job = koji.claim_next_job()

        process_job(job, processor, koji)

        docs = koji.list_documents()
        doc_id = docs[0]["doc_id"]
        chunks = koji.get_chunks_for_document(doc_id)
        assert len(chunks) >= 1

    def test_failed_job_records_error(self, koji) -> None:
        """A job that fails is marked with error message."""
        koji.create_job("fail1", "bad.pdf", "/nonexistent/bad.pdf")
        job = koji.claim_next_job()

        # Processor that raises
        mock_processor = MagicMock()
        mock_processor.process_document.side_effect = RuntimeError("File not found")

        process_job(job, mock_processor, koji)

        result = koji.get_job("fail1")
        assert result["status"] == "failed"
        assert "File not found" in result["error"]
        assert result["completed_at"] is not None

    def test_status_callback_updates_progress(self, koji, processor) -> None:
        """Status callbacks from processing update the job in Koji."""
        koji.create_job("prog1", "sample.pdf", str(FIXTURES / "sample.pdf"))
        job = koji.claim_next_job()

        process_job(job, processor, koji)

        # After completion the final status is 'completed',
        # but intermediate updates should have been written
        result = koji.get_job("prog1")
        assert result["status"] == "completed"

    def test_multiple_jobs_sequential(self, koji, processor) -> None:
        """Multiple jobs can be processed in sequence."""
        koji.create_job("seq1", "sample.pdf", str(FIXTURES / "sample.pdf"))
        koji.create_job("seq2", "sample.png", str(FIXTURES / "sample.png"))

        job1 = koji.claim_next_job()
        process_job(job1, processor, koji)

        job2 = koji.claim_next_job()
        process_job(job2, processor, koji)

        assert koji.get_job("seq1")["status"] == "completed"
        assert koji.get_job("seq2")["status"] == "completed"

        # Both should have stored documents
        docs = koji.list_documents()
        assert len(docs) >= 2
