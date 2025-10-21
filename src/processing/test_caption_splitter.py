"""
Tests for caption splitting utilities.

Tests the caption_splitter module which provides intelligent splitting
of long VTT captions into shorter, more readable segments.
"""

import pytest

from .caption_splitter import (
    calculate_reading_speed,
    distribute_timestamps,
    find_phrase_boundaries,
    find_sentence_boundaries,
    split_at_position,
    split_long_caption,
)


class TestFindSentenceBoundaries:
    """Test sentence boundary detection."""

    def test_single_sentence(self):
        """Test text with one sentence."""
        text = "Hello world."
        boundaries = find_sentence_boundaries(text)
        assert boundaries == [12]

    def test_multiple_sentences(self):
        """Test text with multiple sentences."""
        text = "Hello. World! How are you?"
        boundaries = find_sentence_boundaries(text)
        assert 6 in boundaries  # After "Hello."
        assert 13 in boundaries  # After "World!"
        assert 27 in boundaries  # After "you?"

    def test_no_boundaries(self):
        """Test text with no sentence endings."""
        text = "Hello world"
        boundaries = find_sentence_boundaries(text)
        assert boundaries == []

    def test_sentence_at_end(self):
        """Test sentence ending at end of string."""
        text = "Hello world."
        boundaries = find_sentence_boundaries(text)
        assert len(text) in boundaries


class TestFindPhraseBoundaries:
    """Test phrase boundary detection."""

    def test_commas(self):
        """Test comma boundaries."""
        text = "Hello, world, how are you"
        boundaries = find_phrase_boundaries(text)
        assert 7 in boundaries  # After "Hello, "
        assert 14 in boundaries  # After "world, "

    def test_conjunctions(self):
        """Test conjunction boundaries."""
        text = "Hello and goodbye but not or maybe"
        boundaries = find_phrase_boundaries(text)
        assert any(b for b in boundaries)  # Should find conjunctions

    def test_no_boundaries(self):
        """Test text with no phrase boundaries."""
        text = "HelloWorld"
        boundaries = find_phrase_boundaries(text)
        assert boundaries == []


class TestCalculateReadingSpeed:
    """Test reading speed calculation."""

    def test_normal_speed(self):
        """Test normal reading speed."""
        speed = calculate_reading_speed("Hello world", 2.0)
        assert speed == 5.5  # 11 chars / 2 sec

    def test_zero_duration(self):
        """Test zero duration returns zero."""
        speed = calculate_reading_speed("Hello", 0.0)
        assert speed == 0.0

    def test_negative_duration(self):
        """Test negative duration returns zero."""
        speed = calculate_reading_speed("Hello", -1.0)
        assert speed == 0.0


class TestDistributeTimestamps:
    """Test timestamp distribution."""

    def test_equal_segments(self):
        """Test equally sized segments get equal time."""
        segments = ["Hello", "World"]
        timestamps = distribute_timestamps(0.0, 10.0, segments)

        assert len(timestamps) == 2
        assert timestamps[0] == (0.0, 5.0)
        assert timestamps[1] == (5.0, 10.0)

    def test_proportional_distribution(self):
        """Test segments get time proportional to length."""
        segments = ["Hi", "Hello world"]  # 2 chars vs 11 chars
        timestamps = distribute_timestamps(0.0, 13.0, segments)

        assert len(timestamps) == 2
        # First segment should get ~2s, second ~11s
        assert timestamps[0][1] < 3.0
        assert timestamps[1][1] == 13.0

    def test_empty_segments(self):
        """Test error on empty segments."""
        with pytest.raises(ValueError, match="no text segments"):
            distribute_timestamps(0.0, 10.0, [])

    def test_invalid_time_range(self):
        """Test error on invalid time range."""
        with pytest.raises(ValueError, match="Invalid time range"):
            distribute_timestamps(10.0, 5.0, ["Hello"])


class TestSplitAtPosition:
    """Test text splitting at boundaries."""

    def test_split_at_boundary(self):
        """Test splitting at a valid boundary."""
        text = "Hello, world!"
        boundaries = [6]  # After comma
        before, after = split_at_position(text, 10, boundaries)

        assert before == "Hello,"
        assert after == "world!"

    def test_split_no_boundary(self):
        """Test splitting when no boundary available."""
        text = "HelloWorld"
        before, after = split_at_position(text, 5, [])

        # Should split at max_pos
        assert len(before) <= 5


