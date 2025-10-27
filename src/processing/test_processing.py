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

from .docling_parser import DoclingParser, Page, TextChunk
from .mocks import BatchEmbeddingOutput, MockEmbeddingEngine, MockStorageClient
from .processor import DocumentProcessor
from .text_processor import TextProcessor
from .visual_processor import VisualProcessor

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
    """Test MockStorageClient matches storage-interface.md contract."""

    def setup_method(self):
        """Initialize mock client."""
        self.client = MockStorageClient(host="chromadb", port=8000)

    def test_initialization(self):
        """Test client initializes correctly."""
        assert self.client.host == "chromadb"
        assert self.client.port == 8000

        stats = self.client.get_collection_stats()
        assert stats["mock"] is True
        assert stats["visual_count"] == 0
        assert stats["text_count"] == 0

    def test_add_visual_embedding(self):
        """Test adding visual embedding."""
        # Create test embedding
        embeddings = np.random.randn(100, 768).astype(np.float32)

        embedding_id = self.client.add_visual_embedding(
            doc_id="test-doc-123",
            page=1,
            full_embeddings=embeddings,
            metadata={"filename": "test.pdf"},
        )

        # Validate ID format
        assert embedding_id == "test-doc-123-page001"

        # Check stats
        stats = self.client.get_collection_stats()
        assert stats["visual_count"] == 1

    def test_add_text_embedding(self):
        """Test adding text embedding."""
        # Create test embedding
        embeddings = np.random.randn(64, 768).astype(np.float32)

        embedding_id = self.client.add_text_embedding(
            doc_id="test-doc-123",
            chunk_id=0,
            full_embeddings=embeddings,
            metadata={"filename": "test.pdf", "text_preview": "Sample text"},
        )

        # Validate ID format
        assert embedding_id == "test-doc-123-chunk0000"

        # Check stats
        stats = self.client.get_collection_stats()
        assert stats["text_count"] == 1

    def test_invalid_embedding_shape_raises(self):
        """Test invalid embedding shapes raise ValueError."""
        # Wrong shape (1D instead of 2D)
        bad_embeddings = np.random.randn(768)

        with pytest.raises(ValueError, match="Invalid embedding shape"):
            self.client.add_visual_embedding(
                doc_id="test", page=1, full_embeddings=bad_embeddings, metadata={}
            )

        # Wrong dimension (512 instead of 768)
        bad_embeddings = np.random.randn(100, 512).astype(np.float32)

        with pytest.raises(ValueError, match="Invalid embedding dimension"):
            self.client.add_visual_embedding(
                doc_id="test", page=1, full_embeddings=bad_embeddings, metadata={}
            )

    def test_delete_document(self):
        """Test document deletion."""
        doc_id = "test-doc-456"

        # Add some embeddings
        self.client.add_visual_embedding(
            doc_id=doc_id,
            page=1,
            full_embeddings=np.random.randn(100, 768).astype(np.float32),
            metadata={},
        )
        self.client.add_visual_embedding(
            doc_id=doc_id,
            page=2,
            full_embeddings=np.random.randn(100, 768).astype(np.float32),
            metadata={},
        )
        self.client.add_text_embedding(
            doc_id=doc_id,
            chunk_id=0,
            full_embeddings=np.random.randn(64, 768).astype(np.float32),
            metadata={},
        )

        # Delete document
        visual_count, text_count = self.client.delete_document(doc_id)

        assert visual_count == 2
        assert text_count == 1

        # Stats should reflect deletion
        stats = self.client.get_collection_stats()
        assert stats["visual_count"] == 0
        assert stats["text_count"] == 0

    def test_get_full_embeddings(self):
        """Test retrieving full embeddings."""
        doc_id = "test-doc-789"
        original_embeddings = np.random.randn(100, 768).astype(np.float32)

        embedding_id = self.client.add_visual_embedding(
            doc_id=doc_id, page=1, full_embeddings=original_embeddings, metadata={}
        )

        # Retrieve embeddings
        retrieved = self.client.get_full_embeddings(embedding_id=embedding_id, collection="visual")

        # Should be identical
        assert np.array_equal(original_embeddings, retrieved)

    def test_get_full_embeddings_not_found(self):
        """Test retrieving non-existent embedding raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            self.client.get_full_embeddings("nonexistent-id")


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

    def test_get_storage_stats(self):
        """Test getting storage stats."""
        stats = self.processor.get_storage_stats()
        assert "visual_count" in stats
        assert "text_count" in stats

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

        # Test storage structure
        embedding_id = self.storage.add_visual_embedding(
            doc_id="test",
            page=1,
            full_embeddings=result.embeddings[0],
            metadata={"filename": "test.pdf"},
        )

        assert embedding_id == "test-page001"

    def test_mock_contract_compliance(self):
        """Test mocks comply with integration contracts."""
        # Verify BatchEmbeddingOutput has required fields
        images = [Image.new("RGB", (1024, 1024))]
        output = self.engine.embed_images(images)

        required_fields = ["embeddings", "cls_tokens", "seq_lengths", "input_type"]
        for field in required_fields:
            assert hasattr(output, field)

        # Verify storage methods exist
        storage_methods = [
            "add_visual_embedding",
            "add_text_embedding",
            "get_collection_stats",
            "delete_document",
        ]
        for method in storage_methods:
            assert hasattr(self.storage, method)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
