"""
Unit tests for Documents API endpoints.

Tests cover:
- Document listing with pagination
- Document detail retrieval
- Image serving
- Security validation
- Error handling

Provider: api-agent (Wave 3)
Target Coverage: 95%+
Contract: integration-contracts/03-documents-api.contract.md
"""

import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from src.processing.documents_api import router, validate_doc_id, validate_filename

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
def temp_image_dir(monkeypatch):
    """Create temporary directory for test images."""
    temp_dir = Path(tempfile.mkdtemp())

    # Monkey patch PAGE_IMAGE_DIR
    import src.processing.documents_api as api_module

    monkeypatch.setattr(api_module, "PAGE_IMAGE_DIR", temp_dir)

    # Create test document with images
    doc_id = "test-doc-12345678"
    doc_dir = temp_dir / doc_id
    doc_dir.mkdir(parents=True)

    # Create test images
    img = Image.new("RGB", (800, 1000), color="blue")
    img.save(doc_dir / "page001.png")
    img.save(doc_dir / "page001_thumb.jpg", format="JPEG")
    img.save(doc_dir / "page002.png")
    img.save(doc_dir / "page002_thumb.jpg", format="JPEG")

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================================
# Validation Tests
# ============================================================================


def test_validate_doc_id_valid():
    """Test doc_id validation with valid IDs."""
    assert validate_doc_id("abc123def456") is True
    assert validate_doc_id("test-doc-12345678") is True
    assert validate_doc_id("a" * 64) is True  # Max length


def test_validate_doc_id_invalid():
    """Test doc_id validation with invalid IDs."""
    assert validate_doc_id("short") is False  # Too short
    assert validate_doc_id("a" * 65) is False  # Too long
    assert validate_doc_id("doc/with/slash") is False  # Path traversal
    assert validate_doc_id("doc..id") is False  # Invalid characters
    assert validate_doc_id("../../../etc/passwd") is False  # Path traversal


def test_validate_filename_valid():
    """Test filename validation with valid filenames."""
    assert validate_filename("page001.png") is True
    assert validate_filename("page001_thumb.jpg") is True
    assert validate_filename("page999.png") is True
    assert validate_filename("page100_thumb.jpg") is True


def test_validate_filename_invalid():
    """Test filename validation with invalid filenames."""
    assert validate_filename("page1.png") is False  # Not 3 digits
    assert validate_filename("page001.pdf") is False  # Wrong extension
    assert validate_filename("../page001.png") is False  # Path traversal
    assert validate_filename("page001_thumb.png") is False  # Thumb should be jpg
    assert validate_filename("document.pdf") is False  # Wrong format


# ============================================================================
# GET /documents Tests
# ============================================================================


def test_list_documents_structure(client, monkeypatch):
    """Test GET /documents returns correct structure."""
    # Mock ChromaDB client
    from unittest.mock import Mock

    mock_client = Mock()
    mock_visual = Mock()
    mock_text = Mock()

    mock_visual.get.return_value = {
        "ids": ["testdoc1-page001"],
        "metadatas": [
            {
                "doc_id": "testdoc1",
                "filename": "test.pdf",
                "page": 1,
                "timestamp": "2025-10-11T10:00:00Z",
                "image_path": "/page_images/testdoc1/page001.png",
                "thumb_path": "/page_images/testdoc1/page001_thumb.jpg",
            }
        ],
    }

    mock_text.get.return_value = {
        "ids": ["testdoc1-chunk0000"],
        "metadatas": [
            {
                "doc_id": "testdoc1",
                "filename": "test.pdf",
                "chunk_id": 0,
                "timestamp": "2025-10-11T10:00:00Z",
            }
        ],
    }

    mock_client._visual_collection = mock_visual
    mock_client._text_collection = mock_text

    # Monkey patch get_chroma_client
    import src.processing.documents_api as api_module

    monkeypatch.setattr(api_module, "get_chroma_client", lambda: mock_client)

    response = client.get("/documents")

    assert response.status_code == 200
    data = response.json()

    assert "documents" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert isinstance(data["documents"], list)


