"""
Unit tests for Document Deletion API endpoint.

Tests comprehensive 6-stage deletion process:
1. Koji database records (documents, pages, chunks) - CRITICAL
2. Page images and thumbnails - HIGH
3. Cover art (audio files) - MEDIUM
4. VTT caption files (audio files) - MEDIUM
5. Markdown files - MEDIUM
6. Temporary directories - LOW

Target Coverage: 90%+
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tkr_docusearch.processing.documents_api import router

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def app():
    """Create FastAPI test application."""
    test_app = FastAPI()
    test_app.include_router(router)
    return test_app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_koji_client():
    """Create mock KojiClient.

    Returns a MagicMock configured with default empty document lookup.
    """
    mock = MagicMock()
    mock.get_document.return_value = None
    mock.delete_document.return_value = None
    return mock


@pytest.fixture
def mock_existing_document(mock_koji_client):
    """Configure mock to return an existing document."""
    mock_koji_client.get_document.return_value = {
        "doc_id": "test-doc-12345678",
        "filename": "test.pdf",
        "format": "pdf",
        "created_at": "2025-10-26T12:00:00Z",
    }
    return mock_koji_client


@pytest.fixture
def temp_data_dirs():
    """Create temporary data directories for testing."""
    temp_dir = Path(tempfile.mkdtemp())

    # Create directory structure
    page_images_dir = temp_dir / "page_images"
    images_dir = temp_dir / "images"
    markdown_dir = temp_dir / "markdown"
    vtt_dir = temp_dir / "vtt"

    for directory in [page_images_dir, images_dir, markdown_dir, vtt_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    yield {
        "root": temp_dir,
        "page_images": page_images_dir,
        "images": images_dir,
        "markdown": markdown_dir,
        "vtt": vtt_dir,
    }

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================================
# Tests: Successful Deletion (All 6 Stages)
# ============================================================================


@patch("tkr_docusearch.processing.documents_api.get_storage_client")
@patch("tkr_docusearch.processing.documents_api.delete_document_images")
@patch("tkr_docusearch.processing.documents_api.delete_document_cover_art")
@patch("tkr_docusearch.processing.documents_api.delete_document_vtt")
@patch("tkr_docusearch.processing.documents_api.delete_document_markdown")
@patch("tkr_docusearch.processing.documents_api.cleanup_temp_directories")
def test_delete_document_success_all_stages(
    mock_cleanup_temp,
    mock_delete_markdown,
    mock_delete_vtt,
    mock_delete_cover_art,
    mock_delete_images,
    mock_get_client,
    client,
    mock_existing_document,
):
    """Test successful deletion with all 6 stages completed."""
    # Setup mocks
    mock_get_client.return_value = mock_existing_document
    mock_delete_images.return_value = (10, 10)  # 10 pages, 10 thumbnails
    mock_delete_cover_art.return_value = 1
    mock_delete_vtt.return_value = True
    mock_delete_markdown.return_value = True
    mock_cleanup_temp.return_value = 2

    # Execute deletion
    response = client.delete("/documents/test-doc-12345678")

    # Assertions
    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert data["success"] is True
    assert data["doc_id"] == "test-doc-12345678"
    assert data["filename"] == "test.pdf"
    assert len(data["errors"]) == 0

    # Verify Stage 1: Koji
    assert "koji" in data["deleted"]
    assert data["deleted"]["koji"]["status"] == "deleted"

    # Verify Stage 2: Page images
    assert "page_images" in data["deleted"]
    assert data["deleted"]["page_images"]["pages"] == 10
    assert data["deleted"]["page_images"]["thumbnails"] == 10
    assert data["deleted"]["page_images"]["status"] == "deleted"

    # Verify Stage 3: Cover art
    assert "cover_art" in data["deleted"]
    assert data["deleted"]["cover_art"]["deleted"] == 1
    assert data["deleted"]["cover_art"]["status"] == "deleted"

    # Verify Stage 4: VTT captions
    assert "vtt_captions" in data["deleted"]
    assert data["deleted"]["vtt_captions"]["deleted"] is True
    assert data["deleted"]["vtt_captions"]["status"] == "deleted"

    # Verify Stage 5: Markdown
    assert "markdown" in data["deleted"]
    assert data["deleted"]["markdown"]["deleted"] is True
    assert data["deleted"]["markdown"]["status"] == "deleted"

    # Verify Stage 6: Temp directories
    assert "temp_directories" in data["deleted"]
    assert data["deleted"]["temp_directories"]["cleaned"] == 2
    assert data["deleted"]["temp_directories"]["status"] == "cleaned"

    # Verify all cleanup functions were called
    mock_existing_document.delete_document.assert_called_once_with("test-doc-12345678")
    mock_delete_images.assert_called_once_with("test-doc-12345678")
    mock_delete_cover_art.assert_called_once_with("test-doc-12345678")
    mock_delete_vtt.assert_called_once_with("test-doc-12345678")
    mock_delete_markdown.assert_called_once_with("test-doc-12345678")
    mock_cleanup_temp.assert_called_once_with("test-doc-12345678")


@patch("tkr_docusearch.processing.documents_api.get_storage_client")
@patch("tkr_docusearch.processing.documents_api.delete_document_images")
@patch("tkr_docusearch.processing.documents_api.delete_document_cover_art")
@patch("tkr_docusearch.processing.documents_api.delete_document_vtt")
@patch("tkr_docusearch.processing.documents_api.delete_document_markdown")
@patch("tkr_docusearch.processing.documents_api.cleanup_temp_directories")
def test_delete_document_minimal_cleanup(
    mock_cleanup_temp,
    mock_delete_markdown,
    mock_delete_vtt,
    mock_delete_cover_art,
    mock_delete_images,
    mock_get_client,
    client,
    mock_existing_document,
):
    """Test deletion where only Koji has data (minimal cleanup)."""
    # Setup mocks - only Koji has data
    mock_get_client.return_value = mock_existing_document
    mock_delete_images.return_value = (0, 0)  # No images
    mock_delete_cover_art.return_value = 0  # No cover art
    mock_delete_vtt.return_value = False  # No VTT
    mock_delete_markdown.return_value = False  # No markdown
    mock_cleanup_temp.return_value = 0  # No temp dirs

    # Execute deletion
    response = client.delete("/documents/test-doc-12345678")

    # Assertions
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert len(data["errors"]) == 0

    # Koji should have succeeded
    assert data["deleted"]["koji"]["status"] == "deleted"

    # Everything else should be "not_found"
    assert data["deleted"]["cover_art"]["status"] == "not_found"
    assert data["deleted"]["vtt_captions"]["status"] == "not_found"
    assert data["deleted"]["markdown"]["status"] == "not_found"
    assert data["deleted"]["temp_directories"]["status"] == "none_found"


# ============================================================================
# Tests: Error Scenarios
# ============================================================================


def test_delete_document_not_found(client, mock_koji_client):
    """Test deletion of non-existent document returns 404."""
    with patch(
        "tkr_docusearch.processing.documents_api.get_storage_client"
    ) as mock_get_client:
        # get_document returns None for non-existent doc
        mock_koji_client.get_document.return_value = None
        mock_get_client.return_value = mock_koji_client

        response = client.delete("/documents/nonexistent-doc-id")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"] == "Document not found"
        assert data["detail"]["code"] == "DOCUMENT_NOT_FOUND"
        assert data["detail"]["details"]["doc_id"] == "nonexistent-doc-id"


def test_delete_document_invalid_doc_id_format(client):
    """Test deletion with invalid doc_id format returns 400."""
    invalid_doc_ids = [
        "short12",  # Too short (< 8 chars)
        "a" * 65,  # Too long (> 64 chars)
        "doc..id1234",  # Invalid characters (double dots)
    ]

    for invalid_id in invalid_doc_ids:
        response = client.delete(f"/documents/{invalid_id}")
        assert (
            response.status_code == 400
        ), f"Expected 400 for {invalid_id}, got {response.status_code}"
        data = response.json()
        assert data["detail"]["error"] == "Invalid document ID format"
        assert data["detail"]["code"] == "INVALID_DOC_ID"


def test_delete_document_koji_delete_failure(client):
    """Test that Koji deletion failure returns 500 (critical error)."""
    with patch(
        "tkr_docusearch.processing.documents_api.get_storage_client"
    ) as mock_get_client:
        mock_client = MagicMock()
        mock_client.get_document.return_value = {
            "doc_id": "test-doc-12345678",
            "filename": "test.pdf",
            "format": "pdf",
            "created_at": "2025-10-26T12:00:00Z",
        }
        mock_client.delete_document.side_effect = Exception("Koji database error")
        mock_get_client.return_value = mock_client

        response = client.delete("/documents/test-doc-12345678")

        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["error"] == "Failed to delete document"
        assert data["detail"]["code"] == "DATABASE_DELETE_ERROR"
        assert "Koji database error" in data["detail"]["details"]["message"]


@patch("tkr_docusearch.processing.documents_api.get_storage_client")
@patch("tkr_docusearch.processing.documents_api.delete_document_images")
@patch("tkr_docusearch.processing.documents_api.delete_document_cover_art")
@patch("tkr_docusearch.processing.documents_api.delete_document_vtt")
@patch("tkr_docusearch.processing.documents_api.delete_document_markdown")
@patch("tkr_docusearch.processing.documents_api.cleanup_temp_directories")
def test_delete_document_non_critical_errors(
    mock_cleanup_temp,
    mock_delete_markdown,
    mock_delete_vtt,
    mock_delete_cover_art,
    mock_delete_images,
    mock_get_client,
    client,
    mock_existing_document,
):
    """Test that non-critical cleanup errors don't fail the request."""
    # Setup mocks
    mock_get_client.return_value = mock_existing_document

    # Koji succeeds (critical)
    mock_existing_document.delete_document.return_value = None

    # Non-critical stages fail
    mock_delete_images.side_effect = Exception("Disk I/O error")
    mock_delete_cover_art.side_effect = Exception("Permission denied")
    mock_delete_vtt.side_effect = Exception("File locked")
    mock_delete_markdown.side_effect = Exception("Network error")
    mock_cleanup_temp.side_effect = Exception("Directory not empty")

    # Execute deletion
    response = client.delete("/documents/test-doc-12345678")

    # Should succeed with warnings
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["doc_id"] == "test-doc-12345678"

    # Koji should succeed
    assert data["deleted"]["koji"]["status"] == "deleted"

    # Other stages should have error status
    assert data["deleted"]["page_images"]["status"] == "error"
    assert data["deleted"]["cover_art"]["status"] == "error"
    assert data["deleted"]["vtt_captions"]["status"] == "error"
    assert data["deleted"]["markdown"]["status"] == "error"
    assert data["deleted"]["temp_directories"]["status"] == "error"

    # Should have error messages
    assert len(data["errors"]) == 5
    assert any("Disk I/O error" in err for err in data["errors"])
    assert any("Permission denied" in err for err in data["errors"])


