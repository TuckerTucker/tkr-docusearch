"""
Tests for processing/handlers modules.

Tests cover:
- AlbumArtHandler: Album art saving for audio files
- MetadataFilter: ChromaDB metadata filtering
- VisualEmbeddingHandler: Visual embedding storage
- TextEmbeddingHandler: Text embedding storage

Target: 80%+ coverage for each module
"""

from unittest.mock import Mock, patch

import numpy as np

# =============================================================================
# AlbumArtHandler Tests
# =============================================================================


class TestAlbumArtHandler:
    """Test album art handler for audio files."""

    def test_save_album_art_not_audio_file(self):
        """Test that non-audio files are skipped."""
        from tkr_docusearch.processing.handlers.album_art_handler import AlbumArtHandler

        doc_metadata = {"filename": "document.pdf"}

        result = AlbumArtHandler.save_album_art_if_present("doc123", doc_metadata)

        # Should return None for non-audio files
        assert result is None

    def test_save_album_art_with_album_art(self):
        """Test saving album art when present."""
        from tkr_docusearch.processing.handlers.album_art_handler import AlbumArtHandler

        doc_metadata = {
            "audio_duration_seconds": 180.5,
            "_album_art_data": b"image_data",
            "_album_art_mime": "image/jpeg",
            "album_art_description": "Cover art",
        }

        with patch("tkr_docusearch.processing.audio_metadata.save_album_art") as mock_save:
            with patch("tkr_docusearch.processing.audio_metadata.AudioMetadata") as mock_audio_metadata:
                mock_save.return_value = "/path/to/album_art.jpg"
                mock_metadata_instance = Mock()
                mock_audio_metadata.return_value = mock_metadata_instance

                result = AlbumArtHandler.save_album_art_if_present("doc123", doc_metadata)

                # Should create AudioMetadata with album art
                mock_audio_metadata.assert_called_once_with(
                    has_album_art=True,
                    album_art_data=b"image_data",
                    album_art_mime="image/jpeg",
                    album_art_description="Cover art",
                )

                # Should call save_album_art
                mock_save.assert_called_once()
                call_args = mock_save.call_args
                assert call_args[0][0] == "doc123"
                assert call_args[0][1] == mock_metadata_instance
                assert call_args[1]["use_placeholder"] is True

                # Should add path to metadata
                assert doc_metadata["album_art_path"] == "/path/to/album_art.jpg"
                assert result == "/path/to/album_art.jpg"

    def test_save_album_art_without_album_art(self):
        """Test saving placeholder when no album art."""
        from tkr_docusearch.processing.handlers.album_art_handler import AlbumArtHandler

        doc_metadata = {
            "audio_duration_seconds": 180.5
            # No album art data
        }

        with patch("tkr_docusearch.processing.audio_metadata.save_album_art") as mock_save:
            with patch("tkr_docusearch.processing.audio_metadata.AudioMetadata") as mock_audio_metadata:
                mock_save.return_value = "/path/to/placeholder.jpg"

                result = AlbumArtHandler.save_album_art_if_present("doc123", doc_metadata)

                # Should create AudioMetadata without album art
                mock_audio_metadata.assert_called_once_with(
                    has_album_art=False,
                    album_art_data=None,
                    album_art_mime=None,
                    album_art_description=None,
                )

                # Should still save (uses placeholder)
                assert result == "/path/to/placeholder.jpg"
                assert doc_metadata["album_art_path"] == "/path/to/placeholder.jpg"

    def test_save_album_art_error_handling(self):
        """Test error handling during album art save."""
        from tkr_docusearch.processing.handlers.album_art_handler import AlbumArtHandler

        doc_metadata = {
            "audio_duration_seconds": 180.5,
            "_album_art_data": b"image_data",
            "_album_art_mime": "image/jpeg",
        }

        with patch("tkr_docusearch.processing.audio_metadata.save_album_art") as mock_save:
            with patch("tkr_docusearch.processing.audio_metadata.AudioMetadata"):
                # Simulate error
                mock_save.side_effect = Exception("Save error")

                result = AlbumArtHandler.save_album_art_if_present("doc123", doc_metadata)

                # Should return None on error
                assert result is None
                # Should not add path to metadata
                assert "album_art_path" not in doc_metadata

    def test_save_album_art_no_path_returned(self):
        """Test when save_album_art returns None."""
        from tkr_docusearch.processing.handlers.album_art_handler import AlbumArtHandler

        doc_metadata = {"audio_duration_seconds": 180.5}

        with patch("tkr_docusearch.processing.audio_metadata.save_album_art") as mock_save:
            with patch("tkr_docusearch.processing.audio_metadata.AudioMetadata"):
                # save_album_art returns None
                mock_save.return_value = None

                result = AlbumArtHandler.save_album_art_if_present("doc123", doc_metadata)

                assert result is None
                assert "album_art_path" not in doc_metadata


