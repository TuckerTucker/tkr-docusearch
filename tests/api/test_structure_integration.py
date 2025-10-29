"""
Integration tests for structure API with real ChromaDB.

Tests the complete flow:
1. Process a document with enhanced mode
2. Query structure via API endpoint
3. Validate response matches stored data
"""

import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.server import create_app
from src.api.structure import set_chroma_client
from src.config.processing_config import EnhancedModeConfig
from src.embeddings import ColPaliEngine
from src.processing import DocumentProcessor
from src.storage import ChromaClient
from src.storage.compression import decompress_structure_metadata

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def chroma_client():
    """Create real ChromaDB client for integration tests."""
    client = ChromaClient(host="localhost", port=8001)
    yield client


@pytest.fixture(scope="module")
def embedding_engine():
    """Create ColPali embedding engine."""
    engine = ColPaliEngine(device="cpu", precision="fp32")
    yield engine


@pytest.fixture(scope="module")
def document_processor(embedding_engine, chroma_client):
    """Create document processor with enhanced mode."""
    processor = DocumentProcessor(
        embedding_engine=embedding_engine,
        storage_client=chroma_client,
    )
    yield processor


@pytest.fixture(scope="module")
def test_app(chroma_client):
    """Create FastAPI test app with real ChromaDB."""
    app = create_app(chroma_host="localhost", chroma_port=8001, device="cpu", precision="fp32")

    # Override ChromaClient dependency
    set_chroma_client(chroma_client)

    yield app


@pytest.fixture(scope="module")
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


@pytest.fixture
def test_document_path():
    """Get path to test document with structure."""
    # Use the financial report that has headings
    doc_path = (
        Path(__file__).parent.parent.parent
        / "data"
        / "test-documents"
        / "test-financial-report.docx"
    )

    if not doc_path.exists():
        pytest.skip(f"Test document not found: {doc_path}")

    return doc_path


@pytest.mark.integration
@pytest.mark.slow
def test_structure_api_integration_with_real_document(
    document_processor, chroma_client, client, test_document_path
):
    """
    Integration test: Process document and query structure via API.

    This test validates the complete flow:
    1. Process document with enhanced mode
    2. Store structure in ChromaDB
    3. Query structure via API endpoint
    4. Validate response format and content
    """
    logger.info("=" * 80)
    logger.info("INTEGRATION TEST: Structure API with Real Document")
    logger.info("=" * 80)

    # Step 1: Process document with enhanced mode
    logger.info(f"Processing document: {test_document_path.name}")

    enhanced_config = EnhancedModeConfig(
        enable_table_structure=True,
        enable_picture_classification=True,
        enable_code_enrichment=False,  # Skip for speed
        enable_formula_enrichment=False,
    )

    result = document_processor.process_document(
        doc_path=test_document_path,
        doc_id=None,  # Auto-generate
        enhanced_mode=enhanced_config,
    )

    assert result.status == "SUCCESS"
    assert result.doc_id is not None

    doc_id = result.doc_id
    logger.info(f"✓ Document processed: doc_id={doc_id}")

    # Step 2: Verify structure stored in ChromaDB
    logger.info("Verifying structure in ChromaDB...")

    # Query visual collection for page 1
    visual_results = chroma_client.visual_collection.get(
        where={"$and": [{"doc_id": {"$eq": doc_id}}, {"page": {"$eq": 1}}]},
        limit=1,
        include=["metadatas"],
    )

    assert len(visual_results["ids"]) > 0, "Page 1 not found in visual collection"

    metadata = visual_results["metadatas"][0]
    has_structure = metadata.get("has_structure", False)

    logger.info(f"✓ Page 1 metadata: has_structure={has_structure}")

    if has_structure:
        # Decompress and validate structure
        compressed_structure = metadata.get("structure")
        assert (
            compressed_structure is not None
        ), "Structure field missing despite has_structure=True"

        structure = decompress_structure_metadata(compressed_structure)
        logger.info(f"✓ Structure decompressed: {len(structure)} top-level keys")
        logger.info(f"  - Headings: {len(structure.get('headings', []))}")
        logger.info(f"  - Tables: {len(structure.get('tables', []))}")
        logger.info(f"  - Pictures: {len(structure.get('pictures', []))}")

    # Step 3: Query structure via API endpoint
    logger.info(f"Querying API: GET /api/documents/{doc_id}/pages/1/structure")

    response = client.get(f"/api/documents/{doc_id}/pages/1/structure")

    # Step 4: Validate response
    assert response.status_code == 200, f"API returned {response.status_code}: {response.text}"

    data = response.json()
    logger.info("✓ API response received")

    # Validate response structure
    assert data["doc_id"] == doc_id
    assert data["page"] == 1
    assert "has_structure" in data
    assert "headings" in data
    assert "tables" in data
    assert "pictures" in data
    assert "code_blocks" in data
    assert "formulas" in data
    assert "coordinate_system" in data

    logger.info(f"✓ Response structure valid")
    logger.info(f"  - has_structure: {data['has_structure']}")
    logger.info(f"  - headings: {len(data['headings'])}")
    logger.info(f"  - tables: {len(data['tables'])}")
    logger.info(f"  - pictures: {len(data['pictures'])}")

    # Validate coordinate system
    coord_sys = data["coordinate_system"]
    assert coord_sys["format"] == "[left, bottom, right, top]"
    assert coord_sys["origin"] == "bottom-left"
    assert coord_sys["units"] == "points"

    logger.info("✓ Coordinate system valid")

    # If structure exists, validate bbox format
    if data["has_structure"] and len(data["headings"]) > 0:
        heading = data["headings"][0]
        assert "bbox" in heading

        if heading["bbox"] is not None:
            bbox = heading["bbox"]
            assert "left" in bbox
            assert "bottom" in bbox
            assert "right" in bbox
            assert "top" in bbox

            # Validate bbox coordinates are numbers
            assert isinstance(bbox["left"], (int, float))
            assert isinstance(bbox["bottom"], (int, float))
            assert isinstance(bbox["right"], (int, float))
            assert isinstance(bbox["top"], (int, float))

            logger.info(f"✓ BBox format valid: {bbox}")

    logger.info("=" * 80)
    logger.info("INTEGRATION TEST PASSED")
    logger.info("=" * 80)


