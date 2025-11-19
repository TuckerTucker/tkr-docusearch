"""
Unit tests for Document Deletion API endpoint.

Tests comprehensive 7-stage deletion process:
1. ChromaDB embeddings (visual and text) - CRITICAL
2. Page images and thumbnails - HIGH
3. Cover art (audio files) - MEDIUM
4. VTT caption files (audio files) - MEDIUM
5. Markdown files - MEDIUM
6. Temporary directories - LOW
7. Original file from copyparty - MEDIUM

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
def mock_chroma_client():
    """Create mock ChromaDB client."""
    mock = MagicMock()

    # Mock collections with empty results by default
    mock._visual_collection.get.return_value = {"ids": [], "metadatas": []}
    mock._text_collection.get.return_value = {"ids": [], "metadatas": []}
    mock.delete_document.return_value = (0, 0)

    return mock


@pytest.fixture
def mock_existing_document(mock_chroma_client):
    """Configure mock to return an existing document."""
    # Visual collection has 3 pages
    mock_chroma_client._visual_collection.get.return_value = {
        "ids": ["v1", "v2", "v3"],
        "metadatas": [
            {"doc_id": "test-doc-12345678", "filename": "test.pdf", "page": 1},
            {"doc_id": "test-doc-12345678", "filename": "test.pdf", "page": 2},
            {"doc_id": "test-doc-12345678", "filename": "test.pdf", "page": 3},
        ],
    }

    # Text collection has 5 chunks
    mock_chroma_client._text_collection.get.return_value = {
        "ids": ["t1", "t2", "t3", "t4", "t5"],
        "metadatas": [
            {"doc_id": "test-doc-12345678", "filename": "test.pdf", "chunk_id": 0},
            {"doc_id": "test-doc-12345678", "filename": "test.pdf", "chunk_id": 1},
            {"doc_id": "test-doc-12345678", "filename": "test.pdf", "chunk_id": 2},
            {"doc_id": "test-doc-12345678", "filename": "test.pdf", "chunk_id": 3},
            {"doc_id": "test-doc-12345678", "filename": "test.pdf", "chunk_id": 4},
        ],
    }

    # Mock successful ChromaDB deletion
    mock_chroma_client.delete_document.return_value = (3, 5)

    return mock_chroma_client


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
# Tests: Successful Deletion (All 7 Stages)
# ============================================================================


@patch("tkr_docusearch.processing.documents_api.get_chroma_client")
@patch("tkr_docusearch.processing.documents_api.delete_document_images")
@patch("tkr_docusearch.processing.documents_api.delete_document_cover_art")
@patch("tkr_docusearch.processing.documents_api.delete_document_vtt")
@patch("tkr_docusearch.processing.documents_api.delete_document_markdown")
@patch("tkr_docusearch.processing.documents_api.cleanup_temp_directories")
@patch("tkr_docusearch.processing.documents_api.delete_from_copyparty")
def test_delete_document_success_all_stages(
    mock_copyparty,
    mock_cleanup_temp,
    mock_delete_markdown,
    mock_delete_vtt,
    mock_delete_cover_art,
    mock_delete_images,
    mock_get_client,
    client,
    mock_existing_document,
):
    """Test successful deletion with all 7 stages completed."""
    # Setup mocks
    mock_get_client.return_value = mock_existing_document
    mock_delete_images.return_value = (10, 10)  # 10 pages, 10 thumbnails
    mock_delete_cover_art.return_value = 1
    mock_delete_vtt.return_value = True
    mock_delete_markdown.return_value = True
    mock_cleanup_temp.return_value = 2
    mock_copyparty.return_value = True

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

    # Verify Stage 1: ChromaDB
    assert "chromadb" in data["deleted"]
    assert data["deleted"]["chromadb"]["visual_embeddings"] == 3
    assert data["deleted"]["chromadb"]["text_embeddings"] == 5
    assert data["deleted"]["chromadb"]["status"] == "deleted"

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

    # Verify Stage 7: Copyparty
    assert "copyparty" in data["deleted"]
    assert data["deleted"]["copyparty"]["deleted"] is True
    assert data["deleted"]["copyparty"]["status"] == "deleted"

    # Verify all cleanup functions were called
    mock_existing_document.delete_document.assert_called_once_with("test-doc-12345678")
    mock_delete_images.assert_called_once_with("test-doc-12345678")
    mock_delete_cover_art.assert_called_once_with("test-doc-12345678")
    mock_delete_vtt.assert_called_once_with("test-doc-12345678")
    mock_delete_markdown.assert_called_once_with("test-doc-12345678")
    mock_cleanup_temp.assert_called_once_with("test-doc-12345678")
    mock_copyparty.assert_called_once_with("test.pdf")


@patch("tkr_docusearch.processing.documents_api.get_chroma_client")
@patch("tkr_docusearch.processing.documents_api.delete_document_images")
@patch("tkr_docusearch.processing.documents_api.delete_document_cover_art")
@patch("tkr_docusearch.processing.documents_api.delete_document_vtt")
@patch("tkr_docusearch.processing.documents_api.delete_document_markdown")
@patch("tkr_docusearch.processing.documents_api.cleanup_temp_directories")
@patch("tkr_docusearch.processing.documents_api.delete_from_copyparty")
def test_delete_document_minimal_cleanup(
    mock_copyparty,
    mock_cleanup_temp,
    mock_delete_markdown,
    mock_delete_vtt,
    mock_delete_cover_art,
    mock_delete_images,
    mock_get_client,
    client,
    mock_existing_document,
):
    """Test deletion where only ChromaDB has data (minimal cleanup)."""
    # Setup mocks - only ChromaDB has data
    mock_get_client.return_value = mock_existing_document
    mock_delete_images.return_value = (0, 0)  # No images
    mock_delete_cover_art.return_value = 0  # No cover art
    mock_delete_vtt.return_value = False  # No VTT
    mock_delete_markdown.return_value = False  # No markdown
    mock_cleanup_temp.return_value = 0  # No temp dirs
    mock_copyparty.return_value = True

    # Execute deletion
    response = client.delete("/documents/test-doc-12345678")

    # Assertions
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert len(data["errors"]) == 0

    # ChromaDB should have data
    assert data["deleted"]["chromadb"]["visual_embeddings"] == 3
    assert data["deleted"]["chromadb"]["text_embeddings"] == 5

    # Everything else should be "not_found"
    assert data["deleted"]["cover_art"]["status"] == "not_found"
    assert data["deleted"]["vtt_captions"]["status"] == "not_found"
    assert data["deleted"]["markdown"]["status"] == "not_found"
    assert data["deleted"]["temp_directories"]["status"] == "none_found"


# ============================================================================
# Tests: Error Scenarios
# ============================================================================


def test_delete_document_not_found(client, mock_chroma_client):
    """Test deletion of non-existent document returns 404."""
    with patch("tkr_docusearch.processing.documents_api.get_chroma_client") as mock_get_client:
        # Configure mock to return empty results (document doesn't exist)
        mock_chroma_client._visual_collection.get.return_value = {"ids": [], "metadatas": []}
        mock_chroma_client._text_collection.get.return_value = {"ids": [], "metadatas": []}
        mock_get_client.return_value = mock_chroma_client

        response = client.delete("/documents/nonexistent-doc-id")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"] == "Document not found"
        assert data["detail"]["code"] == "DOCUMENT_NOT_FOUND"
        assert data["detail"]["details"]["doc_id"] == "nonexistent-doc-id"


def test_delete_document_invalid_doc_id_format(client):
    """Test deletion with invalid doc_id format returns 400."""
    # These IDs should fail validation (too short, too long, invalid chars)
    # Note: FastAPI routing may intercept some patterns (like paths with slashes)
    # so we focus on IDs that reach the endpoint but fail validation
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


def test_delete_document_chromadb_delete_failure(client):
    """Test that ChromaDB deletion failure returns 500 (critical error)."""
    with patch("tkr_docusearch.processing.documents_api.get_chroma_client") as mock_get_client:
        # Create a mock client that exists but fails on delete
        mock_client = MagicMock()
        mock_client._visual_collection.get.return_value = {
            "ids": ["v1"],
            "metadatas": [{"doc_id": "test-doc-12345678", "filename": "test.pdf"}],
        }
        mock_client._text_collection.get.return_value = {
            "ids": ["t1"],
            "metadatas": [{"doc_id": "test-doc-12345678", "filename": "test.pdf"}],
        }
        mock_client.delete_document.side_effect = Exception("ChromaDB connection lost")
        mock_get_client.return_value = mock_client

        response = client.delete("/documents/test-doc-12345678")

        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["error"] == "Failed to delete document embeddings"
        assert data["detail"]["code"] == "CHROMADB_DELETE_ERROR"
        assert "ChromaDB connection lost" in data["detail"]["details"]["message"]


@patch("tkr_docusearch.processing.documents_api.get_chroma_client")
@patch("tkr_docusearch.processing.documents_api.delete_document_images")
@patch("tkr_docusearch.processing.documents_api.delete_document_cover_art")
@patch("tkr_docusearch.processing.documents_api.delete_document_vtt")
@patch("tkr_docusearch.processing.documents_api.delete_document_markdown")
@patch("tkr_docusearch.processing.documents_api.cleanup_temp_directories")
@patch("tkr_docusearch.processing.documents_api.delete_from_copyparty")
def test_delete_document_non_critical_errors(
    mock_copyparty,
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

    # ChromaDB succeeds (critical)
    mock_existing_document.delete_document.return_value = (3, 5)

    # Non-critical stages fail
    mock_delete_images.side_effect = Exception("Disk I/O error")
    mock_delete_cover_art.side_effect = Exception("Permission denied")
    mock_delete_vtt.side_effect = Exception("File locked")
    mock_delete_markdown.side_effect = Exception("Network error")
    mock_cleanup_temp.side_effect = Exception("Directory not empty")
    mock_copyparty.side_effect = Exception("HTTP 500")

    # Execute deletion
    response = client.delete("/documents/test-doc-12345678")

    # Should succeed with warnings
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["doc_id"] == "test-doc-12345678"

    # ChromaDB should succeed
    assert data["deleted"]["chromadb"]["status"] == "deleted"

    # Other stages should have error status
    assert data["deleted"]["page_images"]["status"] == "error"
    assert data["deleted"]["cover_art"]["status"] == "error"
    assert data["deleted"]["vtt_captions"]["status"] == "error"
    assert data["deleted"]["markdown"]["status"] == "error"
    assert data["deleted"]["temp_directories"]["status"] == "error"
    assert data["deleted"]["copyparty"]["status"] == "error"

    # Should have error messages
    assert len(data["errors"]) == 6
    assert any("Disk I/O error" in err for err in data["errors"])
    assert any("Permission denied" in err for err in data["errors"])


def test_delete_document_database_connection_error(client):
    """Test deletion when ChromaDB connection fails."""
    from fastapi import HTTPException

    with patch("tkr_docusearch.processing.documents_api.get_chroma_client") as mock_get_client:
        # Simulate HTTPException from get_chroma_client
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


@patch("tkr_docusearch.processing.documents_api.get_chroma_client")
@patch("tkr_docusearch.processing.documents_api.delete_document_images")
@patch("tkr_docusearch.processing.documents_api.delete_document_cover_art")
@patch("tkr_docusearch.processing.documents_api.delete_document_vtt")
@patch("tkr_docusearch.processing.documents_api.delete_document_markdown")
@patch("tkr_docusearch.processing.documents_api.cleanup_temp_directories")
@patch("tkr_docusearch.processing.documents_api.delete_from_copyparty")
def test_delete_document_no_filename_in_metadata(
    mock_copyparty,
    mock_cleanup_temp,
    mock_delete_markdown,
    mock_delete_vtt,
    mock_delete_cover_art,
    mock_delete_images,
    mock_get_client,
    client,
    mock_chroma_client,
):
    """Test deletion when metadata doesn't contain filename."""
    # Configure mock with metadata missing filename
    mock_chroma_client._visual_collection.get.return_value = {
        "ids": ["v1"],
        "metadatas": [{"doc_id": "test-doc-12345678", "page": 1}],  # No filename
    }
    mock_chroma_client._text_collection.get.return_value = {"ids": [], "metadatas": []}
    mock_chroma_client.delete_document.return_value = (1, 0)

    mock_get_client.return_value = mock_chroma_client
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

    # Copyparty deletion should be skipped
    assert data["deleted"]["copyparty"]["status"] == "skipped"
    mock_copyparty.assert_not_called()


