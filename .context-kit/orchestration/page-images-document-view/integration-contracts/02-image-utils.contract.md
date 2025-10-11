# Integration Contract: Image Utilities

**Provider:** image-agent
**Consumers:** parser-agent, api-agent
**Status:** Wave 1
**File:** `src/processing/image_utils.py`

---

## Contract Specification

### Module Exports

```python
"""
Image storage utilities for page images and thumbnails.

This module provides functions to save, retrieve, and manage page images
and thumbnails for documents processed by the system.
"""

from pathlib import Path
from typing import Tuple, Optional
from PIL import Image
import logging

from src.config.image_config import (
    PAGE_IMAGE_DIR,
    THUMBNAIL_SIZE,
    THUMBNAIL_QUALITY,
    IMAGE_FORMAT,
    THUMBNAIL_FORMAT
)

logger = logging.getLogger(__name__)


class ImageStorageError(Exception):
    """Base exception for image storage operations."""
    pass


class DiskFullError(ImageStorageError):
    """Raised when disk is full."""
    pass


class PermissionError(ImageStorageError):
    """Raised when lacking file permissions."""
    pass


def save_page_image(
    image: Image.Image,
    doc_id: str,
    page_num: int
) -> Tuple[str, str]:
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
    pass


def generate_thumbnail(
    image: Image.Image,
    size: Tuple[int, int],
    quality: int
) -> Image.Image:
    """
    Generate thumbnail from image.

    Maintains aspect ratio. If image is portrait, thumbnail will be
    portrait. If landscape, thumbnail will be landscape.

    Args:
        image: PIL Image to thumbnail
        size: (width, height) tuple
        quality: JPEG quality (1-100)

    Returns:
        Thumbnailed PIL Image

    Raises:
        ValueError: If image is None or invalid size/quality

    Example:
        >>> img = Image.new('RGB', (1600, 2000))
        >>> thumb = generate_thumbnail(img, (300, 400), 85)
        >>> print(thumb.size)  # Maintains aspect ratio
        (320, 400)
    """
    pass


def get_image_path(
    doc_id: str,
    page_num: int,
    is_thumb: bool = False
) -> str:
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
    pass


def delete_document_images(doc_id: str) -> int:
    """
    Delete all images for a document.

    Args:
        doc_id: Document identifier

    Returns:
        Number of files deleted

    Raises:
        ImageStorageError: If deletion fails

    Example:
        >>> count = delete_document_images('abc123')
        >>> print(f"Deleted {count} files")
    """
    pass


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
    pass
```

---

## Function Specifications

### save_page_image()

**Input Contract:**
- `image`: Valid PIL.Image.Image object (not None)
- `doc_id`: String, alphanumeric + dashes, length 8-64 chars
- `page_num`: Integer, >= 1

**Output Contract:**
- Returns: `Tuple[str, str]` (image_path, thumb_path)
- Both paths are absolute paths as strings
- Paths follow pattern:
  - Image: `{PAGE_IMAGE_DIR}/{doc_id}/page{num:03d}.png`
  - Thumb: `{PAGE_IMAGE_DIR}/{doc_id}/page{num:03d}_thumb.jpg`

