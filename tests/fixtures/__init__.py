"""
Test fixtures for backend API testing.

This package provides sample files for testing document processing:
- sample.pdf: 2-page PDF with text content
- sample.docx: Microsoft Word document with structure
- sample.txt: Plain text file
- sample.mp3: Minimal MP3 audio file
- sample.wav: WAV audio file (16kHz mono)

All fixtures are minimal but valid, designed for fast testing.
See README.md for detailed documentation.
"""

from pathlib import Path

# Fixtures directory
FIXTURES_DIR = Path(__file__).parent

# Fixture paths
SAMPLE_PDF = FIXTURES_DIR / "sample.pdf"
SAMPLE_DOCX = FIXTURES_DIR / "sample.docx"
SAMPLE_TXT = FIXTURES_DIR / "sample.txt"
SAMPLE_MP3 = FIXTURES_DIR / "sample.mp3"
SAMPLE_WAV = FIXTURES_DIR / "sample.wav"

__all__ = [
    "FIXTURES_DIR",
    "SAMPLE_PDF",
    "SAMPLE_DOCX",
    "SAMPLE_TXT",
    "SAMPLE_MP3",
    "SAMPLE_WAV",
]
