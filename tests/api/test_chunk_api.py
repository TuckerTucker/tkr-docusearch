"""
Tests for chunk context API endpoint.

Tests GET /documents/{doc_id}/chunks/{chunk_id} endpoint for:
- Success cases with chunk context
- Parsing of JSON array fields (related_tables, related_pictures, page_nums)
- 404 errors for non-existent chunks
- 400 errors for invalid parameters
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tkr_docusearch.processing.api.structure_endpoints import router

# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture
def mock_koji_client():
    """Create mock Koji client."""
    with patch("tkr_docusearch.processing.api.structure_endpoints.get_storage_client") as mock_get:
        mock_client = MagicMock()
        mock_get.return_value = mock_client
        yield mock_client


def test_get_chunk_context_success(mock_koji_client):
    """Test successful retrieval of chunk context."""
    doc_id = "test-doc-id-123456"
    chunk_id = "0001"
    full_chunk_id = f"{doc_id}-chunk{chunk_id}"

    mock_koji_client.get_chunk.return_value = {
        "id": full_chunk_id,
        "doc_id": doc_id,
        "page_num": 1,
        "text": "This is a sample text chunk for testing.",
        "context": {
            "parent_heading": "Introduction",
            "parent_heading_level": 1,
            "section_path": "1. Introduction",
            "element_type": "text",
            "is_page_boundary": True,
        },
        "related_tables": json.dumps(["table-0", "table-1"]),
        "related_pictures": json.dumps(["picture-0"]),
        "page_nums": json.dumps([1, 2]),
    }

    response = client.get(f"/api/documents/{doc_id}/chunks/{chunk_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["chunk_id"] == full_chunk_id
    assert data["doc_id"] == doc_id
    assert data["text_content"] == "This is a sample text chunk for testing."
    assert data["parent_heading"] == "Introduction"
    assert data["parent_heading_level"] == 1
    assert data["section_path"] == "1. Introduction"
    assert data["element_type"] == "text"
    assert data["related_tables"] == ["table-0", "table-1"]
    assert data["related_pictures"] == ["picture-0"]
    assert data["page_nums"] == [1, 2]
    assert data["is_page_boundary"] is True


def test_get_chunk_context_full_chunk_id(mock_koji_client):
    """Test request with full chunk_id format."""
    doc_id = "test-doc-id-123456"
    full_chunk_id = f"{doc_id}-chunk0001"

    mock_koji_client.get_chunk.return_value = {
        "id": full_chunk_id,
        "doc_id": doc_id,
        "page_num": 1,
        "text": "Test content",
        "context": {},
    }

    response = client.get(f"/api/documents/{doc_id}/chunks/{full_chunk_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["chunk_id"] == full_chunk_id


def test_get_chunk_context_minimal_metadata(mock_koji_client):
    """Test chunk with minimal metadata (no optional fields)."""
    doc_id = "test-doc-id-123456"
    chunk_id = "0001"
    full_chunk_id = f"{doc_id}-chunk{chunk_id}"

    mock_koji_client.get_chunk.return_value = {
        "id": full_chunk_id,
        "doc_id": doc_id,
        "page_num": 1,
        "text": "Minimal chunk content",
        "context": None,
        "page": 1,
    }

    response = client.get(f"/api/documents/{doc_id}/chunks/{chunk_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["text_content"] == "Minimal chunk content"
    assert data["parent_heading"] is None
    assert data["parent_heading_level"] is None
    assert data["section_path"] == ""
    assert data["element_type"] == "text"
    assert data["related_tables"] == []
    assert data["related_pictures"] == []
    assert data["is_page_boundary"] is False


def test_get_chunk_context_not_found(mock_koji_client):
    """Test 404 error for non-existent chunk."""
    doc_id = "test-doc-id-123456"
    chunk_id = "9999"
    full_chunk_id = f"{doc_id}-chunk{chunk_id}"

    mock_koji_client.get_chunk.return_value = None

    response = client.get(f"/api/documents/{doc_id}/chunks/{chunk_id}")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["code"] == "CHUNK_NOT_FOUND"
    assert data["detail"]["details"]["chunk_id"] == full_chunk_id


def test_get_chunk_context_invalid_doc_id(mock_koji_client):
    """Test 400 error for invalid doc_id."""
    invalid_doc_id = "invalid_id_with_@special_chars!"
    chunk_id = "0001"

    response = client.get(f"/api/documents/{invalid_doc_id}/chunks/{chunk_id}")

    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["code"] == "INVALID_DOC_ID"


def test_get_chunk_context_invalid_chunk_id(mock_koji_client):
    """Test 400 error for invalid chunk_id format."""
    doc_id = "test-doc-id-123456"
    invalid_chunk_id = "invalid-format"

    response = client.get(f"/api/documents/{doc_id}/chunks/{invalid_chunk_id}")

    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["code"] == "INVALID_CHUNK_ID"


def test_get_chunk_context_mismatched_doc_id(mock_koji_client):
    """Test 400 error when chunk_id doesn't match doc_id."""
    doc_id = "test-doc-id-123456"
    wrong_doc_id = "other-doc-id-789012"
    chunk_id = f"{wrong_doc_id}-chunk0001"

    response = client.get(f"/api/documents/{doc_id}/chunks/{chunk_id}")

    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["code"] == "CHUNK_DOC_MISMATCH"


