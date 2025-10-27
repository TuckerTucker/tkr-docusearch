"""
Whisper output validation utilities.

Validates whisper transcription output against Integration Contract IC-001.
"""

import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


def validate_whisper_output(result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate whisper output meets IC-001 contract requirements.

    Args:
        result: Whisper transcription output

    Returns:
        Tuple of (is_valid, error_messages)
        - (True, []) if valid
        - (False, [list of errors]) if invalid

    Examples:
        >>> result = {"text": "...", "segments": [...], "language": "en", "duration": 120.5}
        >>> is_valid, errors = validate_whisper_output(result)
        >>> assert is_valid
    """
    errors = []

    # Check required top-level fields
    required_fields = ["text", "segments", "language", "duration"]
    for field in required_fields:
        if field not in result:
            errors.append(f"Missing required field: {field}")

    # If missing required fields, return early
    if errors:
        return (False, errors)

    # Validate text field
    if not isinstance(result["text"], str):
        errors.append(f"Field 'text' must be string, got {type(result['text'])}")

    # Validate segments
    if not isinstance(result["segments"], list):
        errors.append(f"Field 'segments' must be list, got {type(result['segments'])}")
    else:
        if len(result["segments"]) == 0:
            errors.append("Field 'segments' is empty - no transcription generated")
        else:
            # Validate each segment
            for idx, segment in enumerate(result["segments"]):
                segment_errors = _validate_segment(segment, idx)
                errors.extend(segment_errors)

    # Validate language field
    if not isinstance(result["language"], str):
        errors.append(f"Field 'language' must be string, got {type(result['language'])}")

    # Validate duration field
    if not isinstance(result["duration"], (int, float)):
        errors.append(f"Field 'duration' must be number, got {type(result['duration'])}")
    elif result["duration"] <= 0:
        errors.append(f"Field 'duration' must be positive, got {result['duration']}")

    # Validate timestamp monotonicity
    if not errors:  # Only if segments are valid
        monotonicity_errors = _validate_timestamp_monotonicity(result["segments"])
        errors.extend(monotonicity_errors)

    is_valid = len(errors) == 0

    if not is_valid:
        logger.warning(f"Whisper output validation failed: {len(errors)} errors")
        for error in errors:
            logger.debug(f"  - {error}")

    return (is_valid, errors)


def _validate_segment(segment: Dict[str, Any], segment_idx: int) -> List[str]:
    """
    Validate a single segment structure.

    Args:
        segment: Segment dict
        segment_idx: Segment index (for error messages)

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    prefix = f"Segment {segment_idx}"

    # Check required segment fields
    required_fields = ["id", "start", "end", "text", "words"]
    for field in required_fields:
        if field not in segment:
            errors.append(f"{prefix}: Missing required field '{field}'")

    # If missing required fields, return early
    if errors:
        return errors

    # Validate timing
    if not isinstance(segment["start"], (int, float)):
        errors.append(f"{prefix}: Field 'start' must be number, got {type(segment['start'])}")

    if not isinstance(segment["end"], (int, float)):
        errors.append(f"{prefix}: Field 'end' must be number, got {type(segment['end'])}")

    if isinstance(segment["start"], (int, float)) and isinstance(segment["end"], (int, float)):
        if segment["start"] >= segment["end"]:
            errors.append(f"{prefix}: start ({segment['start']}) must be < end ({segment['end']})")

    # Validate text
    if not isinstance(segment["text"], str):
        errors.append(f"{prefix}: Field 'text' must be string, got {type(segment['text'])}")

    # Validate words (CRITICAL for IC-001)
    if not isinstance(segment["words"], list):
        errors.append(f"{prefix}: Field 'words' must be list, got {type(segment['words'])}")
    else:
        if len(segment["words"]) == 0:
            errors.append(f"{prefix}: Field 'words' is empty - word timestamps required (IC-001)")
        else:
            # Validate each word
            for word_idx, word in enumerate(segment["words"]):
                word_errors = _validate_word(word, segment_idx, word_idx)
                errors.extend(word_errors)

    return errors


def _validate_word(word: Dict[str, Any], segment_idx: int, word_idx: int) -> List[str]:
    """
    Validate a single word structure.

    Args:
        word: Word dict
        segment_idx: Segment index
        word_idx: Word index

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    prefix = f"Segment {segment_idx}, Word {word_idx}"

    # Check required word fields
    required_fields = ["word", "start", "end", "probability"]
    for field in required_fields:
        if field not in word:
            errors.append(f"{prefix}: Missing required field '{field}'")

    # If missing required fields, return early
    if errors:
        return errors

    # Validate word text
    if not isinstance(word["word"], str):
        errors.append(f"{prefix}: Field 'word' must be string, got {type(word['word'])}")

    # Validate timing
    if not isinstance(word["start"], (int, float)):
        errors.append(f"{prefix}: Field 'start' must be number, got {type(word['start'])}")

    if not isinstance(word["end"], (int, float)):
        errors.append(f"{prefix}: Field 'end' must be number, got {type(word['end'])}")

    if isinstance(word["start"], (int, float)) and isinstance(word["end"], (int, float)):
        if word["start"] >= word["end"]:
            errors.append(f"{prefix}: start ({word['start']}) must be < end ({word['end']})")

    # Validate probability
    if not isinstance(word["probability"], (int, float)):
        errors.append(
            f"{prefix}: Field 'probability' must be number, got {type(word['probability'])}"
        )
    elif not (0.0 <= word["probability"] <= 1.0):
        errors.append(f"{prefix}: probability must be in [0.0, 1.0], got {word['probability']}")

    return errors


def _validate_timestamp_monotonicity(segments: List[Dict[str, Any]]) -> List[str]:
    """
    Validate timestamps are monotonically increasing across segments.

    Args:
        segments: List of segments

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    prev_end = 0.0
    for idx, segment in enumerate(segments):
        if "start" not in segment or "end" not in segment:
            continue  # Already caught by segment validation

        start = segment["start"]
        end = segment["end"]

        # Check segment starts after or at previous segment end
        # Allow small overlap (0.1s tolerance) for speech overlap
        if start < prev_end - 0.1:
            errors.append(
                f"Segment {idx}: start ({start:.3f}s) before previous segment end ({prev_end:.3f}s)"
            )

        prev_end = max(prev_end, end)

    return errors
