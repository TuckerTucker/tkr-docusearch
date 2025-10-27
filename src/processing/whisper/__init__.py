"""
Custom MLX-Whisper audio processing module.

This module provides custom whisper-based audio transcription for MP3/WAV files,
replacing Docling's ASR system with MLX-Whisper optimized for Apple Silicon.

Main Entry Point:
    parse_audio_with_whisper() - Parse audio file to Page/metadata format (IC-002)

Components:
    transcriber.py - Core MLX-Whisper transcription engine (IC-001)
    transcript_formatter.py - Format whisper output with timestamp markers
    metadata_builder.py - Build audio metadata dictionaries
    audio_parser.py - Main orchestration and entry point
    output_validator.py - Output validation (Wave 1)

Integration Contracts:
    IC-001: Whisper Output Format
    IC-002: Page and Metadata Format
    IC-003: Configuration Interface
    IC-004: Error Handling Protocol

Usage:
    >>> from src.processing.whisper import parse_audio_with_whisper
    >>> pages, metadata, whisper_result = parse_audio_with_whisper("audio.mp3")
    >>> print(pages[0].text)
    [time: 0.0-4.0] Shakespeare on Scenery by Oscar Wilde.
    [time: 5.28-9.96] This is a LibriVox recording.
"""

# Import main entry point (IC-002)
from .audio_parser import ParsingError, TimestampExtractionError, parse_audio_with_whisper
from .metadata_builder import build_audio_metadata
from .output_validator import validate_whisper_output

# Import core transcriber (IC-001)
from .transcriber import (
    AudioFormatError,
    AudioProcessingError,
    WhisperTranscriptionError,
    transcribe_audio,
)

# Import utilities
from .transcript_formatter import format_transcript_with_timestamps

__all__ = [
    # Main entry point (IC-002)
    "parse_audio_with_whisper",
    # Core transcription (IC-001)
    "transcribe_audio",
    # Utilities
    "format_transcript_with_timestamps",
    "build_audio_metadata",
    "validate_whisper_output",
    # Exceptions (IC-004)
    "ParsingError",
    "AudioProcessingError",
    "WhisperTranscriptionError",
    "AudioFormatError",
    "TimestampExtractionError",
]
