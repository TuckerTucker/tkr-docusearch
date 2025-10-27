"""
Audio metadata builder for ChromaDB storage.

This module builds complete metadata dictionaries from whisper transcription
results and ID3 tags, implementing Integration Contract IC-002 metadata format
requirements.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def build_audio_metadata(
    whisper_result: dict,
    file_path: str,
    asr_model: str,
    asr_language: str,
    audio_id3_metadata: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Build audio metadata dict following IC-002.

    This function creates a complete metadata dictionary with ALL required fields
    for ChromaDB storage and downstream processing. It merges whisper transcription
    data with ID3 metadata (if available) and file properties.

    Args:
        whisper_result: WhisperOutput dictionary from transcriber with:
            - text: Full transcript (str)
            - segments: List of WhisperSegment dicts
            - language: Language code (str)
            - duration: Total audio duration (float)
        file_path: Absolute path to audio file
        asr_model: ASR model name used (turbo, base, small, etc.)
        asr_language: Language used for transcription (en, auto, etc.)
        audio_id3_metadata: Optional AudioMetadata object from mutagen

    Returns:
        Dict with ALL required metadata fields per IC-002:
        - format_type="audio" (REQUIRED)
        - has_word_timestamps=True (REQUIRED)
        - audio_duration_seconds (REQUIRED)
        - num_pages=1 (REQUIRED)
        - has_images=False (REQUIRED)
        - transcript_method="whisper" (REQUIRED)
        - asr_model_used (REQUIRED)
        - Plus ID3 metadata if available
        - Plus file properties

    IC-002 Required Fields:
        REQUIRED_FIELDS = {
            "format_type": "audio",
            "has_word_timestamps": True,
            "audio_duration_seconds": float,
            "num_pages": 1,
            "has_images": False,
            "transcript_method": "whisper",
            "asr_model_used": str,
        }

    Examples:
        >>> from src.config.processing_config import AsrConfig
        >>> whisper_result = {
        ...     "text": "Hello world",
        ...     "segments": [...],
        ...     "language": "en",
        ...     "duration": 10.5
        ... }
        >>> metadata = build_audio_metadata(
        ...     whisper_result, "test.mp3", "turbo", "en", None
        ... )
        >>> metadata["format_type"]
        'audio'
        >>> metadata["has_word_timestamps"]
        True
    """
    # Validate inputs
    if not whisper_result:
        logger.error("Empty whisper_result passed to metadata builder")
        raise ValueError("whisper_result cannot be empty")

    if not file_path:
        logger.error("Empty file_path passed to metadata builder")
        raise ValueError("file_path cannot be empty")

    file_path_obj = Path(file_path)
    file_ext = file_path_obj.suffix.lower().lstrip(".")
    filename = file_path_obj.name

    # Extract duration from whisper result
    duration = whisper_result.get("duration", 0.0)
    detected_language = whisper_result.get("language", asr_language)

    # Start building metadata dict with REQUIRED fields (IC-002)
    metadata: Dict[str, Any] = {
        # Document identification (REQUIRED)
        "title": filename,  # Default, may be overridden by ID3
        "author": "",  # Default, may be overridden by ID3
        "created": "",  # Default, may be overridden by ID3
        "format": file_ext,
        "num_pages": 1,  # ALWAYS 1 for audio (IC-002)
        "format_type": "audio",  # REQUIRED - triggers audio handling (IC-002)
        "has_images": False,  # ALWAYS False for audio (IC-002)
        # Audio-specific (REQUIRED by IC-002)
        "audio_format": file_ext,
        "audio_duration_seconds": duration,
        "transcript_method": "whisper",
        "asr_model_used": asr_model,
        "asr_language": detected_language,
        "has_word_timestamps": True,  # MUST be True (IC-002)
        # Origin metadata (REQUIRED)
        "original_filename": filename,
        "mimetype": _get_mimetype(file_ext),
        # Markdown metadata (OPTIONAL)
        "markdown_extracted": True,
        "markdown_error": None,
    }

    # Add ID3 metadata if available
    if audio_id3_metadata:
        _merge_id3_metadata(metadata, audio_id3_metadata)

    # Calculate markdown length from formatted transcript
    if "text" in whisper_result:
        metadata["markdown_length"] = len(whisper_result["text"])

    # Log metadata construction
    logger.info(
        f"Built audio metadata: {filename} "
        f"(duration: {duration:.1f}s, model: {asr_model}, "
        f"language: {detected_language}, has_id3: {audio_id3_metadata is not None})"
    )

    logger.debug(f"Metadata fields: {list(metadata.keys())}")

    # Validate required fields are present
    _validate_required_fields(metadata)

    return metadata


def _get_mimetype(file_ext: str) -> str:
    """
    Get MIME type from file extension.

    Args:
        file_ext: File extension without dot (mp3, wav)

    Returns:
        MIME type string (audio/mpeg, audio/wav)
    """
    mime_map = {
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "m4a": "audio/mp4",
        "flac": "audio/flac",
        "ogg": "audio/ogg",
    }
    return mime_map.get(file_ext.lower(), "audio/mpeg")


