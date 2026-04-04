"""
Integration tests for the worker webhook POST /uploads/ endpoint.

Tests the upload mechanics on the worker FastAPI app:
- Valid file acceptance and saving to disk
- Filename validation (dot-files, empty names)
- File size enforcement
- Filename collision handling
- File type acceptance (docx, markdown)

These tests use FastAPI TestClient against the worker app with patched
module-level globals to avoid starting real services.
"""

import asyncio
import io
import os
import zipfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import src.processing.worker_webhook as ww


@pytest.fixture
def uploads_dir(tmp_path):
    """Temporary uploads directory."""
    d = tmp_path / "uploads"
    d.mkdir()
    return d


@pytest.fixture
def test_client(uploads_dir, tmp_path):
    """TestClient with patched worker globals.

    Patches module-level globals on the worker_webhook module so the
    API server can be exercised without real infrastructure.
    The API server creates jobs in Koji — we mock koji_client so
    create_job() is a no-op.
    """
    originals = {
        "koji_client": ww.koji_client,
        "query_engine": ww.query_engine,
        "status_manager": ww.status_manager,
        "UPLOADS_DIR": ww.UPLOADS_DIR,
        "processing_status": ww.processing_status,
        "pending_uploads": ww.pending_uploads,
    }

    mock_koji = MagicMock()
    mock_koji.create_job.return_value = None
    mock_koji.get_job.return_value = None

    ww.koji_client = mock_koji
    ww.query_engine = MagicMock()
    ww.status_manager = MagicMock()
    ww.status_manager.create_status.return_value = None
    ww.UPLOADS_DIR = uploads_dir
    ww.processing_status = {}
    ww.pending_uploads = {}

    client = TestClient(ww.app, raise_server_exceptions=False)
    yield client

    for attr, value in originals.items():
        setattr(ww, attr, value)


# ============================================================================
# Upload Endpoint Tests
# ============================================================================


class TestUploadEndpoint:
    """Core upload endpoint behaviour."""

    def test_valid_pdf_upload(self, test_client):
        """Upload a minimal PDF file and verify 200 response."""
        content = b"%PDF-1.4 test"
        response = test_client.post(
            "/uploads/",
            files={"f": ("report.pdf", io.BytesIO(content), "application/pdf")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert "doc_id" in data

    def test_file_saved_to_disk(self, test_client, uploads_dir):
        """Uploaded bytes are persisted to the uploads directory."""
        content = b"%PDF-1.4 saved-to-disk-test"
        response = test_client.post(
            "/uploads/",
            files={"f": ("saved.pdf", io.BytesIO(content), "application/pdf")},
        )

        assert response.status_code == 200

        # At least one file should exist in uploads_dir with the content
        saved_files = list(uploads_dir.iterdir())
        assert len(saved_files) >= 1

        # Find the file whose content matches
        found = any(f.read_bytes() == content for f in saved_files)
        assert found, f"Expected content not found in {saved_files}"

    def test_dot_file_rejected(self, test_client):
        """Filenames starting with a dot are rejected with 400."""
        response = test_client.post(
            "/uploads/",
            files={"f": (".hidden", io.BytesIO(b"secret"), "application/octet-stream")},
        )

        assert response.status_code == 400
        assert "Invalid filename" in response.json()["detail"]

    def test_empty_filename_rejected(self, test_client):
        """An empty filename is rejected.

        FastAPI's multipart validation rejects the empty filename before
        the handler runs, returning 422 Unprocessable Entity.
        """
        response = test_client.post(
            "/uploads/",
            files={"f": ("", io.BytesIO(b"content"), "application/pdf")},
        )

        assert response.status_code == 422

    def test_oversized_file_rejected(self, test_client, monkeypatch):
        """Files exceeding MAX_FILE_SIZE_MB are rejected.

        The upload endpoint reads MAX_FILE_SIZE_MB from os.environ
        on each call and rejects files that exceed the limit with 413.
        """
        # Set a very small limit so even a tiny payload exceeds it
        monkeypatch.setenv("MAX_FILE_SIZE_MB", "0")

        content = b"A" * 100  # Any non-empty payload
        response = test_client.post(
            "/uploads/",
            files={"f": ("big.pdf", io.BytesIO(content), "application/pdf")},
        )

        # The broad except catches the 413 HTTPException and wraps it in 500.
        # If the bug is fixed (HTTPException re-raised directly), this will
        # need updating to assert 413.
        assert response.status_code == 413

    def test_filename_collision_appends_suffix(self, test_client, uploads_dir):
        """When a file with the same name already exists, a counter suffix is appended."""
        # Pre-create a file so the first name is taken
        (uploads_dir / "collision.pdf").write_bytes(b"existing")

        content = b"%PDF-1.4 collision-test"
        response = test_client.post(
            "/uploads/",
            files={"f": ("collision.pdf", io.BytesIO(content), "application/pdf")},
        )

        assert response.status_code == 200

        # The original file should still be untouched
        assert (uploads_dir / "collision.pdf").read_bytes() == b"existing"

        # A new file with a suffix should have been created
        collision_file = uploads_dir / "collision_1.pdf"
        assert collision_file.exists(), (
            f"Expected collision_1.pdf but found: {list(uploads_dir.iterdir())}"
        )
        assert collision_file.read_bytes() == content


# ============================================================================
# File Type Validation Tests
# ============================================================================


class TestUploadFileTypeValidation:
    """Verify that various document types are accepted by the endpoint."""

    def test_docx_accepted(self, test_client):
        """A minimal DOCX file (ZIP with [Content_Types].xml) is accepted."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr(
                "[Content_Types].xml",
                '<?xml version="1.0"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                "</Types>",
            )
            zf.writestr(
                "word/document.xml",
                '<?xml version="1.0"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                "<w:body><w:p><w:r><w:t>Test</w:t></w:r></w:p></w:body>"
                "</w:document>",
            )
        docx_bytes = buf.getvalue()

        response = test_client.post(
            "/uploads/",
            files={
                "f": (
                    "report.docx",
                    io.BytesIO(docx_bytes),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"

    def test_markdown_accepted(self, test_client):
        """A .md (Markdown) file is accepted."""
        md_content = b"# Hello World\n\nThis is a test document."
        response = test_client.post(
            "/uploads/",
            files={"f": ("notes.md", io.BytesIO(md_content), "text/markdown")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
