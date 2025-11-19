"""
Integration tests for enhanced metadata storage.

Tests the full pipeline of processing a document with enhanced mode enabled,
storing enhanced metadata in ChromaDB, and validating the stored data.
"""

import json
from unittest.mock import Mock

import numpy as np
import pytest

from tkr_docusearch.processing.handlers.enhanced_metadata import (
    prepare_enhanced_text_metadata,
    prepare_enhanced_visual_metadata,
)
from tkr_docusearch.storage.compression import decompress_structure_metadata
from tkr_docusearch.storage.metadata_schema import (
    ChunkContext,
    DocumentStructure,
    HeadingInfo,
    HeadingLevel,
    TableInfo,
)


class TestEnhancedVisualMetadataStorage:
    """Test enhanced visual metadata storage."""

    def test_prepare_visual_metadata_with_structure(self):
        """Test preparing visual metadata with DocumentStructure."""
        # Create a sample structure
        structure = DocumentStructure(
            headings=[
                HeadingInfo(
                    text="Introduction",
                    level=HeadingLevel.SECTION_HEADER,
                    page_num=1,
                    bbox=(100.0, 200.0, 400.0, 250.0),
                    section_path="1. Introduction",
                )
            ],
            tables=[
                TableInfo(
                    page_num=1,
                    caption="Results Summary",
                    num_rows=10,
                    num_cols=5,
                    has_header=True,
                    table_id="table-0",
                    bbox=(150.0, 300.0, 500.0, 600.0),
                )
            ],
        )
        structure.total_sections = 1
        structure.max_heading_depth = 1

        # Base metadata
        base_metadata = {
            "filename": "test_report.pdf",
            "page": 1,
            "source_path": "/data/uploads/test_report.pdf",
            "doc_id": "abc123",
        }

        # Prepare enhanced metadata
        enhanced = prepare_enhanced_visual_metadata(
            base_metadata, structure, image_width=1700, image_height=2200
        )

        # Validate enhanced fields
        assert enhanced["has_structure"] is True
        assert enhanced["num_headings"] == 1
        assert enhanced["num_tables"] == 1
        assert enhanced["num_pictures"] == 0
        assert enhanced["max_heading_depth"] == 1
        assert enhanced["image_width"] == 1700
        assert enhanced["image_height"] == 2200
        assert "structure" in enhanced

        # Validate compressed structure can be decompressed
        decompressed = decompress_structure_metadata(enhanced["structure"])
        assert "headings" in decompressed
        assert len(decompressed["headings"]) == 1
        assert decompressed["headings"][0]["text"] == "Introduction"
        assert "tables" in decompressed
        assert len(decompressed["tables"]) == 1
        assert decompressed["tables"][0]["caption"] == "Results Summary"

    def test_prepare_visual_metadata_without_structure(self):
        """Test preparing visual metadata without structure (base mode)."""
        base_metadata = {
            "filename": "test_report.pdf",
            "page": 1,
            "source_path": "/data/uploads/test_report.pdf",
            "doc_id": "abc123",
        }

        # Prepare metadata without structure
        enhanced = prepare_enhanced_visual_metadata(base_metadata, None, None, None)

        # Should have has_structure=False
        assert enhanced["has_structure"] is False
        assert "structure" not in enhanced
        assert "num_headings" not in enhanced

    def test_prepare_visual_metadata_with_invalid_structure(self):
        """Test that invalid structure falls back to base mode."""
        # Create an invalid structure (invalid page numbers)
        structure = DocumentStructure(
            headings=[
                HeadingInfo(
                    text="Invalid",
                    level=HeadingLevel.SECTION_HEADER,
                    page_num=0,  # Invalid: page_num must be > 0
                    section_path="Invalid",
                )
            ]
        )

        base_metadata = {"filename": "test.pdf", "page": 1, "doc_id": "abc123"}

        # Should fall back to base mode due to validation failure
        enhanced = prepare_enhanced_visual_metadata(base_metadata, structure, None, None)
        assert enhanced["has_structure"] is False


class TestEnhancedTextMetadataStorage:
    """Test enhanced text metadata storage."""

    def test_prepare_text_metadata_with_context(self):
        """Test preparing text metadata with ChunkContext."""
        # Create chunk context
        context = ChunkContext(
            parent_heading="Introduction",
            parent_heading_level=1,
            section_path="Report > Introduction",
            element_type="text",
            related_tables=["table-0", "table-1"],
            related_pictures=["picture-0"],
            page_nums=[1, 2],
            is_page_boundary=True,
        )

        # Base metadata
        base_metadata = {
            "filename": "test_report.pdf",
            "chunk_id": "abc123-chunk0001",
            "page": 1,
            "text_preview": "In Q4 2024, our company...",
            "full_text": "In Q4 2024, our company achieved record growth...",
            "word_count": 50,
            "source_path": "/data/uploads/test_report.pdf",
            "doc_id": "abc123",
        }

        # Prepare enhanced metadata
        enhanced = prepare_enhanced_text_metadata(base_metadata, context)

        # Validate enhanced fields
        assert enhanced["has_context"] is True
        assert enhanced["parent_heading"] == "Introduction"
        assert enhanced["parent_heading_level"] == 1
        assert enhanced["section_path"] == "Report > Introduction"
        assert enhanced["element_type"] == "text"
        assert enhanced["is_page_boundary"] is True

        # Validate JSON-encoded arrays
        related_tables = json.loads(enhanced["related_tables"])
        assert related_tables == ["table-0", "table-1"]

        related_pictures = json.loads(enhanced["related_pictures"])
        assert related_pictures == ["picture-0"]

        page_nums = json.loads(enhanced["page_nums"])
        assert page_nums == [1, 2]

    def test_prepare_text_metadata_without_context(self):
        """Test preparing text metadata without context (base mode)."""
        base_metadata = {
            "filename": "test_report.pdf",
            "chunk_id": "abc123-chunk0001",
            "page": 1,
            "text_preview": "Some text...",
            "full_text": "Some text content",
            "word_count": 3,
            "doc_id": "abc123",
        }

        # Prepare metadata without context
        enhanced = prepare_enhanced_text_metadata(base_metadata, None)

        # Should have has_context=False
        assert enhanced["has_context"] is False
        assert "parent_heading" not in enhanced
        assert "section_path" not in enhanced

    def test_prepare_text_metadata_with_minimal_context(self):
        """Test preparing text metadata with minimal context."""
        # Create minimal context (only section path)
        context = ChunkContext(
            section_path="Introduction",
            element_type="text",
            page_nums=[1],
        )

        base_metadata = {
            "filename": "test.pdf",
            "chunk_id": "abc-001",
            "page": 1,
            "text_preview": "Text...",
            "full_text": "Text",
            "word_count": 1,
            "doc_id": "abc",
        }

        # Prepare enhanced metadata
        enhanced = prepare_enhanced_text_metadata(base_metadata, context)

        # Validate
        assert enhanced["has_context"] is True
        assert enhanced["section_path"] == "Introduction"
        # parent_heading is None, so sanitize_metadata_for_chroma filters it out
        assert "parent_heading" not in enhanced
        assert enhanced["element_type"] == "text"

        # Arrays should be JSON strings
        page_nums = json.loads(enhanced["page_nums"])
        assert page_nums == [1]


