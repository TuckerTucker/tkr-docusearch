#!/usr/bin/env python3
"""
Inspect docling Whisper output structure to find timestamps.

Since provenance data is not populated, we need to find where
docling stores the Whisper timestamp information.
"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from docling.document_converter import DocumentConverter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def inspect_whisper_output(audio_path: str):
    """Inspect Whisper output from docling."""

    print(f"\n{'='*80}")
    print(f"INSPECTING WHISPER OUTPUT: {audio_path}")
    print(f"{'='*80}\n")

    # Convert audio file
    print("Converting audio with Whisper...")
    converter = DocumentConverter()
    result = converter.convert(audio_path)

    print(f"\n✓ Conversion complete")
    print(f"  Result type: {type(result)}")
    print(f"  Result attributes: {[a for a in dir(result) if not a.startswith('_')]}")

    # Check result.output
    if hasattr(result, "output"):
        print(f"\n--- result.output ---")
        print(f"  Type: {type(result.output)}")
        if result.output:
            print(f"  Attributes: {[a for a in dir(result.output) if not a.startswith('_')]}")

            # Check for transcript/segments
            for attr in ["transcript", "segments", "words", "word_timestamps", "output"]:
                if hasattr(result.output, attr):
                    value = getattr(result.output, attr)
                    print(f"  {attr}: {type(value)}")
                    if isinstance(value, list) and len(value) > 0:
                        print(f"    First item: {value[0]}")

    # Check document
    doc = result.document
    print(f"\n--- result.document ---")
    print(f"  Type: {type(doc)}")
    print(f"  Attributes: {[a for a in dir(doc) if not a.startswith('_')]}")

    # Check for audio-specific attributes
    for attr in ["audio_metadata", "transcript", "segments", "asr_output"]:
        if hasattr(doc, attr):
            value = getattr(doc, attr)
            print(f"  {attr}: {type(value)}")

    # Check texts structure
    if hasattr(doc, "texts") and doc.texts:
        print(f"\n--- doc.texts ---")
        print(f"  Count: {len(doc.texts)}")

        for idx, text_item in enumerate(doc.texts[:3]):
            print(f"\n  Text {idx}:")
            print(f"    text: {text_item.text[:100] if hasattr(text_item, 'text') else 'N/A'}...")
            print(f"    prov: {text_item.prov if hasattr(text_item, 'prov') else 'N/A'}")

            # Check for any timestamp-related attributes
            attrs = dir(text_item)
            time_attrs = [a for a in attrs if "time" in a.lower() or "stamp" in a.lower()]
            if time_attrs:
                print(f"    time-related attrs: {time_attrs}")

    # Check if there's a _backend or _asr attribute
    if hasattr(result, "_backend"):
        print(f"\n--- result._backend ---")
        backend = result._backend
        print(f"  Type: {type(backend)}")
        print(f"  Attributes: {[a for a in dir(backend) if not a.startswith('__')]}")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_whisper_output.py <audio_file.mp3>")
        sys.exit(1)

    audio_path = sys.argv[1]

    if not Path(audio_path).exists():
        print(f"Error: File not found: {audio_path}")
        sys.exit(1)

    inspect_whisper_output(audio_path)
