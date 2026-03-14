"""
Test audio placeholder functionality.

Verify that audio files without album art get a placeholder image.
"""

from pathlib import Path

import pytest

from tkr_docusearch.processing.audio_metadata import AudioMetadata, save_album_art


def test_placeholder_created_for_audio_without_album_art(tmp_path):
    """Test that placeholder is copied when audio file has no album art."""
    # Setup: Create temporary directories
    base_dir = tmp_path / "images"
    placeholder_dir = base_dir / "placeholders"
    placeholder_dir.mkdir(parents=True)

    # Create a dummy placeholder file
    placeholder_file = placeholder_dir / "audio-placeholder.svg"
    placeholder_file.write_text("<svg>test placeholder</svg>")

    # Create AudioMetadata without album art
    metadata = AudioMetadata(has_album_art=False, album_art_data=None)

    # Execute: Save album art (should use placeholder)
    doc_id = "test-audio-123"
    result_path = save_album_art(
        doc_id=doc_id, metadata=metadata, base_dir=str(base_dir), use_placeholder=True
    )

    # Verify: Placeholder was copied
    assert result_path is not None
    assert "cover.svg" in result_path

    # Check file exists and has correct content
    result_file = Path(result_path)
    assert result_file.exists()
    assert result_file.read_text() == "<svg>test placeholder</svg>"


def test_actual_album_art_saved_instead_of_placeholder(tmp_path):
    """Test that actual album art is saved when present (not placeholder)."""
    # Setup
    base_dir = tmp_path / "images"
    placeholder_dir = base_dir / "placeholders"
    placeholder_dir.mkdir(parents=True)

    # Create placeholder (should NOT be used)
    placeholder_file = placeholder_dir / "audio-placeholder.svg"
    placeholder_file.write_text("<svg>placeholder</svg>")

    # Create AudioMetadata WITH album art
    album_art_data = b"\xff\xd8\xff\xe0"  # JPEG header
    metadata = AudioMetadata(
        has_album_art=True, album_art_data=album_art_data, album_art_mime="image/jpeg"
    )

    # Execute: Save album art (should use actual art)
    doc_id = "test-audio-456"
    result_path = save_album_art(
        doc_id=doc_id, metadata=metadata, base_dir=str(base_dir), use_placeholder=True
    )

    # Verify: Actual album art was saved (not placeholder)
    assert result_path is not None
    assert "cover.jpg" in result_path
    assert "cover.svg" not in result_path

    # Check file contains actual album art data
    result_file = Path(result_path)
    assert result_file.exists()
    assert result_file.read_bytes() == album_art_data


def test_no_placeholder_when_disabled(tmp_path):
    """Test that no placeholder is used when use_placeholder=False."""
    # Setup
    base_dir = tmp_path / "images"

    # Create AudioMetadata without album art
    metadata = AudioMetadata(has_album_art=False, album_art_data=None)

    # Execute: Save album art with placeholder disabled
    doc_id = "test-audio-789"
    result_path = save_album_art(
        doc_id=doc_id, metadata=metadata, base_dir=str(base_dir), use_placeholder=False
    )

    # Verify: No file was created
    assert result_path is None


def test_placeholder_integration_with_real_file():
    """Integration test with actual placeholder file."""
    # Check if real placeholder exists
    placeholder_path = Path("data/images/placeholders/audio-placeholder.svg")

    if not placeholder_path.exists():
        pytest.skip("Placeholder file not found - run from project root")

    # Create metadata without album art
    metadata = AudioMetadata(has_album_art=False, album_art_data=None)

    # Save with real placeholder
    doc_id = "integration-test-audio"
    result_path = save_album_art(
        doc_id=doc_id, metadata=metadata, base_dir="data/images", use_placeholder=True
    )

    # Verify
    assert result_path is not None
    assert Path(result_path).exists()
    assert "cover.svg" in result_path

    # Cleanup
    try:
        Path(result_path).unlink()
        Path(result_path).parent.rmdir()
    except Exception:
        pass  # Cleanup not critical


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
