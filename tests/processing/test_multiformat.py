#!/usr/bin/env python3
"""
Test multi-format document support.

Tests format detection, parsing, and text-only vs visual processing.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tkr_docusearch.processing.docling_parser import (
    AUDIO_FORMATS,
    IMAGE_FORMATS,
    OFFICE_FORMATS,
    TEXT_ONLY_FORMATS,
    VISUAL_FORMATS,
    FormatType,
    get_format_type,
)


def test_format_detection():
    """Test format type detection."""
    print("=" * 60)
    print("Testing Format Detection")
    print("=" * 60)

    test_files = [
        # Visual formats
        ("document.pdf", FormatType.VISUAL),
        # Images
        ("photo.png", FormatType.VISUAL),
        ("chart.jpg", FormatType.VISUAL),
        ("diagram.jpeg", FormatType.VISUAL),
        ("scan.tiff", FormatType.VISUAL),
        # Office (text-only)
        ("report.docx", FormatType.TEXT_ONLY),
        ("data.xlsx", FormatType.TEXT_ONLY),
        ("slides.pptx", FormatType.TEXT_ONLY),
        # Text-only
        ("readme.md", FormatType.TEXT_ONLY),
        ("page.html", FormatType.TEXT_ONLY),
        ("data.csv", FormatType.TEXT_ONLY),
        # Audio
        ("transcript.vtt", FormatType.AUDIO),
        ("audio.wav", FormatType.AUDIO),
        ("podcast.mp3", FormatType.AUDIO),
        # Specialized
        ("patent.xml", FormatType.TEXT_ONLY),
        ("config.json", FormatType.TEXT_ONLY),
    ]

    passed = 0
    failed = 0

    for filename, expected_type in test_files:
        detected_type = get_format_type(filename)
        status = "✓" if detected_type == expected_type else "✗"

        if detected_type == expected_type:
            passed += 1
        else:
            failed += 1

        print(
            f"  {status} {filename:20} → {detected_type.value:10} (expected: {expected_type.value})"
        )

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_format_categories():
    """Test format category definitions."""
    print("\n" + "=" * 60)
    print("Testing Format Categories")
    print("=" * 60)

    categories = {
        "Visual": VISUAL_FORMATS,
        "Images": IMAGE_FORMATS,
        "Office": OFFICE_FORMATS,
        "Text-only": TEXT_ONLY_FORMATS,
        "Audio": AUDIO_FORMATS,
    }

    total_formats = 0
    for name, formats in categories.items():
        print(f"\n  {name} ({len(formats)} formats):")
        for fmt in sorted(formats):
            print(f"    {fmt}")
        total_formats += len(formats)

    print(f"\n  Total formats supported: {total_formats}")
    return True


def test_configuration_loading():
    """Test that configuration properly loads all formats."""
    print("\n" + "=" * 60)
    print("Testing Configuration Loading")
    print("=" * 60)

    # Simulate environment variable
    os.environ["SUPPORTED_FORMATS"] = (
        "pdf,docx,pptx,xlsx,md,html,htm,xhtml,asciidoc,csv,png,jpg,jpeg,tiff,bmp,webp,vtt,wav,mp3,xml,json"
    )

    formats_str = os.getenv("SUPPORTED_FORMATS", "pdf,docx,pptx")
    extensions = {f".{fmt.strip().lower()}" for fmt in formats_str.split(",")}

    print(f"\n  Loaded {len(extensions)} formats from config")
    print(f"  Extensions: {sorted(extensions)}")

    # Test validation
    test_cases = [
        ("document.pdf", True),
        ("readme.md", True),
        ("image.png", True),
        ("audio.mp3", True),
        ("executable.exe", False),
    ]

    print("\n  File validation:")
    passed = 0
    for filename, should_be_valid in test_cases:
        ext = Path(filename).suffix.lower()
        is_valid = ext in extensions
        status = "✓" if is_valid == should_be_valid else "✗"

        if is_valid == should_be_valid:
            passed += 1

        print(
            f"    {status} {filename:20} → {'supported' if is_valid else 'unsupported':12} (expected: {'supported' if should_be_valid else 'unsupported'})"
        )

    print(f"\n  Results: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Multi-Format Support Test Suite")
    print("=" * 60)

    tests = [
        ("Format Detection", test_format_detection),
        ("Format Categories", test_format_categories),
        ("Configuration Loading", test_configuration_loading),
    ]

    passed_tests = 0
    total_tests = len(tests)

    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed_tests += 1
                print(f"\n✓ {test_name} PASSED")
            else:
                print(f"\n✗ {test_name} FAILED")
        except Exception as e:
            print(f"\n✗ {test_name} FAILED with exception: {e}")

    print("\n" + "=" * 60)
    print(f"Overall Results: {passed_tests}/{total_tests} tests passed")
    print("=" * 60)

    return 0 if passed_tests == total_tests else 1


if __name__ == "__main__":
    sys.exit(main())