class TestEnhancedStorageIntegration:
    """Integration tests for the full enhanced storage pipeline."""

    @pytest.fixture
    def mock_storage_client(self):
        """Create a mock ChromaDB storage client."""
        client = Mock()
        client.visual_collection = Mock()
        client.text_collection = Mock()
        return client

    def test_visual_handler_enhanced_mode(self, mock_storage_client):
        """Test visual embedding handler with enhanced mode enabled."""
        from tkr_docusearch.processing.handlers.visual_embedding_handler import VisualEmbeddingHandler

        # Create handler with enhanced mode enabled
        handler = VisualEmbeddingHandler(
            storage_client=mock_storage_client, enhanced_mode_config={"enabled": True}
        )

        # Create sample structure
        structure = DocumentStructure(
            headings=[HeadingInfo(text="Title", level=HeadingLevel.TITLE, page_num=1)]
        )

        # Create sample visual results
        visual_result = Mock()
        visual_result.doc_id = "test-doc"
        visual_result.page_num = 1
        visual_result.embedding = np.random.randn(1031, 128).astype(np.float32)

        # Create sample page with dimensions
        page = Mock()
        page.page_num = 1
        page.image_path = "/data/page_images/test-doc/page001.png"
        page.thumb_path = "/data/page_images/test-doc/page001_thumb.jpg"
        page.width = 1700
        page.height = 2200

        # Mock storage client add_visual_embedding
        mock_storage_client.add_visual_embedding = Mock(return_value="test-embedding-id")

        # Store visual embeddings
        visual_ids, total_size = handler.store_visual_embeddings(
            visual_results=[visual_result],
            filename="test.pdf",
            file_path="/data/uploads/test.pdf",
            safe_doc_metadata={"format": "pdf", "mimetype": "application/pdf"},
            structure=structure,
            pages=[page],
        )

        # Validate storage was called
        assert len(visual_ids) == 1
        assert visual_ids[0] == "test-embedding-id"

        # Check that metadata was enhanced
        call_args = mock_storage_client.add_visual_embedding.call_args
        metadata = call_args[1]["metadata"]
        assert "has_structure" in metadata
        assert metadata["has_structure"] is True

    def test_text_handler_enhanced_mode(self, mock_storage_client):
        """Test text embedding handler with enhanced mode enabled."""
        from tkr_docusearch.processing.handlers.text_embedding_handler import TextEmbeddingHandler

        # Create handler with enhanced mode enabled
        handler = TextEmbeddingHandler(
            storage_client=mock_storage_client, enhanced_mode_config={"enabled": True}
        )

        # Create sample chunk with context
        chunk = Mock()
        chunk.chunk_id = "test-doc-chunk001"
        chunk.page_num = 1
        chunk.text = "Sample text content for testing"
        chunk.context = ChunkContext(
            parent_heading="Introduction",
            section_path="Report > Introduction",
            element_type="text",
            page_nums=[1],
        )

        # Create sample text result
        text_result = Mock()
        text_result.doc_id = "test-doc"
        text_result.chunk_id = "test-doc-chunk001"
        text_result.page_num = 1
        text_result.text = "Sample text content for testing"
        text_result.embedding = np.random.randn(30, 128).astype(np.float32)

        # Mock storage client add_text_embedding
        mock_storage_client.add_text_embedding = Mock(return_value="test-embedding-id")

        # Store text embeddings
        text_ids, total_size = handler.store_text_embeddings(
            text_results=[text_result],
            text_chunks=[chunk],
            filename="test.pdf",
            file_path="/data/uploads/test.pdf",
            safe_doc_metadata={"format": "pdf", "mimetype": "application/pdf"},
        )

        # Validate storage was called
        assert len(text_ids) == 1
        assert text_ids[0] == "test-embedding-id"

        # Check that metadata was enhanced
        call_args = mock_storage_client.add_text_embedding.call_args
        metadata = call_args[1]["metadata"]
        assert "has_context" in metadata
        assert metadata["has_context"] is True
        assert metadata["parent_heading"] == "Introduction"
        assert metadata["section_path"] == "Report > Introduction"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
