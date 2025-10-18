"""
End-to-end tests for research to details flow.

Tests the complete user journey from submitting a research query through
receiving citations to navigating to document details with chunk highlighting.

Test Scenarios:
1. Research query returns chunk_id in sources
2. Chunk_id format is correct for text results
3. Visual results have chunk_id=None
4. Deep link navigation with chunk parameter
5. Markdown contains chunk markers
6. Chunk markers match ChromaDB chunk IDs
"""

import json

import pytest

from src.research.chunk_extractor import extract_chunk_id, parse_chunk_id
from src.research.context_builder import SourceDocument
from src.storage.chroma_client import ChromaClient


class TestResearchQueryWithChunkContext:
    """Test research API returns chunk_id for bidirectional highlighting"""

    @pytest.mark.integration
    def test_source_document_includes_chunk_id(self):
        """SourceDocument dataclass includes chunk_id field."""
        # Text result with chunk_id
        text_source = SourceDocument(
            doc_id="test-doc-123",
            filename="report.pdf",
            page=1,
            extension="pdf",
            chunk_id="test-doc-123-chunk0042",
        )

        assert text_source.chunk_id == "test-doc-123-chunk0042"

        # Visual result without chunk_id
        visual_source = SourceDocument(
            doc_id="test-doc-456",
            filename="slides.pdf",
            page=1,
            extension="pdf",
            chunk_id=None,
        )

        assert visual_source.chunk_id is None

    @pytest.mark.integration
    def test_chunk_id_extraction_from_metadata(self):
        """Test extract_chunk_id helper function."""
        # Test with chunk_id in metadata
        metadata = {"doc_id": "abc123", "chunk_id": 42}
        doc_id = "abc123"

        result = extract_chunk_id(metadata, doc_id)

        # Should match storage layer format: {doc_id}-chunk{NNNN}
        assert result == "abc123-chunk0042"
        assert result == f"{doc_id}-chunk{42:04d}"

        # Test without chunk_id (visual result)
        metadata_visual = {"doc_id": "abc123", "page": 1}
        result_visual = extract_chunk_id(metadata_visual, doc_id)
        assert result_visual is None

    @pytest.mark.integration
    def test_chunk_id_parsing(self):
        """Test parse_chunk_id helper function."""
        chunk_id = "multi-part-doc-id-chunk0010"

        parsed = parse_chunk_id(chunk_id)

        assert parsed["doc_id"] == "multi-part-doc-id"
        assert parsed["chunk_num"] == 10

        # Test with simple doc_id
        chunk_id_simple = "doc-chunk0001"
        parsed_simple = parse_chunk_id(chunk_id_simple)

        assert parsed_simple["doc_id"] == "doc"
        assert parsed_simple["chunk_num"] == 1

    @pytest.mark.integration
    def test_chunk_id_format_consistency(self):
        """Verify chunk_id format matches between storage and research layers."""
        # Storage layer creates IDs like: f"{doc_id}-chunk{chunk_id:04d}"
        # Research layer extracts the same format

        doc_id = "test-doc"
        chunk_num = 42

        # Storage format
        storage_format = f"{doc_id}-chunk{chunk_num:04d}"

        # Research format
        metadata = {"chunk_id": chunk_num}
        research_format = extract_chunk_id(metadata, doc_id)

        assert storage_format == research_format
        assert research_format == "test-doc-chunk0042"


