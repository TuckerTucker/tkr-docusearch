"""
Cover art storage utilities for audio documents.

This module provides functions to manage cover art images for audio files
(MP3, WAV) processed by the system.

Provider: processing-agent
Consumers: worker-webhook
"""

from pathlib import Path
from typing import Optional
import logging
import re

from src.config.image_config import PAGE_IMAGE_DIR

logger = logging.getLogger(__name__)

# Cover art is stored in a sibling directory to page_images
COVER_ART_DIR = PAGE_IMAGE_DIR.parent / "images"

# Validation pattern for doc_id
DOC_ID_PATTERN = re.compile(r'^[a-zA-Z0-9\-]{8,64}$')


# ============================================================================
# Exception Classes
# ============================================================================

class CoverArtError(Exception):
    """Base exception for cover art operations."""
    pass


# ============================================================================
# Core Functions
# ============================================================================

def delete_document_cover_art(doc_id: str) -> int:
    """
    Delete all cover art images for a document.

    Args:
        doc_id: Document identifier

    Returns:
        Number of files deleted

    Raises:
        ValueError: If doc_id format is invalid
        CoverArtError: If deletion fails catastrophically

    Example:
        >>> count = delete_document_cover_art('abc123')
        >>> print(f"Deleted {count} cover art files")
    """
    # Validate input
    if not DOC_ID_PATTERN.match(doc_id):
        raise ValueError(f"Invalid doc_id format: {doc_id}")

    doc_dir = COVER_ART_DIR / doc_id

    # Check if directory exists
    if not doc_dir.exists():
        logger.debug(f"Cover art directory does not exist: {doc_dir}")
        return 0

    if not doc_dir.is_dir():
        logger.warning(f"Path is not a directory: {doc_dir}")
        return 0

    # Delete all files in directory
    deleted_count = 0
    errors = []

    try:
        for file_path in doc_dir.iterdir():
            if file_path.is_file():
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted cover art file: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to delete cover art file {file_path}: {e}")
                    errors.append(str(e))

        # Remove directory after deleting files
        try:
            doc_dir.rmdir()
            logger.info(f"Deleted cover art directory: {doc_dir}")
        except Exception as e:
            logger.error(f"Failed to remove cover art directory {doc_dir}: {e}")
            errors.append(str(e))

    except Exception as e:
        logger.error(f"Failed to delete cover art: {e}", exc_info=True)
        raise CoverArtError(f"Failed to delete cover art for {doc_id}: {e}") from e

    if errors:
        logger.warning(
            f"Deleted {deleted_count} cover art files with {len(errors)} errors: {errors}"
        )
    elif deleted_count > 0:
        logger.info(f"Successfully deleted {deleted_count} cover art files for {doc_id}")

    return deleted_count


def cover_art_exists(doc_id: str) -> bool:
    """
    Check if cover art directory exists for a document.

    Args:
        doc_id: Document identifier

    Returns:
        True if cover art directory exists, False otherwise

    Example:
        >>> if cover_art_exists('abc123'):
        ...     print("Cover art exists")
    """
    try:
        if not DOC_ID_PATTERN.match(doc_id):
            return False

        doc_dir = COVER_ART_DIR / doc_id
        return doc_dir.exists() and doc_dir.is_dir()
    except Exception as e:
        logger.debug(f"Error checking cover art existence: {e}")
        return False


def get_cover_art_path(doc_id: str, filename: str = "cover.jpg") -> Optional[str]:
    """
    Get path to cover art file.

    Args:
        doc_id: Document identifier
        filename: Cover art filename (default: cover.jpg)

    Returns:
        Absolute path to cover art file as string, or None if not found

    Example:
        >>> path = get_cover_art_path('abc123')
        >>> print(path)
        '/data/images/abc123/cover.jpg'
    """
    # Validate input
    if not DOC_ID_PATTERN.match(doc_id):
        raise ValueError(f"Invalid doc_id format: {doc_id}")

    cover_path = COVER_ART_DIR / doc_id / filename

    if cover_path.exists() and cover_path.is_file():
        return str(cover_path)

    return None
