"""
Integration tests for page-to-chunk mapping functionality.

Tests that enhanced metadata enables efficient page-to-chunk queries
and that the page field is correctly populated in text metadata.
"""

import json
from unittest.mock import Mock

import numpy as np
import pytest

from src.processing.handlers.text_embedding_handler import TextEmbeddingHandler
from src.storage.metadata_schema import ChunkContext


class TestPageChunkMapping:
    """Test page-to-chunk mapping with enhanced metadata."""

    @pytest.fixture
    def mock_storage_client(self):
        """Create a mock ChromaDB storage client."""
        client = Mock()
        client.text_collection = Mock()

        # Store metadata for validation
        self.stored_metadata = []

        def mock_add_text_embedding(doc_id, chunk_id, full_embeddings, metadata):
            self.stored_metadata.append(metadata)
            return f"embedding-{len(self.stored_metadata)}"

        client.add_text_embedding = Mock(side_effect=mock_add_text_embedding)
        return client

    def test_page_field_populated_in_text_metadata(self, mock_storage_client):
        """Test that page field is correctly populated in text metadata."""
        # Create handler with enhanced mode
        handler = TextEmbeddingHandler(
            storage_client=mock_storage_client, enhanced_mode_config={"enabled": True}
        )

        # Create chunks spanning multiple pages
        chunks = []
        text_results = []

        # Chunk 1: Page 1 only
        chunk1 = Mock()
        chunk1.chunk_id = "doc-chunk001"
        chunk1.page_num = 1
        chunk1.text = "Text on page 1"
        chunk1.context = ChunkContext(
            parent_heading="Introduction",
            section_path="Introduction",
            element_type="text",
            page_nums=[1],
        )
        chunks.append(chunk1)

        result1 = Mock()
        result1.doc_id = "test-doc"
        result1.chunk_id = "doc-chunk001"
        result1.page_num = 1
        result1.text = "Text on page 1"
        result1.embedding = np.random.randn(30, 128).astype(np.float32)
        text_results.append(result1)

        # Chunk 2: Spans pages 1-2
        chunk2 = Mock()
        chunk2.chunk_id = "doc-chunk002"
        chunk2.page_num = 1  # Primary page where chunk starts
        chunk2.text = "Text spanning pages 1 and 2"
        chunk2.context = ChunkContext(
            parent_heading="Introduction",
            section_path="Introduction",
            element_type="text",
            page_nums=[1, 2],  # Spans multiple pages
            is_page_boundary=True,
        )
        chunks.append(chunk2)

        result2 = Mock()
        result2.doc_id = "test-doc"
        result2.chunk_id = "doc-chunk002"
        result2.page_num = 1
        result2.text = "Text spanning pages 1 and 2"
        result2.embedding = np.random.randn(30, 128).astype(np.float32)
        text_results.append(result2)

        # Chunk 3: Page 2 only
        chunk3 = Mock()
        chunk3.chunk_id = "doc-chunk003"
        chunk3.page_num = 2
        chunk3.text = "Text on page 2"
        chunk3.context = ChunkContext(
            parent_heading="Methods", section_path="Methods", element_type="text", page_nums=[2]
        )
        chunks.append(chunk3)

        result3 = Mock()
        result3.doc_id = "test-doc"
        result3.chunk_id = "doc-chunk003"
        result3.page_num = 2
        result3.text = "Text on page 2"
        result3.embedding = np.random.randn(30, 128).astype(np.float32)
        text_results.append(result3)

        # Store text embeddings
        self.stored_metadata = []  # Reset
        handler.store_text_embeddings(
            text_results=text_results,
            text_chunks=chunks,
            filename="test.pdf",
            file_path="/data/uploads/test.pdf",
            safe_doc_metadata={"format": "pdf"},
        )

        # Validate stored metadata
        assert len(self.stored_metadata) == 3

        # Check chunk 1 (page 1 only)
        meta1 = self.stored_metadata[0]
        assert meta1["page"] == 1
        assert meta1["has_context"] is True
        page_nums1 = json.loads(meta1["page_nums"])
        assert page_nums1 == [1]
        assert meta1["is_page_boundary"] is False

        # Check chunk 2 (spans pages 1-2)
        meta2 = self.stored_metadata[1]
        assert meta2["page"] == 1  # Primary page
        assert meta2["has_context"] is True
        page_nums2 = json.loads(meta2["page_nums"])
        assert page_nums2 == [1, 2]  # Spans both pages
        assert meta2["is_page_boundary"] is True

        # Check chunk 3 (page 2 only)
        meta3 = self.stored_metadata[2]
        assert meta3["page"] == 2
        assert meta3["has_context"] is True
        page_nums3 = json.loads(meta3["page_nums"])
        assert page_nums3 == [2]
        assert meta3["is_page_boundary"] is False

    def test_query_chunks_by_page(self, mock_storage_client):
        """Test that chunks can be queried by page number."""
        # This test demonstrates the ChromaDB query pattern
        # In actual usage, this would be done via ChromaDB's where clause

        # Create handler
        handler = TextEmbeddingHandler(
            storage_client=mock_storage_client, enhanced_mode_config={"enabled": True}
        )

        # Create chunks for different pages
        chunks = []
        text_results = []

        for page in [1, 1, 2, 2, 3]:
            chunk = Mock()
            chunk.chunk_id = f"doc-chunk{len(chunks):03d}"
            chunk.page_num = page
            chunk.text = f"Text on page {page}"
            chunk.context = ChunkContext(
                section_path=f"Section {page}", element_type="text", page_nums=[page]
            )
            chunks.append(chunk)

            result = Mock()
            result.doc_id = "test-doc"
            result.chunk_id = chunk.chunk_id
            result.page_num = page
            result.text = chunk.text
            result.embedding = np.random.randn(30, 128).astype(np.float32)
            text_results.append(result)

        # Store embeddings
        self.stored_metadata = []
        handler.store_text_embeddings(
            text_results=text_results,
            text_chunks=chunks,
            filename="test.pdf",
            file_path="/data/uploads/test.pdf",
            safe_doc_metadata={"format": "pdf"},
        )

        # Simulate ChromaDB query for page 1
        page_1_chunks = [meta for meta in self.stored_metadata if meta["page"] == 1]
        assert len(page_1_chunks) == 2

        # Simulate ChromaDB query for page 2
        page_2_chunks = [meta for meta in self.stored_metadata if meta["page"] == 2]
        assert len(page_2_chunks) == 2

        # Simulate ChromaDB query for page 3
        page_3_chunks = [meta for meta in self.stored_metadata if meta["page"] == 3]
        assert len(page_3_chunks) == 1

    def test_query_chunks_by_page_range(self, mock_storage_client):
        """Test querying chunks that span a page range."""
        # Create handler
        handler = TextEmbeddingHandler(
            storage_client=mock_storage_client, enhanced_mode_config={"enabled": True}
        )

        # Create chunks with different page ranges
        chunks = []
        text_results = []

        # Single page chunks
        for page in [1, 2, 3]:
            chunk = Mock()
            chunk.chunk_id = f"doc-chunk{len(chunks):03d}"
            chunk.page_num = page
            chunk.text = f"Single page {page}"
            chunk.context = ChunkContext(
                section_path=f"Section {page}", element_type="text", page_nums=[page]
            )
            chunks.append(chunk)

            result = Mock()
            result.doc_id = "test-doc"
            result.chunk_id = chunk.chunk_id
            result.page_num = page
            result.text = chunk.text
            result.embedding = np.random.randn(30, 128).astype(np.float32)
            text_results.append(result)

        # Multi-page chunks
        chunk_multi = Mock()
        chunk_multi.chunk_id = "doc-chunk003"
        chunk_multi.page_num = 2
        chunk_multi.text = "Spans pages 2-3"
        chunk_multi.context = ChunkContext(
            section_path="Section 2",
            element_type="text",
            page_nums=[2, 3],
            is_page_boundary=True,
        )
        chunks.append(chunk_multi)

        result_multi = Mock()
        result_multi.doc_id = "test-doc"
        result_multi.chunk_id = chunk_multi.chunk_id
        result_multi.page_num = 2
        result_multi.text = chunk_multi.text
        result_multi.embedding = np.random.randn(30, 128).astype(np.float32)
        text_results.append(result_multi)

        # Store embeddings
        self.stored_metadata = []
        handler.store_text_embeddings(
            text_results=text_results,
            text_chunks=chunks,
            filename="test.pdf",
            file_path="/data/uploads/test.pdf",
            safe_doc_metadata={"format": "pdf"},
        )

        # Query: Find all chunks that include page 2
        # This would use page_nums field in ChromaDB
        chunks_with_page_2 = []
        for meta in self.stored_metadata:
            page_nums = json.loads(meta["page_nums"])
            if 2 in page_nums:
                chunks_with_page_2.append(meta)

        # Should find: single page 2 chunk + multi-page 2-3 chunk
        assert len(chunks_with_page_2) == 2

        # Query: Find all chunks that cross page boundaries
        boundary_chunks = [
            meta for meta in self.stored_metadata if meta.get("is_page_boundary", False)
        ]
        assert len(boundary_chunks) == 1
        assert json.loads(boundary_chunks[0]["page_nums"]) == [2, 3]

    def test_page_nums_consistency(self, mock_storage_client):
        """Test that page field is always included in page_nums array."""
        # Create handler
        handler = TextEmbeddingHandler(
            storage_client=mock_storage_client, enhanced_mode_config={"enabled": True}
        )

        # Create chunks
        chunks = []
        text_results = []

        # Test various page configurations
        test_cases = [
            (1, [1]),  # Single page
            (2, [2, 3]),  # Multi-page starting at 2
            (5, [4, 5, 6]),  # Multi-page in middle
        ]

        for page, page_nums in test_cases:
            chunk = Mock()
            chunk.chunk_id = f"doc-chunk{len(chunks):03d}"
            chunk.page_num = page
            chunk.text = f"Text on pages {page_nums}"
            chunk.context = ChunkContext(
                section_path="Section", element_type="text", page_nums=page_nums
            )
            chunks.append(chunk)

            result = Mock()
            result.doc_id = "test-doc"
            result.chunk_id = chunk.chunk_id
            result.page_num = page
            result.text = chunk.text
            result.embedding = np.random.randn(30, 128).astype(np.float32)
            text_results.append(result)

        # Store embeddings
        self.stored_metadata = []
        handler.store_text_embeddings(
            text_results=text_results,
            text_chunks=chunks,
            filename="test.pdf",
            file_path="/data/uploads/test.pdf",
            safe_doc_metadata={"format": "pdf"},
        )

        # Validate consistency: page field should always be in page_nums
        for meta in self.stored_metadata:
            page = meta["page"]
            page_nums = json.loads(meta["page_nums"])
            assert page in page_nums, f"Page {page} not found in page_nums {page_nums}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