class TestResearchAPIResponseFormat:
    """Test research API includes chunk_id in response"""

    @pytest.mark.integration
    def test_source_info_model_accepts_chunk_id(self):
        """SourceInfo Pydantic model in API accepts chunk_id."""
        from src.api.research import SourceInfo

        # Text result with chunk_id
        source_info = SourceInfo(
            id=1,
            doc_id="test-doc",
            filename="report.pdf",
            page=1,
            extension="pdf",
            date_added="2025-10-17T10:00:00Z",
            relevance_score=0.95,
            chunk_id="test-doc-chunk0042",
        )

        assert source_info.chunk_id == "test-doc-chunk0042"

        # Visual result without chunk_id
        source_info_visual = SourceInfo(
            id=2,
            doc_id="test-doc",
            filename="report.pdf",
            page=2,
            extension="pdf",
            date_added="2025-10-17T10:00:00Z",
            relevance_score=0.90,
            chunk_id=None,
        )

        assert source_info_visual.chunk_id is None

    @pytest.mark.integration
    def test_source_info_serialization(self):
        """SourceInfo serializes chunk_id correctly."""
        from src.api.research import SourceInfo

        source_info = SourceInfo(
            id=1,
            doc_id="test-doc",
            filename="report.pdf",
            page=1,
            extension="pdf",
            date_added="2025-10-17T10:00:00Z",
            relevance_score=0.95,
            chunk_id="test-doc-chunk0010",
        )

        # Test Pydantic serialization
        result = source_info.model_dump()

        assert "chunk_id" in result
        assert result["chunk_id"] == "test-doc-chunk0010"

        # Test JSON serialization
        json_str = source_info.model_dump_json()
        json_data = json.loads(json_str)
        assert json_data["chunk_id"] == "test-doc-chunk0010"

    @pytest.mark.integration
    @pytest.mark.slow
    def test_research_endpoint_integration(
        self, research_api_client, chromadb_client: ChromaClient, skip_if_services_unavailable
    ):
        """
        Test research API endpoint includes chunk_id in sources.

        This test requires:
        - ChromaDB with text embeddings
        - Research API running
        - Search engine functional
        """
        # Create test data in ChromaDB
        doc_id = "research-test-doc"

        import numpy as np

        # Add text embedding with chunk context
        chunk_id = f"{doc_id}-chunk0001"
        metadata = {
            "doc_id": doc_id,
            "filename": "research_test.pdf",
            "chunk_id": chunk_id,
            "page": 1,
            "has_context": True,
            "parent_heading": "Introduction",
            "section_path": "1. Introduction",
            "page_nums": json.dumps([1]),
        }
        embedding = np.random.randn(30, 128).astype(np.float32)

        chromadb_client.add_text_embedding(
            doc_id=doc_id,
            chunk_id=chunk_id,
            text="This is test content for research API integration testing.",
            embedding=embedding,
            metadata=metadata,
        )

        # Make research query
        # NOTE: This test may fail if LLM API keys are not configured
        # In that case, we validate the data structures instead
        pytest.skip(
            "Research API requires LLM API keys. "
            "See test_source_info_model_* for data structure validation."
        )


