# File Validator API Contract

**Version:** 1.0
**Agent:** validation-core-agent
**Status:** Complete
**Location:** `src/processing/file_validator.py`

## Overview

The File Validator module provides shared validation functions for file type and size checks, eliminating duplicate validation code across workers. This module is used by both the worker webhook and any future upload handlers.

## API Specification

### Constants

```python
DEFAULT_FORMATS = "pdf,docx,pptx,xlsx,html,xhtml,md,asciidoc,csv,mp3,wav,vtt,png,jpg,jpeg,tiff,bmp,webp"
```

Default supported file formats (comma-separated, no dots).

---

### `get_supported_extensions() -> Set[str]`

Load supported file extensions from environment.

**Returns:**
- `Set[str]`: Set of extensions with dot prefix (e.g., `{'.pdf', '.png'}`)

**Environment Variables:**
- `SUPPORTED_FORMATS`: Comma-separated list of extensions (without dots)
  - Default: `DEFAULT_FORMATS` constant
  - Example: `"pdf,png,txt"`

**Behavior:**
- Reads from `SUPPORTED_FORMATS` environment variable
- Falls back to `DEFAULT_FORMATS` if not set
- Normalizes to lowercase
- Strips whitespace
- Adds dot prefix to each extension

**Example:**
```python
from file_validator import get_supported_extensions

# Using defaults
exts = get_supported_extensions()
assert '.pdf' in exts
assert '.png' in exts

# Using custom environment
import os
os.environ['SUPPORTED_FORMATS'] = 'pdf,txt,csv'
exts = get_supported_extensions()
assert exts == {'.pdf', '.txt', '.csv'}
```

---

### `validate_file_type(file_path: str) -> Tuple[bool, str]`

Validate file extension against supported formats.

**Parameters:**
- `file_path` (str): Path to file (absolute or relative)

**Returns:**
- `Tuple[bool, str]`:
  - `(True, "")` if file type is supported
  - `(False, "error message")` if file type is not supported

**Validation Rules:**
- Extension must be present (file must have a dot and extension)
- Extension must be in supported extensions set
- Comparison is case-insensitive (`.PDF` == `.pdf`)

**Error Messages:**
- No extension: `"File has no extension: {file_path}"`
- Unsupported: `"Unsupported file type: {extension}. Supported: {list}"`

**Example:**
```python
from file_validator import validate_file_type

# Valid file
valid, msg = validate_file_type("document.pdf")
assert valid is True
assert msg == ""

# Invalid extension
valid, msg = validate_file_type("malware.exe")
assert valid is False
assert "Unsupported file type" in msg

# No extension
valid, msg = validate_file_type("README")
assert valid is False
assert "no extension" in msg.lower()

# Case-insensitive
valid, msg = validate_file_type("DOCUMENT.PDF")
assert valid is True
```

---

### `validate_file_size(size_bytes: int, max_mb: int = 100) -> Tuple[bool, str]`

Validate file size against limit.

**Parameters:**
- `size_bytes` (int): File size in bytes
- `max_mb` (int): Maximum size in MB (default: 100)

**Returns:**
- `Tuple[bool, str]`:
  - `(True, "")` if file size is within limit
  - `(False, "error message")` if file size exceeds limit

**Validation Rules:**
- Size must be non-negative
- Size must not exceed `max_mb * 1024 * 1024` bytes

**Error Messages:**
- Negative size: `"Invalid file size: {size_bytes} bytes"`
- Too large: `"File size {size_mb:.2f} MB exceeds maximum {max_mb} MB"`

**Example:**
```python
from file_validator import validate_file_size

# Valid small file (1 MB)
valid, msg = validate_file_size(1 * 1024 * 1024)
assert valid is True

# Valid at limit (100 MB)
valid, msg = validate_file_size(100 * 1024 * 1024, max_mb=100)
assert valid is True

# Too large (150 MB)
valid, msg = validate_file_size(150 * 1024 * 1024, max_mb=100)
assert valid is False
assert "exceeds maximum" in msg
assert "150" in msg

# Custom limit (20 MB)
valid, msg = validate_file_size(30 * 1024 * 1024, max_mb=20)
assert valid is False
assert "20 MB" in msg
```

---

### `validate_file(file_path: str, size_bytes: int, max_mb: int = 100) -> Tuple[bool, str]`

Complete file validation (type + size).

**Parameters:**
- `file_path` (str): Path to file (absolute or relative)
- `size_bytes` (int): File size in bytes
- `max_mb` (int): Maximum size in MB (default: 100)

**Returns:**
- `Tuple[bool, str]`:
  - `(True, "")` if all validations pass
  - `(False, "error message")` if any validation fails

**Validation Order:**
1. File type validation (via `validate_file_type`)
2. File size validation (via `validate_file_size`)