@patch("tkr_docusearch.processing.documents_api.get_chroma_client")
@patch("tkr_docusearch.processing.documents_api.delete_document_images")
@patch("tkr_docusearch.processing.documents_api.delete_document_cover_art")
@patch("tkr_docusearch.processing.documents_api.delete_document_vtt")
@patch("tkr_docusearch.processing.documents_api.delete_document_markdown")
@patch("tkr_docusearch.processing.documents_api.cleanup_temp_directories")
@patch("tkr_docusearch.processing.documents_api.delete_from_copyparty")
def test_delete_document_visual_only(
    mock_copyparty,
    mock_cleanup_temp,
    mock_delete_markdown,
    mock_delete_vtt,
    mock_delete_cover_art,
    mock_delete_images,
    mock_get_client,
    client,
    mock_chroma_client,
):
    """Test deletion of document with only visual embeddings (no text)."""
    # Configure mock with only visual data
    mock_chroma_client._visual_collection.get.return_value = {
        "ids": ["v1", "v2"],
        "metadatas": [
            {"doc_id": "test-doc-12345678", "filename": "image.pdf", "page": 1},
            {"doc_id": "test-doc-12345678", "filename": "image.pdf", "page": 2},
        ],
    }
    mock_chroma_client._text_collection.get.return_value = {"ids": [], "metadatas": []}
    mock_chroma_client.delete_document.return_value = (2, 0)

    mock_get_client.return_value = mock_chroma_client
    mock_delete_images.return_value = (2, 2)
    mock_delete_cover_art.return_value = 0
    mock_delete_vtt.return_value = False
    mock_delete_markdown.return_value = False
    mock_cleanup_temp.return_value = 0
    mock_copyparty.return_value = True

    # Execute deletion
    response = client.delete("/documents/test-doc-12345678")

    # Should succeed
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["deleted"]["chromadb"]["visual_embeddings"] == 2
    assert data["deleted"]["chromadb"]["text_embeddings"] == 0


