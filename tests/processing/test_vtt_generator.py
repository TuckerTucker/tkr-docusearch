"""
Unit tests for VTT generator.

Tests the WebVTT generation functionality including timestamp formatting,
VTT content generation, file saving, and validation.

Wave 1 - Integration Contract IC-002
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from tkr_docusearch.processing.types import TextChunk
from tkr_docusearch.processing.vtt_generator import (
    EmptyChunkError,
    InvalidTimestampError,
    format_timestamp,
    generate_vtt,
    save_vtt,
    validate_vtt,
)


def test_format_timestamp():
    """Test timestamp formatting."""
    assert format_timestamp(0.0) == "00:00:00.000"
    assert format_timestamp(65.5) == "00:01:05.500"
    assert format_timestamp(3725.123) == "01:02:05.123"
    assert format_timestamp(0.001) == "00:00:00.001"
    assert format_timestamp(3599.999) == "00:59:59.999"


def test_format_timestamp_negative():
    """Test that negative timestamps raise error."""
    with pytest.raises(InvalidTimestampError):
        format_timestamp(-1.0)


def test_validate_vtt_valid():
    """Test VTT validation with valid content."""
    valid_vtt = """WEBVTT

00:00:00.000 --> 00:00:05.000
Test content
"""
    assert validate_vtt(valid_vtt) == True


def test_validate_vtt_invalid():
    """Test VTT validation with invalid content."""
    assert validate_vtt("Not VTT") == False
    assert validate_vtt("") == False
    assert validate_vtt("WEBVTT\n\nNo timestamps here") == False


def test_generate_vtt_basic():
    """Test basic VTT generation."""
    chunks = [
        TextChunk(
            chunk_id="test-0001",
            page_num=1,
            text="First chunk",
            start_offset=0,
            end_offset=11,
            word_count=2,
            start_time=0.0,
            end_time=5.0,
        ),
        TextChunk(
            chunk_id="test-0002",
            page_num=1,
            text="Second chunk",
            start_offset=11,
            end_offset=23,
            word_count=2,
            start_time=5.0,
            end_time=10.0,
        ),
    ]

    vtt = generate_vtt(chunks, "test.mp3")

    assert vtt.startswith("WEBVTT")
    assert "00:00:00.000 --> 00:00:05.000" in vtt
    assert "First chunk" in vtt
    assert "00:00:05.000 --> 00:00:10.000" in vtt
    assert "Second chunk" in vtt
    assert "NOTE Generated from test.mp3" in vtt


def test_generate_vtt_no_timestamps():
    """Test VTT generation fails without timestamps."""
    chunks = [
        TextChunk(
            chunk_id="test-0001",
            page_num=1,
            text="No timestamps",
            start_offset=0,
            end_offset=13,
            word_count=2,
            start_time=None,
            end_time=None,
        ),
    ]

    with pytest.raises(EmptyChunkError, match="No chunks with timestamps"):
        generate_vtt(chunks, "test.mp3")


def test_generate_vtt_partial_timestamps():
    """Test VTT generation with mix of timestamped and non-timestamped chunks."""
    chunks = [
        TextChunk(
            chunk_id="test-0001",
            page_num=1,
            text="With timestamps",
            start_offset=0,
            end_offset=15,
            word_count=2,
            start_time=0.0,
            end_time=5.0,
        ),
        TextChunk(
            chunk_id="test-0002",
            page_num=1,
            text="Without timestamps",
            start_offset=15,
            end_offset=33,
            word_count=2,
            start_time=None,
            end_time=None,
        ),
    ]

    vtt = generate_vtt(chunks, "test.mp3")

    assert "With timestamps" in vtt
    assert "Without timestamps" not in vtt
    assert validate_vtt(vtt)


def test_generate_vtt_invalid_timestamps():
    """Test VTT generation skips chunks with invalid timestamps."""
    chunks = [
        TextChunk(
            chunk_id="test-0001",
            page_num=1,
            text="Valid chunk",
            start_offset=0,
            end_offset=11,
            word_count=2,
            start_time=0.0,
            end_time=5.0,
        ),
        TextChunk(
            chunk_id="test-0002",
            page_num=1,
            text="Invalid chunk (end <= start)",
            start_offset=11,
            end_offset=38,
            word_count=5,
            start_time=10.0,
            end_time=10.0,  # End equals start
        ),
    ]

    vtt = generate_vtt(chunks, "test.mp3")

    assert "Valid chunk" in vtt
    assert "Invalid chunk" not in vtt


def test_save_vtt():
    """Test VTT file saving."""
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()

    try:
        vtt_content = """WEBVTT

00:00:00.000 --> 00:00:05.000
Test content
"""
        doc_id = "test-doc-123"
        output_path = save_vtt(doc_id, vtt_content, Path(temp_dir))

        # Verify file exists
        assert output_path.exists()
        assert output_path.name == f"{doc_id}.vtt"

        # Verify content
        with open(output_path, "r", encoding="utf-8") as f:
            saved_content = f.read()

        assert saved_content == vtt_content

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


def test_save_vtt_creates_directory():
    """Test that save_vtt creates output directory if it doesn't exist."""
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create non-existent subdirectory path
        output_dir = temp_dir / "subdir" / "vtt"

        vtt_content = "WEBVTT\n\n00:00:00.000 --> 00:00:05.000\nTest\n"
        doc_id = "test-doc-456"

        output_path = save_vtt(doc_id, vtt_content, output_dir)

        # Verify directory and file were created
        assert output_dir.exists()
        assert output_path.exists()

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


def test_generate_and_validate():
    """Test that generated VTT passes validation."""
    chunks = [
        TextChunk(
            chunk_id="test-0001",
            page_num=1,
            text="Hello world",
            start_offset=0,
            end_offset=11,
            word_count=2,
            start_time=0.0,
            end_time=2.5,
        ),
        TextChunk(
            chunk_id="test-0002",
            page_num=1,
            text="This is a test",
            start_offset=11,
            end_offset=25,
            word_count=4,
            start_time=2.5,
            end_time=5.0,
        ),
    ]

    vtt = generate_vtt(chunks, "test.mp3")

    # Generated VTT should pass validation
    assert validate_vtt(vtt)


def test_generate_vtt_with_multiline_text():
    """Test VTT generation with text containing newlines."""
    chunks = [
        TextChunk(
            chunk_id="test-0001",
            page_num=1,
            text="Line 1\nLine 2\nLine 3",
            start_offset=0,
            end_offset=20,
            word_count=6,
            start_time=0.0,
            end_time=5.0,
        ),
    ]

    vtt = generate_vtt(chunks, "test.mp3")

    # VTT should contain the text (strip() is applied, but newlines within are preserved)
    assert "Line 1" in vtt or "Line 1\nLine 2\nLine 3" in vtt
    assert validate_vtt(vtt)


def test_generate_vtt_empty_text():
    """Test VTT generation skips chunks with empty text."""
    chunks = [
        TextChunk(
            chunk_id="test-0001",
            page_num=1,
            text="Valid chunk",
            start_offset=0,
            end_offset=11,
            word_count=2,
            start_time=0.0,
            end_time=5.0,
        ),
        TextChunk(
            chunk_id="test-0002",
            page_num=1,
            text="   ",  # Empty when stripped
            start_offset=11,
            end_offset=14,
            word_count=0,
            start_time=5.0,
            end_time=10.0,
        ),
    ]

    vtt = generate_vtt(chunks, "test.mp3")

    assert "Valid chunk" in vtt
    # Should have 1 cue, not 2
    assert vtt.count(" --> ") == 1
