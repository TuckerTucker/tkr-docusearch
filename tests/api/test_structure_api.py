"""
Tests for structure API endpoints.

Tests GET /documents/{doc_id}/pages/{page}/structure endpoint for:
- Success cases with structure metadata
- Empty structure (has_structure=False)
- 404 errors for non-existent documents/pages
- 400 errors for invalid parameters
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tkr_docusearch.processing.api.structure_endpoints import router
from tkr_docusearch.storage.metadata_schema import (
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
def mock_koji_client():
    """Create mock Koji client."""
    with patch("tkr_docusearch.processing.api.structure_endpoints.get_storage_client") as mock_get:
        mock_client = MagicMock()
        mock_get.return_value = mock_client
        yield mock_client


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


def _make_page_data(doc_id, page, structure=None, has_structure=True):
    """Build a mock page dict as returned by KojiClient.get_page()."""
    data = {
        "id": f"{doc_id}-page{page:03d}",
        "doc_id": doc_id,
        "page_num": page,
    }
    if has_structure and structure is not None:
        data["structure"] = structure.to_dict()
    else:
        data["structure"] = None
    return data


def test_get_page_structure_success(mock_koji_client, sample_structure):
    """Test successful retrieval of page structure."""
    doc_id = "test-doc-id-123456"
    page = 1

    mock_koji_client.get_page.return_value = _make_page_data(
        doc_id, page, sample_structure
    )

    response = client.get(f"/api/documents/{doc_id}/pages/{page}/structure")

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

    # Check pictures (page 1)
    assert len(data["pictures"]) == 1
    assert data["pictures"][0]["type"] == "chart"
    assert data["pictures"][0]["confidence"] == 0.95

    # Check tables (none on page 1)
    assert len(data["tables"]) == 0

    # Check summary
    assert data["summary"]["total_sections"] == 2
    assert data["summary"]["max_depth"] == 1

    # Check coordinate system
    assert data["coordinate_system"]["format"] == "[left, bottom, right, top]"
    assert data["coordinate_system"]["origin"] == "bottom-left"
    assert data["coordinate_system"]["units"] == "points"


def test_get_page_structure_empty(mock_koji_client):
    """Test page with no structure metadata."""
    doc_id = "test-doc-id-123456"
    page = 1

    mock_koji_client.get_page.return_value = _make_page_data(
        doc_id, page, has_structure=False
    )

    response = client.get(f"/api/documents/{doc_id}/pages/{page}/structure")

    assert response.status_code == 200
    data = response.json()

    assert data["doc_id"] == doc_id
    assert data["page"] == page
    assert data["has_structure"] is False
    assert data["headings"] == []
    assert data["tables"] == []
    assert data["pictures"] == []
    assert data["summary"] is None


def test_get_page_structure_page_not_found(mock_koji_client):
    """Test 404 error for non-existent page."""
    doc_id = "test-doc-id-123456"
    page = 999

    mock_koji_client.get_page.return_value = None

    response = client.get(f"/api/documents/{doc_id}/pages/{page}/structure")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["code"] == "PAGE_NOT_FOUND"
    assert data["detail"]["details"]["doc_id"] == doc_id
    assert data["detail"]["details"]["page"] == page


def test_get_page_structure_invalid_doc_id(mock_koji_client):
    """Test 400 error for invalid doc_id."""
    invalid_doc_id = "invalid_id_with_underscores_and_@special"
    page = 1

    response = client.get(f"/api/documents/{invalid_doc_id}/pages/{page}/structure")

    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["code"] == "INVALID_DOC_ID"


def test_get_page_structure_invalid_page_number(mock_koji_client):
    """Test 400 error for invalid page number."""
    doc_id = "test-doc-id-123456"
    page = 0

    response = client.get(f"/api/documents/{doc_id}/pages/{page}/structure")

    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["code"] == "INVALID_PAGE_NUMBER"


def test_get_page_structure_multiple_pages(mock_koji_client, sample_structure):
    """Test filtering structure elements by page."""
    doc_id = "test-doc-id-123456"
    page = 2

    mock_koji_client.get_page.return_value = _make_page_data(
        doc_id, page, sample_structure
    )

    response = client.get(f"/api/documents/{doc_id}/pages/{page}/structure")

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


def test_get_page_structure_bbox_validation(mock_koji_client):
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

    mock_koji_client.get_page.return_value = _make_page_data(
        doc_id, page, structure
    )

    response = client.get(f"/api/documents/{doc_id}/pages/{page}/structure")

    assert response.status_code == 200
    data = response.json()

    bbox = data["headings"][0]["bbox"]
    assert bbox["left"] == 10.5
    assert bbox["bottom"] == 20.3
    assert bbox["right"] == 100.7
    assert bbox["top"] == 50.9


def test_get_page_structure_database_error(mock_koji_client):
    """Test 500 error on database failure."""
    doc_id = "test-doc-id-123456"
    page = 1

    mock_koji_client.get_page.side_effect = Exception("Database connection failed")

    response = client.get(f"/api/documents/{doc_id}/pages/{page}/structure")

    assert response.status_code == 500
    data = response.json()
    assert data["detail"]["code"] == "DATABASE_ERROR"


def test_get_page_structure_missing_structure_data(mock_koji_client):
    """Test handling of structure field being None."""
    doc_id = "test-doc-id-123456"
    page = 1

    mock_koji_client.get_page.return_value = {
        "id": f"{doc_id}-page001",
        "doc_id": doc_id,
        "page_num": page,
        "structure": None,
    }

    response = client.get(f"/api/documents/{doc_id}/pages/{page}/structure")

    assert response.status_code == 200
    data = response.json()

    assert data["has_structure"] is False
    assert data["headings"] == []
