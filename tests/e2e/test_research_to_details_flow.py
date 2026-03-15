"""
End-to-end tests for research to details flow.

Tests the complete user journey from submitting a research query through
receiving citations to navigating to document details with chunk highlighting.

Storage-independent tests are preserved; ChromaDB-dependent tests are skipped
pending Koji migration.
"""

import json

import pytest

from tkr_docusearch.research.chunk_extractor import extract_chunk_id, parse_chunk_id
from tkr_docusearch.research.context_builder import SourceDocument


class TestResearchQueryWithChunkContext:
    """Test research API returns chunk_id for bidirectional highlighting."""

    @pytest.mark.integration
    def test_source_document_includes_chunk_id(self):
        """SourceDocument dataclass includes chunk_id field."""
        text_source = SourceDocument(
            doc_id="test-doc-123",
            filename="report.pdf",
            page=1,
            extension="pdf",
            chunk_id="test-doc-123-chunk0042",
        )
        assert text_source.chunk_id == "test-doc-123-chunk0042"

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
        metadata = {"doc_id": "abc123", "chunk_id": 42}
        doc_id = "abc123"

        result = extract_chunk_id(metadata, doc_id)
        assert result == "abc123-chunk0042"

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

    @pytest.mark.integration
    def test_chunk_id_format_consistency(self):
        """Verify chunk_id format matches between storage and research layers."""
        doc_id = "test-doc"
        chunk_num = 42

        storage_format = f"{doc_id}-chunk{chunk_num:04d}"
        metadata = {"chunk_id": chunk_num}
        research_format = extract_chunk_id(metadata, doc_id)

        assert storage_format == research_format
        assert research_format == "test-doc-chunk0042"


class TestResearchAPIResponseFormat:
    """Test research API includes chunk_id in response."""

    @pytest.mark.integration
    def test_source_info_model_accepts_chunk_id(self):
        """SourceInfo Pydantic model in API accepts chunk_id."""
        from tkr_docusearch.api.research import SourceInfo

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

    @pytest.mark.integration
    def test_source_info_serialization(self):
        """SourceInfo serializes chunk_id correctly."""
        from tkr_docusearch.api.research import SourceInfo

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

        result = source_info.model_dump()
        assert result["chunk_id"] == "test-doc-chunk0010"

        json_data = json.loads(source_info.model_dump_json())
        assert json_data["chunk_id"] == "test-doc-chunk0010"

    @pytest.mark.skip(reason="Requires live LLM API keys and Koji storage")
    def test_research_endpoint_integration(self):
        pass


class TestDeepLinkNavigation:
    """Test URL-based navigation to specific chunks."""

    @pytest.mark.integration
    def test_details_url_with_chunk_parameter(self):
        """Test details page URL can include chunk parameter."""
        from urllib.parse import urlencode

        doc_id = "test-doc-123"
        page = 1
        chunk_id = f"{doc_id}-chunk0042"

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

        chunk_id = params["chunk"][0]
        parsed_chunk = parse_chunk_id(chunk_id)
        assert parsed_chunk["doc_id"] == "abc123"
        assert parsed_chunk["chunk_num"] == 10

    @pytest.mark.integration
    def test_navigation_from_research_to_details(self):
        """Test complete navigation flow from research page to details page."""
        from urllib.parse import urlencode

        from tkr_docusearch.api.research import SourceInfo

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

        params = {"doc_id": source.doc_id, "page": source.page, "chunk": source.chunk_id}
        details_url = f"/details.html?{urlencode(params)}"

        assert "doc_id=report-2024" in details_url
        assert "page=5" in details_url
        assert "chunk=report-2024-chunk0023" in details_url


@pytest.mark.skip(reason="Requires migration to Koji storage backend")
class TestMarkdownChunkMarkers:
    """Test markdown contains chunk markers for bidirectional highlighting."""

    def test_markdown_chunk_marker_format(self):
        pass

    def test_chunk_markers_match_storage(self):
        pass

    def test_chunk_marker_extraction_and_navigation(self):
        pass


class TestEdgeCases:
    """Test edge cases in research to details flow."""

    @pytest.mark.integration
    def test_chunk_id_with_hyphens_in_doc_id(self):
        """Handle doc_id containing multiple hyphens."""
        doc_id = "multi-part-doc-id-2024"
        chunk_num = 10
        chunk_id = f"{doc_id}-chunk{chunk_num:04d}"
        assert chunk_id == "multi-part-doc-id-2024-chunk0010"

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

            parsed = parse_chunk_id(result)
            assert parsed["chunk_num"] == chunk_num

    @pytest.mark.integration
    def test_mixed_text_and_visual_results(self):
        """Handle mixed text and visual results in research response."""
        text_source = SourceDocument(
            doc_id="doc1",
            filename="report.pdf",
            page=1,
            extension="pdf",
            chunk_id="doc1-chunk0005",
        )

        visual_source = SourceDocument(
            doc_id="doc2",
            filename="slides.pdf",
            page=1,
            extension="pdf",
            chunk_id=None,
        )

        text_dict = text_source.to_dict()
        visual_dict = visual_source.to_dict()

        assert text_dict["chunk_id"] == "doc1-chunk0005"
        assert visual_dict["chunk_id"] is None

    @pytest.mark.integration
    def test_missing_chunk_parameter(self):
        """Handle details page navigation without chunk parameter."""
        from urllib.parse import parse_qs, urlparse

        url = "/details.html?doc_id=abc123&page=2"
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        assert "chunk" not in params


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