def test_delete_document_database_connection_error(client):
    """Test deletion when database connection fails."""
    from fastapi import HTTPException

    with patch(
        "tkr_docusearch.processing.documents_api.get_storage_client"
    ) as mock_get_client:
        mock_get_client.side_effect = HTTPException(
            status_code=500,
            detail={
                "error": "Database connection failed",
                "code": "DATABASE_ERROR",
                "details": {"message": "Connection refused"},
            },
        )

        response = client.delete("/documents/test-doc-12345678")

        # Should return 500 error
        assert response.status_code == 500


# ============================================================================
# Tests: Edge Cases
# ============================================================================


@patch("tkr_docusearch.processing.documents_api.get_storage_client")
@patch("tkr_docusearch.processing.documents_api.delete_document_images")
@patch("tkr_docusearch.processing.documents_api.delete_document_cover_art")
@patch("tkr_docusearch.processing.documents_api.delete_document_vtt")
@patch("tkr_docusearch.processing.documents_api.delete_document_markdown")
@patch("tkr_docusearch.processing.documents_api.cleanup_temp_directories")
def test_delete_document_no_filename_in_metadata(
    mock_cleanup_temp,
    mock_delete_markdown,
    mock_delete_vtt,
    mock_delete_cover_art,
    mock_delete_images,
    mock_get_client,
    client,
    mock_koji_client,
):
    """Test deletion when document metadata doesn't contain filename."""
    # Configure mock with document missing filename
    mock_koji_client.get_document.return_value = {
        "doc_id": "test-doc-12345678",
        "format": "pdf",
        "created_at": "2025-10-26T12:00:00Z",
        # No "filename" key
    }

    mock_get_client.return_value = mock_koji_client
    mock_delete_images.return_value = (0, 0)
    mock_delete_cover_art.return_value = 0
    mock_delete_vtt.return_value = False
    mock_delete_markdown.return_value = False
    mock_cleanup_temp.return_value = 0

    # Execute deletion
    response = client.delete("/documents/test-doc-12345678")

    # Should succeed
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["filename"] is None  # No filename available


