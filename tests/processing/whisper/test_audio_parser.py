"""
Unit tests for audio parser.

Tests the parse_audio_with_whisper() function to ensure IC-002 contract
compliance and proper integration with all components.
"""

import os
import re
from pathlib import Path

import pytest

from tkr_docusearch.processing.whisper.audio_parser import parse_audio_with_whisper
from tkr_docusearch.processing.whisper.transcriber import AudioFormatError

# Get path to test fixtures
FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"
SAMPLE_MP3 = FIXTURES_DIR / "sample.mp3"
SAMPLE_WAV = FIXTURES_DIR / "sample.wav"


class TestParseAudioWithWhisper:
    """Test main audio parser entry point."""

    @pytest.mark.skipif(not SAMPLE_MP3.exists(), reason="sample.mp3 fixture not found")
    def test_parse_mp3_basic(self):
        """Test basic MP3 parsing."""
        pages, metadata, whisper_result = parse_audio_with_whisper(str(SAMPLE_MP3))

        # Validate return tuple
        assert isinstance(pages, list)
        assert isinstance(metadata, dict)
        assert isinstance(whisper_result, dict)

        # Validate pages
        assert len(pages) == 1
        page = pages[0]

        # IC-002 Page format validation
        assert page.page_num == 1
        assert page.image is None
        assert page.width == 0
        assert page.height == 0
        assert isinstance(page.text, str)
        assert len(page.text) > 0

    @pytest.mark.skipif(not SAMPLE_WAV.exists(), reason="sample.wav fixture not found")
    def test_parse_wav_basic(self):
        """Test basic WAV parsing."""
        pages, metadata, whisper_result = parse_audio_with_whisper(str(SAMPLE_WAV))

        # Validate return tuple
        assert len(pages) == 1
        assert isinstance(metadata, dict)
        assert isinstance(whisper_result, dict)

        # WAV-specific metadata
        assert metadata["format"] == "wav"
        assert metadata["audio_format"] == "wav"

    @pytest.mark.skipif(not SAMPLE_MP3.exists(), reason="sample.mp3 fixture not found")
    def test_parse_ic002_page_format(self):
        """Test IC-002 Page format compliance."""
        pages, metadata, whisper_result = parse_audio_with_whisper(str(SAMPLE_MP3))

        assert len(pages) == 1
        page = pages[0]

        # IC-002 Page Requirements
        assert page.page_num == 1, "Page number must be 1 for audio"
        assert page.image is None, "Image must be None for audio"
        assert page.width == 0, "Width must be 0 for audio"
        assert page.height == 0, "Height must be 0 for audio"

        # IC-002 Text Format Requirements
        text = page.text
        assert "[time:" in text, "Text must contain timestamp markers"

        # Validate timestamp marker format
        timestamp_pattern = r"\[time:\s*([\d.]+)-([\d.]+)\]"
        matches = re.findall(timestamp_pattern, text)
        assert len(matches) > 0, "No timestamp markers found"

        # Each line should start with timestamp marker
        lines = [line for line in text.split("\n") if line.strip()]
        for line in lines:
            assert line.strip().startswith("[time:"), f"Line missing [time: marker: {line}"

    @pytest.mark.skipif(not SAMPLE_MP3.exists(), reason="sample.mp3 fixture not found")
    def test_parse_ic002_metadata_format(self):
        """Test IC-002 metadata format compliance."""
        pages, metadata, whisper_result = parse_audio_with_whisper(str(SAMPLE_MP3))

        # IC-002 Required Fields
        required_fields = [
            "format_type",
            "has_word_timestamps",
            "audio_duration_seconds",
            "num_pages",
            "has_images",
            "transcript_method",
            "asr_model_used",
        ]

        for field in required_fields:
            assert field in metadata, f"Missing required field: {field}"

        # IC-002 Required Values
        assert metadata["format_type"] == "audio", "format_type must be 'audio'"
        assert metadata["has_word_timestamps"] is True, "has_word_timestamps must be True"
        assert metadata["num_pages"] == 1, "num_pages must be 1 for audio"
        assert metadata["has_images"] is False, "has_images must be False for audio"
        assert metadata["transcript_method"] == "whisper", "transcript_method must be 'whisper'"

        # Validate types
        assert isinstance(
            metadata["audio_duration_seconds"], (int, float)
        ), "audio_duration_seconds must be numeric"
        assert isinstance(metadata["asr_model_used"], str), "asr_model_used must be string"

    @pytest.mark.skipif(not SAMPLE_MP3.exists(), reason="sample.mp3 fixture not found")
    def test_parse_whisper_result_format(self):
        """Test whisper result structure."""
        pages, metadata, whisper_result = parse_audio_with_whisper(str(SAMPLE_MP3))

        # Validate whisper result structure (IC-001)
        assert "text" in whisper_result
        assert "segments" in whisper_result
        assert "language" in whisper_result
        assert "duration" in whisper_result

        # Validate segments
        assert isinstance(whisper_result["segments"], list)
        assert len(whisper_result["segments"]) > 0

        # Validate segment structure
        segment = whisper_result["segments"][0]
        assert "start" in segment
        assert "end" in segment
        assert "text" in segment

    @pytest.mark.skipif(not SAMPLE_MP3.exists(), reason="sample.mp3 fixture not found")
    def test_parse_metadata_has_file_info(self):
        """Test that metadata includes file information."""
        pages, metadata, whisper_result = parse_audio_with_whisper(str(SAMPLE_MP3))

        # File metadata
        assert "title" in metadata
        assert "format" in metadata
        assert "original_filename" in metadata
        assert "mimetype" in metadata

        # Format-specific
        assert metadata["format"] == "mp3"
        assert metadata["audio_format"] == "mp3"
        assert metadata["mimetype"] == "audio/mpeg"
        assert metadata["original_filename"] == "sample.mp3"

    @pytest.mark.skipif(not SAMPLE_MP3.exists(), reason="sample.mp3 fixture not found")
    def test_parse_extracts_id3_from_mp3(self):
        """Test that ID3 metadata is extracted from MP3 files."""
        pages, metadata, whisper_result = parse_audio_with_whisper(str(SAMPLE_MP3))

        # ID3 fields may or may not be present depending on the fixture
        # Just verify the extraction was attempted (no errors)
        # and check if has_album_art field exists
        assert "has_album_art" in metadata
        assert isinstance(metadata["has_album_art"], bool)

    def test_parse_missing_file_raises(self):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parse_audio_with_whisper("/nonexistent/file.mp3")

    def test_parse_unsupported_format_raises(self):
        """Test that unsupported format raises AudioFormatError."""
        # Create a temporary .txt file
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = f.name
            f.write(b"This is not audio")

        try:
            with pytest.raises(AudioFormatError):
                parse_audio_with_whisper(temp_path)
        finally:
            os.unlink(temp_path)

    @pytest.mark.skipif(not SAMPLE_MP3.exists(), reason="sample.mp3 fixture not found")
    def test_parse_with_config(self):
        """Test parsing with EnhancedModeConfig (for future use)."""
        from tkr_docusearch.config.processing_config import EnhancedModeConfig

        config = EnhancedModeConfig()

        # Should accept config parameter (even if not used yet)
        pages, metadata, whisper_result = parse_audio_with_whisper(str(SAMPLE_MP3), config=config)

        assert len(pages) == 1
        assert isinstance(metadata, dict)

    @pytest.mark.skipif(not SAMPLE_MP3.exists(), reason="sample.mp3 fixture not found")
    def test_parse_timestamp_extraction_validates(self):
        """Test that timestamp extraction is validated."""
        # This test verifies the TimestampExtractionError path
        # We can't easily trigger it without mocking, so we just verify
        # that normal parsing produces valid timestamps

        pages, metadata, whisper_result = parse_audio_with_whisper(str(SAMPLE_MP3))

        text = pages[0].text

        # Should have timestamp markers
        assert "[time:" in text

        # Should have proper format
        timestamp_pattern = r"\[time:\s*([\d.]+)-([\d.]+)\]"
        matches = re.findall(timestamp_pattern, text)
        assert len(matches) > 0

    @pytest.mark.skipif(not SAMPLE_WAV.exists(), reason="sample.wav fixture not found")
    def test_parse_wav_no_id3_extraction(self):
        """Test that WAV files don't attempt ID3 extraction."""
        pages, metadata, whisper_result = parse_audio_with_whisper(str(SAMPLE_WAV))

        # WAV files may have has_album_art field but should be False
        # (or field may not be present, depending on implementation)
        if "has_album_art" in metadata:
            assert metadata["has_album_art"] is False

    @pytest.mark.skipif(not SAMPLE_MP3.exists(), reason="sample.mp3 fixture not found")
    def test_parse_markdown_metadata(self):
        """Test that markdown metadata is included."""
        pages, metadata, whisper_result = parse_audio_with_whisper(str(SAMPLE_MP3))

        # Markdown metadata
        assert "markdown_extracted" in metadata
        assert metadata["markdown_extracted"] is True

        assert "markdown_error" in metadata
        assert metadata["markdown_error"] is None

        # Should have markdown length
        if "markdown_length" in metadata:
            assert isinstance(metadata["markdown_length"], int)
            # Note: Can be 0 for silent audio files
            assert metadata["markdown_length"] >= 0