def test_get_chunk_context_database_error(mock_koji_client):
    """Test 500 error on database failure."""
    doc_id = "test-doc-id-123456"
    chunk_id = "0001"

    mock_koji_client.get_chunk.side_effect = Exception("Database connection failed")

    response = client.get(f"/api/documents/{doc_id}/chunks/{chunk_id}")

    assert response.status_code == 500
    data = response.json()
    assert data["detail"]["code"] == "DATABASE_ERROR"


def test_get_chunk_context_invalid_json_fallback(mock_koji_client):
    """Test graceful handling of invalid JSON in array fields."""
    doc_id = "test-doc-id-123456"
    chunk_id = "0001"
    full_chunk_id = f"{doc_id}-chunk{chunk_id}"

    mock_koji_client.get_chunk.return_value = {
        "id": full_chunk_id,
        "doc_id": doc_id,
        "page_num": 1,
        "text": "Content",
        "context": {},
        "related_tables": "not-valid-json[",
        "related_pictures": json.dumps(["picture-0"]),
    }

    response = client.get(f"/api/documents/{doc_id}/chunks/{chunk_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["related_tables"] == []
    assert data["related_pictures"] == ["picture-0"]


def test_get_chunk_context_element_types(mock_koji_client):
    """Test different element types."""
    doc_id = "test-doc-id-123456"
    chunk_id = "0001"
    full_chunk_id = f"{doc_id}-chunk{chunk_id}"

    test_types = ["text", "list_item", "table_cell", "caption", "code", "formula"]

    for element_type in test_types:
        mock_koji_client.get_chunk.return_value = {
            "id": full_chunk_id,
            "doc_id": doc_id,
            "page_num": 1,
            "text": f"Content of type {element_type}",
            "context": {"element_type": element_type},
        }

        response = client.get(f"/api/documents/{doc_id}/chunks/{chunk_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["element_type"] == element_type


def test_get_chunk_context_page_boundary(mock_koji_client):
    """Test page boundary detection."""
    doc_id = "test-doc-id-123456"
    chunk_id = "0001"
    full_chunk_id = f"{doc_id}-chunk{chunk_id}"

    mock_koji_client.get_chunk.return_value = {
        "id": full_chunk_id,
        "doc_id": doc_id,
        "page_num": 2,
        "text": "Chunk crossing pages",
        "context": {"is_page_boundary": True},
        "page_nums": json.dumps([2, 3]),
    }

    response = client.get(f"/api/documents/{doc_id}/chunks/{chunk_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["is_page_boundary"] is True
    assert data["page_nums"] == [2, 3]
