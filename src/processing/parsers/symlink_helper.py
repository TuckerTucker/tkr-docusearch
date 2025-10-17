"""
Symlink helper for Docling ASR pipeline workaround.

This module handles the temporary symlink creation for audio files,
which is needed due to a Docling ASR pipeline bug that strips directory paths.
"""

import logging
import os
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)


class SymlinkHelper:
    """Helper for managing temporary symlinks."""

    @staticmethod
    @contextmanager
    def audio_file_symlink(file_path: str):
        """
        Context manager for creating temporary symlink for audio files.

        WORKAROUND: Docling ASR pipeline has a bug where it strips the directory
        from audio file paths. Create a temporary symlink at project root.

        Args:
            file_path: Absolute path to audio file

        Yields:
            None (symlink created and cleaned up automatically)

        Example:
            with SymlinkHelper.audio_file_symlink("/path/to/audio.mp3"):
                # Docling can now access the file
                result = converter.convert(file_path)
        """
        from src.utils.paths import PROJECT_ROOT

        ext = Path(file_path).suffix.lower()
        temp_symlink = None

        # Only create symlink for audio files
        if ext in [".mp3", ".wav"]:
            filename = Path(file_path).name
            temp_symlink = PROJECT_ROOT / filename

            # Only create symlink if it doesn't already exist
            if not temp_symlink.exists():
                try:
                    os.symlink(file_path, temp_symlink)
                    logger.debug(f"Created temporary symlink: {temp_symlink} -> {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to create symlink (continuing anyway): {e}")
                    temp_symlink = None

        try:
            yield
        finally:
            # Clean up temporary symlink (guaranteed to run even on exception)
            if temp_symlink and temp_symlink.exists() and temp_symlink.is_symlink():
                try:
                    temp_symlink.unlink()
                    logger.debug(f"Cleaned up temporary symlink: {temp_symlink}")
                except Exception as e:
                    logger.warning(f"Failed to remove symlink: {e}")
