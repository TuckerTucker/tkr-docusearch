"""
Transcript formatting with timestamp markers.

This module converts whisper segment data into formatted text with [time: X-Y]
timestamp markers, implementing Integration Contract IC-002 text format requirements.
"""

import logging
from typing import List

logger = logging.getLogger(__name__)


def format_transcript_with_timestamps(whisper_result: dict) -> str:
    """
    Format whisper segments into text with [time: X-Y] markers.

    This function implements the IC-002 text format requirement, converting
    whisper segments into a formatted transcript where each line begins with
    a timestamp marker in the format [time: START-END].

    Args:
        whisper_result: WhisperOutput dictionary from transcriber with:
            - text: Full transcript (str)
            - segments: List of WhisperSegment dicts
            - language: Language code (str)
            - duration: Total audio duration (float)

    Returns:
        Formatted text with timestamp markers, one segment per line.
        Format: "[time: 0.0-4.0] Shakespeare on Scenery by Oscar Wilde.\n"

    Examples:
        >>> result = {"segments": [
        ...     {"start": 0.0, "end": 4.0, "text": "Hello world."},
        ...     {"start": 5.28, "end": 9.96, "text": "This is a test."}
        ... ]}
        >>> text = format_transcript_with_timestamps(result)
        >>> print(text)
        [time: 0.0-4.0] Hello world.
        [time: 5.28-9.96] This is a test.

    IC-002 Format Requirements:
        - Each line MUST start with [time: START-END] marker
        - START and END are floats with 1-3 decimal places
        - Space after ] before text begins
        - Text from one segment per line
        - No blank lines between segments
    """
    # Validate input
    if not whisper_result:
        logger.error("Empty whisper_result passed to formatter")
        return ""

    segments = whisper_result.get("segments", [])

    if not segments:
        logger.warning("No segments found in whisper result")
        # If we have text but no segments, create a single segment
        if "text" in whisper_result and whisper_result["text"]:
            duration = whisper_result.get("duration", 0.0)
            logger.info(
                f"Creating single segment from full text "
                f"(duration: {duration:.1f}s, {len(whisper_result['text'])} chars)"
            )
            return f"[time: 0.0-{duration:.1f}] {whisper_result['text']}"
        # No segments and no text - return placeholder for silent/empty audio
        duration = whisper_result.get("duration", 0.0)
        logger.warning(f"No speech detected in audio (duration: {duration:.1f}s)")
        return f"[time: 0.0-{duration:.1f}] [no speech detected]"

    # Format each segment
    formatted_lines: List[str] = []
    total_segments = len(segments)

    for idx, segment in enumerate(segments):
        # Extract timing and text
        start = segment.get("start", 0.0)
        end = segment.get("end", 0.0)
        text = segment.get("text", "").strip()

        # Skip empty segments
        if not text:
            logger.debug(f"Skipping empty segment {idx + 1}/{total_segments}")
            continue

        # Format timestamp marker
        # Use 1 decimal place for clean timestamps, 2-3 for precision when needed
        start_str = _format_timestamp(start)
        end_str = _format_timestamp(end)

        # Build formatted line: [time: X-Y] text
        formatted_line = f"[time: {start_str}-{end_str}] {text}"
        formatted_lines.append(formatted_line)

    # Join with newlines (IC-002: no blank lines between segments)
    formatted_text = "\n".join(formatted_lines)

    # Handle case where all segments were empty
    if not formatted_text:
        duration = whisper_result.get("duration", 0.0)
        logger.warning(f"All {total_segments} segments had empty text (duration: {duration:.1f}s)")
        return f"[time: 0.0-{duration:.1f}] [no speech detected]"

    # Log formatting results
    logger.info(
        f"Formatted {len(formatted_lines)}/{total_segments} segments "
        f"({len(formatted_text)} chars)"
    )

    logger.debug(
        f"Sample formatted text (first 200 chars): "
        f"{formatted_text[:200]}{'...' if len(formatted_text) > 200 else ''}"
    )

    return formatted_text


def _format_timestamp(seconds: float) -> str:
    """
    Format timestamp for display in [time: X-Y] markers.

    Uses 1-3 decimal places to balance readability and precision:
    - 1 decimal: Clean timestamps (0.0, 5.0, 10.0)
    - 2-3 decimals: Precise timestamps (5.28, 10.125)

    Args:
        seconds: Timestamp in seconds

    Returns:
        Formatted timestamp string

    Examples:
        >>> _format_timestamp(0.0)
        '0.0'
        >>> _format_timestamp(5.28)
        '5.28'
        >>> _format_timestamp(10.125)
        '10.125'
    """
    # Round to 3 decimal places to avoid floating point noise
    rounded = round(seconds, 3)

    # Format and strip trailing zeros
    formatted = f"{rounded:.3f}".rstrip("0").rstrip(".")

    # Ensure at least one decimal place (IC-002 requirement)
    if "." not in formatted:
        formatted = f"{formatted}.0"

    return formatted
