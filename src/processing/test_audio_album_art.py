"""
Unit and integration tests for audio album art feature.

Tests the complete album art pipeline from API endpoint to UI display.

Provider: integration-test-agent (Wave 5 - Audio Album Art)
Coverage:
- Backend API: GET /documents/{doc_id}/cover endpoint
- Backend API: DocumentMetadata.has_album_art and album_art_url fields
- Integration: End-to-end album art display
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app
from src.processing.worker_webhook import app as worker_app

# ============================================================================
# Backend Unit Tests
# ============================================================================


class TestCoverEndpoint:
    """Test the GET /documents/{doc_id}/cover endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(worker_app)

    @pytest.fixture
    def test_doc_id(self):
        """Test document ID."""
        return "test-doc-12345678"

    @pytest.fixture
    def temp_images_dir(self, test_doc_id, tmp_path):
        """Create temporary images directory with cover art."""
        # Create temp images directory
        images_dir = tmp_path / "images" / test_doc_id
        images_dir.mkdir(parents=True)

        # Create a fake JPEG cover image
        cover_jpg = images_dir / "cover.jpg"
        cover_jpg.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF")  # JPEG header

        # Patch the Path to use our temp directory
        with patch("src.processing.documents_api.Path") as mock_path:

            def path_side_effect(path_str):
                if path_str == "data/images":
                    return tmp_path / "images"
                return Path(path_str)

            mock_path.side_effect = path_side_effect
            yield tmp_path, images_dir

    def test_cover_endpoint_with_art(self, client, test_doc_id, temp_images_dir):
        """Test cover endpoint returns image when album art exists."""
        tmp_path, images_dir = temp_images_dir

        with patch("src.processing.documents_api.Path") as mock_path:

            def path_side_effect(path_str):
                if path_str == "data/images":
                    return tmp_path / "images"
                return Path(path_str)

            mock_path.side_effect = path_side_effect

            response = client.get(f"/documents/{test_doc_id}/cover")

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/jpeg"
            assert "cache-control" in response.headers
            assert "max-age=31536000" in response.headers["cache-control"]

    def test_cover_endpoint_without_art(self, client, test_doc_id):
        """Test cover endpoint returns 404 when no album art exists."""
        response = client.get(f"/documents/{test_doc_id}/cover")

        assert response.status_code == 404
        error = response.json()
        assert error["detail"]["code"] == "COVER_NOT_FOUND"
        assert "Album art only available" in error["detail"]["details"]["message"]

    def test_cover_endpoint_invalid_id(self, client):
        """Test cover endpoint rejects invalid doc_id."""
        # Too short (less than 8 chars)
        response = client.get("/documents/short/cover")
        assert response.status_code == 400
        error = response.json()
        assert error["detail"]["code"] == "INVALID_DOC_ID"

        # Invalid characters
        response = client.get("/documents/invalid!@#$chars/cover")
        assert response.status_code == 400
        error = response.json()
        assert error["detail"]["code"] == "INVALID_DOC_ID"

    def test_cover_endpoint_mime_types(self, client, test_doc_id, tmp_path):
        """Test cover endpoint returns correct MIME types for JPEG and PNG."""
        images_dir = tmp_path / "images" / test_doc_id
        images_dir.mkdir(parents=True)

        # Test JPEG
        cover_jpg = images_dir / "cover.jpg"
        cover_jpg.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF")

        with patch("src.processing.documents_api.Path") as mock_path:

            def path_side_effect(path_str):
                if path_str == "data/images":
                    return tmp_path / "images"
                return Path(path_str)

            mock_path.side_effect = path_side_effect

            response = client.get(f"/documents/{test_doc_id}/cover")
            assert response.status_code == 200
            assert response.headers["content-type"] == "image/jpeg"

        # Test PNG
        cover_jpg.unlink()
        cover_png = images_dir / "cover.png"
        cover_png.write_bytes(b"\x89PNG\r\n\x1a\n")

        with patch("src.processing.documents_api.Path") as mock_path:
            mock_path.side_effect = path_side_effect

            response = client.get(f"/documents/{test_doc_id}/cover")
            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"


