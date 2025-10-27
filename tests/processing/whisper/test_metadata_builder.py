"""
Unit tests for metadata builder.

Tests the build_audio_metadata() function to ensure IC-002 metadata format
compliance and proper integration with ID3 extraction.
"""

import pytest

from src.processing.audio_metadata import AudioMetadata
from src.processing.whisper.metadata_builder import (
    _get_mimetype,
    _merge_id3_metadata,
    _validate_required_fields,
    build_audio_metadata,
)


class TestGetMimetype:
    """Test MIME type mapping."""

    def test_mp3_mimetype(self):
        """Test MP3 MIME type."""
        assert _get_mimetype("mp3") == "audio/mpeg"

    def test_wav_mimetype(self):
        """Test WAV MIME type."""
        assert _get_mimetype("wav") == "audio/wav"

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        assert _get_mimetype("MP3") == "audio/mpeg"
        assert _get_mimetype("WAV") == "audio/wav"

    def test_unknown_defaults_to_mpeg(self):
        """Test unknown formats default to audio/mpeg."""
        assert _get_mimetype("unknown") == "audio/mpeg"


class TestValidateRequiredFields:
    """Test IC-002 required field validation."""

    def test_validate_all_required_fields_present(self):
        """Test validation passes with all required fields."""
        metadata = {
            "format_type": "audio",
            "has_word_timestamps": True,
            "audio_duration_seconds": 10.5,
            "num_pages": 1,
            "has_images": False,
            "transcript_method": "whisper",
            "asr_model_used": "turbo",
        }

        # Should not raise
        _validate_required_fields(metadata)

    def test_validate_missing_field_raises(self):
        """Test validation fails with missing required field."""
        metadata = {
            "format_type": "audio",
            "has_word_timestamps": True,
            "audio_duration_seconds": 10.5,
            "num_pages": 1,
            "has_images": False,
            # Missing: transcript_method, asr_model_used
        }

        with pytest.raises(ValueError, match="Missing required metadata fields"):
            _validate_required_fields(metadata)

    def test_validate_wrong_format_type_raises(self):
        """Test validation fails with wrong format_type."""
        metadata = {
            "format_type": "pdf",  # Wrong!
            "has_word_timestamps": True,
            "audio_duration_seconds": 10.5,
            "num_pages": 1,
            "has_images": False,
            "transcript_method": "whisper",
            "asr_model_used": "turbo",
        }

        with pytest.raises(ValueError, match="format_type must be 'audio'"):
            _validate_required_fields(metadata)

    def test_validate_wrong_word_timestamps_raises(self):
        """Test validation fails with has_word_timestamps=False."""
        metadata = {
            "format_type": "audio",
            "has_word_timestamps": False,  # Wrong!
            "audio_duration_seconds": 10.5,
            "num_pages": 1,
            "has_images": False,
            "transcript_method": "whisper",
            "asr_model_used": "turbo",
        }

        with pytest.raises(ValueError, match="has_word_timestamps must be True"):
            _validate_required_fields(metadata)

    def test_validate_wrong_num_pages_raises(self):
        """Test validation fails with num_pages != 1."""
        metadata = {
            "format_type": "audio",
            "has_word_timestamps": True,
            "audio_duration_seconds": 10.5,
            "num_pages": 5,  # Wrong!
            "has_images": False,
            "transcript_method": "whisper",
            "asr_model_used": "turbo",
        }

        with pytest.raises(ValueError, match="num_pages must be 1 for audio"):
            _validate_required_fields(metadata)

    def test_validate_wrong_has_images_raises(self):
        """Test validation fails with has_images=True."""
        metadata = {
            "format_type": "audio",
            "has_word_timestamps": True,
            "audio_duration_seconds": 10.5,
            "num_pages": 1,
            "has_images": True,  # Wrong!
            "transcript_method": "whisper",
            "asr_model_used": "turbo",
        }

        with pytest.raises(ValueError, match="has_images must be False for audio"):
            _validate_required_fields(metadata)

    def test_validate_wrong_duration_type_raises(self):
        """Test validation fails with non-numeric duration."""
        metadata = {
            "format_type": "audio",
            "has_word_timestamps": True,
            "audio_duration_seconds": "10.5",  # Wrong type!
            "num_pages": 1,
            "has_images": False,
            "transcript_method": "whisper",
            "asr_model_used": "turbo",
        }

        with pytest.raises(ValueError, match="audio_duration_seconds must be numeric"):
            _validate_required_fields(metadata)


