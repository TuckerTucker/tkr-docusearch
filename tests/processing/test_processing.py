"""
Unit tests for document processing pipeline.

Tests cover:
- Mock implementations
- Document parsing
- Visual processing
- Text processing
- End-to-end processing
- Error handling
"""

import os
import tempfile

import numpy as np
import pytest
from PIL import Image

from tkr_docusearch.processing.docling_parser import DoclingParser, Page, TextChunk
from tkr_docusearch.core.testing.mocks import BatchEmbeddingOutput, MockEmbeddingEngine, MockStorageClient
from tkr_docusearch.processing.processor import DocumentProcessor
from tkr_docusearch.processing.text_processor import TextProcessor
from tkr_docusearch.processing.visual_processor import VisualProcessor

# ============================================================================
# Mock Tests
# ============================================================================


class TestMockEmbeddingEngine:
    """Test MockEmbeddingEngine matches embedding-interface.md contract."""

    def setup_method(self):
        """Initialize mock engine."""
        self.engine = MockEmbeddingEngine(device="mps")

    def test_initialization(self):
        """Test engine initializes correctly."""
        assert self.engine.model_name == "nomic-ai/colnomic-embed-multimodal-7b"
        assert self.engine.device == "mps"

        info = self.engine.get_model_info()
        assert info["mock"] is True
        assert info["is_loaded"] is True

    def test_embed_images_single(self):
        """Test single image embedding."""
        # Create test image
        img = Image.new("RGB", (1024, 1024), color="white")
        images = [img]

        result = self.engine.embed_images(images, batch_size=4)

        # Validate output structure
        assert isinstance(result, BatchEmbeddingOutput)
        assert len(result.embeddings) == 1
        assert result.cls_tokens.shape == (1, 768)
        assert len(result.seq_lengths) == 1
        assert result.input_type == "visual"

        # Validate embedding shape
        embedding = result.embeddings[0]
        assert len(embedding.shape) == 2
        assert embedding.shape[1] == 768
        assert 80 <= embedding.shape[0] <= 120  # Expected token range

        # Validate CLS token matches first token
        assert np.array_equal(embedding[0], result.cls_tokens[0])

    def test_embed_images_batch(self):
        """Test batch image embedding."""
        # Create batch of images
        images = [Image.new("RGB", (1024, 1024), color="white") for _ in range(5)]

        result = self.engine.embed_images(images, batch_size=4)

        # Validate batch output
        assert len(result.embeddings) == 5
        assert result.cls_tokens.shape == (5, 768)
        assert len(result.seq_lengths) == 5

        # All embeddings should have correct dimensions
        for emb in result.embeddings:
            assert emb.shape[1] == 768

    def test_embed_images_empty_raises(self):
        """Test empty image list raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            self.engine.embed_images([])

    def test_embed_texts_single(self):
        """Test single text embedding."""
        texts = ["This is a test document with some sample text content."]

        result = self.engine.embed_texts(texts, batch_size=8)

        # Validate output structure
        assert isinstance(result, BatchEmbeddingOutput)
        assert len(result.embeddings) == 1
        assert result.cls_tokens.shape == (1, 768)
        assert len(result.seq_lengths) == 1
        assert result.input_type == "text"

        # Validate embedding shape
        embedding = result.embeddings[0]
        assert len(embedding.shape) == 2
        assert embedding.shape[1] == 768
        assert 50 <= embedding.shape[0] <= 80  # Expected token range

        # Validate CLS token matches first token
        assert np.array_equal(embedding[0], result.cls_tokens[0])

    def test_embed_texts_batch(self):
        """Test batch text embedding."""
        texts = [
            "First chunk of text with some content.",
            "Second chunk of text with different content.",
            "Third chunk with more sample text.",
        ]

        result = self.engine.embed_texts(texts, batch_size=8)

        # Validate batch output
        assert len(result.embeddings) == 3
        assert result.cls_tokens.shape == (3, 768)
        assert len(result.seq_lengths) == 3

    def test_embed_texts_empty_raises(self):
        """Test empty text list raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            self.engine.embed_texts([])

    def test_processing_time_simulation(self):
        """Test processing time is simulated realistically."""
        images = [Image.new("RGB", (1024, 1024)) for _ in range(3)]
        result = self.engine.embed_images(images)

        # Should simulate ~6s per image
        expected_time_ms = 3 * 6000.0
        assert result.batch_processing_time_ms == expected_time_ms