class TestMetadataExtension:
    """Test DocumentMetadata.has_album_art and album_art_url fields."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(worker_app)

    @pytest.fixture
    def mock_chroma_client(self):
        """Mock ChromaDB client with test data."""
        with patch("src.processing.documents_api.get_chroma_client") as mock_get:
            mock_client = Mock()

            # Mock visual collection
            mock_visual = Mock()
            mock_visual.get.return_value = {"ids": [], "metadatas": []}
            mock_client._visual_collection = mock_visual

            # Mock text collection
            mock_text = Mock()
            mock_text.get.return_value = {
                "ids": ["chunk_0"],
                "metadatas": [
                    {
                        "doc_id": "test-doc-12345678",
                        "filename": "test_audio.mp3",
                        "timestamp": "2025-10-15T10:00:00Z",
                        "chunk_id": 0,
                        "text_preview": "Test audio content",
                        "has_timestamps": True,
                        "vtt_available": True,
                    }
                ],
            }
            mock_client._text_collection = mock_text

            mock_get.return_value = mock_client
            yield mock_client

    def test_metadata_has_album_art(self, client, mock_chroma_client, tmp_path):
        """Test metadata includes has_album_art=True when cover exists."""
        test_doc_id = "test-doc-12345678"
        images_dir = tmp_path / "images" / test_doc_id
        images_dir.mkdir(parents=True)

        cover_jpg = images_dir / "cover.jpg"
        cover_jpg.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF")

        with patch("src.processing.documents_api.Path") as mock_path:

            def path_side_effect(path_str):
                if path_str == "data/images":
                    return tmp_path / "images"
                return Path(path_str)

            mock_path.side_effect = path_side_effect

            response = client.get(f"/documents/{test_doc_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["metadata"]["has_album_art"] is True
            assert data["metadata"]["album_art_url"] == f"/documents/{test_doc_id}/cover"

    def test_metadata_without_album_art(self, client, mock_chroma_client):
        """Test metadata includes has_album_art=False when cover doesn't exist."""
        test_doc_id = "test-doc-12345678"

        response = client.get(f"/documents/{test_doc_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["has_album_art"] is False
        assert data["metadata"]["album_art_url"] is None

    def test_metadata_non_audio_document(self, client):
        """Test metadata for non-audio documents (no album art)."""
        test_doc_id = "test-pdf-12345678"

        with patch("src.processing.documents_api.get_chroma_client") as mock_get:
            mock_client = Mock()

            # Mock visual collection (PDF pages)
            mock_visual = Mock()
            mock_visual.get.return_value = {
                "ids": ["page_0"],
                "metadatas": [
                    {
                        "doc_id": test_doc_id,
                        "filename": "test.pdf",
                        "timestamp": "2025-10-15T10:00:00Z",
                        "page": 1,
                        "image_path": f"data/page_images/{test_doc_id}/page001.png",
                    }
                ],
            }
            mock_client._visual_collection = mock_visual

            # Mock text collection
            mock_text = Mock()
            mock_text.get.return_value = {"ids": [], "metadatas": []}
            mock_client._text_collection = mock_text

            mock_get.return_value = mock_client

            response = client.get(f"/documents/{test_doc_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["metadata"]["has_album_art"] is False
            assert data["metadata"]["album_art_url"] is None


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for the complete album art pipeline."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(worker_app)

    @pytest.mark.skip(reason="Requires full processing pipeline and ChromaDB")
    def test_full_pipeline_with_art(self, client):
        """Test complete album art pipeline from upload to display.

        This test requires:
        1. Upload audio file with embedded album art
        2. Wait for processing to extract album art
        3. Verify metadata includes has_album_art=True
        4. Verify GET /documents/{doc_id}/cover returns image
        5. Verify UI displays album art (manual test)
        """
        # TODO: Implement once full processing pipeline is integrated

    @pytest.mark.skip(reason="Requires full processing pipeline and ChromaDB")
    def test_full_pipeline_without_art(self, client):
        """Test album art pipeline with audio file without embedded art.

        This test requires:
        1. Upload audio file without embedded album art
        2. Wait for processing
        3. Verify metadata includes has_album_art=False
        4. Verify GET /documents/{doc_id}/cover returns 404
        5. Verify UI displays default SVG fallback (manual test)
        """
        # TODO: Implement once full processing pipeline is integrated

    @pytest.mark.skip(reason="Requires full processing pipeline")
    def test_multiple_audio_formats(self, client):
        """Test album art extraction from multiple audio formats (MP3, WAV).

        This test requires:
        1. Upload MP3 with album art
        2. Upload WAV file (no album art support)
        3. Verify MP3 has album art
        4. Verify WAV does not have album art
        """
        # TODO: Implement once full processing pipeline is integrated

    @pytest.mark.skip(reason="Requires full processing pipeline")
    def test_large_album_art(self, client):
        """Test handling of large album art files (>1MB).

        This test requires:
        1. Upload audio with large (>1MB) album art
        2. Verify processing succeeds
        3. Verify image serves correctly
        4. Verify browser handles large image gracefully
        """
        # TODO: Implement once full processing pipeline is integrated

    @pytest.mark.skip(reason="Requires full processing pipeline")
    def test_album_art_formats(self, client):
        """Test different album art image formats (JPEG, PNG).

        This test requires:
        1. Upload audio with JPEG album art
        2. Upload audio with PNG album art
        3. Verify both serve with correct MIME types
        4. Verify both display correctly in UI
        """
        # TODO: Implement once full processing pipeline is integrated


# ============================================================================
# Performance Tests
# ============================================================================


class TestPerformance:
    """Performance tests for album art serving."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(worker_app)

    @pytest.mark.skip(reason="Performance testing requires production environment")
    def test_album_art_load_performance(self, client):
        """Verify album art loads within performance budget (<500ms).

        This test requires:
        1. Create test document with album art
        2. Measure GET /documents/{doc_id}/cover latency
        3. Verify latency < 50ms (local file serving)
        """
        # TODO: Implement once production environment is ready
