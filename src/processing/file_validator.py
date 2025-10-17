"""
File validation utilities for document processing.

This module provides shared validation functions for file type and size checks,
eliminating duplicate validation code across workers.
"""

import os
from pathlib import Path
from typing import Set, Tuple

DEFAULT_FORMATS = (
    "pdf,docx,pptx,xlsx,html,xhtml,md,asciidoc,csv,mp3,wav,vtt,png,jpg,jpeg,tiff,bmp,webp"
)


def get_supported_extensions() -> Set[str]:
    """Load supported file extensions from environment.

    Reads the SUPPORTED_FORMATS environment variable (comma-separated list)
    and returns a set of extensions with dot prefix for easy validation.

    Returns:
        Set of extensions with dot prefix (e.g., {'.pdf', '.png'})

    Example:
        >>> exts = get_supported_extensions()
        >>> '.pdf' in exts
        True
    """
    formats_str = os.getenv("SUPPORTED_FORMATS", DEFAULT_FORMATS)
    # Split by comma, strip whitespace, add dot prefix, convert to lowercase
    extensions = {f".{ext.strip().lower()}" for ext in formats_str.split(",")}
    return extensions


def validate_file_type(file_path: str) -> Tuple[bool, str]:
    """Validate file extension against supported formats.

    Args:
        file_path: Path to file (can be absolute or relative)

    Returns:
        Tuple of (is_valid, error_message):
        - (True, "") if file type is supported
        - (False, "error message") if file type is not supported

    Example:
        >>> valid, msg = validate_file_type("document.pdf")
        >>> valid
        True
        >>> valid, msg = validate_file_type("file.exe")
        >>> valid
        False
    """
    path = Path(file_path)

    # Get extension (lowercase for case-insensitive comparison)
    extension = path.suffix.lower()

    if not extension:
        return False, f"File has no extension: {file_path}"

    supported = get_supported_extensions()

    if extension not in supported:
        return (
            False,
            f"Unsupported file type: {extension}. Supported: {', '.join(sorted(supported))}",
        )

    return True, ""


def validate_file_size(size_bytes: int, max_mb: int = 100) -> Tuple[bool, str]:
    """Validate file size against limit.

    Args:
        size_bytes: File size in bytes
        max_mb: Maximum size in MB (default: 100)

    Returns:
        Tuple of (is_valid, error_message):
        - (True, "") if file size is within limit
        - (False, "error message") if file size exceeds limit

    Example:
        >>> valid, msg = validate_file_size(1024 * 1024)  # 1 MB
        >>> valid
        True
        >>> valid, msg = validate_file_size(200 * 1024 * 1024)  # 200 MB
        >>> valid
        False
    """
    if size_bytes < 0:
        return False, f"Invalid file size: {size_bytes} bytes"

    max_bytes = max_mb * 1024 * 1024

    if size_bytes > max_bytes:
        size_mb = size_bytes / (1024 * 1024)
        return False, f"File size {size_mb:.2f} MB exceeds maximum {max_mb} MB"

    return True, ""


def validate_file(file_path: str, size_bytes: int, max_mb: int = 100) -> Tuple[bool, str]:
    """Complete file validation (type + size).

    Performs both file type and size validation. Returns on first failure.

    Args:
        file_path: Path to file (can be absolute or relative)
        size_bytes: File size in bytes
        max_mb: Maximum size in MB (default: 100)

    Returns:
        Tuple of (is_valid, error_message):
        - (True, "") if all validations pass
        - (False, "error message") if any validation fails

    Example:
        >>> valid, msg = validate_file("document.pdf", 1024 * 1024)
        >>> valid
        True
        >>> valid, msg = validate_file("file.exe", 1024)
        >>> valid
        False
    """
    # Validate file type first
    type_valid, type_msg = validate_file_type(file_path)
    if not type_valid:
        return False, type_msg

    # Then validate size
    size_valid, size_msg = validate_file_size(size_bytes, max_mb)
    if not size_valid:
        return False, size_msg

    return True, ""