@patch("tkr_docusearch.processing.documents_api.get_chroma_client")
@patch("tkr_docusearch.processing.documents_api.delete_document_images")
@patch("tkr_docusearch.processing.documents_api.delete_document_cover_art")
@patch("tkr_docusearch.processing.documents_api.delete_document_vtt")
@patch("tkr_docusearch.processing.documents_api.delete_document_markdown")
@patch("tkr_docusearch.processing.documents_api.cleanup_temp_directories")
@patch("tkr_docusearch.processing.documents_api.delete_from_copyparty")
def test_delete_document_text_only(
    mock_copyparty,
    mock_cleanup_temp,
    mock_delete_markdown,
    mock_delete_vtt,
    mock_delete_cover_art,
    mock_delete_images,
    mock_get_client,
    client,
    mock_chroma_client,
):
    """Test deletion of document with only text embeddings (no visual)."""
    # Configure mock with only text data
    mock_chroma_client._visual_collection.get.return_value = {"ids": [], "metadatas": []}
    mock_chroma_client._text_collection.get.return_value = {
        "ids": ["t1", "t2", "t3"],
        "metadatas": [
            {"doc_id": "test-doc-12345678", "filename": "audio.mp3", "chunk_id": 0},
            {"doc_id": "test-doc-12345678", "filename": "audio.mp3", "chunk_id": 1},
            {"doc_id": "test-doc-12345678", "filename": "audio.mp3", "chunk_id": 2},
        ],
    }
    mock_chroma_client.delete_document.return_value = (0, 3)

    mock_get_client.return_value = mock_chroma_client
    mock_delete_images.return_value = (0, 0)
    mock_delete_cover_art.return_value = 1  # Audio might have cover art
    mock_delete_vtt.return_value = True  # Audio has VTT
    mock_delete_markdown.return_value = True
    mock_cleanup_temp.return_value = 0
    mock_copyparty.return_value = True

    # Execute deletion
    response = client.delete("/documents/test-doc-12345678")

    # Should succeed
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["deleted"]["chromadb"]["visual_embeddings"] == 0
    assert data["deleted"]["chromadb"]["text_embeddings"] == 3
    assert data["deleted"]["cover_art"]["deleted"] == 1
    assert data["deleted"]["vtt_captions"]["deleted"] is True


