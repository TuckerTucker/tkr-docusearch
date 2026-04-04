"""Integration tests for the API server + processing worker split.

Tests the complete job lifecycle: API creates jobs in Koji,
worker claims and processes them, status is readable via API.

Uses real KojiClient with mock embeddings (no GPU required).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import src.processing.worker_webhook as ww
from src.config.koji_config import KojiConfig
from src.core.testing.mocks import MockShikomiIngester
from src.processing.processor import DocumentProcessor
from src.processing.worker import process_job
from src.storage.koji_client import KojiClient

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def koji(tmp_path):
    """Real KojiClient with fresh database."""
    config = KojiConfig(db_path=str(tmp_path / "split_test.db"))
    client = KojiClient(config)
    client.open()
    yield client
    client.close()


@pytest.fixture
def api_client(koji, tmp_path):
    """API server TestClient backed by real Koji."""
    uploads = tmp_path / "uploads"
    uploads.mkdir()

    originals = {
        "koji_client": ww.koji_client,
        "query_engine": ww.query_engine,
        "status_manager": ww.status_manager,
        "UPLOADS_DIR": ww.UPLOADS_DIR,
        "processing_status": ww.processing_status,
        "pending_uploads": ww.pending_uploads,
    }

    ww.koji_client = koji
    ww.query_engine = MagicMock()
    ww.status_manager = MagicMock()
    ww.status_manager.create_status.return_value = None
    ww.UPLOADS_DIR = uploads
    ww.processing_status = {}
    ww.pending_uploads = {}

    client = TestClient(ww.app, raise_server_exceptions=False)
    yield client

    for attr, value in originals.items():
        setattr(ww, attr, value)


@pytest.fixture
def mock_processor(koji):
    """DocumentProcessor with mock ingester + real Koji."""
    ingester = MockShikomiIngester()
    ingester.connect()
    return DocumentProcessor(ingester=ingester, storage_client=koji)


def _upload(client, fixture_name):
    """Upload a fixture file and return the response."""
    path = FIXTURES / fixture_name
    with open(path, "rb") as fh:
        return client.post("/uploads/", files={"f": (fixture_name, fh)})


# ===========================================================================
# Job Queue Round-Trip
# ===========================================================================


class TestJobQueueRoundTrip:
    """API creates job -> worker claims -> processes -> completes."""

    def test_upload_creates_job(self, api_client, koji) -> None:
        """POST /uploads/ creates a queued job in Koji."""
        resp = _upload(api_client, "sample.txt")
        assert resp.status_code == 200

        doc_id = resp.json()["doc_id"]
        job = koji.get_job(doc_id)
        assert job is not None
        assert job["status"] == "queued"
        assert job["filename"] == "sample.txt"

    def test_worker_claims_and_completes(
        self, api_client, koji, mock_processor,
    ) -> None:
        """Worker claims a queued job and marks it completed."""
        resp = _upload(api_client, "sample.txt")
        doc_id = resp.json()["doc_id"]

        # Worker claims
        job = koji.claim_next_job()
        assert job is not None
        assert job["doc_id"] == doc_id

        # Worker processes
        process_job(job, mock_processor, koji)

        # Job is completed
        result = koji.get_job(doc_id)
        assert result["status"] == "completed"

    def test_document_stored_after_processing(
        self, api_client, koji, mock_processor,
    ) -> None:
        """After worker processes, document + chunks exist in Koji."""
        _upload(api_client, "sample.pdf")

        job = koji.claim_next_job()
        process_job(job, mock_processor, koji)

        docs = koji.list_documents()
        assert len(docs) >= 1
        doc = docs[0]
        chunks = koji.get_chunks_for_document(doc["doc_id"])
        assert len(chunks) >= 1


# ===========================================================================
# Status API
# ===========================================================================


class TestStatusAPI:
    """Status endpoints read from Koji processing_jobs."""

    def test_status_shows_queued_job(self, api_client, koji) -> None:
        """GET /status/{doc_id} returns job status from Koji."""
        resp = _upload(api_client, "sample.txt")
        doc_id = resp.json()["doc_id"]

        # Patch status_api to use our test Koji
        with patch("src.processing.status_api._koji_client", koji):
            status_resp = api_client.get(f"/status/{doc_id}")

        assert status_resp.status_code == 200
        data = status_resp.json()
        assert data["status"] == "queued"
        assert data["doc_id"] == doc_id

    def test_status_queue_lists_jobs(self, api_client, koji) -> None:
        """GET /status/queue returns all jobs."""
        _upload(api_client, "sample.txt")
        _upload(api_client, "sample.md")

        with patch("src.processing.status_api._koji_client", koji):
            resp = api_client.get("/status/queue")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2
        assert data["active"] >= 2

    def test_status_updates_after_processing(
        self, api_client, koji, mock_processor,
    ) -> None:
        """Job status updates to 'completed' after worker processes."""
        resp = _upload(api_client, "sample.txt")
        doc_id = resp.json()["doc_id"]

        job = koji.claim_next_job()
        process_job(job, mock_processor, koji)

        with patch("src.processing.status_api._koji_client", koji):
            status_resp = api_client.get(f"/status/{doc_id}")

        assert status_resp.json()["status"] == "completed"


# ===========================================================================
# Error Handling
# ===========================================================================


class TestErrorHandling:
    """Failed jobs are tracked correctly."""

    def test_failed_job_has_error_message(
        self, api_client, koji,
    ) -> None:
        """A job that fails records the error in Koji."""
        _upload(api_client, "sample.txt")

        job = koji.claim_next_job()

        # Processor that raises
        bad_processor = MagicMock()
        bad_processor.process_document.side_effect = RuntimeError("Disk full")

        process_job(job, bad_processor, koji)

        result = koji.get_job(job["doc_id"])
        assert result["status"] == "failed"
        assert "Disk full" in result["error"]

    def test_failed_job_visible_in_status(
        self, api_client, koji,
    ) -> None:
        """Failed jobs appear in the status queue."""
        _upload(api_client, "sample.txt")

        job = koji.claim_next_job()
        koji.fail_job(job["doc_id"], "Test failure")

        with patch("src.processing.status_api._koji_client", koji):
            resp = api_client.get("/status/queue")

        data = resp.json()
        assert data["failed"] >= 1


# ===========================================================================
# Multiple Jobs
# ===========================================================================


class TestMultipleJobs:
    """Multiple jobs processed sequentially."""

    def test_three_jobs_in_order(
        self, api_client, koji, mock_processor,
    ) -> None:
        """Three uploads create three jobs, processed in FIFO order."""
        ids = []
        for fixture in ["sample.txt", "sample.md", "sample.csv"]:
            resp = _upload(api_client, fixture)
            ids.append(resp.json()["doc_id"])

        # Process all three
        for _ in range(3):
            job = koji.claim_next_job()
            assert job is not None
            process_job(job, mock_processor, koji)

        # All completed
        for doc_id in ids:
            assert koji.get_job(doc_id)["status"] == "completed"

        # No more jobs
        assert koji.claim_next_job() is None