# =============================================================================
# MetadataFilter Tests
# =============================================================================


class TestMetadataFilter:
    """Test metadata filter for ChromaDB."""

    def test_filter_metadata_primitives(self):
        """Test that primitives pass through unchanged."""
        from tkr_docusearch.processing.handlers.metadata_filter import MetadataFilter

        metadata = {
            "filename": "test.pdf",
            "page": 1,
            "confidence": 0.95,
            "processed": True,
            "notes": None,
        }

        filtered = MetadataFilter.filter_metadata(metadata)

        assert filtered == metadata

    def test_filter_metadata_excluded_fields(self):
        """Test that excluded fields are removed."""
        from tkr_docusearch.processing.handlers.metadata_filter import MetadataFilter

        metadata = {
            "filename": "test.pdf",
            "full_markdown": "x" * 1000000,  # Large field
            "structure": {"headings": []},
            "full_markdown_compressed": b"compressed_data",
            "markdown_error": "Error message",
            "_album_art_data": b"image_data",
            "_album_art_mime": "image/jpeg",
            "page": 1,
        }

        filtered = MetadataFilter.filter_metadata(metadata)

        # All excluded fields should be removed
        assert "full_markdown" not in filtered
        assert "structure" not in filtered
        assert "full_markdown_compressed" not in filtered
        assert "markdown_error" not in filtered
        assert "_album_art_data" not in filtered
        assert "_album_art_mime" not in filtered

        # Other fields should remain
        assert filtered["filename"] == "test.pdf"
        assert filtered["page"] == 1

    def test_filter_metadata_large_values(self):
        """Test that large values are filtered out."""
        from tkr_docusearch.processing.handlers.metadata_filter import MetadataFilter

        metadata = {
            "filename": "test.pdf",
            "small_text": "short",
            "large_text": "x" * 2000,  # Exceeds MAX_VALUE_SIZE
            "small_bytes": b"data",
            "large_bytes": b"x" * 2000,  # Exceeds MAX_VALUE_SIZE
            "page": 1,
        }

        filtered = MetadataFilter.filter_metadata(metadata)

        # Small values should pass through
        assert filtered["filename"] == "test.pdf"
        assert filtered["small_text"] == "short"
        assert filtered["small_bytes"] == b"data"
        assert filtered["page"] == 1

        # Large values should be filtered
        assert "large_text" not in filtered
        assert "large_bytes" not in filtered

    def test_filter_metadata_mixed_types(self):
        """Test filtering with mixed types."""
        from tkr_docusearch.processing.handlers.metadata_filter import MetadataFilter

        metadata = {
            "filename": "test.pdf",
            "page": 1,
            "full_markdown": "x" * 1000000,  # Excluded
            "large_field": "x" * 2000,  # Too large
            "normal_field": "normal text",
            "confidence": 0.95,
        }

        filtered = MetadataFilter.filter_metadata(metadata)

        # Should keep primitives and small values
        assert filtered["filename"] == "test.pdf"
        assert filtered["page"] == 1
        assert filtered["normal_field"] == "normal text"
        assert filtered["confidence"] == 0.95

        # Should exclude large/problematic fields
        assert "full_markdown" not in filtered
        assert "large_field" not in filtered

    def test_filter_metadata_empty_dict(self):
        """Test filtering empty dictionary."""
        from tkr_docusearch.processing.handlers.metadata_filter import MetadataFilter

        metadata = {}
        filtered = MetadataFilter.filter_metadata(metadata)

        assert filtered == {}

    def test_filter_metadata_all_excluded(self):
        """Test when all fields are excluded."""
        from tkr_docusearch.processing.handlers.metadata_filter import MetadataFilter

        metadata = {"full_markdown": "x" * 1000000, "structure": {}, "_album_art_data": b"data"}

        filtered = MetadataFilter.filter_metadata(metadata)

        assert filtered == {}

    def test_filter_metadata_boundary_size(self):
        """Test filtering at boundary of MAX_VALUE_SIZE."""
        from tkr_docusearch.processing.handlers.metadata_filter import MetadataFilter

        metadata = {
            "at_limit": "x" * 1000,  # Exactly at MAX_VALUE_SIZE
            "over_limit": "x" * 1001,  # Just over MAX_VALUE_SIZE
            "under_limit": "x" * 999,  # Just under MAX_VALUE_SIZE
        }

        filtered = MetadataFilter.filter_metadata(metadata)

        # At limit should pass
        assert "at_limit" in filtered
        # Over limit should be filtered
        assert "over_limit" not in filtered
        # Under limit should pass
        assert "under_limit" in filtered


