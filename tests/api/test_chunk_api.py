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

from src.processing.api.structure_endpoints import router

# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture
def mock_chroma_client():
    """Create mock ChromaDB client."""
    with patch("src.processing.api.structure_endpoints.get_chroma_client") as mock_get:
        mock_client = MagicMock()
        mock_get.return_value = mock_client
        yield mock_client


def test_get_chunk_context_success(mock_chroma_client):
    """Test successful retrieval of chunk context."""
    doc_id = "test-doc-id-123456"
    chunk_id = "0001"
    full_chunk_id = f"{doc_id}-chunk{chunk_id}"

    # Mock ChromaDB response
    mock_chroma_client._text_collection.get.return_value = {
        "ids": [full_chunk_id],
        "metadatas": [
            {
                "doc_id": doc_id,
                "chunk_id": 1,
                "full_text": "This is a sample text chunk for testing.",
                "parent_heading": "Introduction",
                "parent_heading_level": 1,
                "section_path": "1. Introduction",
                "element_type": "text",
                "related_tables": json.dumps(["table-0", "table-1"]),
                "related_pictures": json.dumps(["picture-0"]),
                "page_nums": json.dumps([1, 2]),
                "is_page_boundary": True,
            }
        ],
    }

    # Make request
    response = client.get(f"/api/documents/{doc_id}/chunks/{chunk_id}")

    # Assertions
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


def test_get_chunk_context_full_chunk_id(mock_chroma_client):
    """Test request with full chunk_id format."""
    doc_id = "test-doc-id-123456"
    full_chunk_id = f"{doc_id}-chunk0001"

    # Mock ChromaDB response
    mock_chroma_client._text_collection.get.return_value = {
        "ids": [full_chunk_id],
        "metadatas": [
            {
                "doc_id": doc_id,
                "chunk_id": 1,
                "full_text": "Test content",
                "section_path": "",
                "element_type": "text",
            }
        ],
    }

    # Make request with full chunk_id
    response = client.get(f"/api/documents/{doc_id}/chunks/{full_chunk_id}")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["chunk_id"] == full_chunk_id


def test_get_chunk_context_minimal_metadata(mock_chroma_client):
    """Test chunk with minimal metadata (no optional fields)."""
    doc_id = "test-doc-id-123456"
    chunk_id = "0001"
    full_chunk_id = f"{doc_id}-chunk{chunk_id}"

    # Mock ChromaDB response (minimal metadata)
    mock_chroma_client._text_collection.get.return_value = {
        "ids": [full_chunk_id],
        "metadatas": [
            {
                "doc_id": doc_id,
                "chunk_id": 1,
                "full_text": "Minimal chunk content",
                "page": 1,  # Single page field instead of page_nums
            }
        ],
    }

    # Make request
    response = client.get(f"/api/documents/{doc_id}/chunks/{chunk_id}")

    # Assertions
    assert response.status_code == 200
    data = response.json()

    assert data["text_content"] == "Minimal chunk content"
    assert data["parent_heading"] is None
    assert data["parent_heading_level"] is None
    assert data["section_path"] == ""
    assert data["element_type"] == "text"  # Default value
    assert data["related_tables"] == []
    assert data["related_pictures"] == []
    assert data["page_nums"] == [1]  # Fallback from single page field
    assert data["is_page_boundary"] is False


def test_get_chunk_context_text_preview_fallback(mock_chroma_client):
    """Test fallback to text_preview if full_text not available."""
    doc_id = "test-doc-id-123456"
    chunk_id = "0001"
    full_chunk_id = f"{doc_id}-chunk{chunk_id}"

    # Mock ChromaDB response (no full_text, only text_preview)
    mock_chroma_client._text_collection.get.return_value = {
        "ids": [full_chunk_id],
        "metadatas": [
            {
                "doc_id": doc_id,
                "chunk_id": 1,
                "text_preview": "Preview text only...",
            }
        ],
    }

    # Make request
    response = client.get(f"/api/documents/{doc_id}/chunks/{chunk_id}")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["text_content"] == "Preview text only..."


def test_get_chunk_context_json_parsing(mock_chroma_client):
    """Test parsing of JSON array fields from ChromaDB."""
    doc_id = "test-doc-id-123456"
    chunk_id = "0001"
    full_chunk_id = f"{doc_id}-chunk{chunk_id}"

    # Mock ChromaDB response with JSON strings
    mock_chroma_client._text_collection.get.return_value = {
        "ids": [full_chunk_id],
        "metadatas": [
            {
                "doc_id": doc_id,
                "chunk_id": 1,
                "full_text": "Content",
                "related_tables": '["table-0","table-1","table-2"]',
                "related_pictures": '["picture-0"]',
                "page_nums": "[1,2,3]",
            }
        ],
    }

    # Make request
    response = client.get(f"/api/documents/{doc_id}/chunks/{chunk_id}")

    # Assertions
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data["related_tables"], list)
    assert data["related_tables"] == ["table-0", "table-1", "table-2"]
    assert isinstance(data["related_pictures"], list)
    assert data["related_pictures"] == ["picture-0"]
    assert isinstance(data["page_nums"], list)
    assert data["page_nums"] == [1, 2, 3]


def test_get_chunk_context_bbox_parsing(mock_chroma_client):
    """Test parsing of bbox field if available."""
    doc_id = "test-doc-id-123456"
    chunk_id = "0001"
    full_chunk_id = f"{doc_id}-chunk{chunk_id}"

    # Mock ChromaDB response with bbox
    mock_chroma_client._text_collection.get.return_value = {
        "ids": [full_chunk_id],
        "metadatas": [
            {
                "doc_id": doc_id,
                "chunk_id": 1,
                "full_text": "Content with bbox",
                "bbox": json.dumps([72.0, 100.5, 540.0, 125.3]),
            }
        ],
    }

    # Make request
    response = client.get(f"/api/documents/{doc_id}/chunks/{chunk_id}")

    # Assertions
    assert response.status_code == 200
    data = response.json()

    assert data["bbox"] is not None
    assert data["bbox"]["left"] == 72.0
    assert data["bbox"]["bottom"] == 100.5
    assert data["bbox"]["right"] == 540.0
    assert data["bbox"]["top"] == 125.3


