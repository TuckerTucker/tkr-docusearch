"""
Path utilities for DocuSearch.

Provides centralized path management to ensure consistent file path handling
across the project, especially important for:
- Docling ASR pipeline (Whisper/FFmpeg path requirements)
- Cross-module file operations
- CWD-independent path resolution

All paths returned by these utilities are absolute paths.
"""

import os
import logging
from pathlib import Path
from typing import Union, Optional

logger = logging.getLogger(__name__)

# Project root directory (parent of src/)
# This file is at: PROJECT_ROOT/src/utils/paths.py
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()

# Ensure we're actually at the project root
# (PROJECT_ROOT should contain data/, src/, docker/, scripts/)
if not (PROJECT_ROOT / "src").exists():
    logger.warning(
        f"PROJECT_ROOT detection may be incorrect: {PROJECT_ROOT}. "
        f"Expected to find 'src/' directory."
    )


def resolve_absolute(path: Union[str, Path]) -> Path:
    """
    Convert any path to an absolute Path object.

    Handles:
    - Relative paths (resolved relative to PROJECT_ROOT)
    - Absolute paths (validated and normalized)
    - Path objects (converted to absolute)
    - String paths (converted to Path and made absolute)

    Args:
        path: File or directory path (relative or absolute)

    Returns:
        Absolute Path object

    Examples:
        >>> resolve_absolute("data/uploads/file.mp3")
        PosixPath('/path/to/project/data/uploads/file.mp3')

        >>> resolve_absolute("/absolute/path/file.mp3")
        PosixPath('/absolute/path/file.mp3')
    """
    path_obj = Path(path)

    if path_obj.is_absolute():
        return path_obj.resolve()
    else:
        # Resolve relative to project root
        return (PROJECT_ROOT / path_obj).resolve()


def ensure_absolute(path: Union[str, Path], must_exist: bool = False) -> str:
    """
    Ensure a path is absolute and optionally validate existence.

    This is the primary function to use when passing file paths to external
    libraries (like Docling/Whisper) that may have path handling issues.

    Args:
        path: File or directory path
        must_exist: If True, raise FileNotFoundError if path doesn't exist

    Returns:
        Absolute path as string

    Raises:
        FileNotFoundError: If must_exist=True and path doesn't exist

    Examples:
        >>> ensure_absolute("data/uploads/file.mp3")
        '/path/to/project/data/uploads/file.mp3'

        >>> ensure_absolute("data/uploads/file.mp3", must_exist=True)
        FileNotFoundError: File not found: /path/to/project/data/uploads/file.mp3
    """
    abs_path = resolve_absolute(path)

    if must_exist and not abs_path.exists():
        raise FileNotFoundError(f"File not found: {abs_path}")

    return str(abs_path)


def validate_file_path(
    path: Union[str, Path],
    must_exist: bool = True,
    must_be_file: bool = True,
) -> Path:
    """
    Validate a file path and return absolute Path object.

    Args:
        path: File path to validate
        must_exist: Require file to exist
        must_be_file: Require path to be a file (not directory)

    Returns:
        Absolute Path object

    Raises:
        FileNotFoundError: If must_exist=True and file doesn't exist
        ValueError: If must_be_file=True and path is a directory
    """
    abs_path = resolve_absolute(path)

    if must_exist and not abs_path.exists():
        raise FileNotFoundError(f"File not found: {abs_path}")

    if must_be_file and abs_path.exists() and abs_path.is_dir():
        raise ValueError(f"Expected file but got directory: {abs_path}")

    return abs_path


# Standard directory getters

def get_data_dir() -> Path:
    """Get absolute path to data/ directory."""
    return PROJECT_ROOT / "data"


def get_uploads_dir() -> Path:
    """Get absolute path to data/uploads/ directory."""
    return PROJECT_ROOT / "data" / "uploads"


def get_images_dir() -> Path:
    """Get absolute path to data/images/ directory."""
    return PROJECT_ROOT / "data" / "images"


def get_models_dir() -> Path:
    """Get absolute path to data/models/ directory (for model cache)."""
    return PROJECT_ROOT / "data" / "models"


def get_logs_dir() -> Path:
    """Get absolute path to logs/ directory."""
    return PROJECT_ROOT / "logs"


def get_chroma_db_dir() -> Path:
    """Get absolute path to data/chroma_db/ directory."""
    return PROJECT_ROOT / "data" / "chroma_db"


# Utility functions for common operations

def is_audio_file(path: Union[str, Path]) -> bool:
    """
    Check if a file is an audio file based on extension.

    Args:
        path: File path

    Returns:
        True if file has audio extension (.mp3, .wav, .m4a, .flac, etc.)
    """
    audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac', '.wma'}
    path_obj = Path(path)
    return path_obj.suffix.lower() in audio_extensions


def is_document_file(path: Union[str, Path]) -> bool:
    """
    Check if a file is a document file based on extension.

    Args:
        path: File path

    Returns:
        True if file has document extension (.pdf, .docx, .pptx, etc.)
    """
    doc_extensions = {'.pdf', '.docx', '.pptx', '.doc', '.ppt', '.txt', '.md'}
    path_obj = Path(path)
    return path_obj.suffix.lower() in doc_extensions


def get_file_info(path: Union[str, Path]) -> dict:
    """
    Get information about a file path.

    Args:
        path: File path

    Returns:
        Dict with file information:
        - absolute_path: Absolute path string
        - exists: Whether file exists
        - is_file: Whether it's a file
        - is_dir: Whether it's a directory
        - size_bytes: File size (if exists)
        - extension: File extension
        - filename: File name without directory
    """
    abs_path = resolve_absolute(path)

    info = {
        "absolute_path": str(abs_path),
        "exists": abs_path.exists(),
        "is_file": abs_path.is_file() if abs_path.exists() else False,
        "is_dir": abs_path.is_dir() if abs_path.exists() else False,
        "extension": abs_path.suffix,
        "filename": abs_path.name,
    }

    if abs_path.exists() and abs_path.is_file():
        info["size_bytes"] = abs_path.stat().st_size

    return info


# Logging helpers

def log_path_info(path: Union[str, Path], context: str = "") -> None:
    """
    Log detailed path information for debugging.

    Args:
        path: Path to log information about
        context: Optional context string to prepend to log message
    """
    info = get_file_info(path)
    context_str = f"[{context}] " if context else ""

    logger.debug(
        f"{context_str}Path info: "
        f"abs_path={info['absolute_path']}, "
        f"exists={info['exists']}, "
        f"is_file={info['is_file']}, "
        f"extension={info['extension']}"
    )

    if not info['exists']:
        logger.warning(f"{context_str}Path does not exist: {info['absolute_path']}")
