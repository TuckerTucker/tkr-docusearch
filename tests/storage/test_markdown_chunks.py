"""
Tests for markdown chunk marker insertion functionality.

Tests the core functionality of inserting chunk markers into markdown
for bidirectional highlighting between search results and document content.
"""

import pytest

from tkr_docusearch.storage.markdown_chunking import (
    ChunkMetadata,
    insert_chunk_markers,
    strip_chunk_markers,
    validate_chunk_markers,
)

# ============================================================================
# Test Data
# ============================================================================


@pytest.fixture
def sample_markdown():
    """Sample markdown content for testing."""
    return """---
filename: test.pdf
doc_id: abc123
date_added: 2025-10-17T00:00:00Z
chunk_count: 2
---

# Introduction

This is the first paragraph of the introduction section.
It contains some important information about the document.

## Background

This section provides background information.
It has multiple sentences and paragraphs.

# Conclusion

Final thoughts and summary of the document.
"""


@pytest.fixture
def sample_chunks():
    """Sample chunk metadata for testing."""
    return [
        ChunkMetadata(
            chunk_id="abc123-chunk0000",
            embedding_id="abc123-chunk0000",
            page=1,
            section_path="Introduction",
            text_content="This is the first paragraph of the introduction section.\n"
            "It contains some important information about the document.",
            parent_heading="Introduction",
        ),
        ChunkMetadata(
            chunk_id="abc123-chunk0001",
            embedding_id="abc123-chunk0001",
            page=1,
            section_path="Introduction > Background",
            text_content="This section provides background information.\n"
            "It has multiple sentences and paragraphs.",
            parent_heading="Background",
        ),
        ChunkMetadata(
            chunk_id="abc123-chunk0002",
            embedding_id="abc123-chunk0002",
            page=2,
            section_path="Conclusion",
            text_content="Final thoughts and summary of the document.",
            parent_heading="Conclusion",
        ),
    ]


# ============================================================================
# Tests for insert_chunk_markers()
# ============================================================================


def test_insert_chunk_markers_basic(sample_markdown, sample_chunks):
    """Test basic chunk marker insertion."""
    result = insert_chunk_markers(sample_markdown, sample_chunks)

    # Verify markers are present
    assert "<!-- chunk:abc123-chunk0000" in result
    assert "<!-- chunk:abc123-chunk0001" in result
    assert "<!-- chunk:abc123-chunk0002" in result

    # Verify divs are present
    assert '<div data-chunk-id="abc123-chunk0000"' in result
    assert '<div data-chunk-id="abc123-chunk0001"' in result
    assert '<div data-chunk-id="abc123-chunk0002"' in result

    # Verify closing divs
    assert result.count("</div>") >= 3


def test_insert_chunk_markers_preserves_frontmatter(sample_markdown, sample_chunks):
    """Test that frontmatter is preserved and updated."""
    result = insert_chunk_markers(sample_markdown, sample_chunks)

    # Frontmatter should still be present
    assert result.startswith("---")
    assert "filename: test.pdf" in result
    assert "doc_id: abc123" in result

    # Chunk count should be updated
    assert "chunk_count: 3" in result


def test_insert_chunk_markers_with_section_paths(sample_markdown, sample_chunks):
    """Test that section paths are included in markers."""
    result = insert_chunk_markers(sample_markdown, sample_chunks)

    # Check section paths in markers
    assert 'section:"Introduction"' in result
    assert (
        'section:"Introduction &gt; Background"' in result
        or 'section:"Introduction > Background"' in result
    )
    assert 'section:"Conclusion"' in result


def test_insert_chunk_markers_with_page_numbers(sample_markdown, sample_chunks):
    """Test that page numbers are included in markers."""
    result = insert_chunk_markers(sample_markdown, sample_chunks)

    # Check page numbers in markers
    assert "page:1" in result
    assert "page:2" in result


def test_insert_chunk_markers_empty_markdown():
    """Test with empty markdown."""
    result = insert_chunk_markers("", [])
    assert result == ""


def test_insert_chunk_markers_no_chunks(sample_markdown):
    """Test with no chunks."""
    result = insert_chunk_markers(sample_markdown, [])
    assert result == sample_markdown


def test_insert_chunk_markers_chunk_not_found(sample_markdown):
    """Test with chunk text not found in markdown."""
    chunks = [
        ChunkMetadata(
            chunk_id="abc123-chunk9999",
            embedding_id="abc123-chunk9999",
            page=1,
            section_path="NonExistent",
            text_content="This text does not exist in the markdown.",
        )
    ]

    result = insert_chunk_markers(sample_markdown, chunks)

    # Should return original markdown without markers for non-existent chunks
    assert "<!-- chunk:abc123-chunk9999" not in result


def test_insert_chunk_markers_without_frontmatter():
    """Test with markdown without frontmatter."""
    markdown = "# Simple Document\n\nSimple paragraph."

    chunks = [
        ChunkMetadata(
            chunk_id="test-chunk0000",
            embedding_id="test-chunk0000",
            page=1,
            section_path="",
            text_content="Simple paragraph.",
        )
    ]

    result = insert_chunk_markers(markdown, chunks)

    # Markers should be inserted
    assert "<!-- chunk:test-chunk0000" in result
    assert '<div data-chunk-id="test-chunk0000"' in result


# ============================================================================
# Tests for validate_chunk_markers()
# ============================================================================


