"""Tests for path_utils module.

Tests cover:
- normalize_path() with str and Path inputs
- Absolute and relative path handling
- File existence validation
- safe_cwd_context() CWD restoration
- Helper functions (get_file_extension, is_audio_file)
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.processing.path_utils import (
    normalize_path,
    safe_cwd_context,
    get_file_extension,
    is_audio_file,
    PathLike,
)


class TestNormalizePath:
    """Tests for normalize_path() function."""

    def test_accepts_string_path(self, tmp_path):
        """Should accept string paths and convert to Path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        result = normalize_path(str(test_file))

        assert isinstance(result, Path)
        assert result.is_absolute()
        assert result.exists()

    def test_accepts_path_object(self, tmp_path):
        """Should accept Path objects."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        result = normalize_path(test_file)

        assert isinstance(result, Path)
        assert result.is_absolute()
        assert result.exists()

    def test_converts_relative_to_absolute(self, tmp_path):
        """Should convert relative paths to absolute."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Use relative path
            result = normalize_path("test.txt")

            assert result.is_absolute()
            assert result == test_file
        finally:
            os.chdir(original_cwd)

    def test_resolves_symlinks(self, tmp_path):
        """Should resolve symlinks to actual file."""
        real_file = tmp_path / "real.txt"
        real_file.write_text("test")
        symlink = tmp_path / "link.txt"
        symlink.symlink_to(real_file)

        result = normalize_path(symlink)

        # Result should point to real file, not symlink
        assert result == real_file.resolve()
        assert result.exists()

    def test_raises_if_file_not_exists_by_default(self, tmp_path):
        """Should raise FileNotFoundError if file doesn't exist."""
        nonexistent = tmp_path / "does_not_exist.txt"

        with pytest.raises(FileNotFoundError) as exc_info:
            normalize_path(nonexistent)

        assert "does_not_exist.txt" in str(exc_info.value)

    def test_allows_nonexistent_files_when_specified(self, tmp_path):
        """Should allow non-existent files when must_exist=False."""
        nonexistent = tmp_path / "new_file.txt"

        result = normalize_path(nonexistent, must_exist=False)

        assert isinstance(result, Path)
        assert result.is_absolute()
        # File doesn't exist yet, but path is valid
        assert not result.exists()

    def test_handles_path_with_parent_references(self, tmp_path):
        """Should handle paths with .. (parent directory)."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Create path with unnecessary parent reference
        convoluted_path = tmp_path / "subdir" / ".." / "test.txt"

        result = normalize_path(str(convoluted_path))

        # Should resolve to clean path
        assert result == test_file
        assert ".." not in str(result)


class TestSafeCwdContext:
    """Tests for safe_cwd_context() context manager."""

    def test_changes_cwd_temporarily(self, tmp_path):
        """Should change CWD within context and restore after."""
        original_cwd = Path.cwd()
        target_dir = tmp_path / "subdir"
        target_dir.mkdir()

        with safe_cwd_context(target_dir):
            assert Path.cwd() == target_dir

        # CWD restored after context
        assert Path.cwd() == original_cwd

    def test_restores_cwd_on_exception(self, tmp_path):
        """Should restore CWD even if exception occurs."""
        original_cwd = Path.cwd()
        target_dir = tmp_path / "subdir"
        target_dir.mkdir()

        with pytest.raises(RuntimeError):
            with safe_cwd_context(target_dir):
                assert Path.cwd() == target_dir
                raise RuntimeError("Test exception")

        # CWD still restored despite exception
        assert Path.cwd() == original_cwd

    def test_requires_absolute_path(self, tmp_path):
        """Should raise ValueError for relative paths."""
        # Create relative path
        relative_path = Path("relative/path")

        with pytest.raises(ValueError) as exc_info:
            with safe_cwd_context(relative_path):
                pass

        assert "absolute path" in str(exc_info.value).lower()

    def test_works_with_audio_workaround_pattern(self, tmp_path):
        """Should enable the audio file processing workaround pattern."""
        # Simulate audio file processing
        audio_file = tmp_path / "podcast.mp3"
        audio_file.write_text("fake audio data")

        # Normalize path first (would be done at entry point)
        abs_path = normalize_path(audio_file)

        # Use workaround pattern
        with safe_cwd_context(abs_path.parent):
            # CWD is now the directory containing the file
            assert Path.cwd() == abs_path.parent

            # Can now use just filename (workaround for Docling bug)
            filename_only = abs_path.name
            assert filename_only == "podcast.mp3"

            # File still accessible
            assert (Path.cwd() / filename_only).exists()

        # Original CWD restored
        assert Path.cwd() != abs_path.parent


class TestGetFileExtension:
    """Tests for get_file_extension() helper."""

    def test_returns_lowercase_extension(self):
        """Should return extension in lowercase without dot."""
        assert get_file_extension("/path/to/file.PDF") == "pdf"
        assert get_file_extension("/path/to/file.Mp3") == "mp3"
        assert get_file_extension("/path/to/file.DOCX") == "docx"

    def test_accepts_path_objects(self):
        """Should accept Path objects."""
        path = Path("/path/to/file.TXT")
        assert get_file_extension(path) == "txt"

    def test_handles_no_extension(self):
        """Should return empty string for files without extension."""
        assert get_file_extension("/path/to/file") == ""
        assert get_file_extension(Path("README")) == ""

    def test_handles_multiple_dots(self):
        """Should return only final extension."""
        assert get_file_extension("/path/to/file.tar.gz") == "gz"
        assert get_file_extension("my.file.name.pdf") == "pdf"


class TestIsAudioFile:
    """Tests for is_audio_file() helper."""

    def test_identifies_common_audio_formats(self):
        """Should identify common audio file formats."""
        assert is_audio_file("/path/to/file.mp3") is True
        assert is_audio_file("/path/to/file.wav") is True
        assert is_audio_file("/path/to/file.m4a") is True
        assert is_audio_file("/path/to/file.flac") is True
        assert is_audio_file("/path/to/file.ogg") is True

    def test_case_insensitive(self):
        """Should be case-insensitive."""
        assert is_audio_file("/path/to/file.MP3") is True
        assert is_audio_file("/path/to/file.WaV") is True

    def test_rejects_non_audio_formats(self):
        """Should return False for non-audio formats."""
        assert is_audio_file("/path/to/file.pdf") is False
        assert is_audio_file("/path/to/file.docx") is False
        assert is_audio_file("/path/to/file.txt") is False
        assert is_audio_file("/path/to/file.mp4") is False  # video

    def test_accepts_path_objects(self):
        """Should accept Path objects."""
        assert is_audio_file(Path("/path/to/file.mp3")) is True
        assert is_audio_file(Path("/path/to/file.pdf")) is False


class TestIntegration:
    """Integration tests combining multiple utilities."""

    def test_full_audio_processing_workflow(self, tmp_path):
        """Test complete workflow: normalize → detect audio → CWD workaround."""
        # Setup: Create fake audio file
        audio_file = tmp_path / "subdir" / "podcast.mp3"
        audio_file.parent.mkdir()
        audio_file.write_text("fake audio")

        original_cwd = Path.cwd()

        # Step 1: Normalize path (entry point would do this)
        abs_path = normalize_path(audio_file)
        assert abs_path.is_absolute()

        # Step 2: Detect it's an audio file
        assert is_audio_file(abs_path) is True

        # Step 3: Use CWD workaround for processing
        with safe_cwd_context(abs_path.parent):
            # Simulates what we do for Docling audio bug
            current_dir = Path.cwd()
            filename = abs_path.name

            assert current_dir == abs_path.parent
            assert (current_dir / filename).exists()

        # CWD restored
        assert Path.cwd() == original_cwd

    def test_pathlike_type_accepts_both(self, tmp_path):
        """Test that PathLike type hint accepts both str and Path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Both should work with normalize_path
        result_from_str = normalize_path(str(test_file))
        result_from_path = normalize_path(test_file)

        assert result_from_str == result_from_path
        assert isinstance(result_from_str, Path)
