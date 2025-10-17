"""
Album art handler for audio files.

This module handles album art saving for audio files,
extracted from DocumentProcessor for reduced complexity.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AlbumArtHandler:
    """Handler for album art storage."""

    @staticmethod
    def save_album_art_if_present(doc_id: str, doc_metadata: Dict[str, Any]) -> Optional[str]:
        """
        Save album art if present in metadata.

        Args:
            doc_id: Document ID
            doc_metadata: Document metadata (modified in-place to add album_art_path)

        Returns:
            Path to saved album art, or None if not saved
        """
        # Only process audio files
        if "audio_duration_seconds" not in doc_metadata:
            return None

        try:
            from src.processing.audio_metadata import AudioMetadata, save_album_art

            # Check if album art exists
            has_album_art = "_album_art_data" in doc_metadata and "_album_art_mime" in doc_metadata

            # Create temporary AudioMetadata
            temp_metadata = AudioMetadata(
                has_album_art=has_album_art,
                album_art_data=doc_metadata.get("_album_art_data"),
                album_art_mime=doc_metadata.get("_album_art_mime"),
                album_art_description=doc_metadata.get("album_art_description"),
            )

            # Always save (will use placeholder if no album art)
            album_art_saved_path = save_album_art(
                doc_id,
                temp_metadata,
                use_placeholder=True,  # Use placeholder for audio files without album art
            )

            if album_art_saved_path:
                logger.info(f"Saved album art to: {album_art_saved_path}")
                # Add path to metadata
                doc_metadata["album_art_path"] = album_art_saved_path
                return album_art_saved_path

        except Exception as e:
            logger.error(f"Failed to save album art for {doc_id}: {e}")

        return None
