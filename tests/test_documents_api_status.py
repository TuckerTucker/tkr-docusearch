"""
Comprehensive tests for document status API endpoints.

Tests cover the following endpoints:
- GET /documents (list all documents with various filters and pagination)
- GET /documents/{doc_id} (get document details)

Test coverage includes:
- Pagination parameters (limit, offset)
- Filtering by file type (pdf, audio, office, text, images, all)
- Filtering by search query (filename matching)
- Sorting options (newest_first, oldest_first, name_asc, name_desc)
- Empty result sets
- Invalid doc_id validation
- Response schema validation
- Edge cases and error handling

Target: 90%+ coverage for status endpoints
"""

from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tkr_docusearch.processing.documents_api import router

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def app():
    """Create FastAPI test application with documents router."""
    test_app = FastAPI()
    test_app.include_router(router)
    return test_app


@pytest.fixture
def client(app):
    """Create test client for API testing."""
    return TestClient(app)


@pytest.fixture
def mock_chroma_client():
    """Create mock ChromaDB client with sample data."""
    with patch("tkr_docusearch.processing.documents_api.get_chroma_client") as mock_get:
        mock_client = Mock()
        mock_get.return_value = mock_client
        yield mock_client


@pytest.fixture
def sample_visual_data() -> Dict[str, Any]:
    """Sample visual embeddings data from ChromaDB."""
    return {
        "ids": [
            "doc1-page001",
            "doc1-page002",
            "doc2-page001",
            "doc3-page001",
            "doc4-page001",
        ],
        "metadatas": [
            {
                "doc_id": "doc1",
                "filename": "report.pdf",
                "page": 1,
                "timestamp": "2025-10-26T12:00:00Z",
                "image_path": "/page_images/doc1/page001.png",
                "thumb_path": "/page_images/doc1/page001_thumb.jpg",
            },
            {
                "doc_id": "doc1",
                "filename": "report.pdf",
                "page": 2,
                "timestamp": "2025-10-26T12:00:00Z",
                "image_path": "/page_images/doc1/page002.png",
                "thumb_path": "/page_images/doc1/page002_thumb.jpg",
            },
            {
                "doc_id": "doc2",
                "filename": "presentation.pptx",
                "page": 1,
                "timestamp": "2025-10-25T10:00:00Z",
                "image_path": "/page_images/doc2/page001.png",
                "thumb_path": "/page_images/doc2/page001_thumb.jpg",
            },
            {
                "doc_id": "doc3",
                "filename": "spreadsheet.xlsx",
                "page": 1,
                "timestamp": "2025-10-24T08:00:00Z",
                "image_path": "/page_images/doc3/page001.png",
                "thumb_path": "/page_images/doc3/page001_thumb.jpg",
            },
            {
                "doc_id": "doc4",
                "filename": "audio.mp3",
                "page": 1,
                "timestamp": "2025-10-23T06:00:00Z",
                "image_path": None,
                "thumb_path": None,
            },
        ],
    }


@pytest.fixture
def sample_text_data() -> Dict[str, Any]:
    """Sample text embeddings data from ChromaDB."""
    return {
        "ids": [
            "doc1-chunk0000",
            "doc1-chunk0001",
            "doc2-chunk0000",
            "doc3-chunk0000",
            "doc4-chunk0000",
            "doc4-chunk0001",
        ],
        "metadatas": [
            {
                "doc_id": "doc1",
                "filename": "report.pdf",
                "chunk_id": 0,
                "timestamp": "2025-10-26T12:00:00Z",
                "full_text": "Sample text from report chunk 0",
            },
            {
                "doc_id": "doc1",
                "filename": "report.pdf",
                "chunk_id": 1,
                "timestamp": "2025-10-26T12:00:00Z",
                "full_text": "Sample text from report chunk 1",
            },
            {
                "doc_id": "doc2",
                "filename": "presentation.pptx",
                "chunk_id": 0,
                "timestamp": "2025-10-25T10:00:00Z",
                "full_text": "Sample presentation text",
            },
            {
                "doc_id": "doc3",
                "filename": "spreadsheet.xlsx",
                "chunk_id": 0,
                "timestamp": "2025-10-24T08:00:00Z",
                "full_text": "Sample spreadsheet text",
            },
            {
                "doc_id": "doc4",
                "filename": "audio.mp3",
                "chunk_id": 0,
                "timestamp": "2025-10-23T06:00:00Z",
                "full_text": "Audio transcript chunk 0",
            },
            {
                "doc_id": "doc4",
                "filename": "audio.mp3",
                "chunk_id": 1,
                "timestamp": "2025-10-23T06:00:00Z",
                "full_text": "Audio transcript chunk 1",
            },
        ],
    }