class TestMergeId3Metadata:
    """Test ID3 metadata merging."""

    def test_merge_basic_id3_tags(self):
        """Test merging basic ID3 tags (title, artist, year)."""
        metadata = {
            "title": "original.mp3",
            "author": "",
            "created": "",
        }

        id3 = AudioMetadata(
            title="Test Song",
            artist="Test Artist",
            year="2024",
        )

        _merge_id3_metadata(metadata, id3)

        # Should override defaults
        assert metadata["title"] == "Test Song"
        assert metadata["author"] == "Test Artist"
        assert metadata["created"] == "2024"

        # Should add id3_ prefixed fields
        assert metadata["id3_title"] == "Test Song"
        assert metadata["id3_artist"] == "Test Artist"
        assert metadata["id3_year"] == "2024"

    def test_merge_extended_id3_tags(self):
        """Test merging extended ID3 tags."""
        metadata = {}

        id3 = AudioMetadata(
            title="Test Song",
            artist="Test Artist",
            album="Test Album",
            genre="Rock",
            track_number="1",
            composer="Test Composer",
        )

        _merge_id3_metadata(metadata, id3)

        assert metadata["id3_album"] == "Test Album"
        assert metadata["id3_genre"] == "Rock"
        assert metadata["id3_track"] == "1"
        assert metadata["id3_composer"] == "Test Composer"

    def test_merge_album_art_metadata(self):
        """Test merging album art metadata."""
        metadata = {}

        id3 = AudioMetadata(
            has_album_art=True,
            album_art_mime="image/jpeg",
            album_art_data=b"\xff\xd8\xff\xe0",  # JPEG header
        )

        _merge_id3_metadata(metadata, id3)

        assert metadata["has_album_art"] is True
        assert metadata["_album_art_mime"] == "image/jpeg"
        assert metadata["_album_art_data"] == b"\xff\xd8\xff\xe0"

    def test_merge_audio_properties(self):
        """Test merging audio properties."""
        metadata = {}

        id3 = AudioMetadata(
            bitrate_kbps=320,
            sample_rate_hz=44100,
            channels=2,
            encoder="LAME",
        )

        _merge_id3_metadata(metadata, id3)

        assert metadata["audio_bitrate_kbps"] == 320
        assert metadata["audio_sample_rate_hz"] == 44100
        assert metadata["audio_channels"] == 2
        assert metadata["audio_encoder"] == "LAME"

    def test_merge_partial_id3(self):
        """Test merging partial ID3 data (only some fields present)."""
        metadata = {"title": "original.mp3"}

        id3 = AudioMetadata(
            title="Test Song",
            artist=None,  # Missing
            album="Test Album",
        )

        _merge_id3_metadata(metadata, id3)

        # Should only set present fields
        assert metadata["title"] == "Test Song"
        assert metadata["id3_album"] == "Test Album"
        assert "id3_artist" not in metadata  # Not set since None


