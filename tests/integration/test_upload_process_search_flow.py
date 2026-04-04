"""Integration tests for the upload -> process -> verify flow.

Tests the core end-to-end workflow:
1. Upload a file via ``POST /uploads/`` (API server creates a job in Koji)
2. Process the job inline via ``process_uploaded_job()`` (simulates worker)
3. Verify the document appears in Koji storage

Uses real KojiClient with mock embeddings (no GPU required).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from tkr_docusearch.storage.koji_client import KojiClient

from .conftest import process_uploaded_job

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _upload_fixture(
    client: TestClient,
    fixture_name: str,
    project_id: str = "default",
):
    """Upload a fixture file and return the HTTP response."""
    fixture_path = FIXTURES_DIR / fixture_name
    assert fixture_path.exists(), f"Missing fixture: {fixture_path}"

    with open(fixture_path, "rb") as fh:
        resp = client.post(
            "/uploads/",
            files={"f": (fixture_name, fh)},
            params={"project_id": project_id},
        )
    return resp


def _find_doc_by_filename(
    koji: KojiClient,
    filename: str,
) -> Optional[dict]:
    """Look up a document in Koji by filename."""
    docs = koji.list_documents(limit=1000)
    for doc in docs:
        if doc.get("filename") == filename:
            return doc
    return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestUploadProcessFlow:
    """Upload files via POST /uploads/ and verify storage state."""

    def test_upload_returns_queued_with_doc_id(self, sync_worker_client):
        """POST /uploads/ returns status=queued and a doc_id."""
        client, _ = sync_worker_client
        resp = _upload_fixture(client, "sample.txt")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "queued"
        assert data["doc_id"] is not None
        assert len(data["doc_id"]) > 8

    def test_upload_creates_job_in_koji(self, sync_worker_client):
        """Upload creates a processing_jobs row with status=queued."""
        client, koji = sync_worker_client
        resp = _upload_fixture(client, "sample.txt")
        doc_id = resp.json()["doc_id"]

        job = koji.get_job(doc_id)
        assert job is not None
        assert job["status"] == "queued"
        assert job["filename"] == "sample.txt"

    def test_upload_then_process_stores_document(self, sync_worker_client):
        """After upload + processing, document exists in Koji."""
        client, koji = sync_worker_client
        _upload_fixture(client, "sample.txt")
        process_uploaded_job(koji)

        doc = _find_doc_by_filename(koji, "sample.txt")
        assert doc is not None
        assert doc["filename"] == "sample.txt"

    def test_upload_then_process_stores_chunks(self, sync_worker_client):
        """Processing creates text chunks in Koji."""
        client, koji = sync_worker_client
        _upload_fixture(client, "sample.txt")
        process_uploaded_job(koji)

        doc = _find_doc_by_filename(koji, "sample.txt")
        assert doc is not None

        chunks = koji.get_chunks_for_document(doc["doc_id"])
        assert len(chunks) > 0

    def test_upload_multiple_documents(self, sync_worker_client):
        """Upload multiple distinct files, all stored separately."""
        client, koji = sync_worker_client

        for fixture in ["sample.txt", "sample.md", "sample.csv"]:
            _upload_fixture(client, fixture)
            process_uploaded_job(koji)

        docs = koji.list_documents()
        filenames = {d["filename"] for d in docs}
        assert "sample.txt" in filenames
        assert "sample.md" in filenames

    def test_upload_to_specific_project(self, sync_worker_client):
        """Upload with project_id stores document in that project."""
        client, koji = sync_worker_client
        _upload_fixture(client, "sample.txt", project_id="my-project")
        process_uploaded_job(koji)

        doc = _find_doc_by_filename(koji, "sample.txt")
        assert doc is not None
        assert doc.get("project_id") == "my-project"

    def test_job_completed_after_processing(self, sync_worker_client):
        """Job status is 'completed' after processing."""
        client, koji = sync_worker_client
        resp = _upload_fixture(client, "sample.txt")
        doc_id = resp.json()["doc_id"]
        process_uploaded_job(koji)

        job = koji.get_job(doc_id)
        assert job["status"] == "completed"

    def test_upload_duplicate_content_same_doc_id(self, sync_worker_client):
        """Uploading same file content twice yields same doc_id."""
        client, _ = sync_worker_client

        resp1 = _upload_fixture(client, "sample.txt")
        resp2 = _upload_fixture(client, "sample.txt")

        assert resp1.json()["doc_id"] == resp2.json()["doc_id"]


class TestDocumentDeletion:
    """Verify deletion removes documents from Koji."""

    def test_process_then_delete_removes_document(self, sync_worker_client):
        """Upload, process, then delete via documents API."""
        client, koji = sync_worker_client
        _upload_fixture(client, "sample.txt")
        process_uploaded_job(koji)

        doc = _find_doc_by_filename(koji, "sample.txt")
        assert doc is not None
        doc_id = doc["doc_id"]

        with patch(
            "src.processing.documents_api.get_storage_client",
            return_value=koji,
        ):
            client.delete(f"/documents/{doc_id}")

        assert koji.get_document(doc_id) is None