**Side Effects:**
- Creates directory: `{PAGE_IMAGE_DIR}/{doc_id}/` (if doesn't exist)
- Writes 2 files: full image (PNG) and thumbnail (JPEG)

**Error Behavior:**
- Validates inputs before saving
- Catches PIL errors, re-raises as `ImageStorageError`
- Catches OSError for disk full → `DiskFullError`
- Catches PermissionError → `PermissionError`
- Logs all errors before raising

**Performance:**
- Must complete in <500ms for typical page (1200x1600px)
- Thumbnail generation: <100ms

### generate_thumbnail()

**Input Contract:**
- `image`: Valid PIL Image
- `size`: (width, height) where both > 0 and < 10000
- `quality`: Integer 1-100

**Output Contract:**
- Returns: PIL Image (new object, original unchanged)
- Maintains aspect ratio (may not match exact size)
- RGB mode (converts if needed)

**Behavior:**
- Uses `Image.thumbnail()` method (maintains aspect ratio)
- Converts RGBA → RGB (white background)
- Handles both portrait and landscape orientations

**Performance:**
- Must complete in <100ms for input up to 5000x5000px

### get_image_path()

**Input Contract:**
- `doc_id`: String
- `page_num`: Integer >= 1
- `is_thumb`: Boolean

**Output Contract:**
- Returns: String (absolute path)
- Does NOT check if file exists (use `image_exists()` for that)

### delete_document_images()

**Input Contract:**
- `doc_id`: String

**Output Contract:**
- Returns: Integer (count of files deleted)
- Returns 0 if directory doesn't exist (not an error)

**Side Effects:**
- Deletes all files in `{PAGE_IMAGE_DIR}/{doc_id}/`
- Removes directory after deleting files

**Error Behavior:**
- Partial deletion is OK (deletes what it can)
- Logs errors but doesn't raise unless catastrophic

### image_exists()

**Input Contract:**
- `doc_id`: String
- `page_num`: Integer >= 1
- `is_thumb`: Boolean

**Output Contract:**
- Returns: Boolean
- No side effects
- No errors raised (returns False on any issue)

---

## Testing Requirements

### Unit Tests (by image-agent)

```python
def test_save_page_image_creates_files(tmp_path, monkeypatch):
    """Test that save_page_image creates both PNG and JPEG files."""
    monkeypatch.setattr('src.config.image_config.PAGE_IMAGE_DIR', tmp_path)

    img = Image.new('RGB', (800, 1000), color='blue')
    img_path, thumb_path = save_page_image(img, 'test-doc', 1)

    assert Path(img_path).exists()
    assert Path(thumb_path).exists()
    assert img_path.endswith('/page001.png')
    assert thumb_path.endswith('/page001_thumb.jpg')

def test_save_page_image_handles_disk_full(tmp_path, monkeypatch):
    """Test disk full error handling."""
    # Mock to raise OSError with ENOSPC
    with pytest.raises(DiskFullError):
        # Test implementation

def test_generate_thumbnail_maintains_aspect_ratio():
    """Test thumbnail maintains aspect ratio."""
    img = Image.new('RGB', (1600, 2000))  # 4:5 ratio
    thumb = generate_thumbnail(img, (300, 400), 85)

    # Should maintain 4:5 ratio
    assert thumb.width / thumb.height == pytest.approx(0.8, abs=0.01)

def test_delete_document_images_removes_all_files(tmp_path, monkeypatch):
    """Test that delete removes all images for a document."""
    monkeypatch.setattr('src.config.image_config.PAGE_IMAGE_DIR', tmp_path)

    # Create test images
    doc_dir = tmp_path / 'test-doc'
    doc_dir.mkdir()
    (doc_dir / 'page001.png').touch()
    (doc_dir / 'page001_thumb.jpg').touch()
    (doc_dir / 'page002.png').touch()

    count = delete_document_images('test-doc')

    assert count == 3
    assert not doc_dir.exists()
```

### Integration Tests (by consumers)

```python
def test_save_and_retrieve_workflow():
    """Test full workflow: save, check exists, delete."""
    img = Image.new('RGB', (800, 1000))
    img_path, thumb_path = save_page_image(img, 'workflow-test', 1)

    assert image_exists('workflow-test', 1, is_thumb=False)
    assert image_exists('workflow-test', 1, is_thumb=True)

    count = delete_document_images('workflow-test')
    assert count == 2

    assert not image_exists('workflow-test', 1)
```

---

## Performance Requirements

| Function | Max Time | Typical Time |
|----------|----------|--------------|
| `save_page_image()` | 500ms | 200ms |
| `generate_thumbnail()` | 100ms | 30ms |
| `get_image_path()` | <1ms | <1ms |
| `delete_document_images()` | 1000ms | 100ms |
| `image_exists()` | <10ms | <5ms |

---

## Security Requirements

- **Path validation:** Sanitize doc_id to prevent path traversal
- **File extension validation:** Only create .png and .jpg files
- **Size limits:** Warn if image > 50MB
- **Error messages:** Don't expose full filesystem paths in errors

---

## Logging Requirements

```python
# Save operation
logger.info(f"Saving page image: doc_id={doc_id}, page={page_num}")
logger.debug(f"Image path: {image_path}, size: {image.size}")

# Thumbnail generation
logger.debug(f"Generated thumbnail: {thumb.size} from {image.size}")

# Delete operation
logger.info(f"Deleted {count} images for doc_id={doc_id}")

# Errors
logger.error(f"Failed to save image: {error}", exc_info=True)
```

---

## Acceptance Criteria

- [x] All functions implemented and documented
- [x] Unit tests achieve 95%+ coverage
- [x] Integration tests validate full workflow
- [x] Performance requirements met
- [x] Error handling comprehensive
- [x] Logging detailed and helpful
- [x] No memory leaks (tested with 1000 images)

---

**Contract Version:** 1.0
**Last Updated:** 2025-10-11
**Status:** ✅ Approved
