"""
WebVTT generation for audio transcripts with timestamps.

This module generates WebVTT (Web Video Text Tracks) files from text chunks
with word-level timestamps. VTT files are used for displaying captions/subtitles
in HTML5 audio/video players.

Wave 1 - Integration Contract IC-002
"""

import logging
import re
from pathlib import Path
from typing import List, Optional

from .types import TextChunk

logger = logging.getLogger(__name__)


class VTTGenerationError(Exception):
    """Base exception for VTT generation errors."""


class InvalidTimestampError(VTTGenerationError):
    """Raised when timestamp format is invalid."""


class EmptyChunkError(VTTGenerationError):
    """Raised when no chunks with timestamps available."""


def format_timestamp(seconds: float) -> str:
    """
    Format seconds as VTT timestamp.

    Args:
        seconds: Time in seconds (float)

    Returns:
        VTT timestamp string (HH:MM:SS.mmm)

    Example:
        >>> format_timestamp(65.500)
        '00:01:05.500'
        >>> format_timestamp(3725.123)
        '01:02:05.123'
    """
    if seconds < 0:
        raise InvalidTimestampError(f"Negative timestamp not allowed: {seconds}")

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60

    # Format: HH:MM:SS.mmm
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def validate_vtt(vtt_content: str) -> bool:
    """
    Validate VTT content format.

    Args:
        vtt_content: VTT file content

    Returns:
        True if valid VTT format, False otherwise

    Checks:
        - Starts with "WEBVTT"
        - Has valid timestamp format
        - Cues are properly formatted
    """
    if not vtt_content:
        return False

    lines = vtt_content.split("\n")

    # Must start with WEBVTT
    if not lines or not lines[0].startswith("WEBVTT"):
        return False

    # Check for at least one valid timestamp line
    timestamp_pattern = re.compile(r"\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}")
    has_timestamp = any(timestamp_pattern.match(line) for line in lines)

    return has_timestamp


def generate_vtt(chunks: List[TextChunk], filename: str) -> str:
    """
    Generate WebVTT content from text chunks with timestamps.

    Args:
        chunks: List of TextChunk objects with start_time/end_time
        filename: Original filename (for metadata comment)

    Returns:
        Complete VTT file content as string

    Raises:
        ValueError: If chunks have no timestamps
        VTTGenerationError: If VTT generation fails

    Example:
        >>> chunks = [
        ...     TextChunk(..., start_time=0.0, end_time=5.5, text="Hello"),
        ...     TextChunk(..., start_time=5.5, end_time=10.0, text="World"),
        ... ]
        >>> vtt = generate_vtt(chunks, "test.mp3")
        >>> print(vtt[:6])
        WEBVTT
    """
    try:
        # 1. Header
        vtt_lines = ["WEBVTT"]
        vtt_lines.append("")  # Blank line required

        # 2. Optional metadata comment
        vtt_lines.append(f"NOTE Generated from {filename}")
        vtt_lines.append("")

        # 3. Filter chunks with timestamps
        timestamped_chunks = [
            c for c in chunks if c.start_time is not None and c.end_time is not None
        ]

        if not timestamped_chunks:
            raise EmptyChunkError(f"No chunks with timestamps in {filename}")

        logger.info(
            f"Generating VTT from {len(timestamped_chunks)}/{len(chunks)} chunks "
            f"with timestamps"
        )

        # 4. Generate cues
        cue_number = 1
        for chunk in timestamped_chunks:
            # Validate text first (before adding any lines)
            text = chunk.text.strip()
            if not text:
                logger.warning(f"Skipping chunk {chunk.chunk_id}: empty text")
                continue

            # Validate timestamps
            if chunk.end_time <= chunk.start_time:
                logger.warning(
                    f"Skipping chunk {chunk.chunk_id}: invalid timestamps "
                    f"(start={chunk.start_time}, end={chunk.end_time})"
                )
                continue

            # Format timestamps
            try:
                start = format_timestamp(chunk.start_time)
                end = format_timestamp(chunk.end_time)
            except InvalidTimestampError as e:
                logger.warning(f"Skipping chunk {chunk.chunk_id}: {e}")
                continue

            # Now add the cue (only if all validations pass)
            # Cue identifier (optional but recommended)
            vtt_lines.append(str(cue_number))
            cue_number += 1

            # Cue timings
            vtt_lines.append(f"{start} --> {end}")

            # Cue text
            vtt_lines.append(text)

            # Blank line between cues
            vtt_lines.append("")

        vtt_content = "\n".join(vtt_lines)

        # Validate generated VTT
        if not validate_vtt(vtt_content):
            raise VTTGenerationError("Generated VTT failed validation")

        logger.info(f"Generated VTT file with {cue_number - 1} cues from {filename}")
        return vtt_content

    except EmptyChunkError:
        raise
    except Exception as e:
        raise VTTGenerationError(f"Failed to generate VTT: {e}") from e


def save_vtt(doc_id: str, vtt_content: str, output_dir: Optional[Path] = None) -> Path:
    """
    Save VTT content to filesystem.

    Args:
        doc_id: Document identifier (SHA-256 hash)
        vtt_content: Complete VTT file content
        output_dir: Optional output directory (default: data/vtt/)

    Returns:
        Path to saved VTT file

    Raises:
        IOError: If file write fails

    Example:
        >>> vtt = generate_vtt(chunks, "test.mp3")
        >>> path = save_vtt("abc123...", vtt)
        >>> print(path)
        data/vtt/abc123.vtt
    """
    try:
        # 1. Determine output directory
        if output_dir is None:
            output_dir = Path("data/vtt")

        # 2. Create directory if doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # 3. Generate filename
        filename = f"{doc_id}.vtt"
        output_path = output_dir / filename

        # 4. Write file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(vtt_content)

        logger.info(f"Saved VTT file: {output_path}")

        # 5. Return path
        return output_path

    except Exception as e:
        raise IOError(f"Failed to save VTT file: {e}") from e
