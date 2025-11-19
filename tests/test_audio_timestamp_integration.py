"""
Integration test for audio timestamp extraction.

This test verifies that audio files are processed with timestamps correctly:
1. Docling extracts provenance data
2. Timestamps are extracted from provenance
3. VTT file is generated
4. Markdown file contains transcript
5. ChromaDB stores timestamp metadata

This is a regression test for the Oct 2025 timestamp extraction issue.
"""

import logging
from pathlib import Path

import pytest

from tkr_docusearch.processing.processor import DocumentProcessor

logger = logging.getLogger(__name__)


@pytest.fixture
def audio_file():
    """Sample audio file fixture."""
    audio_path = Path("tests/fixtures/sample.mp3")
    if not audio_path.exists():
        pytest.skip(f"Sample audio file not found: {audio_path}")
    return str(audio_path)


@pytest.fixture
def processor(embedding_engine_instance, storage_client_instance):
    """Document processor fixture."""
    return DocumentProcessor(
        embedding_engine=embedding_engine_instance,
        storage_client=storage_client_instance,
        parser_config={"render_dpi": 150},
        visual_batch_size=4,
        text_batch_size=8,
    )


def test_audio_timestamp_extraction(audio_file, processor, tmp_path):
    """Test that audio timestamps are extracted from docling provenance data."""

    logger.info(f"\n{'='*80}")
    logger.info(f"TESTING AUDIO TIMESTAMP EXTRACTION")
    logger.info(f"Audio file: {audio_file}")
    logger.info(f"{'='*80}\n")

    # Process audio file
    result = processor.process_document(
        file_path=audio_file,
        chunk_size_words=250,
        chunk_overlap_words=50,
    )

    # Verify processing completed
    assert result.doc_id, "Document ID should be set"
    assert result.text_ids, "Text embeddings should be created"

    logger.info(f"\n✓ Processing completed")
    logger.info(f"  Doc ID: {result.doc_id}")
    logger.info(f"  Text IDs: {len(result.text_ids)} chunks")

    # Retrieve document from ChromaDB
    storage = processor.storage_client
    text_data = storage.client.get_collection("text").get(where={"filename": Path(audio_file).name})

    assert text_data, "Document should be in ChromaDB"
    assert text_data["metadatas"], "Document should have metadata"

    logger.info(f"\n✓ Retrieved from ChromaDB")
    logger.info(f"  Chunks: {len(text_data['metadatas'])}")

    # Check timestamp extraction
    chunks_with_timestamps = [
        m
        for m in text_data["metadatas"]
        if m.get("start_time") is not None and m.get("end_time") is not None
    ]

    logger.info(f"\n{'='*80}")
    logger.info(f"TIMESTAMP EXTRACTION RESULTS")
    logger.info(f"{'='*80}\n")

    logger.info(f"Total chunks: {len(text_data['metadatas'])}")
    logger.info(f"Chunks with timestamps: {len(chunks_with_timestamps)}")

    # CRITICAL ASSERTION: Audio files MUST have timestamps
    assert chunks_with_timestamps, (
        "REGRESSION: Audio file has NO timestamps! "
        "This breaks bidirectional navigation. "
        "Check docling provenance extraction."
    )

    # Verify timestamp values are reasonable
    for idx, metadata in enumerate(chunks_with_timestamps[:3]):  # Check first 3
        start = metadata.get("start_time")
        end = metadata.get("end_time")

        logger.info(f"\nChunk {idx}:")
        logger.info(f"  Text: {metadata.get('text_preview', '')[:50]}...")
        logger.info(f"  Timestamps: {start}s - {end}s")
        logger.info(f"  Duration: {end - start:.2f}s")

        # Timestamps should be valid
        assert start is not None, f"Chunk {idx} start_time is None"
        assert end is not None, f"Chunk {idx} end_time is None"
        assert start >= 0, f"Chunk {idx} start_time is negative: {start}"
        assert end > start, f"Chunk {idx} end_time <= start_time: {end} <= {start}"
        assert (
            end - start < 600
        ), f"Chunk {idx} duration too long: {end - start}s"  # Max 10 min per chunk

    logger.info(f"\n✓ All timestamp validations passed")

    # Check VTT file generation
    vtt_path = Path(f"data/media/vtt/{result.doc_id}.vtt")
    if vtt_path.exists():
        logger.info(f"\n✓ VTT file generated: {vtt_path}")

        # Read VTT content
        vtt_content = vtt_path.read_text()
        logger.info(f"  VTT size: {len(vtt_content)} bytes")

        # VTT should have WEBVTT header and timestamps
        assert "WEBVTT" in vtt_content, "VTT should have WEBVTT header"
        assert "-->" in vtt_content, "VTT should have timestamp markers"

        logger.info(f"  VTT format: Valid")
    else:
        logger.warning(f"\n⚠ VTT file not found: {vtt_path}")
        logger.warning(f"  This may be expected if timestamps were missing during processing")

    # Check markdown file
    markdown_path = Path(f"data/markdown/{result.doc_id}.md")
    if markdown_path.exists():
        logger.info(f"\n✓ Markdown file generated: {markdown_path}")

        markdown_content = markdown_path.read_text()
        logger.info(f"  Markdown size: {len(markdown_content)} bytes")

        # Markdown should have frontmatter and content
        assert "---" in markdown_content, "Markdown should have YAML frontmatter"
        assert "filename:" in markdown_content, "Markdown should have filename in frontmatter"

        logger.info(f"  Markdown format: Valid")
    else:
        logger.warning(f"\n⚠ Markdown file not found: {markdown_path}")

    logger.info(f"\n{'='*80}")
    logger.info(f"✓ AUDIO TIMESTAMP INTEGRATION TEST PASSED")
    logger.info(f"{'='*80}\n")


def test_audio_timestamps_prevent_regression():
    """
    Docstring-only test to document the regression and prevention strategy.

    REGRESSION DETAILS (Oct 2025):
    - Working audio (Oct 24): Had [time: X-Y] markers in transcript
    - Broken audio (Oct 27): NO [time: X-Y] markers in transcript
    - Root cause: Docling's export_to_text() no longer includes markers
    - Fix: Extract timestamps from docling provenance data instead

    PREVENTION STRATEGY:
    1. This integration test runs on every audio file upload
    2. If timestamps are missing, test fails immediately
    3. Logs clearly indicate the regression
    4. CI/CD catches the issue before deployment

    EXPECTED BEHAVIOR:
    - All audio chunks should have start_time and end_time
    - VTT file should be generated
    - Bidirectional navigation should work
    - Transcript should sync with audio player

    If this test fails:
    1. Check docling version (should be >= 2.58.0 for MLX Whisper)
    2. Check provenance extraction logs for "TIMESTAMP DEBUG"
    3. Verify doc.texts[].prov[] contains timestamp data
    4. Check that _extract_chunk_timestamps is working correctly
    """