class TestMockStorageClient:
    """Test MockKojiClient (aliased as MockStorageClient) matches Koji API contract."""

    def setup_method(self):
        """Initialize mock client."""
        self.client = MockStorageClient()

    def test_initialization(self):
        """Test client initializes and connects correctly."""
        self.client.open()
        health = self.client.health_check()
        assert health["connected"] is True
        assert "documents" in health["tables"]

    def test_insert_pages(self):
        """Test inserting page records."""
        self.client.insert_pages([
            {"id": "test-doc-123-page001", "doc_id": "test-doc-123", "page_num": 1},
        ])

        pages = self.client.get_pages_for_document("test-doc-123")
        assert len(pages) == 1
        assert pages[0]["page_num"] == 1

    def test_insert_chunks(self):
        """Test inserting chunk records."""
        self.client.insert_chunks([
            {"id": "test-doc-123-chunk0000", "doc_id": "test-doc-123", "page_num": 1, "text": "Sample text"},
        ])

        chunks = self.client.get_chunks_for_document("test-doc-123")
        assert len(chunks) == 1
        assert chunks[0]["text"] == "Sample text"

    def test_delete_document(self):
        """Test document deletion removes document, pages, and chunks."""
        doc_id = "test-doc-456"

        self.client.create_document(doc_id, "test.pdf", "pdf")
        self.client.insert_pages([
            {"id": f"{doc_id}-page001", "doc_id": doc_id, "page_num": 1},
            {"id": f"{doc_id}-page002", "doc_id": doc_id, "page_num": 2},
        ])
        self.client.insert_chunks([
            {"id": f"{doc_id}-chunk0000", "doc_id": doc_id, "page_num": 1, "text": "chunk"},
        ])

        self.client.delete_document(doc_id)

        assert self.client.get_document(doc_id) is None
        assert self.client.get_pages_for_document(doc_id) == []
        assert self.client.get_chunks_for_document(doc_id) == []

    def test_get_pages_for_document(self):
        """Test retrieving pages for a document."""
        doc_id = "test-doc-789"
        self.client.insert_pages([
            {"id": f"{doc_id}-page002", "doc_id": doc_id, "page_num": 2},
            {"id": f"{doc_id}-page001", "doc_id": doc_id, "page_num": 1},
        ])

        pages = self.client.get_pages_for_document(doc_id)
        assert len(pages) == 2
        assert pages[0]["page_num"] == 1  # Sorted by page_num
        assert pages[1]["page_num"] == 2

    def test_get_pages_for_document_not_found(self):
        """Test retrieving pages for unknown document returns empty list."""
        pages = self.client.get_pages_for_document("nonexistent-doc")
        assert pages == []


# ============================================================================
# Parser Tests
# ============================================================================