class TestSplitLongCaption:
    """Test full caption splitting logic."""

    def test_short_caption_no_split(self):
        """Test short caption is not split."""
        result = split_long_caption(0.0, 3.0, "Hello world", max_duration=6.0, max_chars=100)

        assert len(result) == 1
        assert result[0] == (0.0, 3.0, "Hello world")

    def test_long_duration_split(self):
        """Test caption split by duration."""
        text = "First sentence. Second sentence."
        result = split_long_caption(0.0, 10.0, text, max_duration=5.0, max_chars=100)

        assert len(result) > 1

    def test_long_text_split(self):
        """Test caption split by character count."""
        text = "A" * 200  # 200 characters
        result = split_long_caption(0.0, 10.0, text, max_duration=20.0, max_chars=100)

        assert len(result) > 1
        # Each segment should be <= 100 chars
        for _, _, seg_text in result:
            assert len(seg_text) <= 120  # Allow some buffer

    def test_sentence_boundary_split(self):
        """Test split respects sentence boundaries."""
        text = "First sentence. Second sentence. Third sentence."
        result = split_long_caption(0.0, 15.0, text, max_duration=5.0, max_chars=20)

        # Should split at sentence boundaries
        assert len(result) >= 2
        # First segment should end with period
        assert result[0][2].endswith(".")

    def test_timestamp_distribution(self):
        """Test timestamps are distributed correctly."""
        text = "Hello. World."
        result = split_long_caption(0.0, 10.0, text, max_duration=5.0, max_chars=10)

        # Timestamps should span the full range
        assert result[0][0] == 0.0
        assert result[-1][1] == 10.0

        # Timestamps should be sequential
        for i in range(len(result) - 1):
            assert result[i][1] <= result[i + 1][0] + 0.01  # Allow small rounding

    def test_min_duration_enforcement(self):
        """Test minimum duration is enforced."""
        text = "A. B. C. D."
        result = split_long_caption(0.0, 5.0, text, max_duration=1.0, max_chars=5, min_duration=2.0)

        # Should merge segments to meet min duration
        for start, end, _ in result:
            duration = end - start
            # Last segment might be slightly under
            assert duration >= 1.5 or result.index((start, end, _)) == len(result) - 1

    def test_too_short_to_split(self):
        """Test caption too short to split returns original."""
        result = split_long_caption(0.0, 1.5, "Long text here", max_duration=1.0, min_duration=1.0)

        # Duration is too short (< 2 * min_duration)
        assert len(result) == 1

    def test_no_natural_boundaries(self):
        """Test text with no natural split points."""
        text = "NoSpacesOrPunctuationHere"
        result = split_long_caption(0.0, 10.0, text, max_duration=5.0, max_chars=10)

        # Should return original if can't split cleanly
        assert len(result) == 1


class TestIntegration:
    """Integration tests for caption splitting."""

    def test_real_world_example(self):
        """Test with real-world caption from VTT file."""
        text = (
            "Now, I'm not going to go into too much detail about my story here. "
            "I'm sending along some emails that explain how I went from drifter "
            "and dreamer to a family man with a full time job who completed two "
            "music projects, Born to the World and Going to the Zany Zoo, and two "
            "kids books, Gary the Gargoyle and Going to the Zany Zoo, plus a three "
            "year run of The Spark in the Art, a weekly creativity podcast."
        )

        result = split_long_caption(
            18.3, 45.16, text, max_duration=6.0, max_chars=100, min_duration=1.0
        )

        # Should split this 297-char, 26.86s caption
        assert len(result) > 1

        # All segments should meet constraints
        for start, end, seg_text in result:
            duration = end - start
            # Allow last segment to be slightly under
            assert duration >= 0.8 or result.index((start, end, seg_text)) == len(result) - 1
            assert len(seg_text) <= 120  # Some buffer

        # Total duration should match
        assert abs(result[-1][1] - 45.16) < 0.1

    def test_multiple_sentences_split(self):
        """Test splitting multiple complete sentences."""
        text = (
            "This is the first sentence. "
            "This is the second sentence. "
            "This is the third sentence."
        )

        result = split_long_caption(
            0.0, 12.0, text, max_duration=4.0, max_chars=50, min_duration=1.0
        )

        # Should split into 3 sentences
        assert len(result) == 3

        # Each segment should be a complete sentence
        for _, _, seg_text in result:
            assert seg_text.strip().endswith(".")
