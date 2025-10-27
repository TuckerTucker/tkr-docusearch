#!/usr/bin/env python3
"""
Inspect docling provenance data structure for audio files.

This script processes an audio file and dumps the provenance data
to understand the current structure in docling 2.58.0+
"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from docling.document_converter import DocumentConverter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def inspect_audio_file(audio_path: str):
    """Inspect provenance data from audio file."""

    print(f"\n{'='*80}")
    print(f"INSPECTING AUDIO FILE: {audio_path}")
    print(f"{'='*80}\n")

    # Convert audio file
    print("Converting audio with Whisper...")
    converter = DocumentConverter()

    result = converter.convert(audio_path)
    doc = result.document

    print(f"\n✓ Conversion complete")
    print(f"  Document type: {type(doc)}")
    print(f"  Has 'texts' attribute: {hasattr(doc, 'texts')}")

    if not hasattr(doc, "texts"):
        print("\n❌ Document has no 'texts' attribute!")
        return

    print(f"  Number of text items: {len(doc.texts) if doc.texts else 0}")

    # Inspect text items
    if doc.texts:
        print(f"\n{'='*80}")
        print("TEXT ITEMS STRUCTURE")
        print(f"{'='*80}\n")

        for idx, text_item in enumerate(doc.texts[:5]):  # First 5 items
            print(f"\n--- Text Item {idx} ---")
            print(f"Type: {type(text_item)}")
            print(f"Attributes: {dir(text_item)}")

            if hasattr(text_item, "text"):
                text_preview = text_item.text[:100] if text_item.text else ""
                print(f"Text: {text_preview}...")

            if hasattr(text_item, "prov"):
                print(f"\nProvenance data:")
                print(f"  Has 'prov': {text_item.prov is not None}")
                print(f"  Prov type: {type(text_item.prov)}")
                print(f"  Prov length: {len(text_item.prov) if text_item.prov else 0}")

                if text_item.prov:
                    # Inspect first provenance item
                    prov = text_item.prov[0]
                    print(f"\n  First provenance item:")
                    print(f"    Type: {type(prov)}")
                    print(f"    Attributes: {[a for a in dir(prov) if not a.startswith('_')]}")

                    # Check for timestamp fields
                    for attr in ["start_time", "end_time", "time", "timestamp"]:
                        if hasattr(prov, attr):
                            value = getattr(prov, attr)
                            print(f"    {attr}: {value}")

                    # Dump all non-private attributes
                    print(f"\n  All provenance attributes:")
                    for attr in dir(prov):
                        if not attr.startswith("_"):
                            try:
                                value = getattr(prov, attr)
                                if not callable(value):
                                    print(f"    {attr}: {value}")
                            except:
                                pass
            else:
                print("\n❌ Text item has no 'prov' attribute")

            if idx >= 2:  # Limit to first 3 items for readability
                print(f"\n... ({len(doc.texts) - 3} more items)")
                break

    # Try export_to_text
    print(f"\n{'='*80}")
    print("EXPORT_TO_TEXT OUTPUT")
    print(f"{'='*80}\n")

    if hasattr(doc, "export_to_text"):
        text = doc.export_to_text()
        text_preview = text[:500] if text else ""
        print(f"Exported text (first 500 chars):")
        print(text_preview)
        print(f"\n... (total length: {len(text)} chars)")

        # Check for [time: X-Y] markers
        import re

        pattern = r"\[time:\s*([\d.]+)-([\d.]+)\]"
        matches = list(re.finditer(pattern, text))
        print(f"\nFound {len(matches)} [time: X-Y] markers")
        if matches:
            print("First 3 markers:")
            for match in matches[:3]:
                print(f"  {match.group(0)}")
    else:
        print("❌ Document has no 'export_to_text' method")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_audio_provenance.py <audio_file.mp3>")
        sys.exit(1)

    audio_path = sys.argv[1]

    if not Path(audio_path).exists():
        print(f"Error: File not found: {audio_path}")
        sys.exit(1)

    inspect_audio_file(audio_path)
