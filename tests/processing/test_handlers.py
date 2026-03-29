"""
Tests for processing/handlers modules.

Tests cover:
- AlbumArtHandler: Album art saving for audio files
- MetadataFilter: Koji metadata filtering

Target: 80%+ coverage for each module
"""

from unittest.mock import Mock, patch

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

        with patch("src.processing.audio_metadata.save_album_art") as mock_save:
            with patch("src.processing.audio_metadata.AudioMetadata") as mock_audio_metadata:
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

        with patch("src.processing.audio_metadata.save_album_art") as mock_save:
            with patch("src.processing.audio_metadata.AudioMetadata") as mock_audio_metadata:
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

        with patch("src.processing.audio_metadata.save_album_art") as mock_save:
            with patch("src.processing.audio_metadata.AudioMetadata"):
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

        with patch("src.processing.audio_metadata.save_album_art") as mock_save:
            with patch("src.processing.audio_metadata.AudioMetadata"):
                # save_album_art returns None
                mock_save.return_value = None

                result = AlbumArtHandler.save_album_art_if_present("doc123", doc_metadata)

                assert result is None
                assert "album_art_path" not in doc_metadata


# =============================================================================
# MetadataFilter Tests
# =============================================================================


class TestMetadataFilter:
    """Test metadata filter for Koji."""

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
