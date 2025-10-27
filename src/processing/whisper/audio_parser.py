"""
Audio parser with custom whisper integration.

This module provides the main entry point for audio file parsing using custom
MLX-Whisper transcription, implementing Integration Contract IC-002 (Page and
Metadata Format).

This module orchestrates the complete audio parsing pipeline:
1. Load ASR configuration from environment
2. Transcribe audio with MLX-Whisper (via transcriber.py)
3. Format transcript with timestamp markers
4. Extract ID3 metadata from audio file
5. Build complete metadata dictionary
6. Create Page object with formatted text
7. Return (pages, metadata, whisper_result) tuple

Integration Point:
    This module is called by docling_parser.py for .mp3/.wav files, replacing
    Docling's ASR system with custom MLX-Whisper implementation.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.config.processing_config import AsrConfig, EnhancedModeConfig

# Import audio processing utilities
from src.processing.audio_metadata import AudioMetadata, extract_audio_metadata
from src.processing.types import Page

# Import custom whisper components (Wave 2)
from src.processing.whisper.metadata_builder import build_audio_metadata
from src.processing.whisper.transcriber import (
    AudioFormatError,
    AudioProcessingError,
    WhisperTranscriptionError,
    transcribe_audio,
)
from src.processing.whisper.transcript_formatter import format_transcript_with_timestamps

logger = logging.getLogger(__name__)


# ============================================================================
# Exception Hierarchy (IC-004)
# ============================================================================


class ParsingError(Exception):
    """Base exception for document parsing errors."""


class TimestampExtractionError(AudioProcessingError):
    """Failed to extract timestamps from whisper output."""


# ============================================================================
# Main Entry Point (IC-002)
# ============================================================================


def parse_audio_with_whisper(
    file_path: str, config: Optional[EnhancedModeConfig] = None
) -> Tuple[List[Page], Dict[str, Any], Any]:
    """
    Parse audio file with custom whisper (IC-002).

    This is the main entry point for audio parsing, implementing Integration
    Contract IC-002. It orchestrates the complete pipeline from audio file
    to Page objects with formatted text and complete metadata.

    Pipeline Steps:
        1. Load AsrConfig from environment
        2. Transcribe audio using transcribe_audio() from transcriber.py
        3. Format transcript with [time: X-Y] timestamp markers
        4. Extract ID3 metadata from audio file (MP3 only)
        5. Build complete metadata dictionary
        6. Create Page object with formatted text
        7. Return (pages, metadata, whisper_result) tuple

    Args:
        file_path: Absolute path to audio file (.mp3, .wav)
        config: Enhanced mode config (optional, reserved for future use)

    Returns:
        Tuple of:
        - pages: List[Page] with single Page containing formatted transcript
        - metadata: Dict with audio-specific fields (IC-002 compliant)
        - whisper_result: Raw whisper output (for potential chunking improvements)

    Raises:
        FileNotFoundError: Audio file not found
        AudioFormatError: Unsupported audio format
        WhisperTranscriptionError: Transcription failed
        TimestampExtractionError: Timestamp formatting failed
        ParsingError: General parsing error

    IC-002 Return Format:
        pages: [Page(
            page_num=1,
            image=None,
            width=0,
            height=0,
            text="[time: 0.0-4.0] Transcript text...\n[time: 5.0-9.0] More text..."
        )]

        metadata: {
            "format_type": "audio",  # REQUIRED
            "has_word_timestamps": True,  # REQUIRED
            "audio_duration_seconds": float,  # REQUIRED
            "num_pages": 1,  # REQUIRED
            "has_images": False,  # REQUIRED
            "transcript_method": "whisper",  # REQUIRED
            "asr_model_used": str,  # REQUIRED
            ... (plus ID3 and file metadata)
        }

    Examples:
        >>> pages, metadata, whisper_result = parse_audio_with_whisper("sample.mp3")
        >>> len(pages)
        1
        >>> pages[0].page_num
        1
        >>> pages[0].image is None
        True
        >>> "[time:" in pages[0].text
        True
        >>> metadata["format_type"]
        'audio'
    """
    # Log parsing start
    file_path_obj = Path(file_path)
    logger.info(f"Starting audio parsing with custom whisper: {file_path_obj.name}")

    try:
        # Step 1: Load ASR configuration from environment
        asr_config = AsrConfig.from_env()
        logger.debug(f"Loaded ASR config: {asr_config}")

        # Step 2: Transcribe audio with MLX-Whisper
        logger.info(f"Transcribing audio: {file_path_obj.name}")

        whisper_result = transcribe_audio(
            file_path=file_path,
            model=asr_config.model,
            language=asr_config.language if asr_config.language != "auto" else None,
            word_timestamps=asr_config.word_timestamps,
            temperature=asr_config.temperature,
        )

        logger.info(
            f"Transcription complete: {whisper_result['duration']:.1f}s audio, "
            f"{len(whisper_result['segments'])} segments"
        )

        # Step 3: Format transcript with timestamp markers
        logger.info("Formatting transcript with timestamps")

        formatted_text = format_transcript_with_timestamps(whisper_result)

        # Validate timestamp markers are present (IC-002 requirement)
        if not formatted_text or "[time:" not in formatted_text:
            raise TimestampExtractionError(
                f"No timestamp markers found in formatted text for {file_path_obj.name}. "
                f"Expected [time: X-Y] markers but got: {formatted_text[:200]}"
            )

        logger.info(f"Formatted transcript: {len(formatted_text)} chars with timestamp markers")

        # Step 4: Extract ID3 metadata (MP3 only)
        audio_metadata: Optional[AudioMetadata] = None

        if file_path_obj.suffix.lower() == ".mp3":
            try:
                logger.info("Extracting ID3 metadata from MP3 file")
                audio_metadata = extract_audio_metadata(file_path)
                logger.info(
                    f"ID3 extraction complete: title={audio_metadata.title}, "
                    f"artist={audio_metadata.artist}, "
                    f"has_album_art={audio_metadata.has_album_art}"
                )
            except Exception as e:
                # ID3 extraction is optional - continue without it
                logger.warning(f"Failed to extract ID3 metadata: {e}")
                audio_metadata = None

        # Step 5: Build complete metadata dictionary
        logger.info("Building audio metadata dictionary")

        metadata = build_audio_metadata(
            whisper_result=whisper_result,
            file_path=file_path,
            asr_model=asr_config.model,
            asr_language=asr_config.language,
            audio_id3_metadata=audio_metadata,
        )

        logger.info(f"Metadata complete: {len(metadata)} fields")

        # Step 6: Create Page object (IC-002 format)
        logger.info("Creating Page object with formatted transcript")

        page = Page(
            page_num=1,  # ALWAYS 1 for audio (IC-002)
            image=None,  # ALWAYS None for audio (IC-002)
            width=0,  # ALWAYS 0 for audio (IC-002)
            height=0,  # ALWAYS 0 for audio (IC-002)
            text=formatted_text,  # Formatted transcript with [time: X-Y] markers
        )

        pages = [page]

        # Log completion
        logger.info(
            f"Audio parsing complete: {file_path_obj.name} "
            f"({whisper_result['duration']:.1f}s, "
            f"{len(whisper_result['segments'])} segments, "
            f"{len(formatted_text)} chars)"
        )

        # Step 7: Return (pages, metadata, whisper_result) tuple
        return pages, metadata, whisper_result

    except FileNotFoundError:
        # Re-raise without wrapping (IC-004)
        logger.error(f"Audio file not found: {file_path}")
        raise

    except AudioFormatError:
        # Re-raise without wrapping (IC-004)
        logger.error(f"Unsupported audio format: {file_path}")
        raise

    except WhisperTranscriptionError:
        # Re-raise without wrapping (IC-004)
        logger.error(f"Whisper transcription failed: {file_path}")
        raise

    except TimestampExtractionError:
        # Re-raise without wrapping (IC-004)
        logger.error(f"Timestamp extraction failed: {file_path}")
        raise

    except Exception as e:
        # Wrap unexpected errors in ParsingError (IC-004)
        logger.error(f"Audio parsing failed: {file_path} - {e}", exc_info=True)
        raise ParsingError(f"Audio parsing failed for {file_path_obj.name}: {e}") from e
