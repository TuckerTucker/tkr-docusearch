"""
Caption splitting utilities for VTT generation.

This module provides utilities for intelligently splitting long caption segments
into shorter, more readable chunks based on natural language boundaries and
optimal reading speeds.

Overview:
    VTT captions generated from Whisper/Docling often contain very long segments
    (20+ seconds, 200+ characters) which are difficult to read. This module splits
    them into shorter, more digestible chunks while preserving:
    - Complete sentences (prioritized to avoid mid-sentence breaks)
    - Natural phrase boundaries (used only when sentences are too long)
    - Proportional timestamp distribution
    - Minimum duration constraints
    - Optimal reading speeds (15 chars/sec target)

Splitting Priority:
    1. Sentence boundaries (. ! ?) - ALWAYS preferred to keep sentences intact
    2. Phrase boundaries (commas, conjunctions) - Used only if sentence too long
    3. Word boundaries - Fallback if no natural breaks available

Functions:
    find_sentence_boundaries: Detect sentence endings in text
    find_phrase_boundaries: Detect phrase breaks (commas, conjunctions)
    calculate_reading_speed: Calculate characters per second for a caption
    distribute_timestamps: Proportionally distribute time across text segments
    split_long_caption: Main function to split long captions intelligently

Configuration:
    Caption splitting is configured via AsrConfig environment variables:
    - ASR_MAX_CAPTION_DURATION: Maximum duration per caption (default: 6.0s)
    - ASR_MAX_CAPTION_CHARS: Maximum characters per caption (default: 100)
    - ASR_MIN_CAPTION_DURATION: Minimum duration per caption (default: 1.0s)
    - ASR_TARGET_CHARS_PER_SECOND: Target reading speed (default: 15.0)

Example:
    >>> from caption_splitter import split_long_caption
    >>> segments = split_long_caption(
    ...     start_time=0.0,
    ...     end_time=20.0,
    ...     text="Long caption text. With multiple sentences. That needs splitting.",
    ...     max_duration=6.0,
    ...     max_chars=40
    ... )
    >>> for start, end, text in segments:
    ...     print(f"{start:.1f}-{end:.1f}: {text}")
    0.0-7.5: Long caption text.
    7.5-15.0: With multiple sentences.
    15.0-20.0: That needs splitting.

Wave 3 - Caption Splitting Enhancement
"""

import logging
import re
from typing import List, Tuple

logger = logging.getLogger(__name__)


def find_sentence_boundaries(text: str) -> List[int]:
    """
    Find sentence boundary positions in text.

    Detects endings with '. ', '! ', '? ' followed by space or end of string.

    Args:
        text: Input text to analyze

    Returns:
        List of character positions where sentences end (after punctuation)

    Example:
        >>> find_sentence_boundaries("Hello. World! How are you?")
        [6, 13, 27]
    """
    boundaries = []

    # Pattern: sentence-ending punctuation followed by space or end of string
    # Captures position after the punctuation and space
    pattern = r"[.!?]\s+"

    for match in re.finditer(pattern, text):
        # Position after punctuation and space
        boundaries.append(match.end())

    # Check if text ends with punctuation (no space after)
    if text and text[-1] in ".!?":
        boundaries.append(len(text))

    return boundaries


def find_phrase_boundaries(text: str) -> List[int]:
    """
    Find phrase boundary positions in text.

    Detects commas, conjunctions, and other natural pause points.

    Args:
        text: Input text to analyze

    Returns:
        List of character positions where phrases could be split

    Example:
        >>> find_phrase_boundaries("Hello, world and goodbye")
        [6, 17]
    """
    boundaries = []

    # Pattern 1: Commas followed by space
    for match in re.finditer(r",\s+", text):
        boundaries.append(match.end())

    # Pattern 2: Conjunctions with spaces (but not at start/end)
    conjunctions = [" and ", " but ", " so ", " or ", " yet "]
    for conj in conjunctions:
        pos = 0
        while True:
            pos = text.find(conj, pos)
            if pos == -1:
                break
            # Position after the conjunction
            boundaries.append(pos + len(conj))
            pos += len(conj)

    # Sort and deduplicate
    boundaries = sorted(set(boundaries))

    return boundaries