class TestErrorHandling:
    """Test error handling per IC-004."""

    def test_file_not_found_error(self):
        """Test FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            parse_audio_with_whisper("/nonexistent/path/file.mp3")

    def test_audio_format_error(self):
        """Test AudioFormatError is raised for unsupported formats."""
        import tempfile

        # Create temp file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name
            f.write(b"%PDF-1.4")

        try:
            with pytest.raises(AudioFormatError):
                parse_audio_with_whisper(temp_path)
        finally:
            os.unlink(temp_path)

    def test_error_messages_include_context(self):
        """Test that error messages include file path context."""
        try:
            parse_audio_with_whisper("/nonexistent/file.mp3")
        except FileNotFoundError as e:
            # Error message should include file path
            assert "/nonexistent/file.mp3" in str(e) or "file.mp3" in str(e)


class TestIntegrationContractIC002:
    """Comprehensive IC-002 contract compliance tests."""

    @pytest.mark.skipif(not SAMPLE_MP3.exists(), reason="sample.mp3 fixture not found")
    def test_ic002_full_contract(self):
        """
        Comprehensive IC-002 contract validation.

        This test validates ALL requirements from IC-002:
        - Return type (tuple of 3 elements)
        - Page format (page_num=1, image=None, width=0, height=0)
        - Text format ([time: X-Y] markers)
        - Metadata required fields
        - Metadata required values
        """
        # Execute parser
        result = parse_audio_with_whisper(str(SAMPLE_MP3))

        # ===== Return Type Validation =====
        assert isinstance(result, tuple), "Must return tuple"
        assert len(result) == 3, "Must return tuple of 3 elements"

        pages, metadata, whisper_result = result

        # ===== Page Format Validation =====
        assert isinstance(pages, list), "pages must be list"
        assert len(pages) == 1, "Audio must have exactly 1 page"

        page = pages[0]
        assert page.page_num == 1, "IC-002: page_num must be 1"
        assert page.image is None, "IC-002: image must be None"
        assert page.width == 0, "IC-002: width must be 0"
        assert page.height == 0, "IC-002: height must be 0"

        # ===== Text Format Validation =====
        text = page.text
        assert isinstance(text, str), "text must be string"
        assert len(text) > 0, "text must not be empty"

        # IC-002 Text Format Requirements
        timestamp_pattern = r"\[time:\s*([\d.]+)-([\d.]+)\]"
        matches = re.findall(timestamp_pattern, text)
        assert len(matches) > 0, "IC-002: No timestamp markers found"

        # Validate each line starts with [time: X-Y]
        lines = [line for line in text.split("\n") if line.strip()]
        for line in lines:
            assert re.match(
                timestamp_pattern, line.strip()
            ), f"IC-002: Line must start with [time: X-Y]: {line}"

        # ===== Metadata Required Fields Validation =====
        required_fields = {
            "format_type": "audio",
            "has_word_timestamps": True,
            "audio_duration_seconds": float,
            "num_pages": 1,
            "has_images": False,
            "transcript_method": "whisper",
            "asr_model_used": str,
        }

        for field, expected_value_or_type in required_fields.items():
            assert field in metadata, f"IC-002: Missing required field: {field}"

            if isinstance(expected_value_or_type, type):
                # Type check
                if expected_value_or_type == float:
                    assert isinstance(
                        metadata[field], (int, float)
                    ), f"IC-002: {field} must be numeric"
                else:
                    assert isinstance(
                        metadata[field], expected_value_or_type
                    ), f"IC-002: {field} must be {expected_value_or_type}"
            else:
                # Value check
                assert (
                    metadata[field] == expected_value_or_type
                ), f"IC-002: {field} must be {expected_value_or_type}, got {metadata[field]}"

        # ===== Whisper Result Validation =====
        assert isinstance(whisper_result, dict), "whisper_result must be dict"
        assert "segments" in whisper_result, "whisper_result must have segments"
        assert "text" in whisper_result, "whisper_result must have text"
        assert "duration" in whisper_result, "whisper_result must have duration"

        # Contract validation PASSED
        print("\n✅ IC-002 Contract Validation: PASSED")
        print(f"   - Pages: {len(pages)} (expected 1)")
        print(f"   - Metadata fields: {len(metadata)}")
        print(f"   - Timestamp markers: {len(matches)}")
        print(f"   - Audio duration: {metadata['audio_duration_seconds']:.1f}s")
