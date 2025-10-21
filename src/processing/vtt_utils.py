"""
VTT file storage utilities.

This module provides functions to manage VTT (WebVTT) caption files for
audio documents processed by the system.

Provider: processing-agent
Consumers: worker-webhook, documents-api
"""

import logging
import re

from src.utils.paths import PROJECT_ROOT

logger = logging.getLogger(__name__)

# VTT files are stored in data/vtt/
VTT_DIR = PROJECT_ROOT / "data" / "vtt"

# Validation pattern for doc_id
DOC_ID_PATTERN = re.compile(r"^[a-zA-Z0-9\-]{8,64}$")


# ============================================================================
# Exception Classes
# ============================================================================


class VTTStorageError(Exception):
    """Base exception for VTT storage operations."""


# ============================================================================
# Core Functions
# ============================================================================


def delete_document_vtt(doc_id: str) -> bool:
    """
    Delete VTT caption file for a document.

    Args:
        doc_id: Document identifier

    Returns:
        True if file was deleted, False if file didn't exist

    Raises:
        ValueError: If doc_id format is invalid
        VTTStorageError: If deletion fails

    Example:
        >>> deleted = delete_document_vtt('abc123')
        >>> print(f"VTT {'deleted' if deleted else 'not found'}")
    """
    # Validate input
    if not DOC_ID_PATTERN.match(doc_id):
        raise ValueError(f"Invalid doc_id format: {doc_id}")

    vtt_path = VTT_DIR / f"{doc_id}.vtt"

    # Check if file exists
    if not vtt_path.exists():
        logger.debug(f"VTT file does not exist: {vtt_path}")
        return False

    if not vtt_path.is_file():
        logger.warning(f"Path is not a file: {vtt_path}")
        return False

    # Delete file
    try:
        vtt_path.unlink()
        logger.info(f"Deleted VTT file: {vtt_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to delete VTT file {vtt_path}: {e}", exc_info=True)
        raise VTTStorageError(f"Failed to delete VTT for {doc_id}: {e}") from e


def vtt_exists(doc_id: str) -> bool:
    """
    Check if VTT caption file exists for a document.

    Args:
        doc_id: Document identifier

    Returns:
        True if VTT file exists, False otherwise

    Example:
        >>> if vtt_exists('abc123'):
        ...     print("VTT captions exist")
    """
    try:
        if not DOC_ID_PATTERN.match(doc_id):
            return False

        vtt_path = VTT_DIR / f"{doc_id}.vtt"
        return vtt_path.exists() and vtt_path.is_file()

    except Exception:
        return False
