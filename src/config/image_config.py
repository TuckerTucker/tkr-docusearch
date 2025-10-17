"""
Image storage configuration.

This module provides configuration constants for page image and thumbnail storage.
All paths and settings for image persistence are centralized here.

Provider: infra-agent
Consumers: image-agent, parser-agent, api-agent
Contract: integration-contracts/01-image-config.contract.md
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when image storage configuration is invalid."""


# Base directory for page images
# Docker: /page_images (mapped to host: data/page_images/)
# Native: data/page_images/
_DEFAULT_DIR = "/page_images" if os.path.exists("/page_images") else "data/page_images"
PAGE_IMAGE_DIR = Path(os.getenv("PAGE_IMAGE_DIR", _DEFAULT_DIR))

# Thumbnail dimensions (width, height) in pixels
THUMBNAIL_SIZE = (300, 400)

# JPEG quality for thumbnails (1-100, higher = better quality, larger file)
THUMBNAIL_QUALITY = 85

# Image format for full-resolution page images
IMAGE_FORMAT = "PNG"

# Image format for thumbnails
THUMBNAIL_FORMAT = "JPEG"

# Maximum file size for images (in MB) before warning
MAX_IMAGE_SIZE_MB = 50

# Image file extensions allowed
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def validate_config() -> None:
    """
    Validate configuration on module import.

    Raises:
        ConfigurationError: If configuration is invalid
    """
    global PAGE_IMAGE_DIR

    # Ensure PAGE_IMAGE_DIR is a Path object
    if not isinstance(PAGE_IMAGE_DIR, Path):
        PAGE_IMAGE_DIR = Path(PAGE_IMAGE_DIR)

    # Try to create directory if it doesn't exist
    if not PAGE_IMAGE_DIR.exists():
        try:
            PAGE_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created PAGE_IMAGE_DIR: {PAGE_IMAGE_DIR}")
        except PermissionError as e:
            raise ConfigurationError(
                f"PAGE_IMAGE_DIR does not exist and cannot be created: {PAGE_IMAGE_DIR}"
            ) from e
        except Exception as e:
            raise ConfigurationError(
                f"Failed to create PAGE_IMAGE_DIR: {PAGE_IMAGE_DIR}: {e}"
            ) from e

    # Verify it's a directory
    if not PAGE_IMAGE_DIR.is_dir():
        raise ConfigurationError(f"PAGE_IMAGE_DIR is not a directory: {PAGE_IMAGE_DIR}")

    # Check write permissions
    test_file = PAGE_IMAGE_DIR / ".write_test"
    try:
        test_file.touch()
        test_file.unlink()
        logger.debug(f"PAGE_IMAGE_DIR write permission verified: {PAGE_IMAGE_DIR}")
    except PermissionError as e:
        raise ConfigurationError(f"No write permission to PAGE_IMAGE_DIR: {PAGE_IMAGE_DIR}") from e
    except Exception as e:
        logger.warning(f"Could not verify write permissions: {e}")


# Run validation on import
try:
    validate_config()
    logger.info(f"Image config validated: PAGE_IMAGE_DIR={PAGE_IMAGE_DIR}")
except ConfigurationError as e:
    logger.error(f"Image configuration error: {e}")
    raise