def calculate_reading_speed(text: str, duration: float) -> float:
    """
    Calculate reading speed in characters per second.

    Args:
        text: Caption text
        duration: Time duration in seconds

    Returns:
        Characters per second (chars/sec)

    Example:
        >>> calculate_reading_speed("Hello world", 2.0)
        5.5
    """
    if duration <= 0:
        return 0.0

    char_count = len(text)
    return char_count / duration


def distribute_timestamps(
    start_time: float, end_time: float, text_segments: List[str]
) -> List[Tuple[float, float]]:
    """
    Distribute time range proportionally across text segments.

    Time is allocated based on character count ratio. Each segment gets
    duration proportional to its length.

    Args:
        start_time: Start time in seconds
        end_time: End time in seconds
        text_segments: List of text strings to distribute time across

    Returns:
        List of (start_time, end_time) tuples for each segment

    Raises:
        ValueError: If segments are empty or time range invalid

    Example:
        >>> distribute_timestamps(0.0, 10.0, ["Hello", "World!"])
        [(0.0, 4.545...), (4.545..., 10.0)]
    """
    if not text_segments:
        raise ValueError("Cannot distribute timestamps: no text segments")

    if end_time <= start_time:
        raise ValueError(f"Invalid time range: {start_time} to {end_time}")

    total_duration = end_time - start_time
    total_chars = sum(len(seg) for seg in text_segments)

    if total_chars == 0:
        # All segments empty - distribute equally
        segment_duration = total_duration / len(text_segments)
        return [
            (start_time + i * segment_duration, start_time + (i + 1) * segment_duration)
            for i in range(len(text_segments))
        ]

    # Distribute proportionally by character count
    timestamps = []
    current_time = start_time

    for i, segment in enumerate(text_segments):
        char_ratio = len(segment) / total_chars
        duration = total_duration * char_ratio

        # Last segment gets remaining time (avoid rounding errors)
        if i == len(text_segments) - 1:
            segment_end = end_time
        else:
            segment_end = current_time + duration

        timestamps.append((current_time, segment_end))
        current_time = segment_end

    return timestamps


def split_at_position(
    text: str,
    max_pos: int,
    sentence_boundaries: List[int],
    phrase_boundaries: List[int],
) -> Tuple[str, str]:
    """
    Split text at best boundary position before max_pos.

    Prioritizes sentence boundaries over phrase boundaries to avoid breaking
    sentences in the middle. Only uses phrase boundaries if no sentence
    boundary is available.

    Args:
        text: Text to split
        max_pos: Maximum position to split at
        sentence_boundaries: List of sentence boundary positions
        phrase_boundaries: List of phrase boundary positions

    Returns:
        Tuple of (before, after) strings

    Example:
        >>> split_at_position("Hello, world!", 10, [13], [6])
        ("Hello,", " world!")
    """
    # Priority 1: Try sentence boundaries first
    valid_sentence_boundaries = [b for b in sentence_boundaries if b < max_pos]

    if valid_sentence_boundaries:
        # Use last valid sentence boundary
        split_pos = max(valid_sentence_boundaries)
    else:
        # Priority 2: Try phrase boundaries
        valid_phrase_boundaries = [b for b in phrase_boundaries if b < max_pos]

        if valid_phrase_boundaries:
            # Use last valid phrase boundary
            split_pos = max(valid_phrase_boundaries)
        else:
            # Priority 3: Split at word boundary
            space_pos = text.rfind(" ", 0, max_pos)
            if space_pos > 0:
                split_pos = space_pos + 1
            else:
                # Last resort: hard split at max_pos
                split_pos = max_pos

    before = text[:split_pos].strip()
    after = text[split_pos:].strip()

    return before, after


