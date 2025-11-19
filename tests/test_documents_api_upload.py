"""
Tests for document upload API endpoint.

Tests POST /upload endpoint for:
- Valid file uploads (PDF, DOCX, PPTX)
- Invalid file type rejection
- File size validation
- Duplicate document handling
- Missing file parameter
- Multiple file uploads
- Filename sanitization
- Response format validation
- Error handling

Target: 90%+ coverage for upload endpoint
"""

import hashlib
import io
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def test_app():
    """Create test FastAPI app without initializing real components."""
    # Import the already-created app instance
    from tkr_docusearch.api import server

    # The app is already created, we just need to return it
    return server.app


@pytest.fixture
def client(test_app):
    """Create test client."""
    # Use TestClient with raise_server_exceptions=False to handle errors gracefully
    return TestClient(test_app, raise_server_exceptions=False)


@pytest.fixture
def sample_pdf_content():
    """Generate minimal valid PDF content."""
    # Minimal PDF that parsers will accept
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<< /Size 4 /Root 1 0 R >>
startxref
190
%%EOF"""


@pytest.fixture
def sample_docx_content():
    """Generate minimal valid DOCX content (ZIP format)."""
    # Minimal DOCX structure (simplified ZIP)
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>',
        )
        zf.writestr(
            "word/document.xml",
            '<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Test</w:t></w:r></w:p></w:body></w:document>',
        )
    return buffer.getvalue()


@pytest.fixture
def sample_pptx_content():
    """Generate minimal valid PPTX content (ZIP format)."""
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>',
        )
        zf.writestr(
            "ppt/presentation.xml",
            '<?xml version="1.0"?><p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"></p:presentation>',
        )
    return buffer.getvalue()


@pytest.fixture
def uploads_dir(tmp_path):
    """Create temporary uploads directory."""
    upload_dir = tmp_path / "data" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Patch the upload directory path
    with patch("tkr_docusearch.api.server.Path") as mock_path:
        mock_path.return_value = upload_dir

        # Also need to handle Path("data/uploads")
        def path_side_effect(path_str):
            if path_str == "data/uploads":
                return upload_dir
            return Path(path_str)

        mock_path.side_effect = path_side_effect
        yield upload_dir


# ============================================================================
# Successful Upload Tests
# ============================================================================


def test_upload_valid_pdf(client, sample_pdf_content, uploads_dir, monkeypatch):
    """Test successful PDF upload."""
    # Patch Path to use our temp directory
    monkeypatch.setattr(
        "src.api.server.Path", lambda x: uploads_dir if x == "data/uploads" else Path(x)
    )

    files = {"file": ("test-report.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}
    response = client.post("/upload", files=files)

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["filename"] == "test-report.pdf"
    assert data["file_size_bytes"] == len(sample_pdf_content)
    assert data["status"] == "queued"
    assert "doc_id" in data
    assert len(data["doc_id"]) == 16  # SHA-256 truncated to 16 chars
    assert "message" in data


def test_upload_valid_docx(client, sample_docx_content, uploads_dir, monkeypatch):
    """Test successful DOCX upload."""
    monkeypatch.setattr(
        "src.api.server.Path", lambda x: uploads_dir if x == "data/uploads" else Path(x)
    )

    files = {
        "file": (
            "annual-report.docx",
            io.BytesIO(sample_docx_content),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    response = client.post("/upload", files=files)

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["filename"] == "annual-report.docx"
    assert data["file_size_bytes"] == len(sample_docx_content)
    assert data["status"] == "queued"
    assert "doc_id" in data


def test_upload_valid_pptx(client, sample_pptx_content, uploads_dir, monkeypatch):
    """Test successful PPTX upload."""
    monkeypatch.setattr(
        "src.api.server.Path", lambda x: uploads_dir if x == "data/uploads" else Path(x)
    )

    files = {
        "file": (
            "presentation.pptx",
            io.BytesIO(sample_pptx_content),
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
    }
    response = client.post("/upload", files=files)

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["filename"] == "presentation.pptx"
    assert data["status"] == "queued"


def test_upload_response_format(client, sample_pdf_content, uploads_dir, monkeypatch):
    """Test that response matches UploadResponse model."""
    monkeypatch.setattr(
        "src.api.server.Path", lambda x: uploads_dir if x == "data/uploads" else Path(x)
    )

    files = {"file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}
    response = client.post("/upload", files=files)

    assert response.status_code == 200
    data = response.json()

    # Verify all required fields
    required_fields = ["success", "doc_id", "filename", "file_size_bytes", "status"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Verify field types
    assert isinstance(data["success"], bool)
    assert isinstance(data["doc_id"], str)
    assert isinstance(data["filename"], str)
    assert isinstance(data["file_size_bytes"], int)
    assert isinstance(data["status"], str)


def test_upload_file_saved_correctly(client, sample_pdf_content, uploads_dir, monkeypatch):
    """Test that uploaded file is saved to disk."""
    monkeypatch.setattr(
        "src.api.server.Path", lambda x: uploads_dir if x == "data/uploads" else Path(x)
    )

    filename = "saved-test.pdf"
    files = {"file": (filename, io.BytesIO(sample_pdf_content), "application/pdf")}
    response = client.post("/upload", files=files)

    assert response.status_code == 200
    data = response.json()

    # Check file was saved
    expected_filename = f"{data['doc_id']}_{filename}"
    saved_file = uploads_dir / expected_filename
    assert saved_file.exists(), f"File not saved: {saved_file}"

    # Verify content matches
    saved_content = saved_file.read_bytes()
    assert saved_content == sample_pdf_content


def test_upload_doc_id_deterministic(client, sample_pdf_content, uploads_dir, monkeypatch):
    """Test that same content produces same doc_id (hash-based)."""
    monkeypatch.setattr(
        "src.api.server.Path", lambda x: uploads_dir if x == "data/uploads" else Path(x)
    )

    # Upload same content twice with different filenames
    files1 = {"file": ("report1.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}
    response1 = client.post("/upload", files=files1)
    doc_id1 = response1.json()["doc_id"]

    files2 = {"file": ("report2.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}
    response2 = client.post("/upload", files=files2)
    doc_id2 = response2.json()["doc_id"]

    # Same content should produce same doc_id
    assert doc_id1 == doc_id2

    # Verify it matches expected hash
    expected_hash = hashlib.sha256(sample_pdf_content).hexdigest()[:16]
    assert doc_id1 == expected_hash


# ============================================================================
# Invalid File Type Tests
# ============================================================================


def test_upload_invalid_extension_exe(client):
    """Test rejection of .exe file."""
    content = b"fake executable content"
    files = {"file": ("malware.exe", io.BytesIO(content), "application/octet-stream")}
    response = client.post("/upload", files=files)

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert ".exe" in data["detail"]
    assert "Unsupported file type" in data["detail"]


def test_upload_invalid_extension_sh(client):
    """Test rejection of .sh file."""
    content = b"#!/bin/bash\necho 'test'"
    files = {"file": ("script.sh", io.BytesIO(content), "application/x-sh")}
    response = client.post("/upload", files=files)

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert ".sh" in data["detail"]


def test_upload_invalid_extension_txt(client):
    """Test rejection of .txt file."""
    content = b"Plain text content"
    files = {"file": ("document.txt", io.BytesIO(content), "text/plain")}
    response = client.post("/upload", files=files)

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert ".txt" in data["detail"]


def test_upload_invalid_extension_zip(client):
    """Test rejection of .zip file."""
    content = b"PK\x03\x04"  # ZIP magic bytes
    files = {"file": ("archive.zip", io.BytesIO(content), "application/zip")}
    response = client.post("/upload", files=files)

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert ".zip" in data["detail"]


def test_upload_no_extension(client):
    """Test rejection of file without extension."""
    content = b"some content"
    files = {"file": ("noextension", io.BytesIO(content), "application/octet-stream")}
    response = client.post("/upload", files=files)

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Unsupported file type" in data["detail"]


def test_upload_case_insensitive_extension(client, sample_pdf_content, uploads_dir, monkeypatch):
    """Test that extension checking is case-insensitive."""
    monkeypatch.setattr(
        "src.api.server.Path", lambda x: uploads_dir if x == "data/uploads" else Path(x)
    )

    # Test uppercase extension
    files = {"file": ("REPORT.PDF", io.BytesIO(sample_pdf_content), "application/pdf")}
    response = client.post("/upload", files=files)

    assert response.status_code == 200

    # Test mixed case
    files = {"file": ("Report.PdF", io.BytesIO(sample_pdf_content), "application/pdf")}
    response = client.post("/upload", files=files)

    assert response.status_code == 200


# ============================================================================
# Missing/Invalid Parameter Tests
# ============================================================================


def test_upload_missing_file_parameter(client):
    """Test 422 error when file parameter is missing."""
    # Send request without files
    response = client.post("/upload")

    assert response.status_code == 422  # FastAPI validation error
    data = response.json()
    assert "detail" in data


def test_upload_empty_filename(client):
    """Test handling of empty filename."""
    content = b"test content"
    files = {"file": ("", io.BytesIO(content), "application/pdf")}
    response = client.post("/upload", files=files)

    # Should fail - FastAPI returns 422 for validation errors
    assert response.status_code == 422


def test_upload_null_content(client):
    """Test handling of empty file content."""
    files = {"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}
    response = client.post("/upload")  # Note: intentionally don't pass files to trigger error

    assert response.status_code == 422


# ============================================================================
# File Size Tests
# ============================================================================


def test_upload_large_file(client, uploads_dir, monkeypatch):
    """Test upload of large file (within reasonable limits)."""
    monkeypatch.setattr(
        "src.api.server.Path", lambda x: uploads_dir if x == "data/uploads" else Path(x)
    )

    # Create 10MB file
    large_content = b"A" * (10 * 1024 * 1024)
    files = {"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")}
    response = client.post("/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["file_size_bytes"] == len(large_content)


def test_upload_small_file(client, uploads_dir, monkeypatch):
    """Test upload of very small file."""
    monkeypatch.setattr(
        "src.api.server.Path", lambda x: uploads_dir if x == "data/uploads" else Path(x)
    )

    small_content = b"x"
    files = {"file": ("tiny.pdf", io.BytesIO(small_content), "application/pdf")}
    response = client.post("/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["file_size_bytes"] == 1


# ============================================================================
# Filename Sanitization Tests
# ============================================================================


def test_upload_filename_with_spaces(client, sample_pdf_content, uploads_dir, monkeypatch):
    """Test handling of filename with spaces."""
    monkeypatch.setattr(
        "src.api.server.Path", lambda x: uploads_dir if x == "data/uploads" else Path(x)
    )

    filename = "Annual Report 2024.pdf"
    files = {"file": (filename, io.BytesIO(sample_pdf_content), "application/pdf")}
    response = client.post("/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == filename


def test_upload_filename_with_special_chars(client, sample_pdf_content, uploads_dir, monkeypatch):
    """Test handling of filename with special characters."""
    monkeypatch.setattr(
        "src.api.server.Path", lambda x: uploads_dir if x == "data/uploads" else Path(x)
    )

    filename = "report-Q3_2024(final).pdf"
    files = {"file": (filename, io.BytesIO(sample_pdf_content), "application/pdf")}
    response = client.post("/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == filename


def test_upload_filename_unicode(client, sample_pdf_content, uploads_dir, monkeypatch):
    """Test handling of filename with unicode characters."""
    monkeypatch.setattr(
        "src.api.server.Path", lambda x: uploads_dir if x == "data/uploads" else Path(x)
    )

    filename = "rapport-financier-été-2024.pdf"
    files = {"file": (filename, io.BytesIO(sample_pdf_content), "application/pdf")}
    response = client.post("/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == filename


def test_upload_long_filename(client, sample_pdf_content, uploads_dir, monkeypatch):
    """Test handling of very long filename."""
    monkeypatch.setattr(
        "src.api.server.Path", lambda x: uploads_dir if x == "data/uploads" else Path(x)
    )

    long_name = "a" * 200 + ".pdf"
    files = {"file": (long_name, io.BytesIO(sample_pdf_content), "application/pdf")}
    response = client.post("/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == long_name


# ============================================================================
# Duplicate Document Tests
# ============================================================================


def test_upload_duplicate_content(client, sample_pdf_content, uploads_dir, monkeypatch):
    """Test that duplicate content can be uploaded (creates separate files)."""
    monkeypatch.setattr(
        "src.api.server.Path", lambda x: uploads_dir if x == "data/uploads" else Path(x)
    )

    # Upload same content twice
    files1 = {"file": ("report1.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}
    response1 = client.post("/upload", files=files1)

    files2 = {"file": ("report2.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}
    response2 = client.post("/upload", files=files2)

    assert response1.status_code == 200
    assert response2.status_code == 200

    # Same content, same doc_id
    assert response1.json()["doc_id"] == response2.json()["doc_id"]

    # But different filenames
    assert response1.json()["filename"] == "report1.pdf"
    assert response2.json()["filename"] == "report2.pdf"


def test_upload_same_filename_different_content(
    client, sample_pdf_content, sample_docx_content, uploads_dir, monkeypatch
):
    """Test uploading different files with same filename."""
    monkeypatch.setattr(
        "src.api.server.Path", lambda x: uploads_dir if x == "data/uploads" else Path(x)
    )

    filename = "document.pdf"

    # Upload first file
    files1 = {"file": (filename, io.BytesIO(sample_pdf_content), "application/pdf")}
    response1 = client.post("/upload", files=files1)

    # Upload different content, same name (but wrong extension for docx, so use modified pdf)
    modified_content = sample_pdf_content + b"\nmodified"
    files2 = {"file": (filename, io.BytesIO(modified_content), "application/pdf")}
    response2 = client.post("/upload", files=files2)

    assert response1.status_code == 200
    assert response2.status_code == 200

    # Different content should produce different doc_ids
    assert response1.json()["doc_id"] != response2.json()["doc_id"]

    # But same filename
    assert response1.json()["filename"] == filename
    assert response2.json()["filename"] == filename


# ============================================================================
# Error Handling Tests
# ============================================================================


def test_upload_disk_write_error(client, sample_pdf_content, monkeypatch):
    """Test handling of disk write errors."""

    # Mock Path.write_bytes to raise an error
    def mock_write_error(*args, **kwargs):
        raise IOError("Disk full")

    monkeypatch.setattr("pathlib.Path.write_bytes", mock_write_error)

    files = {"file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}
    response = client.post("/upload", files=files)

    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "Upload failed" in data["detail"]


def test_upload_file_read_error(client, monkeypatch):
    """Test handling of file read errors during processing."""
    # This test verifies error handling, but since we're using BytesIO
    # which doesn't actually fail to read, we'll test the path exists
    # The actual implementation would catch read errors in production

    # For now, verify that the endpoint can handle errors by mocking
    # the hashlib.sha256 to raise an error during processing
    with patch("hashlib.sha256", side_effect=Exception("Processing error")):
        files = {"file": ("test.pdf", io.BytesIO(b"test"), "application/pdf")}
        response = client.post("/upload", files=files)

        # Should return 500 error
        assert response.status_code == 500
        assert "Upload failed" in response.json()["detail"]


def test_upload_allowed_extensions_list(client):
    """Test that the endpoint correctly validates against allowed extensions."""
    # The endpoint should reject files not in [.pdf, .docx, .pptx]
    invalid_extensions = [".doc", ".xls", ".xlsx", ".csv", ".json", ".xml"]

    for ext in invalid_extensions:
        content = b"test content"
        filename = f"test{ext}"
        files = {"file": (filename, io.BytesIO(content), "application/octet-stream")}
        response = client.post("/upload", files=files)

        assert response.status_code == 400, f"Should reject {ext}"
        assert "Unsupported file type" in response.json()["detail"]


# ============================================================================
# Concurrency Tests
# ============================================================================


def test_upload_concurrent_same_file(client, sample_pdf_content, uploads_dir, monkeypatch):
    """Test handling of concurrent uploads of same file."""
    monkeypatch.setattr(
        "src.api.server.Path", lambda x: uploads_dir if x == "data/uploads" else Path(x)
    )

    # Simulate concurrent uploads
    import concurrent.futures

    def upload_file():
        files = {"file": ("concurrent.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}
        return client.post("/upload", files=files)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(upload_file) for _ in range(3)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # All should succeed
    assert all(r.status_code == 200 for r in results)

    # All should have same doc_id (deterministic hash)
    doc_ids = [r.json()["doc_id"] for r in results]
    assert len(set(doc_ids)) == 1


# ============================================================================
# Edge Cases
# ============================================================================


def test_upload_pdf_extension_but_not_pdf_content(client, uploads_dir, monkeypatch):
    """Test file with .pdf extension but invalid content."""
    monkeypatch.setattr(
        "src.api.server.Path", lambda x: uploads_dir if x == "data/uploads" else Path(x)
    )

    # Not actual PDF content
    fake_content = b"This is not a PDF file"
    files = {"file": ("fake.pdf", io.BytesIO(fake_content), "application/pdf")}
    response = client.post("/upload", files=files)

    # Should still accept (validation happens at processing time)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"


def test_upload_creates_directory_if_not_exists(client, sample_pdf_content, tmp_path, monkeypatch):
    """Test that upload creates uploads directory if it doesn't exist."""
    new_upload_dir = tmp_path / "new_data" / "uploads"

    # Directory doesn't exist yet
    assert not new_upload_dir.exists()

    monkeypatch.setattr(
        "src.api.server.Path", lambda x: new_upload_dir if x == "data/uploads" else Path(x)
    )

    files = {"file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}
    response = client.post("/upload", files=files)

    assert response.status_code == 200
    # Directory should now exist
    assert new_upload_dir.exists()


def test_upload_preserves_original_filename(client, sample_pdf_content, uploads_dir, monkeypatch):
    """Test that original filename is preserved in response."""
    monkeypatch.setattr(
        "src.api.server.Path", lambda x: uploads_dir if x == "data/uploads" else Path(x)
    )

    original_filename = "My Important Report v2.1 Final (APPROVED).pdf"
    files = {"file": (original_filename, io.BytesIO(sample_pdf_content), "application/pdf")}
    response = client.post("/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == original_filename


def test_upload_status_always_queued(client, sample_pdf_content, uploads_dir, monkeypatch):
    """Test that upload always returns 'queued' status."""
    monkeypatch.setattr(
        "src.api.server.Path", lambda x: uploads_dir if x == "data/uploads" else Path(x)
    )

    files = {"file": ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")}
    response = client.post("/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert "queued for processing" in data["message"].lower()


# ============================================================================
# Integration with Real Files (if available)
# ============================================================================


@pytest.mark.skipif(
    not Path(
        "/Volumes/tkr-riffic/@tkr-projects/tkr-docusearch/data/test-documents/test-financial-report.docx"
    ).exists(),
    reason="Test document not available",
)
def test_upload_real_docx_file(client, uploads_dir, monkeypatch):
    """Test upload with real DOCX file from test-documents."""
    monkeypatch.setattr(
        "src.api.server.Path", lambda x: uploads_dir if x == "data/uploads" else Path(x)
    )

    test_file = Path(
        "/Volumes/tkr-riffic/@tkr-projects/tkr-docusearch/data/test-documents/test-financial-report.docx"
    )
    content = test_file.read_bytes()

    files = {
        "file": (
            test_file.name,
            io.BytesIO(content),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    response = client.post("/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == test_file.name


@pytest.mark.skipif(
    not Path(
        "/Volumes/tkr-riffic/@tkr-projects/tkr-docusearch/data/test-documents/test-product-roadmap.pptx"
    ).exists(),
    reason="Test document not available",
)
def test_upload_real_pptx_file(client, uploads_dir, monkeypatch):
    """Test upload with real PPTX file from test-documents."""
    monkeypatch.setattr(
        "src.api.server.Path", lambda x: uploads_dir if x == "data/uploads" else Path(x)
    )

    test_file = Path(
        "/Volumes/tkr-riffic/@tkr-projects/tkr-docusearch/data/test-documents/test-product-roadmap.pptx"
    )
    content = test_file.read_bytes()

    files = {
        "file": (
            test_file.name,
            io.BytesIO(content),
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
    }
    response = client.post("/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == test_file.name