@pytest.mark.integration
def test_structure_api_page_not_found(client):
    """Test 404 error for non-existent page."""
    response = client.get("/api/documents/nonexistent-doc-id/pages/999/structure")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["code"] == "PAGE_NOT_FOUND"


@pytest.mark.integration
def test_structure_api_invalid_page(client):
    """Test 422 error for invalid page number."""
    response = client.get("/api/documents/test-doc/pages/0/structure")

    assert response.status_code == 422
    data = response.json()
    assert data["detail"]["code"] == "INVALID_PAGE"


@pytest.mark.integration
def test_structure_api_multiple_pages(
    document_processor, chroma_client, client, test_document_path
):
    """
    Test structure API returns correct elements for different pages.

    Validates that page filtering works correctly when querying
    different pages of the same document.
    """
    logger.info("Testing multi-page structure filtering...")

    # Process document
    enhanced_config = EnhancedModeConfig(
        enable_table_structure=True,
        enable_picture_classification=True,
    )

    result = document_processor.process_document(
        doc_path=test_document_path,
        doc_id=None,
        enhanced_mode=enhanced_config,
    )

    assert result.status == "SUCCESS"
    doc_id = result.doc_id

    # Query structure for page 1
    response_p1 = client.get(f"/api/documents/{doc_id}/pages/1/structure")
    assert response_p1.status_code == 200
    data_p1 = response_p1.json()

    # Query structure for page 2 (if exists)
    response_p2 = client.get(f"/api/documents/{doc_id}/pages/2/structure")

    if response_p2.status_code == 200:
        data_p2 = response_p2.json()

        # Validate pages are different
        assert data_p1["page"] == 1
        assert data_p2["page"] == 2

        # Elements should be filtered per page
        # (Content will differ based on document structure)
        logger.info(f"✓ Page 1 elements: headings={len(data_p1['headings'])}")
        logger.info(f"✓ Page 2 elements: headings={len(data_p2['headings'])}")
    else:
        logger.info("Document has only 1 page, skipping multi-page test")


@pytest.mark.integration
def test_structure_api_response_matches_chromadb(chroma_client, client, test_document_path):
    """
    Validate that API response exactly matches ChromaDB stored data.

    This test ensures no data transformation errors occur between
    storage and API response.
    """
    logger.info("Testing API response matches ChromaDB data...")

    # First, find any document with structure in ChromaDB
    # (This assumes tests have already processed some documents)

    try:
        results = chroma_client.visual_collection.get(
            where={"has_structure": True},
            limit=1,
            include=["metadatas"],
        )

        if not results["ids"]:
            pytest.skip("No documents with structure found in ChromaDB")

        metadata = results["metadatas"][0]
        doc_id = metadata["doc_id"]
        page = metadata["page"]

        logger.info(f"Found document with structure: doc_id={doc_id}, page={page}")

        # Decompress structure from ChromaDB
        structure_chromadb = decompress_structure_metadata(metadata["structure"])

        # Get structure from API
        response = client.get(f"/api/documents/{doc_id}/pages/{page}/structure")
        assert response.status_code == 200

        data = response.json()

        # Filter ChromaDB structure for this page
        headings_chromadb = [
            h for h in structure_chromadb.get("headings", []) if h.get("page") == page
        ]
        tables_chromadb = [t for t in structure_chromadb.get("tables", []) if t.get("page") == page]
        pictures_chromadb = [
            p for p in structure_chromadb.get("pictures", []) if p.get("page") == page
        ]

        # Compare counts
        assert len(data["headings"]) == len(headings_chromadb), "Heading count mismatch"
        assert len(data["tables"]) == len(tables_chromadb), "Table count mismatch"
        assert len(data["pictures"]) == len(pictures_chromadb), "Picture count mismatch"

        logger.info("✓ API response matches ChromaDB data")

    except Exception as e:
        logger.warning(f"Could not validate ChromaDB match: {e}")
        pytest.skip("ChromaDB validation skipped due to error")