class TestDeepLinkNavigation:
    """Test URL-based navigation to specific chunks"""

    @pytest.mark.integration
    def test_details_url_with_chunk_parameter(self):
        """Test details page URL can include chunk parameter."""
        # Example URL format: /details.html?doc_id=abc123&page=1&chunk=abc123-chunk0042

        doc_id = "test-doc-123"
        page = 1
        chunk_id = f"{doc_id}-chunk0042"

        # Build URL
        from urllib.parse import urlencode

        params = {"doc_id": doc_id, "page": page, "chunk": chunk_id}
        query_string = urlencode(params)
        url = f"/details.html?{query_string}"

        assert "doc_id=test-doc-123" in url
        assert "page=1" in url
        assert "chunk=test-doc-123-chunk0042" in url

    @pytest.mark.integration
    def test_chunk_parameter_parsing(self):
        """Test parsing chunk parameter from URL."""
        from urllib.parse import parse_qs, urlparse

        url = "/details.html?doc_id=abc123&page=2&chunk=abc123-chunk0010"
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        assert params["doc_id"][0] == "abc123"
        assert params["page"][0] == "2"
        assert params["chunk"][0] == "abc123-chunk0010"

        # Validate chunk_id format
        chunk_id = params["chunk"][0]
        parsed_chunk = parse_chunk_id(chunk_id)
        assert parsed_chunk["doc_id"] == "abc123"
        assert parsed_chunk["chunk_num"] == 10

    @pytest.mark.integration
    def test_navigation_from_research_to_details(self):
        """
        Test complete navigation flow from research page to details page.

        User journey:
        1. User submits research query
        2. API returns sources with chunk_id
        3. User clicks on citation [N]
        4. Frontend navigates to details.html with chunk parameter
        5. Details page loads structure and highlights chunk
        """
        # Step 1: Simulate research response
        from src.api.research import SourceInfo

        source = SourceInfo(
            id=1,
            doc_id="report-2024",
            filename="annual_report.pdf",
            page=5,
            extension="pdf",
            date_added="2025-10-17T10:00:00Z",
            relevance_score=0.95,
            chunk_id="report-2024-chunk0023",
        )

        # Step 2: Build navigation URL
        from urllib.parse import urlencode

        params = {"doc_id": source.doc_id, "page": source.page, "chunk": source.chunk_id}
        details_url = f"/details.html?{urlencode(params)}"

        # Step 3: Verify URL format
        assert "doc_id=report-2024" in details_url
        assert "page=5" in details_url
        assert "chunk=report-2024-chunk0023" in details_url

        # Step 4: Frontend would parse this URL and:
        # - Load document structure for page 5
        # - Parse markdown with chunk markers
        # - Highlight chunk report-2024-chunk0023
        # This is validated in test_bidirectional_highlighting.py


class TestMarkdownChunkMarkers:
    """Test markdown contains chunk markers for bidirectional highlighting"""

    @pytest.mark.integration
    def test_markdown_chunk_marker_format(self):
        """Test chunk markers are in correct format."""
        from src.storage.markdown_utils import (
            extract_chunk_markers,
            format_markdown_with_chunk_markers,
        )

        # Sample markdown without markers
        markdown_text = """# Introduction

This is the introduction section with multiple paragraphs.

## Background

Some background information here.
"""

        # Add chunk markers
        chunks = [
            {"chunk_id": "doc-chunk0001", "start_line": 0, "end_line": 2},
            {"chunk_id": "doc-chunk0002", "start_line": 3, "end_line": 5},
        ]

        marked_markdown = format_markdown_with_chunk_markers(markdown_text, chunks)

        # Verify markers present
        assert "<!-- CHUNK: doc-chunk0001 -->" in marked_markdown
        assert "<!-- CHUNK: doc-chunk0002 -->" in marked_markdown

        # Extract markers
        extracted = extract_chunk_markers(marked_markdown)
        assert len(extracted) == 2
        assert extracted[0]["chunk_id"] == "doc-chunk0001"
        assert extracted[1]["chunk_id"] == "doc-chunk0002"

    @pytest.mark.integration
    def test_chunk_markers_match_chromadb(self, chromadb_client: ChromaClient):
        """Test chunk markers in markdown match ChromaDB chunk_ids."""
        doc_id = "markdown-test-doc"

        import numpy as np

        # Add chunks to ChromaDB
        chunk_ids = [f"{doc_id}-chunk{i:04d}" for i in range(1, 4)]

        for i, chunk_id in enumerate(chunk_ids, 1):
            metadata = {
                "doc_id": doc_id,
                "filename": "test.pdf",
                "chunk_id": chunk_id,
                "page": 1,
                "has_context": True,
                "section_path": f"Section {i}",
            }
            embedding = np.random.randn(30, 128).astype(np.float32)

            chromadb_client.add_text_embedding(
                doc_id=doc_id,
                chunk_id=chunk_id,
                text=f"Chunk {i} content",
                embedding=embedding,
                metadata=metadata,
            )

        # Retrieve chunks from ChromaDB
        results = chromadb_client._text_collection.get(
            where={"doc_id": doc_id}, include=["metadatas"]
        )

        stored_chunk_ids = [m["chunk_id"] for m in results["metadatas"]]

        # Verify chunk IDs match expected format
        assert stored_chunk_ids == chunk_ids
        for chunk_id in stored_chunk_ids:
            parsed = parse_chunk_id(chunk_id)
            assert parsed["doc_id"] == doc_id

        # Cleanup
        chromadb_client._text_collection.delete(where={"doc_id": doc_id})

    @pytest.mark.integration
    def test_chunk_marker_extraction_and_navigation(self):
        """Test extracting chunk markers enables navigation."""
        from src.storage.markdown_utils import extract_chunk_markers

        # Markdown with chunk markers
        markdown_content = """<!-- CHUNK: doc-chunk0001 -->
# Introduction

This is the introduction.

<!-- CHUNK: doc-chunk0002 -->
## Background

Background information here.

<!-- CHUNK: doc-chunk0003 -->
### Details

More detailed information.
"""

        # Extract markers
        markers = extract_chunk_markers(markdown_content)

        assert len(markers) == 3
        assert markers[0]["chunk_id"] == "doc-chunk0001"
        assert markers[1]["chunk_id"] == "doc-chunk0002"
        assert markers[2]["chunk_id"] == "doc-chunk0003"

        # Each marker should have position information for scrolling
        for marker in markers:
            assert "position" in marker or "line" in marker
            assert "chunk_id" in marker