def test_list_documents_pagination(client, monkeypatch):
    """Test pagination parameters."""
    # Mock empty response
    from unittest.mock import Mock

    mock_client = Mock()
    mock_visual = Mock()
    mock_text = Mock()
    mock_visual.get.return_value = {"ids": [], "metadatas": []}
    mock_text.get.return_value = {"ids": [], "metadatas": []}
    mock_client._visual_collection = mock_visual
    mock_client._text_collection = mock_text

    import src.processing.documents_api as api_module

    monkeypatch.setattr(api_module, "get_chroma_client", lambda: mock_client)

    response = client.get("/documents?limit=10&offset=5")

    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 10
    assert data["offset"] == 5


def test_list_documents_invalid_pagination(client):
    """Test invalid pagination parameters."""
    # Limit too high
    response = client.get("/documents?limit=200")
    assert response.status_code == 422  # Validation error

    # Negative offset
    response = client.get("/documents?offset=-1")
    assert response.status_code == 422


# ============================================================================
# GET /documents/{doc_id} Tests
# ============================================================================


def test_get_document_success(client, monkeypatch):
    """Test GET /documents/{doc_id} with valid document."""
    from unittest.mock import Mock

    mock_client = Mock()
    mock_visual = Mock()
    mock_text = Mock()

    doc_id = "testdoc1"

    mock_visual.get.return_value = {
        "ids": [f"{doc_id}-page001", f"{doc_id}-page002"],
        "metadatas": [
            {
                "doc_id": doc_id,
                "filename": "test.pdf",
                "page": 1,
                "timestamp": "2025-10-11T10:00:00Z",
                "image_path": f"/page_images/{doc_id}/page001.png",
                "thumb_path": f"/page_images/{doc_id}/page001_thumb.jpg",
            },
            {
                "doc_id": doc_id,
                "filename": "test.pdf",
                "page": 2,
                "timestamp": "2025-10-11T10:00:00Z",
                "image_path": f"/page_images/{doc_id}/page002.png",
                "thumb_path": f"/page_images/{doc_id}/page002_thumb.jpg",
            },
        ],
    }

    mock_text.get.return_value = {
        "ids": [f"{doc_id}-chunk0000"],
        "metadatas": [
            {
                "doc_id": doc_id,
                "filename": "test.pdf",
                "chunk_id": 0,
                "text_preview": "Sample text...",
                "timestamp": "2025-10-11T10:00:00Z",
            }
        ],
    }

    mock_client._visual_collection = mock_visual
    mock_client._text_collection = mock_text

    import src.processing.documents_api as api_module

    monkeypatch.setattr(api_module, "get_chroma_client", lambda: mock_client)

    response = client.get(f"/documents/{doc_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["doc_id"] == doc_id
    assert data["filename"] == "test.pdf"
    assert len(data["pages"]) == 2
    assert len(data["chunks"]) == 1
    assert data["metadata"]["page_count"] == 2
    assert data["metadata"]["chunk_count"] == 1


def test_get_document_not_found(client, monkeypatch):
    """Test 404 for non-existent document."""
    from unittest.mock import Mock

    mock_client = Mock()
    mock_visual = Mock()
    mock_text = Mock()
    mock_visual.get.return_value = {"ids": [], "metadatas": []}
    mock_text.get.return_value = {"ids": [], "metadatas": []}
    mock_client._visual_collection = mock_visual
    mock_client._text_collection = mock_text

    import src.processing.documents_api as api_module

    monkeypatch.setattr(api_module, "get_chroma_client", lambda: mock_client)

    response = client.get("/documents/nonexistent-doc-id-12345")

    assert response.status_code == 404
    data = response.json()
    assert "code" in data["detail"]
    assert data["detail"]["code"] == "DOCUMENT_NOT_FOUND"


def test_get_document_invalid_id(client):
    """Test 400 for invalid doc_id format."""
    # Use a properly formatted URL but invalid doc_id
    response = client.get("/documents/bad_id")

    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["code"] == "INVALID_DOC_ID"


# ============================================================================
# GET /images/{doc_id}/{filename} Tests
# ============================================================================


def test_get_image_success(client, temp_image_dir):
    """Test GET /images/{doc_id}/{filename} serves image."""
    response = client.get("/images/test-doc-12345678/page001_thumb.jpg")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert "cache-control" in response.headers
    assert len(response.content) > 0


def test_get_image_png_format(client, temp_image_dir):
    """Test serving PNG format image."""
    response = client.get("/images/test-doc-12345678/page001.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


def test_get_image_not_found(client, temp_image_dir):
    """Test 404 for non-existent image."""
    response = client.get("/images/test-doc-12345678/page999.png")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["code"] == "IMAGE_NOT_FOUND"


def test_get_image_invalid_doc_id(client):
    """Test path traversal prevention in doc_id."""
    # Use invalid doc_id format (too short)
    response = client.get("/images/bad/file.png")

    assert response.status_code == 403
    data = response.json()
    assert data["detail"]["code"] == "INVALID_DOC_ID"


def test_get_image_invalid_filename(client):
    """Test path traversal prevention in filename."""
    # Use invalid filename format (doesn't match page\d{3}(_thumb)?\.(png|jpg))
    response = client.get("/images/test-doc-12345678/invalid_file.pdf")

    assert response.status_code == 403
    data = response.json()
    assert data["detail"]["code"] == "INVALID_FILENAME"


def test_get_image_caching_headers(client, temp_image_dir):
    """Test that caching headers are set correctly."""
    response = client.get("/images/test-doc-12345678/page001_thumb.jpg")

    assert response.status_code == 200
    assert "cache-control" in response.headers
    assert "max-age=86400" in response.headers["cache-control"]


# ============================================================================
# Integration Tests
# ============================================================================


def test_full_workflow(client, monkeypatch, temp_image_dir):
    """Test complete workflow: list → detail → image."""
    from unittest.mock import Mock

    # Mock ChromaDB
    mock_client = Mock()
    mock_visual = Mock()
    mock_text = Mock()

    doc_id = "test-doc-12345678"

    mock_visual.get.return_value = {
        "ids": [f"{doc_id}-page001"],
        "metadatas": [
            {
                "doc_id": doc_id,
                "filename": "test.pdf",
                "page": 1,
                "timestamp": "2025-10-11T10:00:00Z",
                "image_path": f"/page_images/{doc_id}/page001.png",
                "thumb_path": f"/page_images/{doc_id}/page001_thumb.jpg",
            }
        ],
    }

    mock_text.get.return_value = {
        "ids": [f"{doc_id}-chunk0000"],
        "metadatas": [
            {
                "doc_id": doc_id,
                "filename": "test.pdf",
                "chunk_id": 0,
                "timestamp": "2025-10-11T10:00:00Z",
            }
        ],
    }

    mock_client._visual_collection = mock_visual
    mock_client._text_collection = mock_text

    import src.processing.documents_api as api_module

    monkeypatch.setattr(api_module, "get_chroma_client", lambda: mock_client)

    # Step 1: List documents
    response = client.get("/documents")
    assert response.status_code == 200
    docs = response.json()["documents"]
    assert len(docs) == 1
    assert docs[0]["doc_id"] == doc_id

    # Step 2: Get document details
    response = client.get(f"/documents/{doc_id}")
    assert response.status_code == 200
    detail = response.json()
    assert detail["doc_id"] == doc_id
    assert len(detail["pages"]) == 1

    # Step 3: Fetch thumbnail
    response = client.get(f"/images/{doc_id}/page001_thumb.jpg")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
