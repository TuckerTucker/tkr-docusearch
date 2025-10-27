"""Shared pytest fixtures for whisper tests."""

from pathlib import Path

import pytest


@pytest.fixture
def sample_audio_file():
    """Path to sample MP3 file for testing."""
    return "tests/fixtures/sample.mp3"


@pytest.fixture
def sample_audio_file_path(sample_audio_file):
    """Validated Path object to sample audio."""
    path = Path(sample_audio_file)
    if not path.exists():
        pytest.skip(f"Test audio file not found: {sample_audio_file}")
    return path


@pytest.fixture
def nonexistent_audio_file():
    """Path to nonexistent audio file for error testing."""
    return "/nonexistent/file.mp3"


@pytest.fixture
def unsupported_format_file():
    """Path to file with unsupported format."""
    # Use a fixture that definitely exists but isn't audio
    return "tests/fixtures/sample.pdf"