# ============================================================================
# GET /documents - List Endpoint Tests
# ============================================================================


class TestListDocuments:
    """Test suite for GET /documents endpoint."""

    def test_list_documents_basic(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test basic document listing returns correct structure."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        response = client.get("/documents")

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "documents" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

        # Validate data types
        assert isinstance(data["documents"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["limit"], int)
        assert isinstance(data["offset"], int)

        # Should have 4 unique documents
        assert data["total"] == 4
        assert len(data["documents"]) == 4

    def test_list_documents_schema_validation(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test each document item has correct schema."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        response = client.get("/documents")
        data = response.json()

        # Validate first document schema
        doc = data["documents"][0]
        assert "doc_id" in doc
        assert "filename" in doc
        assert "page_count" in doc
        assert "chunk_count" in doc
        assert "date_added" in doc
        assert "collections" in doc
        assert "has_images" in doc
        assert "first_page_thumb" in doc or doc["first_page_thumb"] is None

        # Validate data types
        assert isinstance(doc["doc_id"], str)
        assert isinstance(doc["filename"], str)
        assert isinstance(doc["page_count"], int)
        assert isinstance(doc["chunk_count"], int)
        assert isinstance(doc["date_added"], str)
        assert isinstance(doc["collections"], list)
        assert isinstance(doc["has_images"], bool)

    def test_list_documents_empty_database(self, client, mock_chroma_client):
        """Test listing documents when database is empty."""
        mock_chroma_client._visual_collection.get.return_value = {"ids": [], "metadatas": []}
        mock_chroma_client._text_collection.get.return_value = {"ids": [], "metadatas": []}

        response = client.get("/documents")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["documents"]) == 0
        assert data["documents"] == []


class TestPagination:
    """Test suite for pagination parameters."""

    def test_pagination_default_values(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test default pagination values (limit=50, offset=0)."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        response = client.get("/documents")
        data = response.json()

        assert data["limit"] == 50  # Default limit
        assert data["offset"] == 0  # Default offset

    def test_pagination_custom_limit(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test custom limit parameter."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        response = client.get("/documents?limit=2")
        data = response.json()

        assert data["limit"] == 2
        assert data["total"] == 4  # Total count unchanged
        assert len(data["documents"]) == 2  # Only 2 results returned

    def test_pagination_custom_offset(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test custom offset parameter."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        response = client.get("/documents?offset=2")
        data = response.json()

        assert data["offset"] == 2
        assert data["total"] == 4
        assert len(data["documents"]) == 2  # Remaining 2 documents

    def test_pagination_limit_and_offset(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test limit and offset together."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        response = client.get("/documents?limit=1&offset=1")
        data = response.json()

        assert data["limit"] == 1
        assert data["offset"] == 1
        assert data["total"] == 4
        assert len(data["documents"]) == 1

    def test_pagination_offset_beyond_results(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test offset beyond available results."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        response = client.get("/documents?offset=100")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] == 4
        assert len(data["documents"]) == 0  # No documents at this offset

    def test_pagination_limit_validation_too_high(self, client):
        """Test limit validation - maximum is 100."""
        response = client.get("/documents?limit=200")

        assert response.status_code == 422  # Validation error

    def test_pagination_limit_validation_too_low(self, client):
        """Test limit validation - minimum is 1."""
        response = client.get("/documents?limit=0")

        assert response.status_code == 422  # Validation error

    def test_pagination_offset_validation_negative(self, client):
        """Test offset validation - must be non-negative."""
        response = client.get("/documents?offset=-5")

        assert response.status_code == 422  # Validation error


class TestFileTypeFiltering:
    """Test suite for file type filtering."""

    def test_filter_all_documents(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test filtering with 'all' group (default)."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        response = client.get("/documents?file_type_group=all")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] == 4  # All documents

    def test_filter_pdf_documents(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test filtering by PDF file type."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        response = client.get("/documents?file_type_group=pdf")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] == 1
        assert data["documents"][0]["filename"] == "report.pdf"

    def test_filter_audio_documents(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test filtering by audio file type."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        response = client.get("/documents?file_type_group=audio")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] == 1
        assert data["documents"][0]["filename"] == "audio.mp3"

    def test_filter_office_documents(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test filtering by office document types."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        response = client.get("/documents?file_type_group=office")
        data = response.json()

        assert response.status_code == 200
        # Office group includes .docx, .pptx, .xlsx
        # Sample data has presentation.pptx and spreadsheet.xlsx
        assert data["total"] == 2
        assert any(doc["filename"].endswith(".xlsx") for doc in data["documents"])
        assert any(doc["filename"].endswith(".pptx") for doc in data["documents"])

    def test_filter_text_documents(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test filtering by text document types."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        response = client.get("/documents?file_type_group=text")
        data = response.json()

        assert response.status_code == 200
        # Text group includes .md, .csv, .html, .vtt, etc.
        # Sample data has no text documents, so should be 0
        assert data["total"] == 0

    def test_filter_no_matches(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test file type filter with no matching documents."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        # Filter by images when no image documents exist
        response = client.get("/documents?file_type_group=images")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] == 0
        assert len(data["documents"]) == 0


class TestSearchFiltering:
    """Test suite for filename search filtering."""

    def test_search_exact_match(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test search with exact filename match."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        response = client.get("/documents?search=report.pdf")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] == 1
        assert data["documents"][0]["filename"] == "report.pdf"

    def test_search_partial_match(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test search with partial filename match."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        response = client.get("/documents?search=report")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] == 1
        assert "report" in data["documents"][0]["filename"].lower()

    def test_search_case_insensitive(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test search is case-insensitive."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        response = client.get("/documents?search=REPORT")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] == 1
        assert "report" in data["documents"][0]["filename"].lower()

    def test_search_no_matches(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test search with no matching documents."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        response = client.get("/documents?search=nonexistent")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] == 0
        assert len(data["documents"]) == 0

    def test_search_multiple_matches(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test search returning multiple matches."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        # Search for extension that appears in multiple files
        response = client.get("/documents?search=.pdf")
        data = response.json()

        assert response.status_code == 200
        # Only report.pdf in sample data
        assert data["total"] == 1


class TestSorting:
    """Test suite for sorting options."""

    def test_sort_newest_first_default(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test default sort order is newest first."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        response = client.get("/documents")
        data = response.json()

        assert response.status_code == 200
        # First document should be most recent (doc1)
        assert data["documents"][0]["doc_id"] == "doc1"
        # Last should be oldest (doc4)
        assert data["documents"][-1]["doc_id"] == "doc4"

    def test_sort_newest_first_explicit(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test explicit newest_first sorting."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        response = client.get("/documents?sort_by=newest_first")
        data = response.json()

        assert response.status_code == 200
        assert data["documents"][0]["doc_id"] == "doc1"
        assert data["documents"][-1]["doc_id"] == "doc4"

    def test_sort_oldest_first(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test oldest_first sorting."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        response = client.get("/documents?sort_by=oldest_first")
        data = response.json()

        assert response.status_code == 200
        # First should be oldest (doc4)
        assert data["documents"][0]["doc_id"] == "doc4"
        # Last should be newest (doc1)
        assert data["documents"][-1]["doc_id"] == "doc1"

    def test_sort_name_ascending(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test alphabetical sorting (A-Z)."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        response = client.get("/documents?sort_by=name_asc")
        data = response.json()

        assert response.status_code == 200
        filenames = [doc["filename"] for doc in data["documents"]]
        assert filenames == sorted(filenames, key=str.lower)

    def test_sort_name_descending(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test reverse alphabetical sorting (Z-A)."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        response = client.get("/documents?sort_by=name_desc")
        data = response.json()

        assert response.status_code == 200
        filenames = [doc["filename"] for doc in data["documents"]]
        assert filenames == sorted(filenames, key=str.lower, reverse=True)


class TestCombinedFilters:
    """Test suite for combined filter scenarios."""

    def test_search_and_file_type(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test combining search and file type filters."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        response = client.get("/documents?search=report&file_type_group=pdf")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] == 1
        assert data["documents"][0]["filename"] == "report.pdf"

    def test_all_filters_combined(
        self, client, mock_chroma_client, sample_visual_data, sample_text_data
    ):
        """Test all filters combined (search, file_type, sort, pagination)."""
        mock_chroma_client._visual_collection.get.return_value = sample_visual_data
        mock_chroma_client._text_collection.get.return_value = sample_text_data

        response = client.get(
            "/documents?search=.&file_type_group=all&sort_by=name_asc&limit=2&offset=0"
        )
        data = response.json()

        assert response.status_code == 200
        assert data["limit"] == 2
        assert data["offset"] == 0
        # Results should be alphabetically sorted
        filenames = [doc["filename"] for doc in data["documents"]]
        assert filenames == sorted(filenames, key=str.lower)


# ============================================================================
# GET /documents/{doc_id} - Detail Endpoint Tests
# ============================================================================


class TestGetDocument:
    """Test suite for GET /documents/{doc_id} endpoint."""

    def test_get_document_success(self, client, mock_chroma_client):
        """Test successful document retrieval."""
        doc_id = "valid-doc-id-12345678"

        mock_chroma_client._visual_collection.get.return_value = {
            "ids": [f"{doc_id}-page001", f"{doc_id}-page002"],
            "metadatas": [
                {
                    "doc_id": doc_id,
                    "filename": "test.pdf",
                    "page": 1,
                    "timestamp": "2025-10-26T12:00:00Z",
                    "image_path": f"/page_images/{doc_id}/page001.png",
                    "thumb_path": f"/page_images/{doc_id}/page001_thumb.jpg",
                },
                {
                    "doc_id": doc_id,
                    "filename": "test.pdf",
                    "page": 2,
                    "timestamp": "2025-10-26T12:00:00Z",
                    "image_path": f"/page_images/{doc_id}/page002.png",
                    "thumb_path": f"/page_images/{doc_id}/page002_thumb.jpg",
                },
            ],
        }

        mock_chroma_client._text_collection.get.return_value = {
            "ids": [f"{doc_id}-chunk0000"],
            "metadatas": [
                {
                    "doc_id": doc_id,
                    "filename": "test.pdf",
                    "chunk_id": 0,
                    "full_text": "Sample text content",
                    "timestamp": "2025-10-26T12:00:00Z",
                }
            ],
        }

        response = client.get(f"/documents/{doc_id}")

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert data["doc_id"] == doc_id
        assert data["filename"] == "test.pdf"
        assert data["date_added"] == "2025-10-26T12:00:00Z"
        assert len(data["pages"]) == 2
        assert len(data["chunks"]) == 1
        assert "metadata" in data

    def test_get_document_schema_validation(self, client, mock_chroma_client):
        """Test response schema for document detail."""
        doc_id = "valid-doc-id-12345678"

        mock_chroma_client._visual_collection.get.return_value = {
            "ids": [f"{doc_id}-page001"],
            "metadatas": [
                {
                    "doc_id": doc_id,
                    "filename": "test.pdf",
                    "page": 1,
                    "timestamp": "2025-10-26T12:00:00Z",
                    "image_path": f"/page_images/{doc_id}/page001.png",
                    "thumb_path": f"/page_images/{doc_id}/page001_thumb.jpg",
                }
            ],
        }

        mock_chroma_client._text_collection.get.return_value = {
            "ids": [f"{doc_id}-chunk0000"],
            "metadatas": [
                {
                    "doc_id": doc_id,
                    "filename": "test.pdf",
                    "chunk_id": 0,
                    "full_text": "Sample text",
                    "timestamp": "2025-10-26T12:00:00Z",
                }
            ],
        }

        response = client.get(f"/documents/{doc_id}")
        data = response.json()

        # Validate metadata schema
        metadata = data["metadata"]
        assert "page_count" in metadata
        assert "chunk_count" in metadata
        assert "has_images" in metadata
        assert "collections" in metadata
        assert "raw_metadata" in metadata or metadata["raw_metadata"] is None
        assert "vtt_available" in metadata
        assert "markdown_available" in metadata
        assert "has_timestamps" in metadata
        assert "has_album_art" in metadata
        assert "album_art_url" in metadata or metadata["album_art_url"] is None

        # Validate page info schema
        if data["pages"]:
            page = data["pages"][0]
            assert "page_number" in page
            assert "image_path" in page or page["image_path"] is None
            assert "thumb_path" in page or page["thumb_path"] is None
            assert "embedding_id" in page

        # Validate chunk info schema
        if data["chunks"]:
            chunk = data["chunks"][0]
            assert "chunk_id" in chunk
            assert "text_content" in chunk
            assert "embedding_id" in chunk
            assert "start_time" in chunk or chunk["start_time"] is None
            assert "end_time" in chunk or chunk["end_time"] is None
            assert "has_timestamps" in chunk

    def test_get_document_not_found(self, client, mock_chroma_client):
        """Test 404 error for non-existent document."""
        doc_id = "nonexistent-doc-id-12345"

        mock_chroma_client._visual_collection.get.return_value = {"ids": [], "metadatas": []}
        mock_chroma_client._text_collection.get.return_value = {"ids": [], "metadatas": []}

        response = client.get(f"/documents/{doc_id}")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"]["code"] == "DOCUMENT_NOT_FOUND"
        assert doc_id in data["detail"]["details"]["doc_id"]

    def test_get_document_invalid_id_format(self, client, mock_chroma_client):
        """Test 400 error for invalid doc_id format."""
        # Mock empty response for all queries
        mock_chroma_client._visual_collection.get.return_value = {"ids": [], "metadatas": []}
        mock_chroma_client._text_collection.get.return_value = {"ids": [], "metadatas": []}

        # Invalid IDs that will trigger validation errors
        # Pattern: ^[a-zA-Z0-9\-]{8,64}$
        invalid_ids = [
            "short",  # Too short (< 8 chars)
            "invalid@chars12",  # Invalid characters (@)
            "dots..notallowed",  # Invalid characters (..)
            "under_score_bad",  # Invalid characters (_)
            "a" * 65,  # Too long (> 64 chars)
        ]

        for invalid_id in invalid_ids:
            response = client.get(f"/documents/{invalid_id}")

            # Should get 400 validation error before database is queried
            assert (
                response.status_code == 400
            ), f"Expected 400 for {invalid_id}, got {response.status_code}"
            data = response.json()
            assert data["detail"]["code"] == "INVALID_DOC_ID", f"Wrong error code for {invalid_id}"

    def test_get_document_visual_only(self, client, mock_chroma_client):
        """Test document with only visual embeddings."""
        doc_id = "visual-only-doc-12345678"

        mock_chroma_client._visual_collection.get.return_value = {
            "ids": [f"{doc_id}-page001"],
            "metadatas": [
                {
                    "doc_id": doc_id,
                    "filename": "image.png",
                    "page": 1,
                    "timestamp": "2025-10-26T12:00:00Z",
                    "image_path": f"/page_images/{doc_id}/page001.png",
                    "thumb_path": f"/page_images/{doc_id}/page001_thumb.jpg",
                }
            ],
        }

        mock_chroma_client._text_collection.get.return_value = {"ids": [], "metadatas": []}

        response = client.get(f"/documents/{doc_id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["pages"]) == 1
        assert len(data["chunks"]) == 0
        assert "visual" in data["metadata"]["collections"]

    def test_get_document_text_only(self, client, mock_chroma_client):
        """Test document with only text embeddings."""
        doc_id = "text-only-doc-12345678"

        mock_chroma_client._visual_collection.get.return_value = {"ids": [], "metadatas": []}

        mock_chroma_client._text_collection.get.return_value = {
            "ids": [f"{doc_id}-chunk0000"],
            "metadatas": [
                {
                    "doc_id": doc_id,
                    "filename": "text.txt",
                    "chunk_id": 0,
                    "full_text": "Text content",
                    "timestamp": "2025-10-26T12:00:00Z",
                }
            ],
        }

        response = client.get(f"/documents/{doc_id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["pages"]) == 0
        assert len(data["chunks"]) == 1
        assert "text" in data["metadata"]["collections"]

    def test_get_document_database_error(self, client, mock_chroma_client):
        """Test 500 error on database failure."""
        doc_id = "valid-doc-id-12345678"

        # Simulate database error
        mock_chroma_client._visual_collection.get.side_effect = Exception(
            "Database connection failed"
        )

        response = client.get(f"/documents/{doc_id}")

        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["code"] == "DATABASE_ERROR"


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestEdgeCases:
    """Test suite for edge cases and error conditions."""

    def test_list_documents_database_error(self, client, mock_chroma_client):
        """Test 500 error when database fails during list operation."""
        mock_chroma_client._visual_collection.get.side_effect = Exception("Database error")

        response = client.get("/documents")

        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["code"] == "DATABASE_ERROR"

    def test_document_counts_accuracy(self, client, mock_chroma_client):
        """Test that page_count and chunk_count are accurate."""
        doc_id = "count-test-doc-12345678"

        # Create 3 pages and 5 chunks
        mock_chroma_client._visual_collection.get.return_value = {
            "ids": [f"{doc_id}-page{i:03d}" for i in range(1, 4)],
            "metadatas": [
                {
                    "doc_id": doc_id,
                    "filename": "test.pdf",
                    "page": i,
                    "timestamp": "2025-10-26T12:00:00Z",
                    "image_path": f"/page_images/{doc_id}/page{i:03d}.png",
                }
                for i in range(1, 4)
            ],
        }

        mock_chroma_client._text_collection.get.return_value = {
            "ids": [f"{doc_id}-chunk{i:04d}" for i in range(5)],
            "metadatas": [
                {
                    "doc_id": doc_id,
                    "filename": "test.pdf",
                    "chunk_id": i,
                    "full_text": f"Chunk {i}",
                    "timestamp": "2025-10-26T12:00:00Z",
                }
                for i in range(5)
            ],
        }

        response = client.get(f"/documents/{doc_id}")
        data = response.json()

        assert data["metadata"]["page_count"] == 3
        assert data["metadata"]["chunk_count"] == 5
        assert len(data["pages"]) == 3
        assert len(data["chunks"]) == 5

    def test_pages_sorted_by_number(self, client, mock_chroma_client):
        """Test that pages are sorted by page number."""
        doc_id = "sort-test-doc-12345678"

        # Return pages in random order
        mock_chroma_client._visual_collection.get.return_value = {
            "ids": [f"{doc_id}-page003", f"{doc_id}-page001", f"{doc_id}-page002"],
            "metadatas": [
                {
                    "doc_id": doc_id,
                    "filename": "test.pdf",
                    "page": 3,
                    "timestamp": "2025-10-26T12:00:00Z",
                },
                {
                    "doc_id": doc_id,
                    "filename": "test.pdf",
                    "page": 1,
                    "timestamp": "2025-10-26T12:00:00Z",
                },
                {
                    "doc_id": doc_id,
                    "filename": "test.pdf",
                    "page": 2,
                    "timestamp": "2025-10-26T12:00:00Z",
                },
            ],
        }

        mock_chroma_client._text_collection.get.return_value = {"ids": [], "metadatas": []}

        response = client.get(f"/documents/{doc_id}")
        data = response.json()

        # Pages should be sorted 1, 2, 3
        page_numbers = [page["page_number"] for page in data["pages"]]
        assert page_numbers == [1, 2, 3]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.processing.documents_api", "--cov-report=term-missing"])
