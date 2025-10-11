# Integration Contract: Image Configuration

**Provider:** infra-agent
**Consumers:** image-agent, parser-agent, api-agent
**Status:** Wave 1
**File:** `src/config/image_config.py`

---

## Contract Specification

### Module Exports

```python
"""
Image storage configuration.

This module provides configuration constants for page image and thumbnail storage.
All paths and settings for image persistence are centralized here.
"""

from pathlib import Path
import os

# Base directory for page images
# Docker: /page_images (mapped to host: data/page_images/)
# Native: data/page_images/
PAGE_IMAGE_DIR = Path(os.getenv("PAGE_IMAGE_DIR", "/page_images"))

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
```

### Configuration Validation

The module must validate on import:

```python
def validate_config() -> None:
    """Validate configuration on module import."""
    if not PAGE_IMAGE_DIR.exists():
        # Try to create it
        try:
            PAGE_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise ConfigurationError(
                f"PAGE_IMAGE_DIR does not exist and cannot be created: {PAGE_IMAGE_DIR}"
            )

    if not PAGE_IMAGE_DIR.is_dir():
        raise ConfigurationError(
            f"PAGE_IMAGE_DIR is not a directory: {PAGE_IMAGE_DIR}"
        )

    # Check write permissions
    test_file = PAGE_IMAGE_DIR / ".write_test"
    try:
        test_file.touch()
        test_file.unlink()
    except PermissionError:
        raise ConfigurationError(
            f"No write permission to PAGE_IMAGE_DIR: {PAGE_IMAGE_DIR}"
        )

# Run validation on import
validate_config()
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PAGE_IMAGE_DIR` | `/page_images` (Docker) or `data/page_images` (native) | Base directory for image storage |

### Error Handling

**Exception Type:** `ConfigurationError` (new exception class)

**Failure Modes:**
- Directory doesn't exist and can't be created → Raise `ConfigurationError`
- No write permission → Raise `ConfigurationError`
- Invalid path → Raise `ConfigurationError`

### Usage Example

```python
from src.config.image_config import (
    PAGE_IMAGE_DIR,
    THUMBNAIL_SIZE,
    THUMBNAIL_QUALITY,
    IMAGE_FORMAT,
    THUMBNAIL_FORMAT
)

# Create document directory
doc_dir = PAGE_IMAGE_DIR / doc_id
doc_dir.mkdir(exist_ok=True)

# Save image
image_path = doc_dir / f"page{page_num:03d}.{IMAGE_FORMAT.lower()}"
image.save(image_path, format=IMAGE_FORMAT)
```

---

## Consumer Requirements

### image-agent
- **MUST** import all constants
- **MUST** use `PAGE_IMAGE_DIR` for all file operations
- **MUST** use `THUMBNAIL_SIZE` for thumbnail generation
- **MUST** use `IMAGE_FORMAT` and `THUMBNAIL_FORMAT` for file formats

### parser-agent
- **MUST** import `PAGE_IMAGE_DIR` for path construction
- **SHOULD** import format constants if generating paths

### api-agent
- **MUST** import `PAGE_IMAGE_DIR` for serving images
- **MUST** use `ALLOWED_IMAGE_EXTENSIONS` for security validation

---

## Testing Requirements

### Unit Tests (by infra-agent)

```python
def test_page_image_dir_exists():
    """Test that PAGE_IMAGE_DIR exists and is writable."""
    assert PAGE_IMAGE_DIR.exists()
    assert PAGE_IMAGE_DIR.is_dir()

    # Test write permission
    test_file = PAGE_IMAGE_DIR / ".write_test"
    test_file.touch()
    assert test_file.exists()
    test_file.unlink()

def test_config_constants():
    """Test that all required constants are defined."""
    assert THUMBNAIL_SIZE == (300, 400)
    assert THUMBNAIL_QUALITY == 85
    assert IMAGE_FORMAT == "PNG"
    assert THUMBNAIL_FORMAT == "JPEG"

def test_config_validation_catches_invalid_dir(monkeypatch):
    """Test that validation catches invalid directories."""
    monkeypatch.setenv("PAGE_IMAGE_DIR", "/nonexistent/path")
    with pytest.raises(ConfigurationError):
        importlib.reload(image_config)
```

### Integration Tests (by consumers)

```python
def test_image_config_import():
    """Test that image_config can be imported without errors."""
    from src.config.image_config import PAGE_IMAGE_DIR
    assert PAGE_IMAGE_DIR is not None
```

---

## Performance Requirements

- **Import time:** <50ms
- **Validation time:** <100ms
- **No blocking I/O** during normal import (except validation)

---

## Security Requirements

- **Path traversal prevention:** All paths must be validated
- **Permission checking:** Validate write permissions on startup
- **No secrets:** No sensitive information in config constants

---

## Backward Compatibility

- **New module:** No backward compatibility concerns
- **Graceful degradation:** If directory cannot be created, raise clear error (don't fail silently)

---

## Acceptance Criteria

- [x] Module creates `PAGE_IMAGE_DIR` if it doesn't exist
- [x] Module validates write permissions on import
- [x] All constants exported and documented
- [x] Unit tests achieve 100% coverage
- [x] Import succeeds in Docker and native environments
- [x] Clear error messages for configuration failures

---

**Contract Version:** 1.0
**Last Updated:** 2025-10-11
**Status:** ✅ Approved