def _merge_id3_metadata(metadata: Dict[str, Any], id3_metadata: Any) -> None:
    """
    Merge ID3 metadata from AudioMetadata object into metadata dict.

    Updates metadata dict in-place with ID3 tags, overriding defaults
    where appropriate and adding audio_ prefixed fields.

    Args:
        metadata: Metadata dict to update (modified in-place)
        id3_metadata: AudioMetadata object from mutagen
    """
    try:
        # Override title/author/created if ID3 data available
        if id3_metadata.title:
            metadata["title"] = id3_metadata.title
            metadata["id3_title"] = id3_metadata.title

        if id3_metadata.artist:
            metadata["author"] = id3_metadata.artist
            metadata["id3_artist"] = id3_metadata.artist

        if id3_metadata.year:
            metadata["created"] = id3_metadata.year
            metadata["id3_year"] = id3_metadata.year

        # Add additional ID3 fields (OPTIONAL per IC-002)
        if id3_metadata.album:
            metadata["id3_album"] = id3_metadata.album

        if id3_metadata.genre:
            metadata["id3_genre"] = id3_metadata.genre

        if id3_metadata.track_number:
            metadata["id3_track"] = id3_metadata.track_number

        if id3_metadata.composer:
            metadata["id3_composer"] = id3_metadata.composer

        if id3_metadata.album_artist:
            metadata["id3_album_artist"] = id3_metadata.album_artist

        if id3_metadata.publisher:
            metadata["id3_publisher"] = id3_metadata.publisher

        if id3_metadata.comment:
            metadata["id3_comment"] = id3_metadata.comment

        # Album art metadata (not the data itself)
        metadata["has_album_art"] = id3_metadata.has_album_art

        if id3_metadata.album_art_mime:
            metadata["_album_art_mime"] = id3_metadata.album_art_mime

        if id3_metadata.album_art_data:
            # Store raw album art data temporarily (IC-002)
            # This will be extracted and saved to filesystem by storage layer
            metadata["_album_art_data"] = id3_metadata.album_art_data

        # Audio properties (if available)
        if id3_metadata.bitrate_kbps:
            metadata["audio_bitrate_kbps"] = id3_metadata.bitrate_kbps

        if id3_metadata.sample_rate_hz:
            metadata["audio_sample_rate_hz"] = id3_metadata.sample_rate_hz

        if id3_metadata.channels:
            metadata["audio_channels"] = id3_metadata.channels

        if id3_metadata.encoder:
            metadata["audio_encoder"] = id3_metadata.encoder

        logger.debug(
            f"Merged ID3 metadata: title={id3_metadata.title}, "
            f"artist={id3_metadata.artist}, "
            f"album_art={id3_metadata.has_album_art}"
        )

    except Exception as e:
        logger.warning(f"Error merging ID3 metadata: {e}", exc_info=True)
        # Continue without ID3 metadata rather than failing


def _validate_required_fields(metadata: Dict[str, Any]) -> None:
    """
    Validate that all IC-002 required fields are present.

    Args:
        metadata: Metadata dict to validate

    Raises:
        ValueError: If required fields are missing or invalid

    IC-002 Required Fields:
        - format_type="audio"
        - has_word_timestamps=True
        - audio_duration_seconds (float)
        - num_pages=1
        - has_images=False
        - transcript_method="whisper"
        - asr_model_used (str)
    """
    required_fields = [
        "format_type",
        "has_word_timestamps",
        "audio_duration_seconds",
        "num_pages",
        "has_images",
        "transcript_method",
        "asr_model_used",
    ]

    # Check all required fields are present
    missing_fields = [field for field in required_fields if field not in metadata]

    if missing_fields:
        raise ValueError(
            f"Missing required metadata fields (IC-002): {missing_fields}. "
            f"Present fields: {list(metadata.keys())}"
        )

    # Validate field values (IC-002 constraints)
    if metadata["format_type"] != "audio":
        raise ValueError(f"format_type must be 'audio', got '{metadata['format_type']}' (IC-002)")

    if metadata["has_word_timestamps"] is not True:
        raise ValueError(
            f"has_word_timestamps must be True, got {metadata['has_word_timestamps']} (IC-002)"
        )

    if metadata["num_pages"] != 1:
        raise ValueError(f"num_pages must be 1 for audio, got {metadata['num_pages']} (IC-002)")

    if metadata["has_images"] is not False:
        raise ValueError(
            f"has_images must be False for audio, got {metadata['has_images']} (IC-002)"
        )

    if not isinstance(metadata["audio_duration_seconds"], (int, float)):
        raise ValueError(
            f"audio_duration_seconds must be numeric, got {type(metadata['audio_duration_seconds'])} (IC-002)"
        )

    logger.debug("IC-002 required fields validation passed")
