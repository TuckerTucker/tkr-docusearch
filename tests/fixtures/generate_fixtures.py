#!/usr/bin/env python3
"""
Generate test fixture files for backend API testing.

Creates minimal but valid sample files for testing document processing.
"""

import struct
import wave
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def create_sample_pdf(output_path: Path) -> None:
    """Create a simple 2-page PDF with text content."""
    c = canvas.Canvas(str(output_path), pagesize=letter)

    # Page 1
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, 750, "Test Document - Page 1")
    c.setFont("Helvetica", 12)
    c.drawString(72, 720, "This is a sample PDF document for testing purposes.")
    c.drawString(72, 700, "It contains structured content including:")
    c.drawString(90, 680, "• Multiple pages")
    c.drawString(90, 660, "• Headers and body text")
    c.drawString(90, 640, "• Simple formatting")
    c.drawString(72, 600, "Lorem ipsum dolor sit amet, consectetur adipiscing elit.")
    c.drawString(72, 580, "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.")
    c.showPage()

    # Page 2
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, 750, "Test Document - Page 2")
    c.setFont("Helvetica", 12)
    c.drawString(72, 720, "This is the second page of the test document.")
    c.drawString(72, 680, "Search Query Testing:")
    c.drawString(90, 660, "Document processing pipeline")
    c.drawString(90, 640, "Vector embeddings and similarity search")
    c.drawString(90, 620, "ChromaDB integration")
    c.drawString(72, 580, "Expected behavior: Should generate 2 page embeddings and")
    c.drawString(72, 560, "multiple text chunks depending on chunk size settings.")
    c.showPage()

    c.save()
    print(f"✓ Created {output_path.name} ({output_path.stat().st_size} bytes)")


def create_sample_docx(output_path: Path) -> None:
    """Create a simple DOCX with structured text."""
    try:
        from docx import Document
    except ImportError:
        print("✗ python-docx not installed, skipping DOCX generation")
        print("  Install with: pip install python-docx")
        return

    doc = Document()

    # Add title
    doc.add_heading("Test DOCX Document", 0)

    # Add paragraph
    doc.add_paragraph(
        "This is a sample DOCX document for testing the document processing pipeline."
    )

    # Add section
    doc.add_heading("Section 1: Document Features", level=1)
    doc.add_paragraph("This document contains multiple sections and formatting:")

    # Add bullet points
    doc.add_paragraph("Headings and structure", style="List Bullet")
    doc.add_paragraph("Paragraphs with text content", style="List Bullet")
    doc.add_paragraph("Lists and formatting", style="List Bullet")

    # Add another section
    doc.add_heading("Section 2: Testing Notes", level=1)
    doc.add_paragraph(
        "Expected behavior: DOCX files are text-only format in the processing pipeline. "
        "They should generate text chunks but no visual/page embeddings."
    )

    doc.add_paragraph(
        "The Docling parser extracts text content and structure from DOCX files, "
        "which is then processed by the text embedding handler."
    )

    doc.save(str(output_path))
    print(f"✓ Created {output_path.name} ({output_path.stat().st_size} bytes)")


def create_sample_txt(output_path: Path) -> None:
    """Create a plain text file with content."""
    content = """Test Text File
==============

This is a sample plain text file for testing the document processing pipeline.

Section 1: Overview
-------------------
Plain text files are processed as text-only documents. They do not generate
page images or visual embeddings.

Section 2: Content
------------------
The content should be chunked based on the configured chunk size and overlap
settings. Each chunk will receive a text embedding for semantic search.

Testing Notes:
- Text files use simple chunking without structure extraction
- No visual embeddings are generated
- Metadata includes filename and chunk position
- Expected chunks: 1-2 depending on chunk size settings

Keywords for search testing:
text processing, plain text, semantic search, chunking, embeddings
"""

    output_path.write_text(content)
    print(f"✓ Created {output_path.name} ({output_path.stat().st_size} bytes)")


def create_sample_mp3(output_path: Path) -> None:
    """Create a minimal valid MP3 file (silent, 1 second)."""
    # MP3 frame: Layer III, 44.1kHz, 128kbps, mono
    # This is a minimal valid MP3 file header + frame
    mp3_data = bytearray()

    # ID3v2 header (minimal)
    mp3_data.extend(b"ID3")  # ID3v2 identifier
    mp3_data.extend(b"\x04\x00")  # Version 2.4.0
    mp3_data.extend(b"\x00")  # Flags
    mp3_data.extend(b"\x00\x00\x00\x00")  # Size (0 for minimal)

    # MP3 Frame Header (Layer III, 44.1kHz, 128kbps, mono)
    # Frame sync (11 bits) + MPEG version + Layer + Protection bit
    mp3_data.extend(b"\xff\xfb")  # Sync word + MPEG 1 Layer III
    mp3_data.extend(b"\x90\x00")  # Bitrate 128kbps, 44.1kHz, no padding, mono

    # Fill with zeros for frame data (minimal silent audio)
    # 417 bytes per frame at 128kbps/44.1kHz
    # ~38 frames per second, so ~38 frames for 1 second
    frame_size = 417
    for _ in range(38):
        frame = bytearray(frame_size)
        frame[0:2] = b"\xff\xfb"  # Frame header
        frame[2:4] = b"\x90\x00"
        mp3_data.extend(frame)

    output_path.write_bytes(bytes(mp3_data))
    print(f"✓ Created {output_path.name} ({output_path.stat().st_size} bytes)")


def create_sample_wav(output_path: Path) -> None:
    """Create a minimal valid WAV file (silent, 1 second, 16kHz mono)."""
    sample_rate = 16000  # 16kHz (Whisper default)
    duration = 1  # 1 second
    num_samples = sample_rate * duration

    with wave.open(str(output_path), "w") as wav:
        wav.setnchannels(1)  # Mono
        wav.setsampwidth(2)  # 16-bit
        wav.setframerate(sample_rate)

        # Write silent audio (all zeros)
        for _ in range(num_samples):
            wav.writeframes(struct.pack("<h", 0))

    print(f"✓ Created {output_path.name} ({output_path.stat().st_size} bytes)")


def main():
    """Generate all test fixtures."""
    fixtures_dir = Path(__file__).parent

    print("Generating test fixtures...")
    print(f"Output directory: {fixtures_dir}\n")

    # Generate files
    create_sample_pdf(fixtures_dir / "sample.pdf")
    create_sample_docx(fixtures_dir / "sample.docx")
    create_sample_txt(fixtures_dir / "sample.txt")
    create_sample_mp3(fixtures_dir / "sample.mp3")
    create_sample_wav(fixtures_dir / "sample.wav")

    print("\n✓ All fixtures generated successfully!")
    print("\nNext steps:")
    print("1. Review the generated files")
    print("2. Read tests/fixtures/README.md for usage instructions")
    print("3. Use these fixtures in your API tests")


if __name__ == "__main__":
    main()
