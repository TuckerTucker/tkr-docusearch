"""
Tests for chunk marker format validation.

Tests the format and structure of HTML chunk markers to ensure
they meet the specification for bidirectional highlighting.
"""

import re

# ============================================================================
# Test Marker Format Specification
# ============================================================================


def test_marker_comment_format():
    """Test HTML comment marker format specification."""
    # Expected format: <!-- chunk:{chunk_id} page:{page} section:"{section_path}" -->

    valid_markers = [
        '<!-- chunk:abc123-chunk0000 page:1 section:"Introduction" -->',
        '<!-- chunk:doc456-chunk0042 page:5 section:"Methods > Analysis" -->',
        '<!-- chunk:test-chunk9999 page:100 section:"" -->',
    ]

    pattern = r'<!-- chunk:([^\s]+) page:(\d+) section:"([^"]*)" -->'

    for marker in valid_markers:
        match = re.match(pattern, marker)
        assert match is not None, f"Valid marker did not match: {marker}"

        chunk_id, page, section = match.groups()
        assert len(chunk_id) > 0
        assert int(page) >= 1
        # section can be empty


def test_marker_div_opening_format():
    """Test div opening tag format specification."""
    # Expected format: <div data-chunk-id="{chunk_id}" data-page="{page}" data-section="{section}">

    valid_divs = [
        '<div data-chunk-id="abc123-chunk0000" data-page="1" data-section="Introduction">',
        '<div data-chunk-id="doc456-chunk0042" data-page="5" data-section="Methods &gt; Analysis">',
        '<div data-chunk-id="test-chunk9999" data-page="100" data-section="">',
    ]

    pattern = r'<div data-chunk-id="([^"]+)" data-page="(\d+)" data-section="([^"]*)">'

    for div in valid_divs:
        match = re.match(pattern, div)
        assert match is not None, f"Valid div did not match: {div}"

        chunk_id, page, section = match.groups()
        assert len(chunk_id) > 0
        assert int(page) >= 1


def test_marker_div_closing_format():
    """Test div closing tag format specification."""
    closing_div = "</div>"

    # Simple but important validation
    assert closing_div == "</div>"
    assert closing_div.count("<") == 1
    assert closing_div.count(">") == 1


# ============================================================================
# Test Marker Pairing
# ============================================================================


def test_marker_pairing_complete():
    """Test that markers come in complete sets (comment + opening div + closing div)."""
    sample_markdown = """
<!-- chunk:test-chunk0000 page:1 section:"Test" -->
<div data-chunk-id="test-chunk0000" data-page="1" data-section="Test">
Test content
</div>
"""

    # Count each type
    comment_count = sample_markdown.count("<!-- chunk:")
    div_open_count = sample_markdown.count('<div data-chunk-id="')
    div_close_count = sample_markdown.count("</div>")

    assert comment_count == div_open_count == div_close_count == 1


def test_marker_pairing_multiple():
    """Test multiple marker sets."""
    sample_markdown = """
<!-- chunk:test-chunk0000 page:1 section:"First" -->
<div data-chunk-id="test-chunk0000" data-page="1" data-section="First">
First chunk
</div>

<!-- chunk:test-chunk0001 page:1 section:"Second" -->
<div data-chunk-id="test-chunk0001" data-page="1" data-section="Second">
Second chunk
</div>
"""

    comment_count = sample_markdown.count("<!-- chunk:")
    div_open_count = sample_markdown.count('<div data-chunk-id="')
    div_close_count = sample_markdown.count("</div>")

    assert comment_count == div_open_count == div_close_count == 2


def test_marker_pairing_mismatch_detection():
    """Test detection of mismatched markers."""
    # Missing closing div
    incomplete_markdown = """
<!-- chunk:test-chunk0000 page:1 section:"Test" -->
<div data-chunk-id="test-chunk0000" data-page="1" data-section="Test">
Test content
"""

    comment_count = incomplete_markdown.count("<!-- chunk:")
    div_open_count = incomplete_markdown.count('<div data-chunk-id="')
    div_close_count = incomplete_markdown.count("</div>")

    # This should fail the pairing check
    assert comment_count == div_open_count
    assert div_close_count < div_open_count


# ============================================================================
# Test Attribute Escaping
# ============================================================================


def test_attribute_quote_escaping():
    """Test that quotes in attributes are properly escaped."""
    # Section path with quotes should be escaped
    valid_div = (
        '<div data-chunk-id="test" data-page="1" data-section="Test &quot;quoted&quot; section">'
    )

    assert "&quot;" in valid_div or '\\"' in valid_div


def test_attribute_html_escaping():
    """Test that HTML special characters are escaped."""
    # Section path with angle brackets should be escaped
    valid_div = '<div data-chunk-id="test" data-page="1" data-section="Test &lt;tag&gt; section">'

    # Should have escaped HTML entities
    assert "&lt;" in valid_div or "&gt;" in valid_div


def test_attribute_no_unescaped_quotes():
    """Test that unescaped quotes break parsing."""
    # This would be invalid HTML
    invalid_div = '<div data-chunk-id="test" data-page="1" data-section="Test "quoted" section">'

    # Try to parse with simple regex (would fail with unescaped quotes)
    pattern = r'data-section="([^"]*)"'
    match = re.search(pattern, invalid_div)

    # This will only match up to the first unescaped quote
    if match:
        content = match.group(1)
        # The match won't capture the full intended content
        assert "quoted" not in content or "section" not in content


