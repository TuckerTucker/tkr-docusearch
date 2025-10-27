"""
Example test showing how to use test fixtures.

This is a reference implementation for other tests.
"""

from pathlib import Path

import pytest

# Path to fixtures directory
FIXTURES_DIR = Path(__file__).parent


def test_fixtures_exist():
    """Verify all test fixtures exist."""
    expected_fixtures = [
        "sample.pdf",
        "sample.docx",
        "sample.txt",
        "sample.mp3",
        "sample.wav",
    ]

    for fixture in expected_fixtures:
        path = FIXTURES_DIR / fixture
        assert path.exists(), f"Fixture {fixture} not found"
        assert path.stat().st_size > 0, f"Fixture {fixture} is empty"


def test_pdf_fixture():
    """Test PDF fixture properties."""
    pdf_path = FIXTURES_DIR / "sample.pdf"

    # Verify file exists and is readable
    assert pdf_path.exists()
    assert pdf_path.suffix == ".pdf"
    assert pdf_path.stat().st_size > 0

    # Verify it's a valid PDF
    try:
        from pypdf import PdfReader

        pdf = PdfReader(pdf_path)
        assert len(pdf.pages) == 2, "PDF should have 2 pages"
    except ImportError:
        pytest.skip("pypdf not installed")


def test_docx_fixture():
    """Test DOCX fixture properties."""
    docx_path = FIXTURES_DIR / "sample.docx"

    # Verify file exists and is readable
    assert docx_path.exists()
    assert docx_path.suffix == ".docx"
    assert docx_path.stat().st_size > 0

    # Verify it's a valid DOCX
    try:
        from docx import Document

        doc = Document(docx_path)
        assert len(doc.paragraphs) > 0, "DOCX should have paragraphs"
    except ImportError:
        pytest.skip("python-docx not installed")


def test_txt_fixture():
    """Test text fixture properties."""
    txt_path = FIXTURES_DIR / "sample.txt"

    # Verify file exists and is readable
    assert txt_path.exists()
    assert txt_path.suffix == ".txt"

    # Verify content
    content = txt_path.read_text()
    assert len(content) > 0, "Text file should not be empty"
    assert "test" in content.lower(), "Text should contain test content"


def test_mp3_fixture():
    """Test MP3 fixture properties."""
    mp3_path = FIXTURES_DIR / "sample.mp3"

    # Verify file exists and is readable
    assert mp3_path.exists()
    assert mp3_path.suffix == ".mp3"
    assert mp3_path.stat().st_size > 0

    # Verify it has MP3 headers
    data = mp3_path.read_bytes()
    assert data[:3] == b"ID3" or b"\xff\xfb" in data, "Should have MP3 headers"


def test_wav_fixture():
    """Test WAV fixture properties."""
    wav_path = FIXTURES_DIR / "sample.wav"

    # Verify file exists and is readable
    assert wav_path.exists()
    assert wav_path.suffix == ".wav"
    assert wav_path.stat().st_size > 0

    # Verify it's a valid WAV
    import wave

    with wave.open(str(wav_path), "r") as wav:
        assert wav.getnchannels() == 1, "Should be mono"
        assert wav.getframerate() == 16000, "Should be 16kHz"
        assert wav.getsampwidth() == 2, "Should be 16-bit"


def test_fixture_sizes():
    """Verify all fixtures are under size limit."""
    max_size = 100 * 1024  # 100KB

    fixtures = [
        "sample.pdf",
        "sample.docx",
        "sample.txt",
        "sample.mp3",
        "sample.wav",
    ]

    total_size = 0
    for fixture in fixtures:
        path = FIXTURES_DIR / fixture
        size = path.stat().st_size
        total_size += size
        assert size < max_size, f"{fixture} exceeds 100KB limit"

    assert total_size < max_size, "Total fixture size should be under 100KB"


@pytest.mark.parametrize(
    "fixture,expected_ext",
    [
        ("sample.pdf", ".pdf"),
        ("sample.docx", ".docx"),
        ("sample.txt", ".txt"),
        ("sample.mp3", ".mp3"),
        ("sample.wav", ".wav"),
    ],
)
def test_fixture_extensions(fixture, expected_ext):
    """Test fixture file extensions."""
    path = FIXTURES_DIR / fixture
    assert path.suffix == expected_ext


# Example of using fixtures in API tests
@pytest.fixture
def pdf_fixture():
    """Provide PDF fixture path."""
    return FIXTURES_DIR / "sample.pdf"


@pytest.fixture
def all_fixtures():
    """Provide all fixture paths."""
    return {
        "pdf": FIXTURES_DIR / "sample.pdf",
        "docx": FIXTURES_DIR / "sample.docx",
        "txt": FIXTURES_DIR / "sample.txt",
        "mp3": FIXTURES_DIR / "sample.mp3",
        "wav": FIXTURES_DIR / "sample.wav",
    }


def test_fixture_helper_pdf(pdf_fixture):
    """Example using pdf_fixture helper."""
    assert pdf_fixture.exists()
    assert pdf_fixture.suffix == ".pdf"


def test_fixture_helper_all(all_fixtures):
    """Example using all_fixtures helper."""
    assert all(path.exists() for path in all_fixtures.values())
    assert len(all_fixtures) == 5
