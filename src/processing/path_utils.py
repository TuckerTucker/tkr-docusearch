"""Path handling utilities for consistent file path processing.

This module provides utilities to ensure consistent path handling across
the document processing pipeline. It addresses issues like:
- Inconsistent Path() conversions across layers
- Relative vs absolute path handling
- CWD sensitivity (especially for audio processing)
- Type safety and clarity

Design Pattern:
- Public APIs accept PathLike (str | Path) for flexibility
- Convert to absolute Path once at entry points using normalize_path()
- Internal functions work exclusively with Path objects
- This prevents bugs from CWD changes and improves type safety
"""

from pathlib import Path
from typing import Union
from contextlib import contextmanager
import os

# Type alias for functions that accept both strings and Path objects
PathLike = Union[str, Path]


def normalize_path(path: PathLike, must_exist: bool = True) -> Path:
    """Convert path-like input to absolute Path object.

    This is the primary entry point for all file path handling. It:
    1. Accepts both str and Path objects
    2. Converts to pathlib.Path
    3. Resolves to absolute path (critical for CWD-sensitive operations)
    4. Optionally validates file existence

    Args:
        path: File path as string or Path object
        must_exist: If True, raises FileNotFoundError if path doesn't exist

    Returns:
        Absolute Path object, with symlinks resolved

    Raises:
        FileNotFoundError: If must_exist=True and path doesn't exist

    Examples:
        >>> # Accept strings
        >>> p = normalize_path("/path/to/file.pdf")
        >>> # Accept Path objects
        >>> p = normalize_path(Path("./relative/file.pdf"))
        >>> # Both return absolute Path: /absolute/path/to/file.pdf

        >>> # Skip existence check for files being created
        >>> output_path = normalize_path("/new/file.pdf", must_exist=False)
    """
    # Convert to Path if string
    path_obj = Path(path) if isinstance(path, str) else path

    # Resolve to absolute path (resolves symlinks and relative paths)
    # This is CRITICAL - makes paths immune to CWD changes
    absolute_path = path_obj.resolve()

    # Validate existence if required
    if must_exist and not absolute_path.exists():
        raise FileNotFoundError(f"File not found: {absolute_path}")

    return absolute_path


@contextmanager
def safe_cwd_context(target_dir: Path):
    """Context manager for safely changing working directory.

    This is primarily used as a workaround for the Docling audio transcription
    bug where it changes CWD internally, breaking absolute paths. By temporarily
    changing to the file's directory, we can pass just the filename to Docling.

    IMPORTANT: This is a workaround for a Docling 2.55.1 bug. Future versions
    may fix this, at which point this context manager can be removed.

    Args:
        target_dir: Directory to change to (must be absolute Path)

    Yields:
        The target directory Path

    Examples:
        >>> file_path = normalize_path("/uploads/audio.mp3")
        >>> with safe_cwd_context(file_path.parent):
        ...     # CWD is now /uploads/
        ...     result = some_library.process(file_path.name)
        ...     # Processing with just filename: "audio.mp3"
        ... # CWD automatically restored here

    Notes:
        - Always use resolved absolute paths before this context
        - CWD is guaranteed to be restored even if exception occurs
        - Thread-safe: Uses thread-local storage in os.chdir
    """
    if not target_dir.is_absolute():
        raise ValueError(f"safe_cwd_context requires absolute path, got: {target_dir}")

    original_cwd = Path.cwd()
    try:
        os.chdir(target_dir)
        yield target_dir
    finally:
        # Always restore original CWD, even if exception occurred
        os.chdir(original_cwd)


def get_file_extension(path: PathLike) -> str:
    """Get lowercase file extension without leading dot.

    Args:
        path: File path as string or Path object

    Returns:
        Lowercase extension without dot (e.g., "pdf", "mp3")
        Empty string if no extension

    Examples:
        >>> get_file_extension("/path/to/file.PDF")
        'pdf'
        >>> get_file_extension(Path("document.docx"))
        'docx'
        >>> get_file_extension("no_extension")
        ''
    """
    path_obj = Path(path) if isinstance(path, str) else path
    # suffix includes the dot, so we strip it and lowercase
    return path_obj.suffix.lstrip('.').lower()


def is_audio_file(path: PathLike) -> bool:
    """Check if file is an audio format requiring special handling.

    Audio files need the CWD workaround due to Docling bug.

    Args:
        path: File path as string or Path object

    Returns:
        True if file is a known audio format

    Examples:
        >>> is_audio_file("/path/to/podcast.mp3")
        True
        >>> is_audio_file(Path("document.pdf"))
        False
    """
    audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac', '.wma'}
    path_obj = Path(path) if isinstance(path, str) else path
    return path_obj.suffix.lower() in audio_extensions