def test_validate_chunk_markers_valid(sample_markdown, sample_chunks):
    """Test validation of valid chunk markers."""
    marked_markdown = insert_chunk_markers(sample_markdown, sample_chunks)
    result = validate_chunk_markers(marked_markdown)

    assert result["valid"] is True
    assert result["marker_count"] > 0
    assert len(result["errors"]) == 0


def test_validate_chunk_markers_missing_closing_div():
    """Test validation detects missing closing divs."""
    markdown = """
<!-- chunk:test-chunk0000 page:1 section:"Test" -->
<div data-chunk-id="test-chunk0000" data-page="1" data-section="Test">
Some content
"""

    result = validate_chunk_markers(markdown)

    assert result["valid"] is False
    assert "Mismatch" in " ".join(result["errors"])


def test_validate_chunk_markers_no_markers():
    """Test validation of markdown without markers."""
    markdown = "# Simple Document\n\nNo markers here."

    result = validate_chunk_markers(markdown)

    assert result["valid"] is True
    assert result["marker_count"] == 0


# ============================================================================
# Tests for strip_chunk_markers()
# ============================================================================


def test_strip_chunk_markers_removes_all(sample_markdown, sample_chunks):
    """Test that all chunk markers are removed."""
    marked_markdown = insert_chunk_markers(sample_markdown, sample_chunks)
    result = strip_chunk_markers(marked_markdown)

    # No markers should remain
    assert "<!-- chunk:" not in result
    assert "data-chunk-id=" not in result
    assert "</div>" not in result or result.count("</div>") == 0


def test_strip_chunk_markers_preserves_content(sample_markdown, sample_chunks):
    """Test that content is preserved after stripping markers."""
    marked_markdown = insert_chunk_markers(sample_markdown, sample_chunks)
    result = strip_chunk_markers(marked_markdown)

    # Original content should still be present (approximately)
    assert "Introduction" in result
    assert "Background" in result
    assert "Conclusion" in result


def test_strip_chunk_markers_idempotent(sample_markdown):
    """Test that stripping markers twice has same effect."""
    result1 = strip_chunk_markers(sample_markdown)
    result2 = strip_chunk_markers(result1)

    assert result1 == result2


# ============================================================================
# Tests for edge cases
# ============================================================================


def test_chunk_metadata_with_special_characters():
    """Test handling of special characters in metadata."""
    markdown = '# Test\n\nQuoted text with "quotes" and <brackets>.'

    chunks = [
        ChunkMetadata(
            chunk_id="test-chunk0000",
            embedding_id="test-chunk0000",
            page=1,
            section_path='Test "quoted" section',
            text_content='Quoted text with "quotes" and <brackets>.',
        )
    ]

    result = insert_chunk_markers(markdown, chunks)

    # Should escape quotes in attributes
    assert "&quot;" in result or '\\"' in result


def test_chunk_metadata_empty_section_path():
    """Test handling of empty section path."""
    markdown = "# Test\n\nSimple content."

    chunks = [
        ChunkMetadata(
            chunk_id="test-chunk0000",
            embedding_id="test-chunk0000",
            page=1,
            section_path="",
            text_content="Simple content.",
        )
    ]

    result = insert_chunk_markers(markdown, chunks)

    # Should handle empty section gracefully
    assert 'section:""' in result


def test_overlapping_chunks():
    """Test handling of overlapping chunk text."""
    markdown = "# Test\n\nThis is a test. This is only a test."

    chunks = [
        ChunkMetadata(
            chunk_id="test-chunk0000",
            embedding_id="test-chunk0000",
            page=1,
            section_path="Test",
            text_content="This is a test.",
        ),
        ChunkMetadata(
            chunk_id="test-chunk0001",
            embedding_id="test-chunk0001",
            page=1,
            section_path="Test",
            text_content="This is only a test.",
        ),
    ]

    result = insert_chunk_markers(markdown, chunks)

    # Both chunks should be marked
    assert "chunk:test-chunk0000" in result
    assert "chunk:test-chunk0001" in result


def test_multiline_chunks():
    """Test handling of multi-line chunks."""
    markdown = """# Test

This is a paragraph
that spans multiple
lines in the markdown.

Another paragraph.
"""

    chunks = [
        ChunkMetadata(
            chunk_id="test-chunk0000",
            embedding_id="test-chunk0000",
            page=1,
            section_path="Test",
            text_content="This is a paragraph\nthat spans multiple\nlines in the markdown.",
        )
    ]

    result = insert_chunk_markers(markdown, chunks)

    # Should find and wrap multi-line content
    assert "chunk:test-chunk0000" in result
    assert '<div data-chunk-id="test-chunk0000"' in result


# ============================================================================
# Integration-like tests
# ============================================================================


def test_round_trip_insert_and_strip(sample_markdown, sample_chunks):
    """Test inserting and then stripping markers."""
    marked = insert_chunk_markers(sample_markdown, sample_chunks)
    stripped = strip_chunk_markers(marked)

    # Should be approximately equal (may have whitespace differences)
    # Just check key content is present
    assert "Introduction" in stripped
    assert "Background" in stripped
    assert "Conclusion" in stripped


def test_validation_after_insertion(sample_markdown, sample_chunks):
    """Test that inserted markers pass validation."""
    marked = insert_chunk_markers(sample_markdown, sample_chunks)
    validation = validate_chunk_markers(marked)

    assert validation["valid"] is True
    assert validation["marker_count"] > 0
    assert len(validation["errors"]) == 0