# =============================================================================
# VisualEmbeddingHandler Tests
# =============================================================================


class TestVisualEmbeddingHandler:
    """Test visual embedding handler."""

    def test_init(self):
        """Test handler initialization."""
        from tkr_docusearch.processing.handlers.visual_embedding_handler import VisualEmbeddingHandler

        mock_storage = Mock()
        mock_config = Mock()

        handler = VisualEmbeddingHandler(mock_storage, mock_config)

        assert handler.storage_client == mock_storage
        assert handler.enhanced_mode_config == mock_config

    def test_store_visual_embeddings_basic(self):
        """Test storing basic visual embeddings."""
        from tkr_docusearch.processing.handlers.visual_embedding_handler import VisualEmbeddingHandler

        mock_storage = Mock()
        mock_storage.add_visual_embedding.return_value = "emb_123"

        handler = VisualEmbeddingHandler(mock_storage)

        # Create mock results
        mock_result_1 = Mock()
        mock_result_1.doc_id = "doc_123"
        mock_result_1.page_num = 1
        mock_result_1.embedding = np.random.randn(1031, 128).astype(np.float32)

        mock_result_2 = Mock()
        mock_result_2.doc_id = "doc_123"
        mock_result_2.page_num = 2
        mock_result_2.embedding = np.random.randn(1031, 128).astype(np.float32)

        visual_results = [mock_result_1, mock_result_2]

        safe_metadata = {"source": "test"}

        visual_ids, total_size = handler.store_visual_embeddings(
            visual_results=visual_results,
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            safe_doc_metadata=safe_metadata,
        )

        # Should call storage for each result
        assert mock_storage.add_visual_embedding.call_count == 2

        # Should return IDs and size
        assert visual_ids == ["emb_123", "emb_123"]
        assert total_size > 0

    def test_store_visual_embeddings_with_pages(self):
        """Test storing visual embeddings with page image paths."""
        from tkr_docusearch.processing.handlers.visual_embedding_handler import VisualEmbeddingHandler

        mock_storage = Mock()
        mock_storage.add_visual_embedding.return_value = "emb_123"

        handler = VisualEmbeddingHandler(mock_storage)

        # Create mock result
        mock_result = Mock()
        mock_result.doc_id = "doc_123"
        mock_result.page_num = 1
        mock_result.embedding = np.random.randn(1031, 128).astype(np.float32)

        # Create mock page
        mock_page = Mock()
        mock_page.page_num = 1
        mock_page.image_path = "/images/page_1.png"
        mock_page.thumb_path = "/images/page_1_thumb.png"

        visual_ids, total_size = handler.store_visual_embeddings(
            visual_results=[mock_result],
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            safe_doc_metadata={},
            pages=[mock_page],
        )

        # Should call storage with image paths
        call_args = mock_storage.add_visual_embedding.call_args
        assert call_args[1]["image_path"] == "/images/page_1.png"
        assert call_args[1]["thumb_path"] == "/images/page_1_thumb.png"

    def test_store_visual_embeddings_with_structure(self):
        """Test storing visual embeddings with structure metadata."""
        from tkr_docusearch.processing.handlers.visual_embedding_handler import VisualEmbeddingHandler

        mock_storage = Mock()
        mock_storage.add_visual_embedding.return_value = "emb_123"

        handler = VisualEmbeddingHandler(mock_storage)

        # Create mock result
        mock_result = Mock()
        mock_result.doc_id = "doc_123"
        mock_result.page_num = 1
        mock_result.embedding = np.random.randn(1031, 128).astype(np.float32)

        mock_structure = Mock()

        visual_ids, total_size = handler.store_visual_embeddings(
            visual_results=[mock_result],
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            safe_doc_metadata={},
            structure=mock_structure,
        )

        # Should call add_visual_embedding with metadata
        mock_storage.add_visual_embedding.assert_called_once()
        call_args = mock_storage.add_visual_embedding.call_args
        assert "metadata" in call_args[1]

    def test_store_visual_embeddings_no_pages(self):
        """Test storing visual embeddings without page lookup."""
        from tkr_docusearch.processing.handlers.visual_embedding_handler import VisualEmbeddingHandler

        mock_storage = Mock()
        mock_storage.add_visual_embedding.return_value = "emb_123"

        handler = VisualEmbeddingHandler(mock_storage)

        mock_result = Mock()
        mock_result.doc_id = "doc_123"
        mock_result.page_num = 1
        mock_result.embedding = np.random.randn(1031, 128).astype(np.float32)

        visual_ids, total_size = handler.store_visual_embeddings(
            visual_results=[mock_result],
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            safe_doc_metadata={},
        )

        # Should call storage with None paths
        call_args = mock_storage.add_visual_embedding.call_args
        assert call_args[1]["image_path"] is None
        assert call_args[1]["thumb_path"] is None

    def test_get_image_paths_page_exists(self):
        """Test getting image paths when page exists in lookup."""
        from tkr_docusearch.processing.handlers.visual_embedding_handler import VisualEmbeddingHandler

        handler = VisualEmbeddingHandler(Mock())

        mock_page = Mock()
        mock_page.image_path = "/images/page_1.png"
        mock_page.thumb_path = "/images/page_1_thumb.png"

        page_lookup = {1: mock_page}

        image_path, thumb_path = handler._get_image_paths(1, page_lookup)

        assert image_path == "/images/page_1.png"
        assert thumb_path == "/images/page_1_thumb.png"

    def test_get_image_paths_page_not_exists(self):
        """Test getting image paths when page doesn't exist."""
        from tkr_docusearch.processing.handlers.visual_embedding_handler import VisualEmbeddingHandler

        handler = VisualEmbeddingHandler(Mock())

        page_lookup = {}

        image_path, thumb_path = handler._get_image_paths(1, page_lookup)

        assert image_path is None
        assert thumb_path is None

    def test_prepare_metadata_no_enhanced(self):
        """Test metadata preparation without enhanced mode."""
        from tkr_docusearch.processing.handlers.visual_embedding_handler import VisualEmbeddingHandler

        mock_storage = Mock(spec=[])  # No _prepare_enhanced_visual_metadata

        handler = VisualEmbeddingHandler(mock_storage)

        base_metadata = {"filename": "test.pdf"}
        result = handler._prepare_metadata(base_metadata, None)

        assert result == base_metadata


