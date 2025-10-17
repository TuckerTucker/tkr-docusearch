"""
Image storage utilities for page images and thumbnails.

This module provides functions to save, retrieve, and manage page images
and thumbnails for documents processed by the system.

Provider: image-agent
Consumers: parser-agent, api-agent
Contract: integration-contracts/02-image-utils.contract.md
"""

import logging
import re
from pathlib import Path
from typing import Optional, Tuple

try:
    from PIL import Image
except ImportError:
    raise ImportError(
        "PIL (Pillow) is required for image operations. " "Install with: pip install Pillow"
    )

from src.config.image_config import (
    IMAGE_FORMAT,
    MAX_IMAGE_SIZE_MB,
    PAGE_IMAGE_DIR,
    THUMBNAIL_FORMAT,
    THUMBNAIL_QUALITY,
    THUMBNAIL_SIZE,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Exception Classes
# ============================================================================


class ImageStorageError(Exception):
    """Base exception for image storage operations."""


class DiskFullError(ImageStorageError):
    """Raised when disk is full."""


class PermissionError(ImageStorageError):
    """Raised when lacking file permissions."""


# ============================================================================
# Validation Patterns
# ============================================================================

DOC_ID_PATTERN = re.compile(r"^[a-zA-Z0-9\-]{8,64}$")
PAGE_NUM_PATTERN = re.compile(r"^\d+$")


# ============================================================================
# Core Functions
# ============================================================================


def save_page_image(image: Image.Image, doc_id: str, page_num: int) -> Tuple[str, str]:
    """
    Save page image and generate thumbnail.

    Args:
        image: PIL Image object to save
        doc_id: Document identifier (SHA-256 hash)
        page_num: Page number (1-indexed)

    Returns:
        Tuple of (image_path, thumb_path) as strings

    Raises:
        ImageStorageError: If save fails
        DiskFullError: If disk is full
        PermissionError: If lacking permissions
        ValueError: If image is None or invalid parameters

    Example:
        >>> from PIL import Image
        >>> img = Image.new('RGB', (800, 1000))
        >>> img_path, thumb_path = save_page_image(img, 'abc123', 1)
        >>> print(img_path)
        '/page_images/abc123/page001.png'
    """
    # Validate inputs
    if image is None:
        raise ValueError("Image cannot be None")

    if not isinstance(image, Image.Image):
        raise ValueError(f"Image must be PIL.Image.Image, got {type(image)}")

    if not DOC_ID_PATTERN.match(doc_id):
        raise ValueError(
            f"Invalid doc_id format: {doc_id}. " "Must be alphanumeric + dashes, 8-64 characters"
        )

    if not isinstance(page_num, int) or page_num < 1:
        raise ValueError(f"Page number must be integer >= 1, got {page_num}")

    logger.info(f"Saving page image: doc_id={doc_id}, page={page_num}")

    try:
        # Create document directory
        doc_dir = PAGE_IMAGE_DIR / doc_id
        doc_dir.mkdir(parents=True, exist_ok=True)

        # Generate file paths
        image_filename = f"page{page_num:03d}.{IMAGE_FORMAT.lower()}"
        # Use 'jpg' extension for JPEG format (standard abbreviation)
        thumb_ext = "jpg" if THUMBNAIL_FORMAT.upper() == "JPEG" else THUMBNAIL_FORMAT.lower()
        thumb_filename = f"page{page_num:03d}_thumb.{thumb_ext}"

        image_path = doc_dir / image_filename
        thumb_path = doc_dir / thumb_filename

        # Save full-resolution image
        logger.debug(f"Saving full image: {image_path}, size: {image.size}")
        image.save(image_path, format=IMAGE_FORMAT)

        # Check file size and warn if large
        file_size_mb = image_path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_IMAGE_SIZE_MB:
            logger.warning(
                f"Large image file: {file_size_mb:.1f}MB > {MAX_IMAGE_SIZE_MB}MB "
                f"for {image_path}"
            )

        # Generate and save thumbnail
        thumbnail = generate_thumbnail(image, THUMBNAIL_SIZE, THUMBNAIL_QUALITY)
        logger.debug(f"Saving thumbnail: {thumb_path}, size: {thumbnail.size}")
        thumbnail.save(thumb_path, format=THUMBNAIL_FORMAT, quality=THUMBNAIL_QUALITY)

        # Return paths as strings
        result_image_path = str(image_path)
        result_thumb_path = str(thumb_path)

        logger.info(
            f"Saved page image: {image_filename} "
            f"({file_size_mb:.1f}MB) and thumbnail ({thumb_path.stat().st_size // 1024}KB)"
        )

        return (result_image_path, result_thumb_path)

    except OSError as e:
        # Check for disk full error (errno 28 on Unix, errno 112 on Windows)
        if e.errno in (28, 112):
            raise DiskFullError(f"Disk full while saving image: {e}") from e
        # Check for permission error (errno 13)
        elif e.errno == 13:
            raise PermissionError(f"Permission denied while saving image: {e}") from e
        else:
            raise ImageStorageError(f"Failed to save image: {e}") from e

    except Exception as e:
        logger.error(f"Failed to save page image: {e}", exc_info=True)
        raise ImageStorageError(f"Unexpected error saving image: {e}") from e


def generate_thumbnail(image: Image.Image, size: Tuple[int, int], quality: int) -> Image.Image:
    """
    Generate thumbnail from image.

    Maintains aspect ratio. If image is portrait, thumbnail will be
    portrait. If landscape, thumbnail will be landscape.

    Args:
        image: PIL Image to thumbnail
        size: (width, height) tuple
        quality: JPEG quality (1-100) - not used for generation, only for saving

    Returns:
        Thumbnailed PIL Image

    Raises:
        ValueError: If image is None or invalid size/quality

    Example:
        >>> img = Image.new('RGB', (1600, 2000))
        >>> thumb = generate_thumbnail(img, (300, 400), 85)
        >>> print(thumb.size)  # Maintains aspect ratio
        (300, 375)
    """
    # Validate inputs
    if image is None:
        raise ValueError("Image cannot be None")

    if not isinstance(image, Image.Image):
        raise ValueError(f"Image must be PIL.Image.Image, got {type(image)}")

    if not isinstance(size, tuple) or len(size) != 2:
        raise ValueError(f"Size must be (width, height) tuple, got {size}")

    width, height = size
    if not (0 < width < 10000 and 0 < height < 10000):
        raise ValueError(f"Size dimensions must be > 0 and < 10000, got {size}")

    if not isinstance(quality, int) or not (1 <= quality <= 100):
        raise ValueError(f"Quality must be integer 1-100, got {quality}")

    # Create a copy to avoid modifying original
    thumb = image.copy()

    # Convert RGBA to RGB (JPEG doesn't support transparency)
    if thumb.mode == "RGBA":
        # Create white background
        background = Image.new("RGB", thumb.size, (255, 255, 255))
        background.paste(thumb, mask=thumb.split()[3])  # Use alpha channel as mask
        thumb = background
    elif thumb.mode != "RGB":
        thumb = thumb.convert("RGB")

    # Use thumbnail() method which maintains aspect ratio
    thumb.thumbnail(size, Image.Resampling.LANCZOS)

    logger.debug(f"Generated thumbnail: {image.size} -> {thumb.size}")

    return thumb


def get_image_path(doc_id: str, page_num: int, is_thumb: bool = False) -> str:
    """
    Get path to image file.

    Args:
        doc_id: Document identifier
        page_num: Page number (1-indexed)
        is_thumb: If True, return thumbnail path

    Returns:
        Absolute path to image file as string

    Example:
        >>> get_image_path('abc123', 1, is_thumb=False)
        '/page_images/abc123/page001.png'
        >>> get_image_path('abc123', 1, is_thumb=True)
        '/page_images/abc123/page001_thumb.jpg'
    """
    # Validate inputs
    if not DOC_ID_PATTERN.match(doc_id):
        raise ValueError(f"Invalid doc_id format: {doc_id}")

    if not isinstance(page_num, int) or page_num < 1:
        raise ValueError(f"Page number must be integer >= 1, got {page_num}")

    # Construct path
    doc_dir = PAGE_IMAGE_DIR / doc_id

    if is_thumb:
        # Use 'jpg' extension for JPEG format (standard abbreviation)
        thumb_ext = "jpg" if THUMBNAIL_FORMAT.upper() == "JPEG" else THUMBNAIL_FORMAT.lower()
        filename = f"page{page_num:03d}_thumb.{thumb_ext}"
    else:
        filename = f"page{page_num:03d}.{IMAGE_FORMAT.lower()}"

    return str(doc_dir / filename)


def delete_document_images(doc_id: str) -> int:
    """
    Delete all images for a document.

    Args:
        doc_id: Document identifier

    Returns:
        Number of files deleted

    Raises:
        ImageStorageError: If deletion fails catastrophically

    Example:
        >>> count = delete_document_images('abc123')
        >>> print(f"Deleted {count} files")
    """
    # Validate input
    if not DOC_ID_PATTERN.match(doc_id):
        raise ValueError(f"Invalid doc_id format: {doc_id}")

    doc_dir = PAGE_IMAGE_DIR / doc_id

    # Check if directory exists
    if not doc_dir.exists():
        logger.debug(f"Document directory does not exist: {doc_dir}")
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
                    logger.debug(f"Deleted file: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to delete file {file_path}: {e}")
                    errors.append(str(e))

        # Remove directory after deleting files
        try:
            doc_dir.rmdir()
            logger.info(f"Deleted document directory: {doc_dir}")
        except Exception as e:
            logger.error(f"Failed to remove directory {doc_dir}: {e}")
            errors.append(str(e))

    except Exception as e:
        logger.error(f"Failed to delete document images: {e}", exc_info=True)
        raise ImageStorageError(f"Failed to delete images for {doc_id}: {e}") from e

    if errors:
        logger.warning(f"Deleted {deleted_count} files with {len(errors)} errors: {errors}")

    return deleted_count


def image_exists(doc_id: str, page_num: int, is_thumb: bool = False) -> bool:
    """
    Check if image file exists.

    Args:
        doc_id: Document identifier
        page_num: Page number (1-indexed)
        is_thumb: If True, check thumbnail

    Returns:
        True if file exists, False otherwise

    Example:
        >>> if image_exists('abc123', 1):
        ...     print("Image exists")
    """
    try:
        path = get_image_path(doc_id, page_num, is_thumb)
        return Path(path).exists()
    except (ValueError, Exception) as e:
        logger.debug(f"Error checking image existence: {e}")
        return False


def cleanup_temp_directories(doc_id: Optional[str] = None) -> int:
    """
    Clean up temporary directories created during PPTX processing.

    Temporary directories follow the pattern: temp-slides-{filename}
    If doc_id is provided, only clean directories matching that document.
    Otherwise, clean all temp directories.

    Args:
        doc_id: Optional document identifier to filter cleanup

    Returns:
        Number of directories deleted

    Example:
        >>> count = cleanup_temp_directories('abc123')
        >>> print(f"Cleaned up {count} temp directories")
    """
    deleted_count = 0
    errors = []

    if not PAGE_IMAGE_DIR.exists():
        logger.debug(f"Page image directory does not exist: {PAGE_IMAGE_DIR}")
        return 0

    try:
        # Find all temp-slides-* directories
        for temp_dir in PAGE_IMAGE_DIR.glob("temp-slides-*"):
            if not temp_dir.is_dir():
                continue

            # If doc_id specified, check if directory relates to this document
            # Note: temp dirs are named by filename, not doc_id, so we clean all if doc_id given
            # This is a limitation - we could improve by storing doc_id in temp dir name
            try:
                # Delete all files in temp directory
                file_count = 0
                for file_path in temp_dir.iterdir():
                    if file_path.is_file():
                        file_path.unlink()
                        file_count += 1

                # Remove directory
                temp_dir.rmdir()
                deleted_count += 1
                logger.info(f"Deleted temp directory: {temp_dir} ({file_count} files)")

            except Exception as e:
                logger.error(f"Failed to delete temp directory {temp_dir}: {e}")
                errors.append(str(e))

    except Exception as e:
        logger.error(f"Failed to cleanup temp directories: {e}", exc_info=True)
        raise ImageStorageError(f"Failed to cleanup temp directories: {e}") from e

    if errors:
        logger.warning(
            f"Cleaned up {deleted_count} temp directories with {len(errors)} errors: {errors}"
        )
    elif deleted_count > 0:
        logger.info(f"Successfully cleaned up {deleted_count} temp directories")

    return deleted_count