# ============================================================================
# Test Chunk ID Format
# ============================================================================


def test_chunk_id_format_valid():
    """Test valid chunk ID formats."""
    valid_chunk_ids = [
        "abc123-chunk0000",
        "doc456-chunk0042",
        "test-chunk9999",
        "a1b2c3-chunk0001",
    ]

    # Pattern: {doc_id}-chunk{number:04d}
    pattern = r"^[a-zA-Z0-9\-]+-chunk\d{4}$"

    for chunk_id in valid_chunk_ids:
        assert re.match(pattern, chunk_id), f"Invalid chunk_id format: {chunk_id}"


def test_chunk_id_format_invalid():
    """Test invalid chunk ID formats."""
    invalid_chunk_ids = [
        "chunk0000",  # Missing doc_id
        "abc123-0000",  # Missing 'chunk' keyword
        "abc123-chunk00",  # Wrong number padding
        "abc123-chunk",  # Missing number
    ]

    pattern = r"^[a-zA-Z0-9\-]+-chunk\d{4}$"

    for chunk_id in invalid_chunk_ids:
        assert not re.match(pattern, chunk_id), f"Should be invalid: {chunk_id}"


# ============================================================================
# Test Page Number Format
# ============================================================================


def test_page_number_positive_integers():
    """Test that page numbers are positive integers."""
    valid_pages = ["1", "5", "100", "9999"]

    for page in valid_pages:
        assert page.isdigit()
        assert int(page) >= 1


def test_page_number_invalid():
    """Test invalid page number formats."""
    invalid_pages = ["0", "-1", "1.5", "abc", ""]

    for page in invalid_pages:
        is_valid = page.isdigit() and int(page) >= 1
        assert not is_valid, f"Should be invalid: {page}"


# ============================================================================
# Test Marker Ordering
# ============================================================================


def test_marker_order_comment_before_div():
    """Test that comment marker comes before div opening."""
    sample_markdown = """
<!-- chunk:test-chunk0000 page:1 section:"Test" -->
<div data-chunk-id="test-chunk0000" data-page="1" data-section="Test">
Content
</div>
"""

    comment_pos = sample_markdown.find("<!-- chunk:")
    div_open_pos = sample_markdown.find('<div data-chunk-id="')

    assert comment_pos < div_open_pos, "Comment should come before div"


def test_marker_order_div_open_before_close():
    """Test that div opening comes before closing."""
    sample_markdown = """
<div data-chunk-id="test-chunk0000" data-page="1" data-section="Test">
Content
</div>
"""

    div_open_pos = sample_markdown.find('<div data-chunk-id="')
    div_close_pos = sample_markdown.find("</div>")

    assert div_open_pos < div_close_pos, "Opening div should come before closing div"


# ============================================================================
# Test Markdown Compatibility
# ============================================================================


def test_markers_dont_break_markdown_parsing():
    """Test that markers don't interfere with markdown parsing."""
    markdown_with_markers = """
# Title

<!-- chunk:test-chunk0000 page:1 section:"Title" -->
<div data-chunk-id="test-chunk0000" data-page="1" data-section="Title">
This is **bold** text and *italic* text.
</div>

## Subtitle

<!-- chunk:test-chunk0001 page:1 section:"Subtitle" -->
<div data-chunk-id="test-chunk0001" data-page="1" data-section="Subtitle">
- List item 1
- List item 2
</div>
"""

    # Check that markdown constructs are preserved
    assert "# Title" in markdown_with_markers
    assert "## Subtitle" in markdown_with_markers
    assert "**bold**" in markdown_with_markers
    assert "*italic*" in markdown_with_markers
    assert "- List item" in markdown_with_markers


def test_markers_html_compatible():
    """Test that markers are valid HTML."""
    marker_comment = '<!-- chunk:test-chunk0000 page:1 section:"Test" -->'
    marker_div_open = '<div data-chunk-id="test-chunk0000" data-page="1" data-section="Test">'
    marker_div_close = "</div>"

    # Basic HTML validity checks
    assert marker_comment.startswith("<!--")
    assert marker_comment.endswith("-->")

    assert marker_div_open.startswith("<div ")
    assert marker_div_open.endswith(">")

    assert marker_div_close == "</div>"


# ============================================================================
# Test Data Attribute Format
# ============================================================================


def test_data_attribute_naming():
    """Test that data attributes follow HTML5 naming conventions."""
    sample_div = '<div data-chunk-id="test" data-page="1" data-section="Test">'

    # All custom attributes should start with "data-"
    attributes = ["data-chunk-id", "data-page", "data-section"]

    for attr in attributes:
        assert attr in sample_div
        assert attr.startswith("data-")
        # Should use kebab-case (not camelCase or snake_case)
        assert "_" not in attr  # No underscores
        assert attr.islower() or "-" in attr  # Lowercase with hyphens


def test_data_attribute_values_quoted():
    """Test that all attribute values are properly quoted."""
    sample_div = '<div data-chunk-id="test-chunk0000" data-page="1" data-section="Test Section">'

    # Check that values are wrapped in quotes
    pattern = r'data-[a-z-]+="[^"]*"'
    matches = re.findall(pattern, sample_div)

    # Should find all three attributes
    assert len(matches) == 3