# ============================================================================
# Tests: Validation
# ============================================================================


def test_delete_document_validates_doc_id_length(client):
    """Test doc_id length validation (min 8, max 64 characters)."""
    # Too short
    response = client.delete("/documents/short")
    assert response.status_code == 400

    # Too long
    response = client.delete("/documents/" + "a" * 65)
    assert response.status_code == 400

    # Valid lengths
    response = client.delete("/documents/12345678")  # Min length
    # Will return 404 or 500, but not 400 (validation passed)
    assert response.status_code != 400


def test_delete_document_validates_doc_id_characters(client):
    """Test doc_id character validation (alphanumeric + dash only)."""
    invalid_chars = [
        "test@doc",  # @ not allowed
        "test#doc",  # # not allowed
        "test$doc",  # $ not allowed
        "test doc",  # space not allowed
        "test_doc",  # underscore not allowed (only dash)
    ]

    for invalid_id in invalid_chars:
        response = client.delete(f"/documents/{invalid_id}")
        assert response.status_code == 400


# ============================================================================
# Tests: Response Format
# ============================================================================


@patch("tkr_docusearch.processing.documents_api.get_storage_client")
@patch("tkr_docusearch.processing.documents_api.delete_document_images")
@patch("tkr_docusearch.processing.documents_api.delete_document_cover_art")
@patch("tkr_docusearch.processing.documents_api.delete_document_vtt")
@patch("tkr_docusearch.processing.documents_api.delete_document_markdown")
@patch("tkr_docusearch.processing.documents_api.cleanup_temp_directories")
def test_delete_document_response_format(
    mock_cleanup_temp,
    mock_delete_markdown,
    mock_delete_vtt,
    mock_delete_cover_art,
    mock_delete_images,
    mock_get_client,
    client,
    mock_existing_document,
):
    """Test that deletion response has correct format and fields."""
    # Setup mocks
    mock_get_client.return_value = mock_existing_document
    mock_delete_images.return_value = (5, 5)
    mock_delete_cover_art.return_value = 0
    mock_delete_vtt.return_value = False
    mock_delete_markdown.return_value = True
    mock_cleanup_temp.return_value = 1

    # Execute deletion
    response = client.delete("/documents/test-doc-12345678")

    assert response.status_code == 200
    data = response.json()

    # Required top-level fields
    assert "success" in data
    assert "doc_id" in data
    assert "filename" in data
    assert "deleted" in data
    assert "errors" in data

    # Verify types
    assert isinstance(data["success"], bool)
    assert isinstance(data["doc_id"], str)
    assert isinstance(data["deleted"], dict)
    assert isinstance(data["errors"], list)

    # Verify all stages present in deleted dict
    expected_stages = [
        "koji",
        "page_images",
        "cover_art",
        "vtt_captions",
        "markdown",
        "temp_directories",
    ]
    for stage in expected_stages:
        assert stage in data["deleted"], f"Stage '{stage}' missing from response"


