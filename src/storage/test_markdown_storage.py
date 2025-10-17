"""
Unit tests for markdown storage in ChromaDB.

Tests markdown compression, storage, and retrieval in ChromaClient.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.storage.chroma_client import ChromaClient, DocumentNotFoundError
from src.storage.compression import compress_markdown


@pytest.fixture
def mock_chroma_client():
    """Mock ChromaDB HttpClient."""
    with patch("chromadb.HttpClient") as mock:
        client = mock.return_value
        client.heartbeat.return_value = None
        yield mock


@pytest.fixture
def chroma_client(mock_chroma_client):
    """Create ChromaClient for testing with mocked backend."""
    # Create real ChromaClient but with mocked ChromaDB backend
    client = ChromaClient(host="localhost", port=8001)

    # Create mock collections
    visual_collection = MagicMock()
    text_collection = MagicMock()

    # Setup collection responses
    visual_collection.get.return_value = {"ids": [], "metadatas": []}
    text_collection.get.return_value = {"ids": [], "metadatas": []}

    client._visual_collection = visual_collection
    client._text_collection = text_collection

    yield client


class TestMarkdownCompression:
    """Test markdown compression in storage."""

    def test_small_markdown_stored_uncompressed(self, chroma_client):
        """Test that small markdown (<1KB) is stored uncompressed."""
        # Create small markdown
        small_markdown = "# Test\n\nShort content"  # ~25 chars

        # Create mock embedding
        embeddings = np.random.randn(10, 128).astype(np.float32)

        # Metadata with markdown
        metadata = {
            "filename": "test.md",
            "source_path": "/test/test.md",
            "full_markdown": small_markdown,
            "markdown_extracted": True,
            "markdown_length": len(small_markdown),
        }

        # Store
        embedding_id = chroma_client.add_visual_embedding(
            doc_id="test-doc-1", page=1, full_embeddings=embeddings, metadata=metadata
        )

        # Retrieve metadata
        results = chroma_client._visual_collection.get(ids=[embedding_id], include=["metadatas"])

        stored_metadata = results["metadatas"][0]

        # Check uncompressed storage
        assert "full_markdown" in stored_metadata
        assert stored_metadata["full_markdown"] == small_markdown
        assert stored_metadata["markdown_compression"] == "none"
        assert "full_markdown_compressed" not in stored_metadata

    def test_large_markdown_stored_compressed(self, chroma_client):
        """Test that large markdown (>1KB) is stored compressed."""
        # Create large markdown (>1KB)
        large_markdown = "# Large Document\n\n" + ("Content. " * 200)  # ~2KB

        # Create mock embedding
        embeddings = np.random.randn(10, 128).astype(np.float32)

        # Metadata with markdown
        metadata = {
            "filename": "test.md",
            "source_path": "/test/test.md",
            "full_markdown": large_markdown,
            "markdown_extracted": True,
            "markdown_length": len(large_markdown),
        }

        # Store
        embedding_id = chroma_client.add_visual_embedding(
            doc_id="test-doc-2", page=1, full_embeddings=embeddings, metadata=metadata
        )

        # Retrieve metadata
        results = chroma_client._visual_collection.get(ids=[embedding_id], include=["metadatas"])

        stored_metadata = results["metadatas"][0]

        # Check compressed storage
        assert "full_markdown_compressed" in stored_metadata
        assert "full_markdown" not in stored_metadata
        assert stored_metadata["markdown_compression"] == "gzip+base64"

        # Verify compression worked
        compressed = stored_metadata["full_markdown_compressed"]
        assert len(compressed) < len(large_markdown)


class TestMarkdownRetrieval:
    """Test markdown retrieval via get_document_markdown()."""

    def test_retrieve_small_markdown(self, chroma_client):
        """Test retrieving small uncompressed markdown."""
        small_markdown = "# Test\n\nShort content"

        # Mock the collection response
        chroma_client._visual_collection.get.return_value = {
            "ids": ["test-doc-3-page001"],
            "metadatas": [
                {
                    "doc_id": "test-doc-3",
                    "full_markdown": small_markdown,
                    "markdown_extracted": True,
                    "markdown_compression": "none",
                }
            ],
        }

        # Retrieve markdown
        retrieved = chroma_client.get_document_markdown("test-doc-3")

        assert retrieved == small_markdown

    def test_retrieve_large_markdown_decompressed(self, chroma_client):
        """Test retrieving large compressed markdown (auto-decompressed)."""
        large_markdown = "# Large Document\n\n" + ("Content. " * 200)
        compressed = compress_markdown(large_markdown)

        # Mock the collection response with compressed markdown
        chroma_client._visual_collection.get.return_value = {
            "ids": ["test-doc-4-page001"],
            "metadatas": [
                {
                    "doc_id": "test-doc-4",
                    "full_markdown_compressed": compressed,
                    "markdown_extracted": True,
                    "markdown_compression": "gzip+base64",
                }
            ],
        }

        # Retrieve markdown
        retrieved = chroma_client.get_document_markdown("test-doc-4")

        # Should be decompressed automatically
        assert retrieved == large_markdown

    def test_retrieve_markdown_not_extracted(self, chroma_client):
        """Test retrieving markdown when extraction failed."""
        # Mock the collection response for failed extraction
        chroma_client._visual_collection.get.return_value = {
            "ids": ["test-doc-5-page001"],
            "metadatas": [
                {
                    "doc_id": "test-doc-5",
                    "full_markdown": "",
                    "markdown_extracted": False,  # Extraction failed
                    "markdown_error": "Test error",
                }
            ],
        }

        # Retrieve markdown
        retrieved = chroma_client.get_document_markdown("test-doc-5")

        # Should return None for failed extraction
        assert retrieved is None

    def test_retrieve_markdown_document_not_found(self, chroma_client):
        """Test retrieving markdown for non-existent document."""
        # Mock empty response (document not found)
        chroma_client._visual_collection.get.return_value = {"ids": [], "metadatas": []}
        chroma_client._text_collection.get.return_value = {"ids": [], "metadatas": []}

        with pytest.raises(DocumentNotFoundError, match="not found"):
            chroma_client.get_document_markdown("non-existent-doc")

    def test_retrieve_from_text_collection(self, chroma_client):
        """Test retrieving markdown from text collection."""
        markdown = "# Text Chunk\n\nContent"

        # Mock visual collection has no results, text collection has results
        chroma_client._visual_collection.get.return_value = {"ids": [], "metadatas": []}
        chroma_client._text_collection.get.return_value = {
            "ids": ["test-doc-6-chunk0000"],
            "metadatas": [
                {
                    "doc_id": "test-doc-6",
                    "full_markdown": markdown,
                    "markdown_extracted": True,
                    "markdown_compression": "none",
                }
            ],
        }

        # Retrieve markdown
        retrieved = chroma_client.get_document_markdown("test-doc-6")

        assert retrieved == markdown


class TestMarkdownEdgeCases:
    """Test edge cases for markdown storage."""

    def test_exactly_1kb_threshold(self, chroma_client):
        """Test markdown at exactly 1KB threshold."""
        # Create markdown exactly 1024 bytes
        markdown = "x" * 1024
        embeddings = np.random.randn(10, 128).astype(np.float32)

        metadata = {
            "filename": "test.md",
            "source_path": "/test/test.md",
            "full_markdown": markdown,
            "markdown_extracted": True,
            "markdown_length": len(markdown),
        }

        chroma_client.add_visual_embedding(
            doc_id="test-doc-7", page=1, full_embeddings=embeddings, metadata=metadata
        )

        # Retrieve metadata
        results = chroma_client._visual_collection.get(
            where={"doc_id": "test-doc-7"}, limit=1, include=["metadatas"]
        )

        stored_metadata = results["metadatas"][0]

        # Should be stored uncompressed (<=1KB)
        assert "full_markdown" in stored_metadata
        assert stored_metadata["markdown_compression"] == "none"

    def test_markdown_just_over_1kb(self, chroma_client):
        """Test markdown just over 1KB threshold."""
        # Create markdown 1025 bytes (over threshold)
        markdown = "x" * 1025
        embeddings = np.random.randn(10, 128).astype(np.float32)

        metadata = {
            "filename": "test.md",
            "source_path": "/test/test.md",
            "full_markdown": markdown,
            "markdown_extracted": True,
            "markdown_length": len(markdown),
        }

        chroma_client.add_visual_embedding(
            doc_id="test-doc-8", page=1, full_embeddings=embeddings, metadata=metadata
        )

        # Retrieve metadata
        results = chroma_client._visual_collection.get(
            where={"doc_id": "test-doc-8"}, limit=1, include=["metadatas"]
        )

        stored_metadata = results["metadatas"][0]

        # Should be compressed (>1KB)
        assert "full_markdown_compressed" in stored_metadata
        assert stored_metadata["markdown_compression"] == "gzip+base64"

    def test_empty_markdown(self, chroma_client):
        """Test storing empty markdown."""
        markdown = ""
        embeddings = np.random.randn(10, 128).astype(np.float32)

        metadata = {
            "filename": "test.md",
            "source_path": "/test/test.md",
            "full_markdown": markdown,
            "markdown_extracted": True,
            "markdown_length": len(markdown),
        }

        chroma_client.add_visual_embedding(
            doc_id="test-doc-9", page=1, full_embeddings=embeddings, metadata=metadata
        )

        # Retrieve markdown
        retrieved = chroma_client.get_document_markdown("test-doc-9")

        assert retrieved == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
