"""
Unit tests for compression utilities.

Tests markdown compression/decompression and error handling.
"""

import pytest
import time
from src.storage.compression import (
    compress_markdown,
    decompress_markdown,
    CompressionError,
    MarkdownTooLargeError,
    CorruptedDataError
)


class TestMarkdownCompression:
    """Test markdown compression and decompression."""

    def test_compress_markdown_basic(self):
        """Test basic markdown compression."""
        markdown = "# Title\n\nContent here..."
        compressed = compress_markdown(markdown)

        assert isinstance(compressed, str)
        assert len(compressed) > 0
        # Small strings may actually get larger due to gzip overhead, that's OK

    def test_decompress_markdown_basic(self):
        """Test basic markdown decompression."""
        original = "# Title\n\nContent here..."
        compressed = compress_markdown(original)
        decompressed = decompress_markdown(compressed)

        assert decompressed == original  # Exact equality

    def test_round_trip_small(self):
        """Test round-trip with small markdown."""
        original = "Short"
        compressed = compress_markdown(original)
        decompressed = decompress_markdown(compressed)

        assert decompressed == original

    def test_round_trip_1kb(self):
        """Test round-trip with ~1KB markdown."""
        original = "# Heading\n\n" + "Paragraph. " * 100  # ~1KB
        compressed = compress_markdown(original)
        decompressed = decompress_markdown(compressed)

        assert decompressed == original
        # Should achieve some compression
        assert len(compressed) < len(original)

    def test_round_trip_100kb(self):
        """Test round-trip with ~100KB markdown."""
        original = "# Document\n\n" + "Content. " * 10000  # ~100KB
        compressed = compress_markdown(original)
        decompressed = decompress_markdown(compressed)

        assert decompressed == original
        # Should achieve significant compression
        assert len(compressed) < len(original) * 0.5  # At least 2x compression

    def test_round_trip_1mb(self):
        """Test round-trip with ~1MB markdown."""
        original = "# Large Doc\n\n" + "Text. " * 100000  # ~1MB
        compressed = compress_markdown(original)
        decompressed = decompress_markdown(compressed)

        assert decompressed == original
        # Should achieve good compression
        compression_ratio = len(original) / len(compressed)
        assert compression_ratio > 2.0  # At least 2x compression

    def test_unicode_and_emoji(self):
        """Test handling of unicode and emoji."""
        markdown = "# Test 中文 🚀\n\nContent with émojis 😀 and unicode: こんにちは"
        compressed = compress_markdown(markdown)
        decompressed = decompress_markdown(compressed)

        assert decompressed == markdown

    def test_empty_string(self):
        """Test empty markdown handling."""
        compressed = compress_markdown("")
        assert isinstance(compressed, str)

        decompressed = decompress_markdown(compressed)
        assert decompressed == ""

    def test_markdown_too_large(self):
        """Test size limit enforcement."""
        huge_markdown = "x" * (11 * 1024 * 1024)  # 11MB

        with pytest.raises(MarkdownTooLargeError) as exc_info:
            compress_markdown(huge_markdown)

        assert "exceeds limit of 10MB" in str(exc_info.value)

    def test_corrupted_base64(self):
        """Test detection of corrupted base64 data."""
        with pytest.raises(CorruptedDataError) as exc_info:
            decompress_markdown("invalid_base64!@#$")

        assert "base64" in str(exc_info.value).lower() or "corrupt" in str(exc_info.value).lower()

    def test_corrupted_gzip(self):
        """Test detection of corrupted gzip data."""
        import base64

        # Valid base64 but invalid gzip
        invalid_gzip = base64.b64encode(b"not gzip data").decode('utf-8')

        with pytest.raises(CorruptedDataError) as exc_info:
            decompress_markdown(invalid_gzip)

        assert "gzip" in str(exc_info.value).lower() or "corrupt" in str(exc_info.value).lower()

    def test_deterministic_output(self):
        """Test that compression is deterministic."""
        markdown = "# Test\n\nDeterministic content"

        compressed1 = compress_markdown(markdown)
        compressed2 = compress_markdown(markdown)

        assert compressed1 == compressed2


