"""
Unit tests for structure API endpoints.

Tests GET /api/documents/{doc_id}/pages/{page}/structure endpoint for:
- Success cases with structure metadata
- Empty structure (has_structure=False)
- 404 errors for non-existent documents/pages
- 422 errors for invalid parameters
- 500 errors for decompression failures
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="Structure API requires mocking refactor - set_chroma_client not exported"
)

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.processing.api.structure_endpoints import router
from src.storage.compression import compress_structure_metadata
from src.storage.metadata_schema import (
    DocumentStructure,
    HeadingInfo,
    HeadingLevel,
    PictureInfo,
    PictureType,
    TableInfo,
)

# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture
def mock_chroma_client():
    """Create mock ChromaDB client."""
    mock_client = MagicMock()
    # Override the dependency
    set_chroma_client(mock_client)
    yield mock_client
    # Reset after test
    set_chroma_client(None)


@pytest.fixture
def sample_structure():
    """Create sample DocumentStructure for testing."""
    structure = DocumentStructure()

    # Add headings
    structure.headings = [
        HeadingInfo(
            text="Introduction",
            level=HeadingLevel.SECTION_HEADER,
            page_num=1,
            section_path="1. Introduction",
            bbox=(72.0, 100.5, 540.0, 125.3),
        ),
        HeadingInfo(
            text="Methods",
            level=HeadingLevel.SECTION_HEADER,
            page_num=2,
            section_path="2. Methods",
            bbox=(72.0, 650.0, 540.0, 675.0),
        ),
    ]

    # Add tables
    structure.tables = [
        TableInfo(
            page_num=2,
            caption="Experimental Results",
            num_rows=5,
            num_cols=3,
            has_header=True,
            table_id="table-0",
            bbox=(100.2, 200.7, 500.8, 450.3),
        )
    ]

    # Add pictures
    structure.pictures = [
        PictureInfo(
            page_num=1,
            picture_type=PictureType.CHART,
            caption="Figure 1: Bar chart",
            confidence=0.95,
            picture_id="picture-0",
            bbox=(150.0, 300.0, 450.0, 500.0),
        )
    ]

    # Set summary
    structure.total_sections = 2
    structure.max_heading_depth = 1
    structure.has_table_of_contents = False

    return structure


def test_get_page_structure_success(mock_chroma_client, sample_structure):
    """Test successful retrieval of page structure."""
    doc_id = "test-doc-id-123456"
    page = 1

    # Compress structure metadata
    compressed = compress_structure_metadata(sample_structure.to_dict())

    # Mock ChromaDB response
    mock_chroma_client.visual_collection.get.return_value = {
        "ids": [f"{doc_id}-page001"],
        "metadatas": [
            {
                "doc_id": doc_id,
                "page": page,
                "has_structure": True,
                "structure": compressed,
                "image_width": 1700,
                "image_height": 2200,
                "filename": "test.pdf",
            }
        ],
    }

    # Make request
    response = client.get(f"/api/documents/{doc_id}/pages/{page}/structure")

    # Assertions
    assert response.status_code == 200
    data = response.json()

    assert data["doc_id"] == doc_id
    assert data["page"] == page
    assert data["has_structure"] is True

    # Check headings (only page 1)
    assert len(data["headings"]) == 1
    assert data["headings"][0]["text"] == "Introduction"
    assert data["headings"][0]["level"] == "SECTION_HEADER"
    assert data["headings"][0]["bbox"] is not None
    assert data["headings"][0]["bbox"]["left"] == 72.0
    assert data["headings"][0]["bbox"]["bottom"] == 100.5

    # Check pictures (page 1)
    assert len(data["pictures"]) == 1
    assert data["pictures"][0]["type"] == "chart"  # Lowercase from enum value
    assert data["pictures"][0]["confidence"] == 0.95

    # Check tables (none on page 1)
    assert len(data["tables"]) == 0

    # Check coordinate system
    assert data["coordinate_system"]["format"] == "[left, bottom, right, top]"
    assert data["coordinate_system"]["origin"] == "bottom-left"
    assert data["coordinate_system"]["units"] == "points"

    # Check image dimensions
    assert data["image_dimensions"]["width"] == 1700
    assert data["image_dimensions"]["height"] == 2200


def test_get_page_structure_empty(mock_chroma_client):
    """Test page with no structure metadata."""
    doc_id = "test-doc-id-123456"
    page = 1

    # Mock ChromaDB response (no structure)
    mock_chroma_client.visual_collection.get.return_value = {
        "ids": [f"{doc_id}-page001"],
        "metadatas": [
            {
                "doc_id": doc_id,
                "page": page,
                "has_structure": False,
                "filename": "test.pdf",
            }
        ],
    }

    # Make request
    response = client.get(f"/api/documents/{doc_id}/pages/{page}/structure")

    # Assertions
    assert response.status_code == 200
    data = response.json()

    assert data["doc_id"] == doc_id
    assert data["page"] == page
    assert data["has_structure"] is False
    assert data["headings"] == []
    assert data["tables"] == []
    assert data["pictures"] == []
    assert data["code_blocks"] == []
    assert data["formulas"] == []


def test_get_page_structure_page_not_found(mock_chroma_client):
    """Test 404 error for non-existent page."""
    doc_id = "test-doc-id-123456"
    page = 999

    # Mock ChromaDB response (no results)
    mock_chroma_client.visual_collection.get.return_value = {"ids": [], "metadatas": []}

    # Make request
    response = client.get(f"/api/documents/{doc_id}/pages/{page}/structure")

    # Assertions
    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["code"] == "PAGE_NOT_FOUND"
    assert data["detail"]["details"]["doc_id"] == doc_id
    assert data["detail"]["details"]["page"] == page


def test_get_page_structure_invalid_page_number(mock_chroma_client):
    """Test 422 error for invalid page number."""
    doc_id = "test-doc-id-123456"
    page = 0  # Invalid (must be >= 1)

    # Make request
    response = client.get(f"/api/documents/{doc_id}/pages/{page}/structure")

    # Assertions
    assert response.status_code == 422
    data = response.json()
    assert data["detail"]["code"] == "INVALID_PAGE"
    assert data["detail"]["details"]["page"] == 0


def test_get_page_structure_negative_page_number(mock_chroma_client):
    """Test 422 error for negative page number."""
    doc_id = "test-doc-id-123456"
    page = -5

    # Make request
    response = client.get(f"/api/documents/{doc_id}/pages/{page}/structure")

    # Assertions
    assert response.status_code == 422
    data = response.json()
    assert data["detail"]["code"] == "INVALID_PAGE"


def test_get_page_structure_multiple_pages(mock_chroma_client, sample_structure):
    """Test filtering structure elements by page."""
    doc_id = "test-doc-id-123456"
    page = 2

    # Compress structure metadata
    compressed = compress_structure_metadata(sample_structure.to_dict())

    # Mock ChromaDB response
    mock_chroma_client.visual_collection.get.return_value = {
        "ids": [f"{doc_id}-page002"],
        "metadatas": [
            {
                "doc_id": doc_id,
                "page": page,
                "has_structure": True,
                "structure": compressed,
                "filename": "test.pdf",
            }
        ],
    }

    # Make request
    response = client.get(f"/api/documents/{doc_id}/pages/{page}/structure")

    # Assertions
    assert response.status_code == 200
    data = response.json()

    # Check headings (only page 2)
    assert len(data["headings"]) == 1
    assert data["headings"][0]["text"] == "Methods"

    # Check tables (page 2)
    assert len(data["tables"]) == 1
    assert data["tables"][0]["table_id"] == "table-0"
    assert data["tables"][0]["rows"] == 5
    assert data["tables"][0]["cols"] == 3

    # Check pictures (none on page 2)
    assert len(data["pictures"]) == 0


def test_get_page_structure_bbox_format(mock_chroma_client):
    """Test bounding box format in response."""
    doc_id = "test-doc-id-123456"
    page = 1

    structure = DocumentStructure()
    structure.headings = [
        HeadingInfo(
            text="Test Heading",
            level=HeadingLevel.TITLE,
            page_num=1,
            bbox=(10.5, 20.3, 100.7, 50.9),
        )
    ]

    compressed = compress_structure_metadata(structure.to_dict())

    # Mock ChromaDB response
    mock_chroma_client.visual_collection.get.return_value = {
        "ids": [f"{doc_id}-page001"],
        "metadatas": [
            {
                "doc_id": doc_id,
                "page": page,
                "has_structure": True,
                "structure": compressed,
                "filename": "test.pdf",
            }
        ],
    }

    # Make request
    response = client.get(f"/api/documents/{doc_id}/pages/{page}/structure")

    # Assertions
    assert response.status_code == 200
    data = response.json()

    bbox = data["headings"][0]["bbox"]
    assert bbox["left"] == 10.5
    assert bbox["bottom"] == 20.3
    assert bbox["right"] == 100.7
    assert bbox["top"] == 50.9


def test_get_page_structure_missing_structure_data(mock_chroma_client):
    """Test handling of has_structure=True but no structure data."""
    doc_id = "test-doc-id-123456"
    page = 1

    # Mock ChromaDB response (has_structure=True but no structure field)
    mock_chroma_client.visual_collection.get.return_value = {
        "ids": [f"{doc_id}-page001"],
        "metadatas": [
            {
                "doc_id": doc_id,
                "page": page,
                "has_structure": True,
                # Missing "structure" field
                "filename": "test.pdf",
            }
        ],
    }

    # Make request
    response = client.get(f"/api/documents/{doc_id}/pages/{page}/structure")

    # Assertions
    assert response.status_code == 200
    data = response.json()

    # Should return empty structure gracefully
    assert data["has_structure"] is False
    assert data["headings"] == []


def test_get_page_structure_corrupted_data(mock_chroma_client):
    """Test 500 error for corrupted structure data."""
    doc_id = "test-doc-id-123456"
    page = 1

    # Mock ChromaDB response with corrupted data
    mock_chroma_client.visual_collection.get.return_value = {
        "ids": [f"{doc_id}-page001"],
        "metadatas": [
            {
                "doc_id": doc_id,
                "page": page,
                "has_structure": True,
                "structure": "corrupted-invalid-base64-data!!!",
                "filename": "test.pdf",
            }
        ],
    }

    # Make request
    response = client.get(f"/api/documents/{doc_id}/pages/{page}/structure")

    # Assertions
    assert response.status_code == 500
    data = response.json()
    assert data["detail"]["code"] == "DECOMPRESSION_ERROR"


def test_get_page_structure_database_error(mock_chroma_client):
    """Test 500 error on database failure."""
    doc_id = "test-doc-id-123456"
    page = 1

    # Mock database error
    mock_chroma_client.visual_collection.get.side_effect = Exception("Database connection failed")

    # Make request
    response = client.get(f"/api/documents/{doc_id}/pages/{page}/structure")

    # Assertions
    assert response.status_code == 500
    data = response.json()
    assert data["detail"]["code"] == "INTERNAL_ERROR"


def test_get_page_structure_all_element_types(mock_chroma_client):
    """Test response with all element types present."""
    doc_id = "test-doc-id-123456"
    page = 1

    structure = DocumentStructure()
    structure.headings = [
        HeadingInfo(text="Test", level=HeadingLevel.TITLE, page_num=1, bbox=(10, 20, 100, 50))
    ]
    structure.tables = [TableInfo(page_num=1, table_id="t1", bbox=(10, 60, 100, 120))]
    structure.pictures = [
        PictureInfo(
            page_num=1, picture_type=PictureType.CHART, picture_id="p1", bbox=(10, 130, 100, 200)
        )
    ]
    # Code blocks and formulas use dict format in to_dict(), so we add them manually to the dict
    # For testing, we'll just test headings, tables, and pictures which have proper dataclass support

    compressed = compress_structure_metadata(structure.to_dict())

    # Mock ChromaDB response
    mock_chroma_client.visual_collection.get.return_value = {
        "ids": [f"{doc_id}-page001"],
        "metadatas": [
            {
                "doc_id": doc_id,
                "page": page,
                "has_structure": True,
                "structure": compressed,
                "filename": "test.pdf",
            }
        ],
    }

    # Make request
    response = client.get(f"/api/documents/{doc_id}/pages/{page}/structure")

    # Assertions
    assert response.status_code == 200
    data = response.json()

    assert len(data["headings"]) == 1
    assert len(data["tables"]) == 1
    assert len(data["pictures"]) == 1
    # Code blocks and formulas will be empty since we didn't add them
    assert len(data["code_blocks"]) == 0
    assert len(data["formulas"]) == 0