class TestBuildAudioMetadata:
    """Test complete metadata building."""

    def test_build_basic_metadata(self):
        """Test building metadata without ID3."""
        whisper_result = {
            "text": "Hello world",
            "segments": [{"start": 0.0, "end": 5.0, "text": "Hello world"}],
            "language": "en",
            "duration": 10.5,
        }

        metadata = build_audio_metadata(
            whisper_result=whisper_result,
            file_path="/path/to/test.mp3",
            asr_model="turbo",
            asr_language="en",
            audio_id3_metadata=None,
        )

        # Validate IC-002 required fields
        assert metadata["format_type"] == "audio"
        assert metadata["has_word_timestamps"] is True
        assert metadata["audio_duration_seconds"] == 10.5
        assert metadata["num_pages"] == 1
        assert metadata["has_images"] is False
        assert metadata["transcript_method"] == "whisper"
        assert metadata["asr_model_used"] == "turbo"
        assert metadata["asr_language"] == "en"

        # Validate file metadata
        assert metadata["title"] == "test.mp3"
        assert metadata["format"] == "mp3"
        assert metadata["audio_format"] == "mp3"
        assert metadata["mimetype"] == "audio/mpeg"
        assert metadata["original_filename"] == "test.mp3"

        # Validate markdown metadata
        assert metadata["markdown_extracted"] is True
        assert metadata["markdown_error"] is None
        assert metadata["markdown_length"] == len("Hello world")

    def test_build_with_id3_metadata(self):
        """Test building metadata with ID3 tags."""
        whisper_result = {
            "text": "Test transcript",
            "segments": [{"start": 0.0, "end": 5.0, "text": "Test"}],
            "language": "en",
            "duration": 15.0,
        }

        id3 = AudioMetadata(
            title="Test Song",
            artist="Test Artist",
            album="Test Album",
            year="2024",
            has_album_art=True,
        )

        metadata = build_audio_metadata(
            whisper_result=whisper_result,
            file_path="/path/to/test.mp3",
            asr_model="base",
            asr_language="en",
            audio_id3_metadata=id3,
        )

        # ID3 should override defaults
        assert metadata["title"] == "Test Song"
        assert metadata["author"] == "Test Artist"
        assert metadata["created"] == "2024"

        # ID3 fields should be present
        assert metadata["id3_title"] == "Test Song"
        assert metadata["id3_artist"] == "Test Artist"
        assert metadata["id3_album"] == "Test Album"
        assert metadata["id3_year"] == "2024"
        assert metadata["has_album_art"] is True

    def test_build_wav_file_metadata(self):
        """Test building metadata for WAV file."""
        whisper_result = {
            "text": "WAV test",
            "segments": [{"start": 0.0, "end": 3.0, "text": "WAV"}],
            "language": "en",
            "duration": 5.0,
        }

        metadata = build_audio_metadata(
            whisper_result=whisper_result,
            file_path="/path/to/test.wav",
            asr_model="turbo",
            asr_language="en",
            audio_id3_metadata=None,
        )

        assert metadata["format"] == "wav"
        assert metadata["audio_format"] == "wav"
        assert metadata["mimetype"] == "audio/wav"

    def test_build_language_detection(self):
        """Test language detection override."""
        whisper_result = {
            "text": "Bonjour",
            "segments": [{"start": 0.0, "end": 2.0, "text": "Bonjour"}],
            "language": "fr",  # Detected by whisper
            "duration": 3.0,
        }

        metadata = build_audio_metadata(
            whisper_result=whisper_result,
            file_path="/path/to/test.mp3",
            asr_model="turbo",
            asr_language="auto",  # Requested auto-detect
            audio_id3_metadata=None,
        )

        # Should use detected language
        assert metadata["asr_language"] == "fr"

    def test_build_empty_whisper_result_raises(self):
        """Test that empty whisper result raises error."""
        with pytest.raises(ValueError, match="whisper_result cannot be empty"):
            build_audio_metadata(
                whisper_result=None,
                file_path="/path/to/test.mp3",
                asr_model="turbo",
                asr_language="en",
                audio_id3_metadata=None,
            )

    def test_build_empty_file_path_raises(self):
        """Test that empty file path raises error."""
        whisper_result = {
            "text": "Test",
            "segments": [{"start": 0.0, "end": 1.0, "text": "Test"}],
            "language": "en",
            "duration": 1.0,
        }

        with pytest.raises(ValueError, match="file_path cannot be empty"):
            build_audio_metadata(
                whisper_result=whisper_result,
                file_path="",
                asr_model="turbo",
                asr_language="en",
                audio_id3_metadata=None,
            )

    def test_build_validates_required_fields(self):
        """Test that build_audio_metadata validates required fields."""
        whisper_result = {
            "text": "Test",
            "segments": [{"start": 0.0, "end": 1.0, "text": "Test"}],
            "language": "en",
            "duration": 5.0,
        }

        # Should not raise - validation should pass
        metadata = build_audio_metadata(
            whisper_result=whisper_result,
            file_path="/path/to/test.mp3",
            asr_model="turbo",
            asr_language="en",
            audio_id3_metadata=None,
        )

        # All required fields should be present and valid
        assert metadata["format_type"] == "audio"
        assert metadata["has_word_timestamps"] is True
        assert metadata["num_pages"] == 1
        assert metadata["has_images"] is False
