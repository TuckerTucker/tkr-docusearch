"""
Markdown file storage utilities.

This module provides functions to manage extracted markdown files for
documents processed by the system.

Provider: storage-agent
Consumers: worker-webhook
"""

import logging
import re

from tkr_docusearch.utils.paths import PROJECT_ROOT

logger = logging.getLogger(__name__)

# Markdown files are stored in data/markdown/
MARKDOWN_DIR = PROJECT_ROOT / "data" / "markdown"

# Validation pattern for doc_id
DOC_ID_PATTERN = re.compile(r"^[a-zA-Z0-9\-]{8,64}$")


# ============================================================================
# Exception Classes
# ============================================================================


class MarkdownStorageError(Exception):
    """Base exception for markdown storage operations."""


# ============================================================================
# Core Functions
# ============================================================================


def delete_document_markdown(doc_id: str) -> bool:
    """
    Delete markdown file for a document.

    Args:
        doc_id: Document identifier

    Returns:
        True if file was deleted, False if file didn't exist

    Raises:
        ValueError: If doc_id format is invalid
        MarkdownStorageError: If deletion fails

    Example:
        >>> deleted = delete_document_markdown('abc123')
        >>> print(f"Markdown {'deleted' if deleted else 'not found'}")
    """
    # Validate input
    if not DOC_ID_PATTERN.match(doc_id):
        raise ValueError(f"Invalid doc_id format: {doc_id}")

    markdown_path = MARKDOWN_DIR / f"{doc_id}.md"

    # Check if file exists
    if not markdown_path.exists():
        logger.debug(f"Markdown file does not exist: {markdown_path}")
        return False

    if not markdown_path.is_file():
        logger.warning(f"Path is not a file: {markdown_path}")
        return False

    # Delete file
    try:
        markdown_path.unlink()
        logger.info(f"Deleted markdown file: {markdown_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to delete markdown file {markdown_path}: {e}", exc_info=True)
        raise MarkdownStorageError(f"Failed to delete markdown for {doc_id}: {e}") from e


def markdown_exists(doc_id: str) -> bool:
    """
    Check if markdown file exists for a document.

    Args:
        doc_id: Document identifier

    Returns:
        True if markdown file exists, False otherwise

    Example:
        >>> if markdown_exists('abc123'):
        ...     print("Markdown exists")
    """
    try:
        if not DOC_ID_PATTERN.match(doc_id):
            return False

        markdown_path = MARKDOWN_DIR / f"{doc_id}.md"
        return markdown_path.exists() and markdown_path.is_file()
    except Exception as e:
        logger.debug(f"Error checking markdown existence: {e}")
        return False


def get_markdown_path(doc_id: str) -> str:
    """
    Get path to markdown file.

    Args:
        doc_id: Document identifier

    Returns:
        Absolute path to markdown file as string

    Raises:
        ValueError: If doc_id format is invalid

    Example:
        >>> path = get_markdown_path('abc123')
        >>> print(path)
        '/data/markdown/abc123.md'
    """
    # Validate input
    if not DOC_ID_PATTERN.match(doc_id):
        raise ValueError(f"Invalid doc_id format: {doc_id}")

    return str(MARKDOWN_DIR / f"{doc_id}.md")


def cleanup_orphaned_markdown(max_age_days: int = 7) -> int:
    """
    Clean up old markdown files that may be orphaned.

    This is a maintenance utility to remove markdown files older than
    a specified age. Should be run periodically.

    Args:
        max_age_days: Delete files older than this many days

    Returns:
        Number of files deleted

    Example:
        >>> count = cleanup_orphaned_markdown(max_age_days=30)
        >>> print(f"Cleaned up {count} old markdown files")
    """
    if not MARKDOWN_DIR.exists():
        logger.debug(f"Markdown directory does not exist: {MARKDOWN_DIR}")
        return 0

    import time

    deleted_count = 0
    cutoff_time = time.time() - (max_age_days * 86400)  # 86400 seconds per day

    try:
        for markdown_file in MARKDOWN_DIR.glob("*.md"):
            if markdown_file.is_file():
                try:
                    # Check file age
                    file_mtime = markdown_file.stat().st_mtime
                    if file_mtime < cutoff_time:
                        markdown_file.unlink()
                        deleted_count += 1
                        logger.debug(f"Deleted old markdown file: {markdown_file}")
                except Exception as e:
                    logger.error(f"Failed to delete old markdown file {markdown_file}: {e}")

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old markdown files (>{max_age_days} days)")

    except Exception as e:
        logger.error(f"Error during markdown cleanup: {e}", exc_info=True)

    return deleted_count
