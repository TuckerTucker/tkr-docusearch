"""Tests for processing_jobs queue in KojiClient.

Validates the job queue CRUD operations used by the API server
(create_job) and processing worker (claim_next_job, update, complete, fail).
"""

from __future__ import annotations

import time

import pytest

from src.config.koji_config import KojiConfig
from src.storage.koji_client import KojiClient, KojiDuplicateError


@pytest.fixture
def koji(tmp_path):
    """Real KojiClient with fresh database."""
    config = KojiConfig(db_path=str(tmp_path / "jobs_test.db"))
    client = KojiClient(config)
    client.open()
    yield client
    client.close()


class TestCreateJob:
    """Tests for create_job()."""

    def test_create_job(self, koji) -> None:
        """Creates a job with correct fields."""
        koji.create_job("abc123", "test.pdf", "/tmp/test.pdf", "default")

        job = koji.get_job("abc123")
        assert job is not None
        assert job["doc_id"] == "abc123"
        assert job["filename"] == "test.pdf"
        assert job["file_path"] == "/tmp/test.pdf"
        assert job["project_id"] == "default"
        assert job["status"] == "queued"
        assert job["progress"] == 0.0
        assert job["queued_at"] is not None
        assert job["started_at"] is None
        assert job["completed_at"] is None
        assert job["error"] is None

    def test_duplicate_keeps_original(self, koji) -> None:
        """Inserting a duplicate doc_id silently keeps the original row."""
        koji.create_job("dup1", "a.pdf", "/tmp/a.pdf")
        koji.create_job("dup1", "b.pdf", "/tmp/b.pdf")

        job = koji.get_job("dup1")
        assert job["filename"] == "a.pdf"


class TestClaimNextJob:
    """Tests for claim_next_job()."""

    def test_claim_returns_oldest(self, koji) -> None:
        """Claims the oldest queued job."""
        koji.create_job("first", "a.pdf", "/tmp/a.pdf")
        koji.create_job("second", "b.pdf", "/tmp/b.pdf")

        job = koji.claim_next_job()
        assert job is not None
        assert job["doc_id"] == "first"
        assert job["status"] == "processing"
        assert job["started_at"] is not None

    def test_claim_skips_processing(self, koji) -> None:
        """Only claims queued jobs, not already-processing ones."""
        koji.create_job("running", "a.pdf", "/tmp/a.pdf")
        koji.claim_next_job()  # claims "running"

        koji.create_job("waiting", "b.pdf", "/tmp/b.pdf")
        job = koji.claim_next_job()
        assert job["doc_id"] == "waiting"

    def test_claim_returns_none_when_empty(self, koji) -> None:
        """Returns None when no queued jobs exist."""
        assert koji.claim_next_job() is None

    def test_claim_returns_none_when_all_processing(self, koji) -> None:
        """Returns None when all jobs are already claimed."""
        koji.create_job("only", "a.pdf", "/tmp/a.pdf")
        koji.claim_next_job()

        assert koji.claim_next_job() is None

    def test_claimed_job_visible_in_koji(self, koji) -> None:
        """After claiming, the job's status is 'processing' in the database."""
        koji.create_job("check", "a.pdf", "/tmp/a.pdf")
        koji.claim_next_job()

        job = koji.get_job("check")
        assert job["status"] == "processing"


class TestUpdateJobProgress:
    """Tests for update_job_progress()."""

    def test_update_progress(self, koji) -> None:
        """Updates status, progress, and stage."""
        koji.create_job("prog", "a.pdf", "/tmp/a.pdf")
        koji.update_job_progress("prog", "processing", 0.5, "Chunking")

        job = koji.get_job("prog")
        assert job["status"] == "processing"
        assert job["progress"] == 0.5
        assert job["stage"] == "Chunking"


class TestCompleteAndFailJob:
    """Tests for complete_job() and fail_job()."""

    def test_complete_job(self, koji) -> None:
        """Marks job as completed with progress=1.0."""
        koji.create_job("done", "a.pdf", "/tmp/a.pdf")
        koji.claim_next_job()
        koji.complete_job("done")

        job = koji.get_job("done")
        assert job["status"] == "completed"
        assert job["progress"] == 1.0
        assert job["completed_at"] is not None

    def test_fail_job(self, koji) -> None:
        """Marks job as failed with error message."""
        koji.create_job("bad", "a.pdf", "/tmp/a.pdf")
        koji.claim_next_job()
        koji.fail_job("bad", "Out of memory")

        job = koji.get_job("bad")
        assert job["status"] == "failed"
        assert job["error"] == "Out of memory"
        assert job["completed_at"] is not None


class TestListJobs:
    """Tests for list_jobs()."""

    def test_list_all(self, koji) -> None:
        """Lists all jobs regardless of status."""
        koji.create_job("j1", "a.pdf", "/tmp/a.pdf")
        koji.create_job("j2", "b.pdf", "/tmp/b.pdf")
        koji.claim_next_job()
        koji.complete_job("j1")

        jobs = koji.list_jobs()
        assert len(jobs) == 2

    def test_list_by_status(self, koji) -> None:
        """Filters jobs by status."""
        koji.create_job("q1", "a.pdf", "/tmp/a.pdf")
        koji.create_job("q2", "b.pdf", "/tmp/b.pdf")
        koji.claim_next_job()  # q1 → processing

        queued = koji.list_jobs(status="queued")
        assert len(queued) == 1
        assert queued[0]["doc_id"] == "q2"

        processing = koji.list_jobs(status="processing")
        assert len(processing) == 1
        assert processing[0]["doc_id"] == "q1"

    def test_list_respects_limit(self, koji) -> None:
        """Respects the limit parameter."""
        for i in range(5):
            koji.create_job(f"lim{i}", f"{i}.pdf", f"/tmp/{i}.pdf")

        jobs = koji.list_jobs(limit=3)
        assert len(jobs) == 3


class TestGetJob:
    """Tests for get_job()."""

    def test_get_existing(self, koji) -> None:
        """Returns job dict for existing doc_id."""
        koji.create_job("exists", "a.pdf", "/tmp/a.pdf")
        job = koji.get_job("exists")
        assert job is not None
        assert job["doc_id"] == "exists"

    def test_get_nonexistent(self, koji) -> None:
        """Returns None for unknown doc_id."""
        assert koji.get_job("nope") is None


class TestCleanupOldJobs:
    """Tests for cleanup_old_jobs()."""

    def test_cleanup_removes_old_completed(self, koji) -> None:
        """Deletes completed jobs older than threshold."""
        koji.create_job("old", "a.pdf", "/tmp/a.pdf")
        koji.claim_next_job()
        koji.complete_job("old")

        # With max_age=0, everything completed is "old"
        deleted = koji.cleanup_old_jobs(max_age_seconds=0)
        assert deleted >= 1
        assert koji.get_job("old") is None

    def test_cleanup_keeps_queued(self, koji) -> None:
        """Does not delete queued jobs."""
        koji.create_job("keep", "a.pdf", "/tmp/a.pdf")

        koji.cleanup_old_jobs(max_age_seconds=0)
        assert koji.get_job("keep") is not None