@patch("tkr_docusearch.processing.documents_api.get_chroma_client")
@patch("tkr_docusearch.processing.documents_api.delete_document_images")
@patch("tkr_docusearch.processing.documents_api.delete_document_cover_art")
@patch("tkr_docusearch.processing.documents_api.delete_document_vtt")
@patch("tkr_docusearch.processing.documents_api.delete_document_markdown")
@patch("tkr_docusearch.processing.documents_api.cleanup_temp_directories")
@patch("tkr_docusearch.processing.documents_api.delete_from_copyparty")
def test_delete_document_copyparty_failure_non_critical(
    mock_copyparty,
    mock_cleanup_temp,
    mock_delete_markdown,
    mock_delete_vtt,
    mock_delete_cover_art,
    mock_delete_images,
    mock_get_client,
    client,
    mock_existing_document,
):
    """Test that copyparty deletion failure doesn't fail the entire request."""
    # Setup mocks
    mock_get_client.return_value = mock_existing_document
    mock_delete_images.return_value = (3, 3)
    mock_delete_cover_art.return_value = 0
    mock_delete_vtt.return_value = False
    mock_delete_markdown.return_value = True
    mock_cleanup_temp.return_value = 0
    mock_copyparty.return_value = False  # Copyparty deletion fails

    # Execute deletion
    response = client.delete("/documents/test-doc-12345678")

    # Should succeed with warning
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["deleted"]["chromadb"]["status"] == "deleted"
    assert data["deleted"]["copyparty"]["status"] == "failed"


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


