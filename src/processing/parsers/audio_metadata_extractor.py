"""
Audio metadata extraction helper.

This module handles ID3 metadata and album art extraction from audio files,
extracted from DoclingParser for reduced complexity.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AudioMetadataExtractor:
    """Helper for extracting audio metadata."""

    @staticmethod
    def extract_id3_metadata(file_path: str) -> Optional[Any]:
        """
        Extract ID3 metadata from audio file.

        Args:
            file_path: Path to audio file (MP3 or WAV)

        Returns:
            AudioMetadata object or None if extraction fails
        """
        try:
            from src.processing.audio_metadata import extract_audio_metadata

            logger.info(f"Extracting ID3 metadata from {file_path}")
            audio_id3_metadata = extract_audio_metadata(file_path)
            logger.debug(f"ID3 extraction complete: {audio_id3_metadata.to_chromadb_metadata()}")
            return audio_id3_metadata
        except Exception as e:
            logger.warning(f"Failed to extract ID3 metadata from {file_path}: {e}")
            return None

    @staticmethod
    def merge_audio_metadata(
        metadata: Dict[str, Any], doc, audio_id3_metadata: Optional[Any], asr_config: Optional[Any]
    ) -> None:
        """
        Merge audio-specific metadata into document metadata.

        This method modifies the metadata dict in-place, adding:
        - ASR transcription metadata
        - Audio file format and duration
        - ID3 tags (title, artist, album, etc.)
        - Album art data (temporary, saved later)
        - Timestamp availability

        Args:
            metadata: Document metadata dict (modified in-place)
            doc: DoclingDocument with audio data
            audio_id3_metadata: Extracted ID3 metadata (optional)
            asr_config: ASR configuration (optional)
        """
        # ASR-specific metadata (transcription)
        metadata["transcript_method"] = "whisper"
        metadata["asr_model_used"] = asr_config.model if asr_config else "unknown"
        metadata["asr_language"] = asr_config.language if asr_config else "unknown"

        # Try to extract duration from Docling document
        if hasattr(doc, "audio_duration"):
            metadata["audio_duration_seconds"] = doc.audio_duration
        elif hasattr(doc.origin, "duration"):
            metadata["audio_duration_seconds"] = doc.origin.duration

        # Merge ID3 metadata (tags, audio properties) if extracted
        if audio_id3_metadata:
            id3_fields = audio_id3_metadata.to_chromadb_metadata()
            metadata.update(id3_fields)
            logger.debug(f"Merged {len(id3_fields)} ID3 fields into metadata")

            # Save album art if present (requires doc_id from processor)
            # Note: Album art will be saved during document processing
            # when doc_id is available. We store the raw data in the metadata object for now.
            if audio_id3_metadata.has_album_art:
                # Store album art data temporarily in a special metadata field
                # It will be saved to disk by the processor
                metadata["_album_art_data"] = audio_id3_metadata.album_art_data
                metadata["_album_art_mime"] = audio_id3_metadata.album_art_mime

        # Extract timestamp information if available
        if hasattr(doc, "texts") and doc.texts:
            # Check if timestamps are in provenance
            has_timestamps = False
            for text_item in doc.texts:
                if hasattr(text_item, "prov") and text_item.prov:
                    for prov in text_item.prov:
                        if hasattr(prov, "start_time") and hasattr(prov, "end_time"):
                            has_timestamps = True
                            break
                    if has_timestamps:
                        break

            metadata["has_word_timestamps"] = has_timestamps
