# File Validator Usage Guide

## Overview

This guide provides practical examples for using the file validation system in DocuSearch. The file validation utilities eliminate duplicate validation code and provide a consistent interface for validating file types and sizes across all components.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Common Patterns](#common-patterns)
3. [FastAPI Integration](#fastapi-integration)
4. [Worker Integration](#worker-integration)
5. [Advanced Usage](#advanced-usage)
6. [Testing](#testing)
7. [Best Practices](#best-practices)

---

## Quick Start

### Basic File Validation

```python
from src.processing.file_validator import validate_file

# Complete validation (type + size)
file_path = "/uploads/document.pdf"
file_size = 5 * 1024 * 1024  # 5 MB

valid, error = validate_file(file_path, file_size)
if valid:
    print("✓ File is valid")
else:
    print(f"✗ Validation failed: {error}")
```

### Using ProcessingConfig

```python
from src.config.processing_config import ProcessingConfig

config = ProcessingConfig()

# Validate using config method (convenience wrapper)
valid, error = config.validate_file("document.pdf", 5 * 1024 * 1024)
if valid:
    print("✓ File is valid")
else:
    print(f"✗ Validation failed: {error}")
```

### Individual Validation Functions

```python
from src.processing.file_validator import validate_file_type, validate_file_size

# Type validation only
valid, error = validate_file_type("document.pdf")
if not valid:
    print(f"Unsupported file type: {error}")

# Size validation only
valid, error = validate_file_size(5 * 1024 * 1024, max_mb=10)
if not valid:
    print(f"File too large: {error}")
```

---

## Common Patterns

### Pattern 1: Pre-Upload Validation

Validate files before accepting them for processing.

```python
from pathlib import Path
from src.processing.file_validator import validate_file

def can_process_file(file_path: str) -> bool:
    """Check if a file can be processed."""
    path = Path(file_path)

    # Check existence
    if not path.exists():
        print(f"File not found: {file_path}")
        return False

    # Get file size
    file_size = path.stat().st_size

    # Validate
    valid, error = validate_file(str(path), file_size)
    if not valid:
        print(f"Cannot process {path.name}: {error}")
        return False

    return True

# Usage
if can_process_file("/uploads/document.pdf"):
    process_document("/uploads/document.pdf")
```

### Pattern 2: Batch Validation

Validate multiple files and report results.

```python
from pathlib import Path
from src.processing.file_validator import validate_file

def validate_directory(directory: Path) -> dict:
    """Validate all files in a directory."""
    results = {
        "valid": [],
        "invalid": []
    }

    for file_path in directory.iterdir():
        if file_path.is_file():
            file_size = file_path.stat().st_size
            valid, error = validate_file(str(file_path), file_size)

            if valid:
                results["valid"].append(file_path.name)
            else:
                results["invalid"].append({
                    "filename": file_path.name,
                    "error": error
                })

    return results

# Usage
results = validate_directory(Path("/uploads"))
print(f"Valid files: {len(results['valid'])}")
print(f"Invalid files: {len(results['invalid'])}")

for item in results["invalid"]:
    print(f"  ✗ {item['filename']}: {item['error']}")
```

### Pattern 3: Extension Checking

Check if specific file types are supported.

```python
from src.processing.file_validator import get_supported_extensions

def is_pdf_supported() -> bool:
    """Check if PDF files are supported."""
    supported = get_supported_extensions()
    return '.pdf' in supported

def is_image_supported(extension: str) -> bool:
    """Check if an image extension is supported."""
    supported = get_supported_extensions()
    # Normalize extension (add dot if missing, lowercase)
    ext = extension if extension.startswith('.') else f'.{extension}'
    return ext.lower() in supported

# Usage
if is_pdf_supported():
    print("✓ PDF files are supported")

if is_image_supported("png"):
    print("✓ PNG images are supported")

if is_image_supported(".jpg"):
    print("✓ JPEG images are supported")
```

### Pattern 4: Custom Size Limits

Apply different size limits based on file type.

```python
from pathlib import Path
from src.processing.file_validator import validate_file_type, validate_file_size

def validate_with_custom_limits(file_path: str, file_size: int) -> tuple[bool, str]:
    """Validate file with type-specific size limits."""
    path = Path(file_path)
    extension = path.suffix.lower()

    # Type validation
    valid, error = validate_file_type(file_path)
    if not valid:
        return False, error

    # Custom size limits by type
    size_limits = {
        '.pdf': 100,      # 100 MB for PDFs
        '.docx': 50,      # 50 MB for Word docs
        '.png': 25,       # 25 MB for images
        '.jpg': 25,
        '.jpeg': 25,
        '.mp3': 200,      # 200 MB for audio
        '.wav': 500,      # 500 MB for WAV files
    }

    max_mb = size_limits.get(extension, 100)  # Default 100 MB

    # Size validation
    return validate_file_size(file_size, max_mb=max_mb)

# Usage
file_path = "/uploads/presentation.pdf"
file_size = 150 * 1024 * 1024  # 150 MB

valid, error = validate_with_custom_limits(file_path, file_size)
if not valid:
    print(f"Validation failed: {error}")
```

---

## FastAPI Integration

### Basic Endpoint with Validation

```python
from fastapi import FastAPI, UploadFile, HTTPException
from src.config.processing_config import ProcessingConfig

app = FastAPI()
config = ProcessingConfig()

@app.post("/upload")
async def upload_document(file: UploadFile):
    """Upload a document with validation."""
    # Read file contents
    contents = await file.read()
    file_size = len(contents)

    # Validate using centralized config
    valid, error = config.validate_file(file.filename, file_size)
    if not valid:
        raise HTTPException(status_code=400, detail=error)

    # Save file (validation passed)
    file_path = f"/uploads/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(contents)

    return {
        "message": "Upload successful",
        "filename": file.filename,
        "size": file_size
    }
```

### Advanced Endpoint with Detailed Feedback

```python
from fastapi import FastAPI, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
from src.processing.file_validator import validate_file_type, validate_file_size
from src.config.processing_config import ProcessingConfig

app = FastAPI()
config = ProcessingConfig()

@app.post("/upload/validate")
async def validate_upload(file: UploadFile):
    """Validate uploaded file without saving."""
    contents = await file.read()
    file_size = len(contents)

    # Type validation
    type_valid, type_error = validate_file_type(file.filename)

    # Size validation
    size_valid, size_error = validate_file_size(
        file_size,
        max_mb=config.max_file_size_mb
    )

    # Return detailed validation results
    return {
        "filename": file.filename,
        "size_bytes": file_size,
        "size_mb": round(file_size / (1024 * 1024), 2),
        "validation": {
            "type": {
                "valid": type_valid,
                "error": type_error or None
            },
            "size": {
                "valid": size_valid,
                "error": size_error or None
            },
            "overall": type_valid and size_valid
        },
        "supported_formats": list(config.supported_extensions_set)
    }

@app.post("/upload/process")
async def upload_and_process(file: UploadFile):
    """Upload and process document with comprehensive validation."""
    contents = await file.read()
    file_size = len(contents)

    # Validate
    valid, error = config.validate_file(file.filename, file_size)
    if not valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Validation failed",
                "detail": error,
                "filename": file.filename,
                "supported_formats": list(config.supported_extensions_set),
                "max_file_size_mb": config.max_file_size_mb
            }
        )

    # Save and process
    file_path = f"/uploads/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(contents)

    # Queue for processing (example)
    return {
        "message": "Document queued for processing",
        "filename": file.filename,
        "file_path": file_path
    }
```

### Webhook Integration (Copyparty)

```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from pathlib import Path
from src.processing.file_validator import validate_file_type

app = FastAPI()

class WebhookRequest(BaseModel):
    """Webhook request from copyparty."""
    event: str
    path: str
    filename: str

@app.post("/webhook")
async def webhook_handler(
    request: WebhookRequest,
    background_tasks: BackgroundTasks
):
    """Handle copyparty webhook with validation."""
    # Validate file type
    valid, error = validate_file_type(request.filename)
    if not valid:
        # Skip unsupported files
        return {
            "message": f"Skipped unsupported file: {request.filename}",
            "reason": error
        }

    # Check file exists
    file_path = Path(request.path)
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {request.path}"
        )

    # Queue for processing
    background_tasks.add_task(process_document, str(file_path), request.filename)

    return {
        "message": "Document queued for processing",
        "filename": request.filename
    }
```

---

## Worker Integration

### Watchdog Event Handler

```python
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from pathlib import Path
from src.processing.file_validator import validate_file_type
import logging

logger = logging.getLogger(__name__)

class DocumentUploadHandler(FileSystemEventHandler):
    """Handle document uploads with validation."""

    def on_created(self, event: FileCreatedEvent):
        """Handle file creation events."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Skip temp files
        if file_path.name.startswith('.') or file_path.name.startswith('~'):
            return

        # Validate file type
        valid, error = validate_file_type(str(file_path))
        if not valid:
            logger.debug(f"Ignoring file: {error}")
            return

        # Process file
        logger.info(f"Processing new upload: {file_path.name}")
        self.process_file(file_path)

    def process_file(self, file_path: Path):
        """Process validated file."""
        # Your processing logic here
        pass
```

### Batch Processing Worker

```python
from pathlib import Path
from src.processing.file_validator import validate_file
from src.config.processing_config import ProcessingConfig
import logging

logger = logging.getLogger(__name__)

class BatchProcessor:
    """Process multiple documents with validation."""

    def __init__(self):
        self.config = ProcessingConfig()

    def process_directory(self, directory: Path):
        """Process all valid files in a directory."""
        logger.info(f"Processing directory: {directory}")

        for file_path in directory.iterdir():
            if not file_path.is_file():
                continue

            # Get file size
            file_size = file_path.stat().st_size

            # Validate
            valid, error = validate_file(
                str(file_path),
                file_size,
                self.config.max_file_size_mb
            )

            if valid:
                self.process_file(file_path)
            else:
                logger.warning(f"Skipping {file_path.name}: {error}")

    def process_file(self, file_path: Path):
        """Process a single validated file."""
        logger.info(f"Processing: {file_path.name}")
        # Your processing logic here
        pass

# Usage
processor = BatchProcessor()
processor.process_directory(Path("/uploads"))
```

---

## Advanced Usage

### Dynamic Format Support

Support different formats in different environments.

```python
import os
from src.processing.file_validator import get_supported_extensions

# Development: Support all formats
os.environ["SUPPORTED_FORMATS"] = "pdf,docx,pptx,xlsx,png,jpg,mp3"

# Production: Limited formats
os.environ["SUPPORTED_FORMATS"] = "pdf,docx,png"

# Get currently supported formats
supported = get_supported_extensions()
print(f"Supported formats: {supported}")
```

### Custom Validation Logic

Add custom validation on top of base validation.

```python
from pathlib import Path
from src.processing.file_validator import validate_file

def validate_document_with_custom_rules(
    file_path: str,
    file_size: int
) -> tuple[bool, str]:
    """Validate document with custom business rules."""
    path = Path(file_path)

    # Base validation
    valid, error = validate_file(file_path, file_size)
    if not valid:
        return False, error

    # Custom rule: No spaces in filename
    if ' ' in path.name:
        return False, "Filenames cannot contain spaces"

    # Custom rule: No uppercase extensions
    if path.suffix != path.suffix.lower():
        return False, "File extension must be lowercase"

    # Custom rule: Filename length limit
    if len(path.stem) > 100:
        return False, "Filename too long (max 100 characters)"

    return True, ""

# Usage
valid, error = validate_document_with_custom_rules(
    "My Document.pdf",
    1024 * 1024
)
# Returns: (False, "Filenames cannot contain spaces")
```

### Validation with Context

Provide additional context in error messages.

```python
from pathlib import Path
from src.processing.file_validator import validate_file

def validate_with_context(
    file_path: str,
    file_size: int,
    user_id: str,
    context: str = ""
) -> dict:
    """Validate file and return detailed result with context."""
    path = Path(file_path)

    valid, error = validate_file(file_path, file_size)

    result = {
        "valid": valid,
        "filename": path.name,
        "size_mb": round(file_size / (1024 * 1024), 2),
        "user_id": user_id,
        "context": context,
        "timestamp": datetime.now().isoformat()
    }

    if not valid:
        result["error"] = error
        result["error_type"] = (
            "type" if "Unsupported file type" in error else "size"
        )

    return result

# Usage
from datetime import datetime

result = validate_with_context(
    "/uploads/document.pdf",
    150 * 1024 * 1024,  # 150 MB
    user_id="user123",
    context="Monthly report upload"
)

print(result)
# {
#     "valid": False,
#     "filename": "document.pdf",
#     "size_mb": 150.0,
#     "user_id": "user123",
#     "context": "Monthly report upload",
#     "timestamp": "2025-01-15T10:30:00",
#     "error": "File size 150.00 MB exceeds maximum 100 MB",
#     "error_type": "size"
# }
```

---

## Testing

### Unit Tests for Validation

```python
import pytest
from src.processing.file_validator import (
    validate_file,
    validate_file_type,
    validate_file_size
)

class TestFileValidation:
    """Test file validation functions."""

    def test_validate_file_type_valid(self):
        """Test valid file types."""
        valid, error = validate_file_type("document.pdf")
        assert valid is True
        assert error == ""

    def test_validate_file_type_invalid(self):
        """Test invalid file types."""
        valid, error = validate_file_type("file.exe")
        assert valid is False
        assert "Unsupported file type" in error

    def test_validate_file_type_no_extension(self):
        """Test file without extension."""
        valid, error = validate_file_type("README")
        assert valid is False
        assert "no extension" in error

    def test_validate_file_size_valid(self):
        """Test valid file size."""
        valid, error = validate_file_size(1024 * 1024)  # 1 MB
        assert valid is True
        assert error == ""

    def test_validate_file_size_exceeds_limit(self):
        """Test file size exceeds limit."""
        valid, error = validate_file_size(200 * 1024 * 1024)  # 200 MB
        assert valid is False
        assert "exceeds maximum" in error

    def test_validate_file_size_custom_limit(self):
        """Test custom size limit."""
        valid, error = validate_file_size(60 * 1024 * 1024, max_mb=50)
        assert valid is False
        assert "exceeds maximum 50 MB" in error

    def test_validate_file_complete(self):
        """Test complete file validation."""
        valid, error = validate_file("document.pdf", 1024 * 1024)
        assert valid is True
        assert error == ""

    def test_validate_file_type_failure(self):
        """Test complete validation with type failure."""
        valid, error = validate_file("file.exe", 1024)
        assert valid is False
        assert "Unsupported file type" in error

    def test_validate_file_size_failure(self):
        """Test complete validation with size failure."""
        valid, error = validate_file("document.pdf", 200 * 1024 * 1024)
        assert valid is False
        assert "exceeds maximum" in error
```

### Integration Tests

```python
import pytest
from pathlib import Path
from src.config.processing_config import ProcessingConfig

class TestProcessingConfig:
    """Test ProcessingConfig integration."""

    def test_config_validate_file(self):
        """Test config.validate_file method."""
        config = ProcessingConfig()

        # Valid file
        valid, error = config.validate_file("document.pdf", 1024 * 1024)
        assert valid is True

        # Invalid type
        valid, error = config.validate_file("file.exe", 1024)
        assert valid is False

        # Size exceeds limit
        size = (config.max_file_size_mb + 1) * 1024 * 1024
        valid, error = config.validate_file("document.pdf", size)
        assert valid is False

    def test_supported_extensions_set(self):
        """Test supported_extensions_set property."""
        config = ProcessingConfig()
        extensions = config.supported_extensions_set

        assert '.pdf' in extensions
        assert '.docx' in extensions
        assert '.exe' not in extensions
```

---

## Best Practices

### 1. Always Validate Before Processing

Never process a file without validation.

```python
# ✓ GOOD
def process_document(file_path: str):
    path = Path(file_path)
    file_size = path.stat().st_size

    # Validate first
    valid, error = validate_file(str(path), file_size)
    if not valid:
        raise ValueError(f"Invalid file: {error}")

    # Then process
    return do_processing(path)

# ✗ BAD
def process_document(file_path: str):
    # No validation - could crash or produce unexpected results
    return do_processing(file_path)
```

### 2. Use Centralized Configuration

Always use `ProcessingConfig` instead of hardcoding values.

```python
# ✓ GOOD
from src.config.processing_config import ProcessingConfig

config = ProcessingConfig()
max_size = config.max_file_size_mb

# ✗ BAD
max_size = 100  # Hardcoded - inconsistent with other components
```

### 3. Handle Validation Errors Gracefully

Provide clear error messages to users.

```python
# ✓ GOOD
def upload_handler(file_path: str, file_size: int):
    valid, error = validate_file(file_path, file_size)
    if not valid:
        logger.warning(f"Upload rejected: {error}")
        return {
            "success": False,
            "error": error,
            "help": "Please check file type and size requirements"
        }

    return process_file(file_path)

# ✗ BAD
def upload_handler(file_path: str, file_size: int):
    valid, error = validate_file(file_path, file_size)
    if not valid:
        raise Exception(error)  # Unclear to user what went wrong
```

### 4. Log Validation Failures

Always log validation failures for debugging.

```python
import logging

logger = logging.getLogger(__name__)

def process_upload(file_path: str, file_size: int):
    valid, error = validate_file(file_path, file_size)
    if not valid:
        logger.warning(
            f"Validation failed: {error}",
            extra={
                "file_path": file_path,
                "file_size": file_size,
                "error": error
            }
        )
        return False

    return True
```

### 5. Use Type Hints

Add type hints for better IDE support and documentation.

```python
from pathlib import Path
from typing import Tuple

def validate_document(file_path: Path) -> Tuple[bool, str]:
    """
    Validate document file.

    Args:
        file_path: Path to document file

    Returns:
        Tuple of (is_valid, error_message)
    """
    file_size = file_path.stat().st_size
    return validate_file(str(file_path), file_size)
```

### 6. Test Edge Cases

Always test edge cases in validation.

```python
import pytest

def test_edge_cases():
    """Test edge cases in validation."""
    # Empty filename
    valid, error = validate_file_type("")
    assert valid is False

    # Zero size
    valid, error = validate_file_size(0)
    assert valid is True

    # Negative size
    valid, error = validate_file_size(-1)
    assert valid is False

    # Exact limit
    valid, error = validate_file_size(100 * 1024 * 1024, max_mb=100)
    assert valid is True

    # Just over limit
    valid, error = validate_file_size(100 * 1024 * 1024 + 1, max_mb=100)
    assert valid is False
```

### 7. Document Custom Validation

If adding custom validation, document it clearly.

```python
def validate_with_business_rules(
    file_path: str,
    file_size: int
) -> Tuple[bool, str]:
    """
    Validate file with business-specific rules.

    Business Rules:
    1. Standard validation (type + size)
    2. Filename must not contain spaces
    3. Filename must be lowercase
    4. Extension must be lowercase

    Args:
        file_path: Path to file
        file_size: File size in bytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Implementation...
    pass
```

---

## See Also

- [CONFIGURATION.md](./CONFIGURATION.md) - Complete configuration reference
- [enhanced_mode_config.md](./enhanced_mode_config.md) - Docling enhanced mode documentation
- [TECHNICAL_DEBT.md](./TECHNICAL_DEBT.md) - Technical debt resolution tracking