# =============================================================================
# TextEmbeddingHandler Tests
# =============================================================================


class TestTextEmbeddingHandler:
    """Test text embedding handler."""

    def test_init(self):
        """Test handler initialization."""
        from tkr_docusearch.processing.handlers.text_embedding_handler import TextEmbeddingHandler

        mock_storage = Mock()
        mock_config = Mock()

        handler = TextEmbeddingHandler(mock_storage, mock_config)

        assert handler.storage_client == mock_storage
        assert handler.enhanced_mode_config == mock_config

    def test_store_text_embeddings_basic(self):
        """Test storing basic text embeddings."""
        from tkr_docusearch.processing.handlers.text_embedding_handler import TextEmbeddingHandler

        mock_storage = Mock()
        mock_storage.add_text_embedding.return_value = "emb_123"

        handler = TextEmbeddingHandler(mock_storage)

        # Create mock results
        mock_result_1 = Mock()
        mock_result_1.doc_id = "doc_123"
        mock_result_1.chunk_id = "doc_123-chunk0"
        mock_result_1.page_num = 1
        mock_result_1.text = "This is test text for embedding"
        mock_result_1.embedding = np.random.randn(30, 128).astype(np.float32)

        mock_result_2 = Mock()
        mock_result_2.doc_id = "doc_123"
        mock_result_2.chunk_id = "doc_123-chunk1"
        mock_result_2.page_num = 1
        mock_result_2.text = "Another chunk of text"
        mock_result_2.embedding = np.random.randn(30, 128).astype(np.float32)

        text_results = [mock_result_1, mock_result_2]

        # Create mock chunks
        mock_chunk_1 = Mock()
        mock_chunk_1.chunk_id = "doc_123-chunk0"
        mock_chunk_1.context = None
        mock_chunk_1.start_time = None
        mock_chunk_1.end_time = None

        mock_chunk_2 = Mock()
        mock_chunk_2.chunk_id = "doc_123-chunk1"
        mock_chunk_2.context = None
        mock_chunk_2.start_time = None
        mock_chunk_2.end_time = None

        text_chunks = [mock_chunk_1, mock_chunk_2]

        safe_metadata = {"source": "test"}

        text_ids, total_size = handler.store_text_embeddings(
            text_results=text_results,
            text_chunks=text_chunks,
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            safe_doc_metadata=safe_metadata,
        )

        # Should call storage for each result
        assert mock_storage.add_text_embedding.call_count == 2

        # Should return IDs and size
        assert text_ids == ["emb_123", "emb_123"]
        assert total_size > 0

    def test_store_text_embeddings_with_timestamps(self):
        """Test storing text embeddings with timestamps."""
        from tkr_docusearch.processing.handlers.text_embedding_handler import TextEmbeddingHandler

        mock_storage = Mock()
        mock_storage.add_text_embedding.return_value = "emb_123"

        handler = TextEmbeddingHandler(mock_storage)

        # Create mock result
        mock_result = Mock()
        mock_result.doc_id = "doc_123"
        mock_result.chunk_id = "doc_123-chunk0"
        mock_result.page_num = 1
        mock_result.text = "This is test text"
        mock_result.embedding = np.random.randn(30, 128).astype(np.float32)

        # Create mock chunk with timestamps
        mock_chunk = Mock()
        mock_chunk.chunk_id = "doc_123-chunk0"
        mock_chunk.context = None
        mock_chunk.start_time = 0.5
        mock_chunk.end_time = 5.2

        text_ids, total_size = handler.store_text_embeddings(
            text_results=[mock_result],
            text_chunks=[mock_chunk],
            filename="audio.mp3",
            file_path="/path/to/audio.mp3",
            safe_doc_metadata={},
        )

        # Should call storage with timestamps in metadata
        call_args = mock_storage.add_text_embedding.call_args
        metadata = call_args[1]["metadata"]
        assert metadata["start_time"] == 0.5
        assert metadata["end_time"] == 5.2
        assert metadata["has_timestamps"] is True

    def test_store_text_embeddings_without_timestamps(self):
        """Test storing text embeddings without timestamps."""
        from tkr_docusearch.processing.handlers.text_embedding_handler import TextEmbeddingHandler

        mock_storage = Mock()
        mock_storage.add_text_embedding.return_value = "emb_123"

        handler = TextEmbeddingHandler(mock_storage)

        mock_result = Mock()
        mock_result.doc_id = "doc_123"
        mock_result.chunk_id = "doc_123-chunk0"
        mock_result.page_num = 1
        mock_result.text = "This is test text"
        mock_result.embedding = np.random.randn(30, 128).astype(np.float32)

        # Create mock chunk without timestamps
        mock_chunk = Mock()
        mock_chunk.chunk_id = "doc_123-chunk0"
        mock_chunk.context = None
        mock_chunk.start_time = None
        mock_chunk.end_time = None

        text_ids, total_size = handler.store_text_embeddings(
            text_results=[mock_result],
            text_chunks=[mock_chunk],
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            safe_doc_metadata={},
        )

        # Should call storage without timestamps in metadata
        call_args = mock_storage.add_text_embedding.call_args
        metadata = call_args[1]["metadata"]
        assert "start_time" not in metadata
        assert "end_time" not in metadata
        assert metadata["has_timestamps"] is False

    def test_store_text_embeddings_with_context(self):
        """Test storing text embeddings with context metadata."""
        from tkr_docusearch.processing.handlers.text_embedding_handler import TextEmbeddingHandler

        mock_storage = Mock()
        mock_storage.add_text_embedding.return_value = "emb_123"

        handler = TextEmbeddingHandler(mock_storage)

        mock_result = Mock()
        mock_result.doc_id = "doc_123"
        mock_result.chunk_id = "doc_123-chunk0"
        mock_result.page_num = 1
        mock_result.text = "This is test text"
        mock_result.embedding = np.random.randn(30, 128).astype(np.float32)

        # Create mock chunk with context
        mock_context = Mock()
        mock_chunk = Mock()
        mock_chunk.chunk_id = "doc_123-chunk0"
        mock_chunk.context = mock_context
        mock_chunk.start_time = None
        mock_chunk.end_time = None

        text_ids, total_size = handler.store_text_embeddings(
            text_results=[mock_result],
            text_chunks=[mock_chunk],
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            safe_doc_metadata={},
        )

        # Should call add_text_embedding with metadata
        mock_storage.add_text_embedding.assert_called_once()
        call_args = mock_storage.add_text_embedding.call_args
        assert "metadata" in call_args[1]

    def test_build_base_metadata(self):
        """Test building base metadata for text embedding."""
        from tkr_docusearch.processing.handlers.text_embedding_handler import TextEmbeddingHandler

        handler = TextEmbeddingHandler(Mock())

        mock_result = Mock()
        mock_result.chunk_id = "doc_123-chunk0"
        mock_result.page_num = 1
        mock_result.text = "This is test text for metadata building"

        mock_chunk = Mock()
        mock_chunk.start_time = 1.5
        mock_chunk.end_time = 3.0

        base_metadata = handler._build_base_metadata(
            result=mock_result,
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            safe_doc_metadata={"extra": "data"},
            chunk=mock_chunk,
        )

        assert base_metadata["filename"] == "test.pdf"
        assert base_metadata["chunk_id"] == "doc_123-chunk0"
        assert base_metadata["page"] == 1
        assert "This is test text" in base_metadata["text_preview"]
        assert base_metadata["word_count"] == 7
        assert base_metadata["source_path"] == "/path/to/test.pdf"
        assert base_metadata["extra"] == "data"
        assert base_metadata["start_time"] == 1.5
        assert base_metadata["end_time"] == 3.0
        assert base_metadata["has_timestamps"] is True

    def test_build_base_metadata_no_chunk(self):
        """Test building base metadata without chunk."""
        from tkr_docusearch.processing.handlers.text_embedding_handler import TextEmbeddingHandler

        handler = TextEmbeddingHandler(Mock())

        mock_result = Mock()
        mock_result.chunk_id = "doc_123-chunk0"
        mock_result.page_num = 1
        mock_result.text = "Test text"

        base_metadata = handler._build_base_metadata(
            result=mock_result,
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            safe_doc_metadata={},
            chunk=None,
        )

        assert base_metadata["filename"] == "test.pdf"
        assert "start_time" not in base_metadata
        assert "end_time" not in base_metadata
        assert "has_timestamps" not in base_metadata

    def test_get_chunk_context_with_context(self):
        """Test getting chunk context when present."""
        from tkr_docusearch.processing.handlers.text_embedding_handler import TextEmbeddingHandler

        handler = TextEmbeddingHandler(Mock())

        mock_context = Mock()
        mock_chunk = Mock()
        mock_chunk.context = mock_context

        result = handler._get_chunk_context(mock_chunk)

        assert result == mock_context

    def test_get_chunk_context_no_context(self):
        """Test getting chunk context when not present."""
        from tkr_docusearch.processing.handlers.text_embedding_handler import TextEmbeddingHandler

        handler = TextEmbeddingHandler(Mock())

        mock_chunk = Mock()
        mock_chunk.context = None

        result = handler._get_chunk_context(mock_chunk)

        assert result is None

    def test_get_chunk_context_no_chunk(self):
        """Test getting chunk context with None chunk."""
        from tkr_docusearch.processing.handlers.text_embedding_handler import TextEmbeddingHandler

        handler = TextEmbeddingHandler(Mock())

        result = handler._get_chunk_context(None)

        assert result is None

    def test_prepare_metadata_no_enhanced(self):
        """Test metadata preparation without enhanced mode."""
        from tkr_docusearch.processing.handlers.text_embedding_handler import TextEmbeddingHandler

        mock_storage = Mock(spec=[])  # No _prepare_enhanced_text_metadata

        handler = TextEmbeddingHandler(mock_storage)

        base_metadata = {"filename": "test.pdf"}
        result = handler._prepare_metadata(base_metadata, None)

        assert result == base_metadata

    def test_prepare_metadata_no_context(self):
        """Test metadata preparation without context."""
        from tkr_docusearch.processing.handlers.text_embedding_handler import TextEmbeddingHandler

        mock_storage = Mock()
        mock_storage._prepare_enhanced_text_metadata = Mock(return_value={"enhanced": True})

        handler = TextEmbeddingHandler(mock_storage)

        base_metadata = {"filename": "test.pdf"}
        result = handler._prepare_metadata(base_metadata, None)

        # Should not call enhanced metadata when no context
        mock_storage._prepare_enhanced_text_metadata.assert_not_called()
        assert result == base_metadata
