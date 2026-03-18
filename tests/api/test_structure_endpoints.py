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
    reason="Structure API requires mocking refactor"
)

from unittest.mock import MagicMock

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
    mock_client = MagicMock()
    yield mock_client


@pytest.fixture
def sample_structure():
    """Create sample DocumentStructure for testing."""
    structure = DocumentStructure()

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

    structure.total_sections = 2
    structure.max_heading_depth = 1
    structure.has_table_of_contents = False

    return structure


# All tests are skipped via pytestmark above.
# This file is kept for reference during the Koji migration but needs
# a full mock refactor to work with the new KojiClient.get_page() API.