def split_long_caption(
    start_time: float,
    end_time: float,
    text: str,
    max_duration: float = 6.0,
    max_chars: int = 100,
    min_duration: float = 1.0,
) -> List[Tuple[float, float, str]]:
    """
    Split a long caption into shorter segments with timestamps.

    Uses natural language boundaries (sentences, phrases) to split captions
    that exceed maximum duration or character count. Time is distributed
    proportionally across segments.

    Args:
        start_time: Caption start time in seconds
        end_time: Caption end time in seconds
        text: Caption text
        max_duration: Maximum duration per caption (seconds)
        max_chars: Maximum characters per caption
        min_duration: Minimum duration per caption (seconds)

    Returns:
        List of (start_time, end_time, text) tuples for each caption segment

    Example:
        >>> split_long_caption(0.0, 10.0, "Hello. World.", max_duration=5.0)
        [(0.0, 5.0, "Hello."), (5.0, 10.0, "World.")]
    """
    duration = end_time - start_time

    # Check if splitting is needed
    needs_split = duration > max_duration or len(text) > max_chars

    if not needs_split:
        # Caption is fine as-is
        return [(start_time, end_time, text)]

    # Check if caption is too short to split
    if duration < (min_duration * 2):
        logger.warning(
            f"Caption too short to split: {duration:.1f}s (min {min_duration * 2:.1f}s needed)"
        )
        return [(start_time, end_time, text)]

    # Find all possible split points
    sentence_boundaries = find_sentence_boundaries(text)
    phrase_boundaries = find_phrase_boundaries(text)

    # Check if any boundaries exist
    if not sentence_boundaries and not phrase_boundaries:
        # No natural boundaries - can't split cleanly
        logger.warning(f"No natural boundaries found in: {text[:50]}...")
        return [(start_time, end_time, text)]

    # Split into segments
    segments = []
    remaining_text = text
    current_pos = 0

    while remaining_text:
        # Determine max chars for this segment
        target_chars = max_chars

        if len(remaining_text) <= target_chars:
            # Remaining text fits - done
            segments.append(remaining_text)
            break

        # Find boundaries relative to current position
        relative_sentence_boundaries = [
            b - current_pos for b in sentence_boundaries if b > current_pos
        ]
        relative_phrase_boundaries = [b - current_pos for b in phrase_boundaries if b > current_pos]

        if not relative_sentence_boundaries and not relative_phrase_boundaries:
            # No more boundaries - take remaining text
            segments.append(remaining_text)
            break

        # Split at best boundary (prioritizes sentences over phrases)
        before, after = split_at_position(
            remaining_text,
            target_chars,
            relative_sentence_boundaries,
            relative_phrase_boundaries,
        )

        if not before:
            # Split failed - take whole remaining text
            segments.append(remaining_text)
            break

        segments.append(before)
        current_pos += len(before) + (len(remaining_text) - len(before) - len(after))
        remaining_text = after

    # Distribute timestamps
    try:
        timestamps = distribute_timestamps(start_time, end_time, segments)
    except ValueError as e:
        logger.error(f"Failed to distribute timestamps: {e}")
        return [(start_time, end_time, text)]

    # Filter out segments that are too short
    result: List[Tuple[float, float, str]] = []
    for (seg_start, seg_end), seg_text in zip(timestamps, segments):
        seg_duration = seg_end - seg_start

        if seg_duration < min_duration and len(result) > 0:
            # Merge with previous segment
            prev_start, prev_end, prev_text = result[-1]
            result[-1] = (prev_start, seg_end, f"{prev_text} {seg_text}")
        else:
            result.append((seg_start, seg_end, seg_text))

    logger.info(f"Split caption {duration:.1f}s ({len(text)}chars) -> {len(result)} segments")

    return result
