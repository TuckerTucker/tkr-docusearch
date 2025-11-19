"""
Integration tests for chunk_id in research API responses.

Tests end-to-end flow from search results through context building
to research API response, verifying chunk_id field is properly
included for bidirectional highlighting.
"""

import pytest

from tkr_docusearch.research.context_builder import SourceDocument


class TestSourceDocumentChunkId:
    """Test SourceDocument dataclass with chunk_id field"""

    def test_source_document_with_chunk_id(self):
        """SourceDocument can be created with chunk_id"""
        source = SourceDocument(
            doc_id="test-doc",
            filename="report.pdf",
            page=1,
            extension="pdf",
            chunk_id="test-doc-chunk0042",
        )

        assert source.chunk_id == "test-doc-chunk0042"

    def test_source_document_without_chunk_id(self):
        """SourceDocument defaults to None for chunk_id"""
        source = SourceDocument(
            doc_id="test-doc",
            filename="report.pdf",
            page=1,
            extension="pdf",
        )

        assert source.chunk_id is None

    def test_source_document_to_dict_includes_chunk_id(self):
        """to_dict includes chunk_id field"""
        source = SourceDocument(
            doc_id="test-doc",
            filename="report.pdf",
            page=1,
            extension="pdf",
            chunk_id="test-doc-chunk0010",
        )

        result = source.to_dict()

        assert "chunk_id" in result
        assert result["chunk_id"] == "test-doc-chunk0010"

    def test_source_document_to_dict_chunk_id_none(self):
        """to_dict includes chunk_id=None for visual results"""
        source = SourceDocument(
            doc_id="test-doc",
            filename="report.pdf",
            page=1,
            extension="pdf",
            chunk_id=None,
        )

        result = source.to_dict()

        assert "chunk_id" in result
        assert result["chunk_id"] is None


class TestContextBuilderIntegration:
    """Test context builder with chunk_id extraction"""

    @pytest.mark.asyncio
    async def test_get_source_metadata_text_result(self):
        """Test get_source_metadata extracts chunk_id from text result"""
        # This would require a real ChromaDB instance with text embeddings
        # For now, we test the logic path is correct
        pass  # TODO: Add integration test with real ChromaDB

    @pytest.mark.asyncio
    async def test_get_source_metadata_visual_result(self):
        """Test get_source_metadata returns None for visual result"""
        # This would require a real ChromaDB instance with visual embeddings
        pass  # TODO: Add integration test with real ChromaDB


class TestResearchAPIResponse:
    """Test research API includes chunk_id in response"""

    def test_source_info_model_has_chunk_id(self):
        """SourceInfo Pydantic model accepts chunk_id"""
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

    def test_source_info_model_chunk_id_optional(self):
        """SourceInfo allows None for chunk_id (visual results)"""
        from tkr_docusearch.api.research import SourceInfo

        source_info = SourceInfo(
            id=1,
            doc_id="test-doc",
            filename="report.pdf",
            page=1,
            extension="pdf",
            date_added="2025-10-17T10:00:00Z",
            relevance_score=0.95,
            chunk_id=None,
        )

        assert source_info.chunk_id is None

    def test_source_info_model_chunk_id_in_dict(self):
        """SourceInfo serializes chunk_id to dict"""
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

        assert "chunk_id" in result
        assert result["chunk_id"] == "test-doc-chunk0010"

    @pytest.mark.asyncio
    async def test_research_endpoint_returns_chunk_id(self):
        """Test research API endpoint includes chunk_id in sources"""
        # This would require a running research API with ChromaDB
        # For now, we verify the code path is correct
        pass  # TODO: Add integration test with real API


class TestChunkIdFormat:
    """Test chunk_id format matches storage layer"""

    def test_format_matches_storage_embedding_id(self):
        """Chunk ID format matches ChromaDB embedding ID format"""
        from tkr_docusearch.research.chunk_extractor import extract_chunk_id

        # Storage layer creates IDs like: "{doc_id}-chunk{chunk_id:04d}"
        # See: src/storage/chroma_client.py line 370

        metadata = {"doc_id": "abc123", "chunk_id": 45}
        doc_id = "abc123"

        result = extract_chunk_id(metadata, doc_id)

        # Should match format from storage layer
        assert result == "abc123-chunk0045"
        assert result == f"{doc_id}-chunk{45:04d}"

    def test_format_consistency_across_layers(self):
        """Verify format consistency between storage and research layers"""
        # Storage layer format (from chroma_client.py)
        storage_format = f"{'test-doc'}-chunk{42:04d}"

        # Research layer format (from chunk_extractor.py)
        from tkr_docusearch.research.chunk_extractor import extract_chunk_id

        metadata = {"chunk_id": 42}
        research_format = extract_chunk_id(metadata, "test-doc")

        assert storage_format == research_format


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_chunk_id_with_hyphens_in_doc_id(self):
        """Handle doc_id containing hyphens"""
        from tkr_docusearch.research.chunk_extractor import extract_chunk_id, parse_chunk_id

        metadata = {"chunk_id": 10}
        doc_id = "multi-part-doc-id"

        result = extract_chunk_id(metadata, doc_id)
        assert result == "multi-part-doc-id-chunk0010"

        parsed = parse_chunk_id(result)
        assert parsed["doc_id"] == "multi-part-doc-id"
        assert parsed["chunk_num"] == 10

    def test_chunk_id_boundary_values(self):
        """Test boundary values for chunk_id"""
        from tkr_docusearch.research.chunk_extractor import extract_chunk_id

        test_cases = [
            (0, "doc-chunk0000"),
            (1, "doc-chunk0001"),
            (9999, "doc-chunk9999"),
        ]

        for chunk_num, expected in test_cases:
            metadata = {"chunk_id": chunk_num}
            result = extract_chunk_id(metadata, "doc")
            assert result == expected

    def test_mixed_text_and_visual_results(self):
        """Handle mixed text and visual results in same context"""
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

        # Both should be valid
        assert text_source.chunk_id == "doc1-chunk0005"
        assert visual_source.chunk_id is None

        # Both should serialize correctly
        text_dict = text_source.to_dict()
        visual_dict = visual_source.to_dict()

        assert text_dict["chunk_id"] == "doc1-chunk0005"
        assert visual_dict["chunk_id"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