class TestMarkdownCompressionPerformance:
    """Test compression performance benchmarks."""

    def test_compression_performance_1mb(self):
        """Test compression performance targets (<100ms for 1MB)."""
        # 1MB markdown
        markdown = "# Document\n\n" + "Content. " * 100000

        start = time.time()
        compressed = compress_markdown(markdown)
        duration = time.time() - start

        assert duration < 0.1, f"Compression too slow: {duration:.3f}s (target <100ms)"
        # Ensure compression worked
        assert len(compressed) > 0

    def test_decompression_performance_1mb(self):
        """Test decompression performance targets (<50ms for 1MB)."""
        # 1MB markdown
        markdown = "# Document\n\n" + "Content. " * 100000
        compressed = compress_markdown(markdown)

        start = time.time()
        decompressed = decompress_markdown(compressed)
        duration = time.time() - start

        assert duration < 0.05, f"Decompression too slow: {duration:.3f}s (target <50ms)"
        # Ensure decompression worked
        assert decompressed == markdown

    def test_compression_ratio(self):
        """Test compression ratio for typical markdown."""
        # Typical markdown with structure
        markdown = """# Document Title

## Introduction

This is a sample document with various elements.

### Section 1.1

- List item 1
- List item 2
- List item 3

### Section 1.2

Some text content that repeats. """ * 100  # Repeating pattern

        compressed = compress_markdown(markdown)

        original_size = len(markdown.encode('utf-8'))
        compressed_size = len(compressed.encode('utf-8'))
        ratio = original_size / compressed_size

        # Should achieve at least 3x compression for repetitive content
        assert ratio > 3.0, f"Compression ratio too low: {ratio:.2f}x (expected >3x)"


class TestExceptionHierarchy:
    """Test exception hierarchy."""

    def test_compression_error_base(self):
        """Test CompressionError is base exception."""
        assert issubclass(MarkdownTooLargeError, CompressionError)
        assert issubclass(CorruptedDataError, CompressionError)

    def test_can_catch_with_base_exception(self):
        """Test that all compression errors can be caught with base exception."""
        try:
            huge_markdown = "x" * (11 * 1024 * 1024)
            compress_markdown(huge_markdown)
        except CompressionError:
            pass  # Should catch MarkdownTooLargeError

        try:
            decompress_markdown("invalid")
        except CompressionError:
            pass  # Should catch CorruptedDataError


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_markdown_exactly_10mb(self):
        """Test markdown at exactly 10MB limit."""
        # 10MB exactly
        size_bytes = 10 * 1024 * 1024
        markdown = "x" * size_bytes

        # Should work at exactly 10MB
        compressed = compress_markdown(markdown)
        assert len(compressed) > 0

    def test_markdown_just_over_10mb(self):
        """Test markdown just over 10MB limit."""
        # 10MB + 1 byte
        size_bytes = 10 * 1024 * 1024 + 1
        markdown = "x" * size_bytes

        # Should raise error
        with pytest.raises(MarkdownTooLargeError):
            compress_markdown(markdown)

    def test_whitespace_only(self):
        """Test markdown with only whitespace."""
        markdown = "   \n\n\t\t\n   "
        compressed = compress_markdown(markdown)
        decompressed = decompress_markdown(compressed)

        assert decompressed == markdown

    def test_special_characters(self):
        """Test markdown with special characters."""
        markdown = "# Test\n\n`code` **bold** *italic* [link](url) ![image](url)"
        compressed = compress_markdown(markdown)
        decompressed = decompress_markdown(compressed)

        assert decompressed == markdown

    def test_multiline_code_blocks(self):
        """Test markdown with code blocks."""
        markdown = """# Code Example

```python
def hello():
    print("Hello, world!")
```

More content here.
"""
        compressed = compress_markdown(markdown)
        decompressed = decompress_markdown(compressed)

        assert decompressed == markdown


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
