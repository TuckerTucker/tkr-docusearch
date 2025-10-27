#!/usr/bin/env python3
"""
Validate test fixtures.

Ensures all fixtures are valid and meet requirements.
"""

import wave
from pathlib import Path


def validate_pdf(path: Path) -> dict:
    """Validate PDF fixture."""
    try:
        from pypdf import PdfReader

        pdf = PdfReader(path)
        return {
            "valid": True,
            "pages": len(pdf.pages),
            "size": path.stat().st_size,
            "details": f"{len(pdf.pages)} pages, {path.stat().st_size} bytes",
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}


def validate_docx(path: Path) -> dict:
    """Validate DOCX fixture."""
    try:
        from docx import Document

        doc = Document(path)
        return {
            "valid": True,
            "paragraphs": len(doc.paragraphs),
            "size": path.stat().st_size,
            "details": f"{len(doc.paragraphs)} paragraphs, {path.stat().st_size} bytes",
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}


def validate_txt(path: Path) -> dict:
    """Validate text fixture."""
    try:
        content = path.read_text()
        return {
            "valid": True,
            "lines": len(content.splitlines()),
            "chars": len(content),
            "size": path.stat().st_size,
            "details": f"{len(content.splitlines())} lines, {len(content)} chars, {path.stat().st_size} bytes",
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}


def validate_mp3(path: Path) -> dict:
    """Validate MP3 fixture."""
    try:
        # Basic validation - check file exists and has MP3 header
        data = path.read_bytes()
        has_id3 = data[:3] == b"ID3"
        has_sync = b"\xff\xfb" in data or b"\xff\xfa" in data

        return {
            "valid": has_id3 or has_sync,
            "size": path.stat().st_size,
            "has_id3": has_id3,
            "details": f"{'ID3 tag' if has_id3 else 'No ID3'}, {path.stat().st_size} bytes",
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}


def validate_wav(path: Path) -> dict:
    """Validate WAV fixture."""
    try:
        with wave.open(str(path), "r") as wav:
            return {
                "valid": True,
                "channels": wav.getnchannels(),
                "sample_width": wav.getsampwidth(),
                "framerate": wav.getframerate(),
                "frames": wav.getnframes(),
                "duration": wav.getnframes() / wav.getframerate(),
                "size": path.stat().st_size,
                "details": f"{wav.getnchannels()}ch, {wav.getframerate()}Hz, {wav.getnframes() / wav.getframerate():.1f}s, {path.stat().st_size} bytes",
            }
    except Exception as e:
        return {"valid": False, "error": str(e)}


def main():
    """Validate all fixtures."""
    fixtures_dir = Path(__file__).parent

    print("Validating test fixtures...\n")

    validators = {
        "sample.pdf": validate_pdf,
        "sample.docx": validate_docx,
        "sample.txt": validate_txt,
        "sample.mp3": validate_mp3,
        "sample.wav": validate_wav,
    }

    results = {}
    all_valid = True
    total_size = 0

    for filename, validator in validators.items():
        path = fixtures_dir / filename
        if not path.exists():
            print(f"✗ {filename}: NOT FOUND")
            all_valid = False
            continue

        result = validator(path)
        results[filename] = result

        if result["valid"]:
            print(f"✓ {filename}: {result['details']}")
            total_size += result["size"]
        else:
            print(f"✗ {filename}: INVALID - {result.get('error', 'Unknown error')}")
            all_valid = False

    print(f"\n{'='*60}")
    print(f"Total size: {total_size:,} bytes ({total_size / 1024:.1f} KB)")
    print(f"Status: {'✓ All valid' if all_valid else '✗ Some fixtures invalid'}")

    if total_size > 100 * 1024:
        print(f"⚠ Warning: Total size exceeds 100KB target")

    return 0 if all_valid else 1


if __name__ == "__main__":
    exit(main())