Returns on first failure (short-circuit evaluation).

**Example:**
```python
from file_validator import validate_file

# Valid file (PDF, 10 MB)
valid, msg = validate_file("document.pdf", 10 * 1024 * 1024)
assert valid is True
assert msg == ""

# Invalid type, valid size
valid, msg = validate_file("malware.exe", 1024)
assert valid is False
assert "Unsupported file type" in msg

# Valid type, invalid size
valid, msg = validate_file("document.pdf", 150 * 1024 * 1024, max_mb=100)
assert valid is False
assert "exceeds maximum" in msg

# Both invalid (fails on type first)
valid, msg = validate_file("malware.exe", 150 * 1024 * 1024)
assert valid is False
assert "Unsupported file type" in msg
```

---

## Integration Requirements

### For Worker Webhook (`worker_webhook.py`)

Replace current validation code with:

```python
from file_validator import validate_file

# In webhook handler
file_path = "/path/to/uploaded/file.pdf"
size_bytes = os.path.getsize(file_path)

valid, error_msg = validate_file(file_path, size_bytes, max_mb=100)

if not valid:
    logger.warning(f"Validation failed: {error_msg}")
    return JSONResponse(
        status_code=400,
        content={"status": "error", "message": error_msg}
    )

# Proceed with processing...
```

### For Future Upload Handlers

Any component that needs file validation should:

1. Import validation functions:
   ```python
   from file_validator import validate_file, get_supported_extensions
   ```

2. Use `validate_file()` for complete validation:
   ```python
   valid, error = validate_file(file_path, size_bytes, max_mb=100)
   if not valid:
       # Handle error
   ```

3. Use `get_supported_extensions()` for UI display:
   ```python
   supported = get_supported_extensions()
   # Display supported extensions in UI
   ```

### Environment Configuration

To customize supported formats:

```bash
# In .env or environment
export SUPPORTED_FORMATS="pdf,png,jpg,docx,txt"
```

To customize max file size, pass `max_mb` parameter:

```python
# For 50 MB limit
validate_file(file_path, size_bytes, max_mb=50)
```

---

## Type Hints

All functions use Python type hints:

```python
from typing import Set, Tuple

def get_supported_extensions() -> Set[str]: ...
def validate_file_type(file_path: str) -> Tuple[bool, str]: ...
def validate_file_size(size_bytes: int, max_mb: int = 100) -> Tuple[bool, str]: ...
def validate_file(file_path: str, size_bytes: int, max_mb: int = 100) -> Tuple[bool, str]: ...
```

---

## Dependencies

**Standard Library Only:**
- `os` - Environment variable access
- `pathlib.Path` - Path manipulation
- `typing` - Type hints

**No External Dependencies.**

---

## Testing

Comprehensive test suite in `test_file_validator.py`:

- **Coverage:** >95%
- **Test Classes:**
  - `TestGetSupportedExtensions` - Extension loading
  - `TestValidateFileType` - Type validation
  - `TestValidateFileSize` - Size validation
  - `TestValidateFile` - Combined validation
  - `TestErrorMessages` - Error message quality
  - `TestIntegration` - Realistic scenarios

**Run Tests:**
```bash
cd src/processing
pytest test_file_validator.py -v --cov=file_validator --cov-report=term-missing
```

---

## Error Handling

All validation functions return `(bool, str)` tuples:

- **Success:** `(True, "")`
- **Failure:** `(False, "descriptive error message")`

Functions never raise exceptions for validation failures. All errors are returned as messages.

**Error Message Format:**

- Clear and descriptive
- Include relevant details (file path, size, supported formats)
- Suitable for direct display to users or logging

---

## Performance

All validation operations are O(1) or O(n) where n is small:

- `get_supported_extensions()`: O(n) where n = number of formats (typically <20)
- `validate_file_type()`: O(1) set lookup
- `validate_file_size()`: O(1) arithmetic
- `validate_file()`: O(1) combined

Expected latency: <1ms per validation.

---

## Migration Guide

### Before (worker_webhook.py)

```python
# Inline validation code
extension = file_path.split('.')[-1].lower()
if extension not in SUPPORTED_EXTENSIONS:
    return error_response("Unsupported file type")

if size > MAX_SIZE:
    return error_response("File too large")
```

### After (worker_webhook.py)

```python
from file_validator import validate_file

valid, error = validate_file(file_path, size_bytes, max_mb=100)
if not valid:
    return error_response(error)
```

**Benefits:**
- Single source of truth for validation logic
- Consistent error messages across components
- Environment-based configuration
- Comprehensive test coverage
- Type safety with hints

---

## Version History

- **v1.0** (2025-10-13): Initial release with core validation functions

---

## Support

For issues or questions:
1. Check test suite for usage examples
2. Review this contract document
3. Contact validation-core-agent maintainer