def test_get_chunk_context_not_found(mock_chroma_client):
    """Test 404 error for non-existent chunk."""
    doc_id = "test-doc-id-123456"
    chunk_id = "9999"
    full_chunk_id = f"{doc_id}-chunk{chunk_id}"

    # Mock ChromaDB response (no results)
    mock_chroma_client._text_collection.get.return_value = {"ids": [], "metadatas": []}

    # Make request
    response = client.get(f"/api/documents/{doc_id}/chunks/{chunk_id}")

    # Assertions
    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["code"] == "CHUNK_NOT_FOUND"
    assert data["detail"]["details"]["chunk_id"] == full_chunk_id


def test_get_chunk_context_invalid_doc_id(mock_chroma_client):
    """Test 400 error for invalid doc_id."""
    # Use a doc_id that clearly doesn't match the pattern
    invalid_doc_id = "invalid_id_with_@special_chars!"
    chunk_id = "0001"

    # Make request
    response = client.get(f"/api/documents/{invalid_doc_id}/chunks/{chunk_id}")

    # Assertions
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["code"] == "INVALID_DOC_ID"


def test_get_chunk_context_invalid_chunk_id(mock_chroma_client):
    """Test 400 error for invalid chunk_id format."""
    doc_id = "test-doc-id-123456"
    invalid_chunk_id = "invalid-format"

    # Make request
    response = client.get(f"/api/documents/{doc_id}/chunks/{invalid_chunk_id}")

    # Assertions
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["code"] == "INVALID_CHUNK_ID"


def test_get_chunk_context_mismatched_doc_id(mock_chroma_client):
    """Test 400 error when chunk_id doesn't match doc_id."""
    doc_id = "test-doc-id-123456"
    wrong_doc_id = "other-doc-id-789012"
    chunk_id = f"{wrong_doc_id}-chunk0001"

    # Make request
    response = client.get(f"/api/documents/{doc_id}/chunks/{chunk_id}")

    # Assertions
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["code"] == "CHUNK_DOC_MISMATCH"


def test_get_chunk_context_database_error(mock_chroma_client):
    """Test 500 error on database failure."""
    doc_id = "test-doc-id-123456"
    chunk_id = "0001"

    # Mock database error
    mock_chroma_client._text_collection.get.side_effect = Exception("Database connection failed")

    # Make request
    response = client.get(f"/api/documents/{doc_id}/chunks/{chunk_id}")

    # Assertions
    assert response.status_code == 500
    data = response.json()
    assert data["detail"]["code"] == "DATABASE_ERROR"


def test_get_chunk_context_invalid_json_fallback(mock_chroma_client):
    """Test graceful handling of invalid JSON in array fields."""
    doc_id = "test-doc-id-123456"
    chunk_id = "0001"
    full_chunk_id = f"{doc_id}-chunk{chunk_id}"

    # Mock ChromaDB response with invalid JSON
    mock_chroma_client._text_collection.get.return_value = {
        "ids": [full_chunk_id],
        "metadatas": [
            {
                "doc_id": doc_id,
                "chunk_id": 1,
                "full_text": "Content",
                "related_tables": "not-valid-json[",  # Invalid JSON
                "related_pictures": json.dumps(["picture-0"]),
            }
        ],
    }

    # Make request
    response = client.get(f"/api/documents/{doc_id}/chunks/{chunk_id}")

    # Assertions
    assert response.status_code == 200
    data = response.json()

    # Should fallback to empty list for invalid JSON
    assert data["related_tables"] == []
    # Valid JSON should work
    assert data["related_pictures"] == ["picture-0"]


def test_get_chunk_context_element_types(mock_chroma_client):
    """Test different element types."""
    doc_id = "test-doc-id-123456"
    chunk_id = "0001"
    full_chunk_id = f"{doc_id}-chunk{chunk_id}"

    test_types = ["text", "list_item", "table_cell", "caption", "code", "formula"]

    for element_type in test_types:
        # Mock ChromaDB response
        mock_chroma_client._text_collection.get.return_value = {
            "ids": [full_chunk_id],
            "metadatas": [
                {
                    "doc_id": doc_id,
                    "chunk_id": 1,
                    "full_text": f"Content of type {element_type}",
                    "element_type": element_type,
                }
            ],
        }

        # Make request
        response = client.get(f"/api/documents/{doc_id}/chunks/{chunk_id}")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["element_type"] == element_type


def test_get_chunk_context_page_boundary(mock_chroma_client):
    """Test page boundary detection."""
    doc_id = "test-doc-id-123456"
    chunk_id = "0001"
    full_chunk_id = f"{doc_id}-chunk{chunk_id}"

    # Mock ChromaDB response with page boundary
    mock_chroma_client._text_collection.get.return_value = {
        "ids": [full_chunk_id],
        "metadatas": [
            {
                "doc_id": doc_id,
                "chunk_id": 1,
                "full_text": "Chunk crossing pages",
                "page_nums": json.dumps([2, 3]),
                "is_page_boundary": True,
            }
        ],
    }

    # Make request
    response = client.get(f"/api/documents/{doc_id}/chunks/{chunk_id}")

    # Assertions
    assert response.status_code == 200
    data = response.json()

    assert data["is_page_boundary"] is True
    assert data["page_nums"] == [2, 3]