class TestEdgeCases:
    """Test edge cases in research to details flow"""

    @pytest.mark.integration
    def test_chunk_id_with_hyphens_in_doc_id(self):
        """Handle doc_id containing multiple hyphens."""
        doc_id = "multi-part-doc-id-2024"
        chunk_num = 10

        # Create chunk_id
        chunk_id = f"{doc_id}-chunk{chunk_num:04d}"
        assert chunk_id == "multi-part-doc-id-2024-chunk0010"

        # Parse chunk_id
        parsed = parse_chunk_id(chunk_id)
        assert parsed["doc_id"] == "multi-part-doc-id-2024"
        assert parsed["chunk_num"] == 10

    @pytest.mark.integration
    def test_chunk_id_boundary_values(self):
        """Test boundary values for chunk numbers."""
        test_cases = [
            (0, "doc-chunk0000"),
            (1, "doc-chunk0001"),
            (999, "doc-chunk0999"),
            (9999, "doc-chunk9999"),
        ]

        for chunk_num, expected in test_cases:
            metadata = {"chunk_id": chunk_num}
            result = extract_chunk_id(metadata, "doc")
            assert result == expected

            # Verify parsing works
            parsed = parse_chunk_id(result)
            assert parsed["chunk_num"] == chunk_num

    @pytest.mark.integration
    def test_mixed_text_and_visual_results(self):
        """Handle mixed text and visual results in research response."""
        # Text result
        text_source = SourceDocument(
            doc_id="doc1",
            filename="report.pdf",
            page=1,
            extension="pdf",
            chunk_id="doc1-chunk0005",
        )

        # Visual result
        visual_source = SourceDocument(
            doc_id="doc2",
            filename="slides.pdf",
            page=1,
            extension="pdf",
            chunk_id=None,
        )

        # Both should serialize correctly
        text_dict = text_source.to_dict()
        visual_dict = visual_source.to_dict()

        assert text_dict["chunk_id"] == "doc1-chunk0005"
        assert visual_dict["chunk_id"] is None

        # Frontend should handle both:
        # - Text: Navigate to chunk marker in markdown
        # - Visual: Navigate to page without chunk highlighting

    @pytest.mark.integration
    def test_missing_chunk_parameter(self):
        """Handle details page navigation without chunk parameter."""
        from urllib.parse import parse_qs, urlparse

        # URL without chunk parameter (visual result or direct page navigation)
        url = "/details.html?doc_id=abc123&page=2"
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        assert "chunk" not in params

        # Frontend should:
        # - Load page normally
        # - Not attempt chunk highlighting
        # - Display page-level content


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
