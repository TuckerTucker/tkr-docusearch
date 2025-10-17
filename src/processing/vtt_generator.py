"""
WebVTT generation for audio transcripts with timestamps.

This module generates WebVTT (Web Video Text Tracks) files from text chunks
with word-level timestamps. VTT files are used for displaying captions/subtitles
in HTML5 audio/video players.

Wave 1 - Integration Contract IC-002
Wave 2 - Enhanced with fine-grained caption extraction from [time: X-Y] markers
"""

import logging
import re
from pathlib import Path
from typing import List, Optional

from .types import Page, TextChunk

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


def extract_all_timestamp_markers(text: str) -> List[tuple]:
    """
    Extract ALL [time: X-Y] markers and their associated text from transcript.

    Args:
        text: Original transcript text with [time: X-Y] markers

    Returns:
        List of (start_time, end_time, caption_text) tuples

    Example:
        >>> text = "[time: 0.5-3.2] Hello. [time: 3.2-5.0] World."
        >>> extract_all_timestamp_markers(text)
        [(0.5, 3.2, "Hello."), (3.2, 5.0, "World.")]
    """
    captions = []

    # Pattern to match [time: X-Y] followed by text until next marker or end
    # Captures: (start_time)-(end_time) and text until next [time: or end of string
    pattern = r"\[time:\s*([\d.]+)-([\d.]+)\]\s*([^\[]+?)(?=\[time:|$)"

    matches = re.finditer(pattern, text, re.DOTALL)

    for match in matches:
        try:
            start_time = float(match.group(1))
            end_time = float(match.group(2))
            caption_text = match.group(3).strip()

            # Validate
            if start_time < 0 or end_time <= start_time or not caption_text:
                continue

            captions.append((start_time, end_time, caption_text))
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse timestamp marker: {e}")
            continue

    return captions


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


def generate_vtt(chunks: List[TextChunk], filename: str, pages: Optional[List[Page]] = None) -> str:
    """
    Generate WebVTT content from text chunks with timestamps.

    Wave 2: If pages provided (audio), extracts ALL [time: X-Y] markers for
    fine-grained captions. Otherwise falls back to chunk-level timestamps.

    Args:
        chunks: List of TextChunk objects with start_time/end_time
        filename: Original filename (for metadata comment)
        pages: Optional list of Page objects with original transcript text

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

        # 3. Determine caption source: fine-grained (pages) or chunk-level
        captions = []

        if pages and len(pages) > 0:
            # Wave 2: Extract ALL [time: X-Y] markers from original transcript
            logger.info("Extracting fine-grained captions from transcript markers")

            # For audio, original transcript is in pages[0].text
            original_text = pages[0].text

            # Extract all timestamp markers and their text
            captions = extract_all_timestamp_markers(original_text)

            if not captions:
                logger.warning("No timestamp markers found in transcript, falling back to chunks")

        # Fallback: Use chunk-level timestamps if no fine-grained captions
        if not captions:
            logger.info("Using chunk-level timestamps for VTT generation")
            timestamped_chunks = [
                c for c in chunks if c.start_time is not None and c.end_time is not None
            ]

            if not timestamped_chunks:
                raise EmptyChunkError(f"No chunks with timestamps in {filename}")

            # Convert chunks to caption tuples
            for chunk in timestamped_chunks:
                captions.append((chunk.start_time, chunk.end_time, chunk.text))

        logger.info(f"Generating VTT from {len(captions)} captions")

        # 4. Generate cues from captions
        cue_number = 1
        for start_time, end_time, text in captions:
            # Validate text first
            text = text.strip()
            if not text:
                logger.warning(f"Skipping caption {cue_number}: empty text")
                continue

            # Validate timestamps
            if end_time <= start_time:
                logger.warning(
                    f"Skipping caption {cue_number}: invalid timestamps "
                    f"(start={start_time}, end={end_time})"
                )
                continue

            # Format timestamps
            try:
                start = format_timestamp(start_time)
                end = format_timestamp(end_time)
            except InvalidTimestampError as e:
                logger.warning(f"Skipping caption {cue_number}: {e}")
                continue

            # Add the cue
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