@patch("tkr_docusearch.processing.documents_api.get_chroma_client")
@patch("tkr_docusearch.processing.documents_api.delete_document_images")
@patch("tkr_docusearch.processing.documents_api.delete_document_cover_art")
@patch("tkr_docusearch.processing.documents_api.delete_document_vtt")
@patch("tkr_docusearch.processing.documents_api.delete_document_markdown")
@patch("tkr_docusearch.processing.documents_api.cleanup_temp_directories")
@patch("tkr_docusearch.processing.documents_api.delete_from_copyparty")
def test_delete_document_response_format(
    mock_copyparty,
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
    mock_copyparty.return_value = True

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
        "chromadb",
        "page_images",
        "cover_art",
        "vtt_captions",
        "markdown",
        "temp_directories",
        "copyparty",
    ]
    for stage in expected_stages:
        assert stage in data["deleted"], f"Stage '{stage}' missing from response"


# ============================================================================
# Tests: Cascade Deletion
# ============================================================================


@patch("tkr_docusearch.processing.documents_api.get_chroma_client")
@patch("tkr_docusearch.processing.documents_api.delete_document_images")
@patch("tkr_docusearch.processing.documents_api.delete_document_cover_art")
@patch("tkr_docusearch.processing.documents_api.delete_document_vtt")
@patch("tkr_docusearch.processing.documents_api.delete_document_markdown")
@patch("tkr_docusearch.processing.documents_api.cleanup_temp_directories")
@patch("tkr_docusearch.processing.documents_api.delete_from_copyparty")
def test_delete_document_cascade_order(
    mock_copyparty,
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

    def track_chromadb(*args, **kwargs):
        call_order.append("chromadb")
        return (3, 5)

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

    def track_copyparty(*args, **kwargs):
        call_order.append("copyparty")
        return True

    mock_existing_document.delete_document.side_effect = track_chromadb
    mock_delete_images.side_effect = track_images
    mock_delete_cover_art.side_effect = track_cover_art
    mock_delete_vtt.side_effect = track_vtt
    mock_delete_markdown.side_effect = track_markdown
    mock_cleanup_temp.side_effect = track_temp
    mock_copyparty.side_effect = track_copyparty

    mock_get_client.return_value = mock_existing_document

    # Execute deletion
    response = client.delete("/documents/test-doc-12345678")

    assert response.status_code == 200

    # Verify execution order (ChromaDB must be first, rest can be in any order)
    assert call_order[0] == "chromadb", "ChromaDB deletion must be first (critical)"
    assert "images" in call_order
    assert "cover_art" in call_order
    assert "vtt" in call_order
    assert "markdown" in call_order
    assert "temp" in call_order
    assert "copyparty" in call_order


def test_delete_document_stops_on_chromadb_failure(client):
    """Test that deletion stops if ChromaDB deletion fails (critical stage)."""
    with patch("tkr_docusearch.processing.documents_api.get_chroma_client") as mock_get_client:
        with patch("tkr_docusearch.processing.documents_api.delete_document_images") as mock_images:
            # Create a mock client that exists but fails on delete
            mock_client = MagicMock()
            mock_client._visual_collection.get.return_value = {
                "ids": ["v1"],
                "metadatas": [{"doc_id": "test-doc-12345678", "filename": "test.pdf"}],
            }
            mock_client._text_collection.get.return_value = {"ids": [], "metadatas": []}
            mock_client.delete_document.side_effect = Exception("Database error")
            mock_get_client.return_value = mock_client

            # Execute deletion
            response = client.delete("/documents/test-doc-12345678")

            # Should fail with 500
            assert response.status_code == 500

            # Other cleanup functions should NOT be called
            mock_images.assert_not_called()
