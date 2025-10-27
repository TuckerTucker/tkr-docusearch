"""
Core MLX-Whisper transcription engine.

This module provides direct integration with mlx_whisper for audio transcription,
implementing Integration Contract IC-001 (Whisper Output Format).
"""

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

logger = logging.getLogger(__name__)


# ============================================================================
# Exception Hierarchy (IC-004)
# ============================================================================


class AudioProcessingError(Exception):
    """Base exception for audio processing errors."""


class WhisperTranscriptionError(AudioProcessingError):
    """Whisper transcription failed."""


class AudioFormatError(AudioProcessingError):
    """Invalid or unsupported audio format."""


# ============================================================================
# Type Definitions (IC-001)
# ============================================================================


class WhisperWord(TypedDict):
    """Word-level timestamp data."""

    word: str
    start: float  # seconds
    end: float  # seconds
    probability: float  # 0.0-1.0


class WhisperSegment(TypedDict):
    """Transcript segment with timing."""

    id: int
    seek: int
    start: float  # seconds
    end: float  # seconds
    text: str
    tokens: List[int]
    temperature: float
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float
    words: List[WhisperWord]  # REQUIRED - word_timestamps=True


class WhisperOutput(TypedDict):
    """Complete whisper transcription output (IC-001)."""

    text: str  # Full transcript (no timestamps)
    segments: List[WhisperSegment]
    language: str
    duration: float  # Total audio duration in seconds


# ============================================================================
# Model Configuration
# ============================================================================

# MLX Whisper HuggingFace repo mapping
MODEL_MAPPING = {
    "turbo": "mlx-community/whisper-large-v3-turbo",
    "base": "mlx-community/whisper-base-mlx",
    "small": "mlx-community/whisper-small-mlx",
    "medium": "mlx-community/whisper-medium-mlx",
    "large": "mlx-community/whisper-large-v3-mlx",
}


# ============================================================================
# Core Transcription Function
# ============================================================================


def transcribe_audio(
    file_path: str,
    model: str = "turbo",
    language: Optional[str] = None,
    word_timestamps: bool = True,
    temperature: float = 0.0,
) -> WhisperOutput:
    """
    Transcribe audio file using MLX-Whisper.

    This function implements Integration Contract IC-001 (Whisper Output Format),
    providing direct MLX-Whisper integration with word-level timestamps.

    Args:
        file_path: Absolute path to audio file (MP3/WAV)
        model: Model name (turbo, base, small, medium, large)
        language: ISO 639-1 code or None for auto-detection
        word_timestamps: MUST be True for timestamp extraction
        temperature: Sampling temperature (0.0 = deterministic)

    Returns:
        WhisperOutput with segments and word-level timestamps

    Raises:
        FileNotFoundError: Audio file not found
        AudioFormatError: Unsupported audio format
        WhisperTranscriptionError: Transcription failed
        ValueError: Invalid model or parameters

    Examples:
        >>> result = transcribe_audio("audio.mp3")
        >>> print(result["text"])
        'Full transcript...'
        >>> print(len(result["segments"]))
        10
    """
    # Validate inputs
    _validate_inputs(file_path, model, word_timestamps)

    # Get model repo ID
    model_repo = MODEL_MAPPING.get(model)
    if not model_repo:
        raise ValueError(f"Invalid model: {model}. Must be one of {list(MODEL_MAPPING.keys())}")

    # Log transcription start
    file_path_obj = Path(file_path)
    file_size_mb = file_path_obj.stat().st_size / (1024 * 1024)
    logger.info(
        f"Starting whisper transcription: {file_path} "
        f"(size: {file_size_mb:.2f}MB, model: {model}, language: {language or 'auto'})"
    )

    try:
        # Import mlx_whisper
        import mlx_whisper

        # Transcribe with MLX-Whisper
        start_time = time.time()

        result = mlx_whisper.transcribe(
            file_path,
            path_or_hf_repo=model_repo,
            language=language,
            word_timestamps=word_timestamps,
            temperature=temperature,
            fp16=False,  # MPS optimization
        )

        elapsed = time.time() - start_time

        # Validate result structure
        if not result or "segments" not in result:
            raise WhisperTranscriptionError("Whisper returned empty or invalid result")

        # Extract duration
        duration = _extract_duration(result, file_path)

        # Build output following IC-001 format
        output: WhisperOutput = {
            "text": result.get("text", ""),
            "segments": result.get("segments", []),
            "language": result.get("language", language or "unknown"),
            "duration": duration,
        }

        # Log completion
        total_words = sum(len(seg.get("words", [])) for seg in output["segments"])
        logger.info(
            f"Transcription complete: {duration:.1f}s audio in {elapsed:.1f}s "
            f"({len(output['segments'])} segments, {total_words} words, "
            f"{duration/elapsed:.2f}x real-time)"
        )

        logger.debug(
            f"Whisper output: {len(output['text'])} chars, " f"language: {output['language']}"
        )

        return output

    except ImportError as e:
        logger.error(f"MLX-Whisper not installed: {e}")
        raise WhisperTranscriptionError(
            "mlx_whisper library not available. Install with: pip install mlx-whisper"
        ) from e

    except FileNotFoundError:
        # Re-raise without wrapping
        raise

    except AudioFormatError:
        # Re-raise without wrapping
        raise

    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}", exc_info=True)
        raise WhisperTranscriptionError(f"Transcription failed: {e}") from e


# ============================================================================
# Helper Functions
# ============================================================================


def _validate_inputs(file_path: str, model: str, word_timestamps: bool) -> None:
    """
    Validate transcription inputs.

    Args:
        file_path: Path to audio file
        model: Model name
        word_timestamps: Word timestamps flag

    Raises:
        FileNotFoundError: File doesn't exist
        AudioFormatError: Unsupported format
        ValueError: Invalid parameters
    """
    # Check file exists
    path = Path(file_path)
    if not path.exists():
        logger.error(f"Audio file not found: {file_path}")
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    # Check file format
    ext = path.suffix.lower()
    if ext not in [".mp3", ".wav"]:
        logger.error(f"Unsupported audio format: {ext}")
        raise AudioFormatError(f"Unsupported audio format: {ext}. Supported formats: .mp3, .wav")

    # Check model name
    if model not in MODEL_MAPPING:
        raise ValueError(f"Invalid model: {model}. Must be one of {list(MODEL_MAPPING.keys())}")

    # Enforce word_timestamps=True (IC-001 requirement)
    if not word_timestamps:
        logger.warning("word_timestamps=False is not recommended - timestamps may not work")


def _extract_duration(result: Dict[str, Any], file_path: str) -> float:
    """
    Extract audio duration from whisper result or file.

    Args:
        result: Whisper transcription result
        file_path: Path to audio file

    Returns:
        Audio duration in seconds
    """
    # Try to get duration from whisper result
    if "duration" in result:
        return float(result["duration"])

    # Fall back to last segment end time
    if result.get("segments"):
        last_segment = result["segments"][-1]
        return float(last_segment.get("end", 0.0))

    # Last resort: use librosa (if available)
    try:
        import librosa

        duration = librosa.get_duration(path=file_path)
        logger.debug(f"Extracted duration from file: {duration:.2f}s")
        return duration
    except Exception as e:
        logger.warning(f"Could not extract audio duration: {e}")
        return 0.0