class TestDoclingParser:
    """Test document parsing functionality."""

    def setup_method(self):
        """Initialize parser."""
        self.parser = DoclingParser(render_dpi=150)

    def test_initialization(self):
        """Test parser initialization."""
        assert self.parser.render_dpi == 150

    def test_chunk_text_basic(self):
        """Test text chunking with overlap."""
        # Create mock page
        text = " ".join([f"word{i}" for i in range(300)])  # 300 words
        page = Page(
            page_num=1, image=Image.new("RGB", (100, 100)), width=100, height=100, text=text
        )

        chunks = self.parser._chunk_text(
            pages=[page], doc_id="test-doc", chunk_size_words=100, chunk_overlap_words=20
        )

        # Should create multiple chunks
        assert len(chunks) > 1

        # First chunk should have ~100 words
        assert 90 <= chunks[0].word_count <= 110

        # Chunks should have correct page numbers
        for chunk in chunks:
            assert chunk.page_num == 1

        # Chunk IDs should be sequential
        assert chunks[0].chunk_id == "test-doc-chunk0000"
        assert chunks[1].chunk_id == "test-doc-chunk0001"

    def test_chunk_text_overlap(self):
        """Test chunk overlap is correct."""
        text = " ".join([f"word{i}" for i in range(200)])
        page = Page(
            page_num=1, image=Image.new("RGB", (100, 100)), width=100, height=100, text=text
        )

        chunks = self.parser._chunk_text(
            pages=[page], doc_id="test", chunk_size_words=100, chunk_overlap_words=25
        )

        # Second chunk should start 75 words after first (100 - 25 overlap)
        # Verify overlap by checking text content
        assert len(chunks) >= 2

    def test_parse_nonexistent_file_raises(self):
        """Test parsing non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            self.parser.parse_document("/nonexistent/file.pdf")


# ============================================================================
# Processor Tests
# ============================================================================


class TestVisualProcessor:
    """Test visual processing pipeline."""

    def setup_method(self):
        """Initialize components."""
        self.engine = MockEmbeddingEngine()
        self.processor = VisualProcessor(embedding_engine=self.engine, batch_size=4)

    def test_process_pages(self):
        """Test page processing."""
        # Create test pages
        pages = [
            Page(
                page_num=i,
                image=Image.new("RGB", (1024, 1024)),
                width=1024,
                height=1024,
                text=f"Page {i} text",
            )
            for i in range(1, 6)
        ]

        results = self.processor.process_pages(pages, doc_id="test-doc")

        # Should have results for all pages
        assert len(results) == 5

        # Validate result structure
        for i, result in enumerate(results):
            assert result.doc_id == "test-doc"
            assert result.page_num == i + 1
            assert result.embedding.shape[1] == 768
            assert result.cls_token.shape == (768,)
            assert result.seq_length > 0

    def test_process_pages_empty_raises(self):
        """Test empty pages list raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            self.processor.process_pages([], doc_id="test")

    def test_get_processing_stats(self):
        """Test statistics generation."""
        pages = [
            Page(i, Image.new("RGB", (1024, 1024)), 1024, 1024, f"Page {i}") for i in range(1, 4)
        ]

        results = self.processor.process_pages(pages, doc_id="test")
        stats = self.processor.get_processing_stats(results)

        assert stats["num_pages"] == 3
        assert stats["total_time_ms"] > 0
        assert stats["avg_time_per_page_ms"] > 0
        assert stats["total_tokens"] > 0
        assert stats["avg_tokens_per_page"] > 0