# ============================================================================
# Tests: Cascade Deletion
# ============================================================================


@patch("tkr_docusearch.processing.documents_api.get_storage_client")
@patch("tkr_docusearch.processing.documents_api.delete_document_images")
@patch("tkr_docusearch.processing.documents_api.delete_document_cover_art")
@patch("tkr_docusearch.processing.documents_api.delete_document_vtt")
@patch("tkr_docusearch.processing.documents_api.delete_document_markdown")
@patch("tkr_docusearch.processing.documents_api.cleanup_temp_directories")
def test_delete_document_cascade_order(
    mock_cleanup_temp,
    mock_delete_markdown,
    mock_delete_vtt,
    mock_delete_cover_art,
    mock_delete_images,
    mock_get_client,
    client,
    mock_existing_document,
):
    """Test that deletion stages execute in correct order."""
    # Setup mocks with side effects to track call order
    call_order = []

    def track_koji(*args, **kwargs):
        call_order.append("koji")
        return None

    def track_images(*args, **kwargs):
        call_order.append("images")
        return (5, 5)

    def track_cover_art(*args, **kwargs):
        call_order.append("cover_art")
        return 1

    def track_vtt(*args, **kwargs):
        call_order.append("vtt")
        return True

    def track_markdown(*args, **kwargs):
        call_order.append("markdown")
        return True

    def track_temp(*args, **kwargs):
        call_order.append("temp")
        return 1

    mock_existing_document.delete_document.side_effect = track_koji
    mock_delete_images.side_effect = track_images
    mock_delete_cover_art.side_effect = track_cover_art
    mock_delete_vtt.side_effect = track_vtt
    mock_delete_markdown.side_effect = track_markdown
    mock_cleanup_temp.side_effect = track_temp

    mock_get_client.return_value = mock_existing_document

    # Execute deletion
    response = client.delete("/documents/test-doc-12345678")

    assert response.status_code == 200

    # Verify execution order (Koji must be first, rest can be in any order)
    assert call_order[0] == "koji", "Koji deletion must be first (critical)"
    assert "images" in call_order
    assert "cover_art" in call_order
    assert "vtt" in call_order
    assert "markdown" in call_order
    assert "temp" in call_order


def test_delete_document_stops_on_koji_failure(client):
    """Test that deletion stops if Koji deletion fails (critical stage)."""
    with patch(
        "tkr_docusearch.processing.documents_api.get_storage_client"
    ) as mock_get_client:
        with patch(
            "tkr_docusearch.processing.documents_api.delete_document_images"
        ) as mock_images:
            mock_client = MagicMock()
            mock_client.get_document.return_value = {
                "doc_id": "test-doc-12345678",
                "filename": "test.pdf",
                "format": "pdf",
                "created_at": "2025-10-26T12:00:00Z",
            }
            mock_client.delete_document.side_effect = Exception("Database error")
            mock_get_client.return_value = mock_client

            # Execute deletion
            response = client.delete("/documents/test-doc-12345678")

            # Should fail with 500
            assert response.status_code == 500

            # Other cleanup functions should NOT be called
            mock_images.assert_not_called()
