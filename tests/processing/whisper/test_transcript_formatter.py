"""
Unit tests for transcript formatter.

Tests the format_transcript_with_timestamps() function to ensure IC-002
text format compliance.
"""

from src.processing.whisper.transcript_formatter import (
    _format_timestamp,
    format_transcript_with_timestamps,
)


class TestFormatTimestamp:
    """Test timestamp formatting helper."""

    def test_format_timestamp_clean(self):
        """Test clean timestamps (X.0)."""
        assert _format_timestamp(0.0) == "0.0"
        assert _format_timestamp(5.0) == "5.0"
        assert _format_timestamp(10.0) == "10.0"

    def test_format_timestamp_precise(self):
        """Test precise timestamps (X.YZ)."""
        assert _format_timestamp(5.28) == "5.28"
        assert _format_timestamp(10.125) == "10.125"
        assert _format_timestamp(3.456) == "3.456"

    def test_format_timestamp_rounds(self):
        """Test floating point rounding."""
        # Should round to 3 decimal places
        assert _format_timestamp(5.28999999) == "5.29"
        assert _format_timestamp(10.1234567) == "10.123"

    def test_format_timestamp_strips_trailing_zeros(self):
        """Test trailing zero removal."""
        assert _format_timestamp(5.2000) == "5.2"
        assert _format_timestamp(10.1000) == "10.1"

    def test_format_timestamp_always_has_decimal(self):
        """Test that result always has at least one decimal place."""
        result = _format_timestamp(5.0)
        assert "." in result
        assert result == "5.0"


class TestFormatTranscriptWithTimestamps:
    """Test transcript formatting with timestamp markers."""

    def test_format_basic_segments(self):
        """Test formatting of basic segment structure."""
        whisper_result = {
            "text": "Full transcript",
            "segments": [
                {"start": 0.0, "end": 4.0, "text": "Hello world."},
                {"start": 5.28, "end": 9.96, "text": "This is a test."},
            ],
            "language": "en",
            "duration": 10.0,
        }

        formatted = format_transcript_with_timestamps(whisper_result)

        # Verify format
        lines = formatted.strip().split("\n")
        assert len(lines) == 2

        # Verify first line
        assert lines[0] == "[time: 0.0-4.0] Hello world."

        # Verify second line
        assert lines[1] == "[time: 5.28-9.96] This is a test."

    def test_format_ic002_compliance(self):
        """Test IC-002 format requirements."""
        whisper_result = {
            "segments": [
                {"start": 0.0, "end": 4.0, "text": "Shakespeare on Scenery by Oscar Wilde."},
                {"start": 5.28, "end": 9.96, "text": "This is a LibriVox recording."},
            ],
            "duration": 10.0,
        }

        formatted = format_transcript_with_timestamps(whisper_result)

        # IC-002 Requirements:
        # 1. Each line MUST start with [time: START-END] marker
        lines = formatted.strip().split("\n")
        for line in lines:
            assert line.startswith("[time: "), f"Line missing [time: marker: {line}"

        # 2. Space after ] before text begins
        for line in lines:
            assert "] " in line, f"Line missing space after ]: {line}"

        # 3. No blank lines between segments
        assert "\n\n" not in formatted

    def test_format_empty_result(self):
        """Test handling of empty whisper result."""
        formatted = format_transcript_with_timestamps({})
        assert formatted == ""

    def test_format_no_segments(self):
        """Test handling when segments are missing."""
        whisper_result = {
            "text": "Full transcript text",
            "segments": [],
            "duration": 10.0,
        }

        formatted = format_transcript_with_timestamps(whisper_result)

        # Should create single segment from full text
        assert formatted == "[time: 0.0-10.0] Full transcript text"

    def test_format_skips_empty_segments(self):
        """Test that empty segments are skipped."""
        whisper_result = {
            "segments": [
                {"start": 0.0, "end": 4.0, "text": "Hello world."},
                {"start": 4.0, "end": 5.0, "text": "   "},  # Whitespace only
                {"start": 5.0, "end": 6.0, "text": ""},  # Empty
                {"start": 6.0, "end": 10.0, "text": "Goodbye."},
            ],
            "duration": 10.0,
        }

        formatted = format_transcript_with_timestamps(whisper_result)
        lines = formatted.strip().split("\n")

        # Should only have 2 non-empty segments
        assert len(lines) == 2
        assert lines[0] == "[time: 0.0-4.0] Hello world."
        assert lines[1] == "[time: 6.0-10.0] Goodbye."

    def test_format_preserves_text(self):
        """Test that segment text is preserved exactly."""
        whisper_result = {
            "segments": [
                {
                    "start": 0.0,
                    "end": 5.0,
                    "text": "  This has leading/trailing spaces.  ",
                },
            ],
            "duration": 5.0,
        }

        formatted = format_transcript_with_timestamps(whisper_result)

        # Text should be stripped of leading/trailing whitespace
        assert formatted == "[time: 0.0-5.0] This has leading/trailing spaces."

    def test_format_multiple_segments(self):
        """Test formatting of many segments."""
        segments = [
            {"start": float(i), "end": float(i + 1), "text": f"Segment {i}"} for i in range(10)
        ]

        whisper_result = {"segments": segments, "duration": 10.0}

        formatted = format_transcript_with_timestamps(whisper_result)
        lines = formatted.strip().split("\n")

        assert len(lines) == 10

        for i, line in enumerate(lines):
            expected = f"[time: {i}.0-{i + 1}.0] Segment {i}"
            assert line == expected

    def test_format_precise_timestamps(self):
        """Test that precise timestamps are preserved."""
        whisper_result = {
            "segments": [
                {"start": 0.123, "end": 4.567, "text": "Precise timing."},
                {"start": 5.289, "end": 9.876, "text": "More precise."},
            ],
            "duration": 10.0,
        }

        formatted = format_transcript_with_timestamps(whisper_result)
        lines = formatted.strip().split("\n")

        # Check first segment preserves precision
        assert lines[0] == "[time: 0.123-4.567] Precise timing."

        # Check second segment preserves precision
        assert lines[1] == "[time: 5.289-9.876] More precise."

    def test_format_handles_missing_timestamps(self):
        """Test handling when start/end times are missing."""
        whisper_result = {
            "segments": [
                {"text": "No timestamps"},  # Missing start/end
                {"start": 5.0, "end": 10.0, "text": "Has timestamps"},
            ],
            "duration": 10.0,
        }

        formatted = format_transcript_with_timestamps(whisper_result)
        lines = formatted.strip().split("\n")

        # First segment should default to 0.0
        assert lines[0] == "[time: 0.0-0.0] No timestamps"

        # Second segment should be normal
        assert lines[1] == "[time: 5.0-10.0] Has timestamps"

    def test_format_unicode_text(self):
        """Test handling of Unicode text in segments."""
        whisper_result = {
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "Hello 世界"},
                {"start": 5.0, "end": 10.0, "text": "Bonjour 🌍"},
            ],
            "duration": 10.0,
        }

        formatted = format_transcript_with_timestamps(whisper_result)
        lines = formatted.strip().split("\n")

        assert lines[0] == "[time: 0.0-5.0] Hello 世界"
        assert lines[1] == "[time: 5.0-10.0] Bonjour 🌍"

    def test_format_newlines_in_text(self):
        """Test handling of newlines within segment text."""
        whisper_result = {
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "Line 1\nLine 2"},
            ],
            "duration": 5.0,
        }

        formatted = format_transcript_with_timestamps(whisper_result)

        # Newlines should be preserved in text
        assert formatted == "[time: 0.0-5.0] Line 1\nLine 2"