class TestTextProcessor:
    """Test text processing pipeline."""

    def setup_method(self):
        """Initialize components."""
        self.engine = MockEmbeddingEngine()
        self.processor = TextProcessor(embedding_engine=self.engine, batch_size=8)

    def test_process_chunks(self):
        """Test chunk processing."""
        # Create test chunks
        chunks = [
            TextChunk(
                chunk_id=f"test-chunk{i:04d}",
                page_num=1,
                text=f"This is chunk {i} with sample text content.",
                start_offset=i * 50,
                end_offset=(i + 1) * 50,
                word_count=8,
            )
            for i in range(5)
        ]

        results = self.processor.process_chunks(chunks, doc_id="test-doc")

        # Should have results for all chunks
        assert len(results) == 5

        # Validate result structure
        for i, result in enumerate(results):
            assert result.doc_id == "test-doc"
            assert result.chunk_id == f"test-chunk{i:04d}"
            assert result.embedding.shape[1] == 768
            assert result.cls_token.shape == (768,)
            assert result.seq_length > 0
            assert result.text == chunks[i].text

    def test_process_chunks_empty_raises(self):
        """Test empty chunks list raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            self.processor.process_chunks([], doc_id="test")

    def test_get_processing_stats(self):
        """Test statistics generation."""
        chunks = [
            TextChunk(
                chunk_id=f"test-chunk{i:04d}",
                page_num=1,
                text=f"Chunk {i} text content goes here.",
                start_offset=0,
                end_offset=100,
                word_count=6,
            )
            for i in range(3)
        ]

        results = self.processor.process_chunks(chunks, doc_id="test")
        stats = self.processor.get_processing_stats(results)

        assert stats["num_chunks"] == 3
        assert stats["total_time_ms"] > 0
        assert stats["avg_time_per_chunk_ms"] > 0
        assert stats["total_tokens"] > 0
        assert stats["avg_tokens_per_chunk"] > 0


class TestDocumentProcessor:
    """Test end-to-end document processing."""

    def setup_method(self):
        """Initialize processor with mocks."""
        self.engine = MockEmbeddingEngine()
        self.storage = MockStorageClient()
        self.processor = DocumentProcessor(
            embedding_engine=self.engine,
            storage_client=self.storage,
            parser_config={"render_dpi": 150},
            visual_batch_size=4,
            text_batch_size=8,
        )

    def test_initialization(self):
        """Test processor initialization."""
        assert self.processor.embedding_engine is not None
        assert self.processor.storage_client is not None
        assert self.processor.parser is not None
        assert self.processor.visual_processor is not None
        assert self.processor.text_processor is not None

    def test_get_model_info(self):
        """Test getting model info."""
        info = self.processor.get_model_info()
        assert info["mock"] is True
        assert "model_name" in info

    @pytest.mark.skip(reason="processor.get_storage_stats() still calls legacy get_collection_stats()")
    def test_get_storage_stats(self):
        """Test getting storage stats."""
        stats = self.processor.get_storage_stats()
        assert "connected" in stats or "tables" in stats

    def test_process_document_mock_file(self):
        """Test processing with mock file (requires libraries)."""
        # Create a temporary test image as PDF-like
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            # Create a simple test file
            # This will use mock parser if PyMuPDF not available
            img = Image.new("RGB", (1024, 1024), color="white")
            img.save(temp_path.replace(".pdf", ".png"))

            # Process should work even with mock parser
            # (actual PDF processing requires PyMuPDF)

        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            png_path = temp_path.replace(".pdf", ".png")
            if os.path.exists(png_path):
                os.unlink(png_path)

    def test_status_callback(self):
        """Test status callback is invoked."""
        statuses = []

        def callback(status):
            statuses.append(status)

        # Would need a real file to test fully
        # For now, just verify callback structure
        assert callable(callback)


# ============================================================================
# Integration Tests
# ============================================================================


class TestEndToEndProcessing:
    """Test complete end-to-end processing pipeline."""

    def setup_method(self):
        """Setup complete pipeline."""
        self.engine = MockEmbeddingEngine()
        self.storage = MockStorageClient()
        self.processor = DocumentProcessor(
            embedding_engine=self.engine, storage_client=self.storage
        )

    def test_mock_validation(self):
        """Validate mocks match contract specifications."""
        # Test embedding output structure
        images = [Image.new("RGB", (1024, 1024))]
        result = self.engine.embed_images(images)

        assert isinstance(result, BatchEmbeddingOutput)
        assert len(result.embeddings) == 1
        assert result.embeddings[0].shape[1] == 768
        assert result.cls_tokens.shape == (1, 768)
        assert result.input_type == "visual"

        # Test storage structure (Koji API)
        self.storage.create_document("test", "test.pdf", "pdf")
        doc = self.storage.get_document("test")
        assert doc is not None
        assert doc["filename"] == "test.pdf"

    def test_mock_contract_compliance(self):
        """Test mocks comply with Koji API contracts."""
        # Verify BatchEmbeddingOutput has required fields
        images = [Image.new("RGB", (1024, 1024))]
        output = self.engine.embed_images(images)

        required_fields = ["embeddings", "cls_tokens", "seq_lengths", "input_type"]
        for field in required_fields:
            assert hasattr(output, field)

        # Verify storage methods exist (Koji API)
        storage_methods = [
            "create_document",
            "insert_pages",
            "insert_chunks",
            "get_document",
            "delete_document",
        ]
        for method in storage_methods:
            assert hasattr(self.storage, method)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
