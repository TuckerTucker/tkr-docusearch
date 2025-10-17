"""
Unit tests for timestamp extraction from text markers.

Tests the extract_timestamps_from_text() function which parses
[time: X-Y] markers from chunk text.

Wave 2 - Backend Implementation
"""

import pytest

from src.processing.text_processor import extract_timestamps_from_text


class TestTimestampExtraction:
    """Test suite for timestamp extraction function."""

    # Category 1: Valid Timestamps

    def test_simple_timestamp(self):
        """Basic valid timestamp"""
        start, end, text = extract_timestamps_from_text("[time: 1.5-3.2] Hello")
        assert start == 1.5
        assert end == 3.2
        assert text == " Hello"  # Preserves space after ]

    def test_timestamp_with_decimals(self):
        """High precision decimals"""
        start, end, text = extract_timestamps_from_text("[time: 0.6199999-3.96] Text")
        assert abs(start - 0.62) < 0.001
        assert end == 3.96
        assert text == " Text"  # Preserves space after ]

    def test_timestamp_at_zero(self):
        """Start at zero"""
        start, end, text = extract_timestamps_from_text("[time: 0.0-5.5] Start")
        assert start == 0.0
        assert end == 5.5
        assert text == " Start"  # Preserves space after ]

    def test_large_timestamp(self):
        """Hour-long timestamp"""
        start, end, text = extract_timestamps_from_text("[time: 3600.5-3725.8] Hour")
        assert start == 3600.5
        assert end == 3725.8
        assert text == " Hour"  # Preserves space after ]

    def test_whitespace_variations(self):
        """Various whitespace patterns"""
        start, end, text = extract_timestamps_from_text(" [time: 1.5-3.2]  Text  ")
        assert start == 1.5
        assert text == "  Text  "  # Preserve all whitespace after ]

    def test_no_whitespace(self):
        """No whitespace in marker"""
        start, end, text = extract_timestamps_from_text("[time:1.5-3.2]Text")
        assert start == 1.5
        assert end == 3.2
        assert text == "Text"

    # Category 2: Text Cleaning

    def test_text_cleaning(self):
        """Marker removed from text"""
        _, _, text = extract_timestamps_from_text("[time: 1-2] Clean")
        assert text == " Clean"  # Preserves space after ]
        assert "[time:" not in text

    def test_multiline_text(self):
        """Multiline text preserved"""
        _, _, text = extract_timestamps_from_text("[time: 1-2] Line1\nLine2")
        assert text == " Line1\nLine2"  # Preserves space after ]

    def test_unicode_preservation(self):
        """Unicode characters preserved"""
        _, _, text = extract_timestamps_from_text("[time: 1-2] Café 你好")
        assert text == " Café 你好"  # Preserves space after ]

    def test_special_characters(self):
        """Special characters preserved"""
        _, _, text = extract_timestamps_from_text("[time: 1-2] $100 & <tag>")
        assert text == " $100 & <tag>"  # Preserves space after ]

    # Category 3: Invalid Cases

    def test_no_timestamp(self):
        """No timestamp marker"""
        start, end, text = extract_timestamps_from_text("No timestamp")
        assert start is None
        assert end is None
        assert text == "No timestamp"

    def test_malformed_timestamp(self):
        """Non-numeric values"""
        start, end, text = extract_timestamps_from_text("[time: abc-def] Text")
        assert start is None
        assert end is None
        assert text == "[time: abc-def] Text"

    def test_negative_start(self):
        """Negative start time"""
        start, end, text = extract_timestamps_from_text("[time: -1.5-3.2] Text")
        assert start is None
        assert end is None

    def test_reversed_times(self):
        """End before start"""
        start, end, text = extract_timestamps_from_text("[time: 5.0-2.0] Text")
        assert start is None
        assert end is None

    def test_zero_duration(self):
        """Same start and end"""
        start, end, text = extract_timestamps_from_text("[time: 2.0-2.0] Text")
        assert start is None
        assert end is None

    def test_incomplete_timestamp(self):
        """Missing end time"""
        start, end, text = extract_timestamps_from_text("[time: 1.5] Text")
        assert start is None
        assert end is None

    def test_wrong_format(self):
        """Wrong marker format"""
        start, end, text = extract_timestamps_from_text("[timestamp: 1.5-3.2] Text")
        assert start is None
        assert end is None

    # Category 4: Edge Cases

    def test_multiple_timestamps(self):
        """Multiple markers - use first"""
        start, end, text = extract_timestamps_from_text("[time: 1-2] A [time: 3-4] B")
        assert start == 1.0
        assert end == 2.0
        assert "[time: 3-4]" in text  # Second marker remains

    def test_timestamp_not_at_start(self):
        """Timestamp not at beginning"""
        start, end, text = extract_timestamps_from_text("Text [time: 1-2] More")
        assert start is None
        assert end is None
        assert text == "Text [time: 1-2] More"

    def test_empty_text_after_marker(self):
        """Only marker, no text"""
        start, end, text = extract_timestamps_from_text("[time: 1-2]")
        assert start == 1.0
        assert end == 2.0
        assert text == ""

    def test_empty_string(self):
        """Empty input"""
        start, end, text = extract_timestamps_from_text("")
        assert start is None
        assert end is None
        assert text == ""

    def test_whitespace_only(self):
        """Only whitespace"""
        start, end, text = extract_timestamps_from_text("   ")
        assert start is None
        assert end is None

    def test_very_long_text(self):
        """Long text after marker"""
        long_text = "A" * 1000
        start, end, text = extract_timestamps_from_text(f"[time: 1-2] {long_text}")
        assert start == 1.0
        assert end == 2.0
        assert text == f" {long_text}"

    # Category 5: Real-World Examples

    def test_real_audio_example_1(self):
        """Real example from Myth 1.mp3"""
        start, end, text = extract_timestamps_from_text(
            "[time: 0.6199999999999986-3.96]  Myth 1. Ideas come in a flash."
        )
        assert abs(start - 0.62) < 0.001
        assert end == 3.96
        assert text == "  Myth 1. Ideas come in a flash."  # Preserves both spaces
        assert "[time:" not in text

    def test_real_audio_example_2(self):
        """Real example with longer text"""
        start, end, text = extract_timestamps_from_text(
            "[time: 5.92-12.04]  Ideas may feel like they come in a flash, "
            "but it's actually after your brain has done a lot of work."
        )
        assert start == 5.92
        assert end == 12.04
        assert "Ideas may feel" in text
        assert "[time:" not in text

    def test_real_audio_example_3(self):
        """Real example with multiline"""
        start, end, text = extract_timestamps_from_text(
            "[time: 12.6-19.1]  If you get frustrated and can't seem to "
            "figure out a certain problem\nor get past a certain limitation "
            "in your understanding,"
        )
        assert start == 12.6
        assert end == 19.1
        assert "\n" in text
        assert "[time:" not in text

    # Category 6: Boundary Conditions

    def test_very_small_duration(self):
        """Minimum valid duration"""
        start, end, text = extract_timestamps_from_text("[time: 1.0-1.001] Text")
        assert start == 1.0
        assert end == 1.001

    def test_very_large_numbers(self):
        """Very large timestamps"""
        start, end, text = extract_timestamps_from_text("[time: 10000.5-20000.8] Text")
        assert start == 10000.5
        assert end == 20000.8

    def test_float_precision(self):
        """High precision floats"""
        start, end, text = extract_timestamps_from_text("[time: 1.123456789-2.987654321] Text")
        assert start == pytest.approx(1.123456789, rel=1e-6)
        assert end == pytest.approx(2.987654321, rel=1e-6)

    def test_integer_timestamps(self):
        """Integer timestamps (no decimals)"""
        start, end, text = extract_timestamps_from_text("[time: 1-2] Text")
        assert start == 1.0
        assert end == 2.0


# Run tests with: pytest src/processing/test_timestamp_extraction.py -v
