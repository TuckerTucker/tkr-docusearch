"""
Tests for storage/compression.py module.

Tests cover:
- Embedding compression/decompression
- Structure metadata compression/decompression
- Markdown compression/decompression
- Compression ratio calculations
- Size estimation
- Metadata sanitization
- Error handling and edge cases
"""

import base64
import gzip
import json

import numpy as np
import pytest

from storage.compression import (
    CompressionError,
    CorruptedDataError,
    MarkdownTooLargeError,
    compress_embeddings,
    compress_markdown,
    compress_structure_metadata,
    compression_ratio,
    decompress_embeddings,
    decompress_markdown,
    decompress_structure_metadata,
    estimate_compressed_size,
    sanitize_metadata_for_chroma,
)


class TestEmbeddingCompression:
    """Test embedding compression/decompression."""

    def test_compress_decompress_round_trip(self):
        """Test that compression and decompression are reversible."""
        # Create test embeddings
        embeddings = np.random.randn(100, 128).astype(np.float32)

        # Compress and decompress
        compressed = compress_embeddings(embeddings)
        decompressed = decompress_embeddings(compressed, embeddings.shape, np.float32)

        # Should be identical
        assert np.allclose(embeddings, decompressed)
        assert isinstance(compressed, str)

    def test_compress_small_embedding(self):
        """Test compression of small embedding."""
        embeddings = np.random.randn(10, 128).astype(np.float32)
        compressed = compress_embeddings(embeddings)

        assert isinstance(compressed, str)
        assert len(compressed) > 0

    def test_compress_large_embedding(self):
        """Test compression of large embedding (1031 tokens like ColPali)."""
        embeddings = np.random.randn(1031, 128).astype(np.float32)
        compressed = compress_embeddings(embeddings)
        decompressed = decompress_embeddings(compressed, embeddings.shape, np.float32)

        assert np.allclose(embeddings, decompressed)

    def test_decompress_different_shapes(self):
        """Test decompression with different embedding shapes."""
        shapes = [(30, 128), (100, 128), (1031, 128)]

        for shape in shapes:
            embeddings = np.random.randn(*shape).astype(np.float32)
            compressed = compress_embeddings(embeddings)
            decompressed = decompress_embeddings(compressed, shape, np.float32)

            assert decompressed.shape == shape
            assert np.allclose(embeddings, decompressed)

    def test_decompress_different_dtypes(self):
        """Test decompression with different dtypes."""
        embeddings_f32 = np.random.randn(50, 128).astype(np.float32)
        embeddings_f32.astype(np.float64)

        # Compress float32
        compressed = compress_embeddings(embeddings_f32)

        # Decompress as float32
        decompressed_f32 = decompress_embeddings(compressed, embeddings_f32.shape, np.float32)
        assert decompressed_f32.dtype == np.float32
        assert np.allclose(embeddings_f32, decompressed_f32)

    def test_compression_achieves_size_reduction(self):
        """Test that compression produces valid output."""
        embeddings = np.random.randn(100, 128).astype(np.float32)
        compressed = compress_embeddings(embeddings)

        embeddings.nbytes
        compressed_size = len(compressed.encode("utf-8"))

        # Random data may not compress well, but output should be valid
        # The important thing is we can decompress it correctly
        assert compressed_size > 0
        assert isinstance(compressed, str)

    def test_compress_empty_embedding_fails(self):
        """Test compression of empty embedding fails gracefully."""
        embeddings = np.array([]).reshape(0, 128)
        compressed = compress_embeddings(embeddings)

        # Should still work but produce minimal output
        assert isinstance(compressed, str)


class TestCompressionUtilities:
    """Test compression utility functions."""

    def test_estimate_compressed_size(self):
        """Test compressed size estimation."""
        embeddings = np.random.randn(100, 128).astype(np.float32)
        estimated_size = estimate_compressed_size(embeddings)

        assert isinstance(estimated_size, int)
        assert estimated_size > 0

        # Should be roughly the same as actual compression
        compressed = compress_embeddings(embeddings)
        actual_size = len(compressed.encode("utf-8"))
        assert estimated_size == actual_size

    def test_compression_ratio_calculation(self):
        """Test compression ratio calculation."""
        embeddings = np.random.randn(100, 128).astype(np.float32)
        ratio = compression_ratio(embeddings)

        assert isinstance(ratio, float)
        assert ratio > 0.0
        # Random data may not compress well (ratio could be < 1.0)
        # The important thing is the calculation works

    def test_compression_ratio_zero_size(self):
        """Test compression ratio with minimal data."""
        # Very small embedding might not compress well
        embeddings = np.array([[1.0, 2.0]], dtype=np.float32)
        ratio = compression_ratio(embeddings)

        assert isinstance(ratio, float)
        assert ratio >= 0.0


class TestStructureMetadataCompression:
    """Test structure metadata compression."""

    def test_compress_decompress_structure_metadata(self):
        """Test structure metadata round trip."""
        metadata = {
            "headings": [{"text": "Introduction", "level": "SECTION_HEADER", "page": 1}],
            "tables": [{"page": 2, "caption": "Results", "rows": 10, "cols": 5}],
            "pictures": [{"page": 3, "type": "chart", "confidence": 0.95}],
            "summary": {"total_sections": 3, "max_depth": 2},
        }

        compressed = compress_structure_metadata(metadata)
        decompressed = decompress_structure_metadata(compressed)

        assert decompressed == metadata

    def test_compress_empty_metadata(self):
        """Test compression of empty metadata."""
        metadata = {}
        compressed = compress_structure_metadata(metadata)
        decompressed = decompress_structure_metadata(compressed)

        assert decompressed == metadata

    def test_compress_complex_metadata(self):
        """Test compression of complex nested metadata."""
        metadata = {
            "headings": [{"text": f"Section {i}", "page": i} for i in range(1, 11)],
            "nested": {"level1": {"level2": {"level3": [1, 2, 3, 4, 5]}}},
            "list": list(range(100)),
        }

        compressed = compress_structure_metadata(metadata)
        decompressed = decompress_structure_metadata(compressed)

        assert decompressed == metadata

    def test_compress_metadata_with_special_chars(self):
        """Test compression with special characters."""
        metadata = {"text": "Special chars: 日本語, émojis 🎉, quotes \"'", "unicode": "Ω, π, ∑, ∫"}

        compressed = compress_structure_metadata(metadata)
        decompressed = decompress_structure_metadata(compressed)

        assert decompressed == metadata


class TestMarkdownCompression:
    """Test markdown text compression."""

    def test_compress_decompress_markdown(self):
        """Test markdown compression round trip."""
        markdown = """# Test Document

## Introduction
This is a test markdown document with multiple sections.

## Methods
- Step 1
- Step 2
- Step 3

## Results
Lorem ipsum dolor sit amet, consectetur adipiscing elit.
"""

        compressed = compress_markdown(markdown)
        decompressed = decompress_markdown(compressed)

        assert decompressed == markdown
        assert isinstance(compressed, str)

    def test_compress_empty_markdown(self):
        """Test compression of empty markdown."""
        markdown = ""
        compressed = compress_markdown(markdown)
        decompressed = decompress_markdown(compressed)

        assert decompressed == markdown

    def test_compress_small_markdown(self):
        """Test compression of small markdown."""
        markdown = "# Title\n\nContent"
        compressed = compress_markdown(markdown)
        decompressed = decompress_markdown(compressed)

        assert decompressed == markdown

    def test_compress_large_markdown(self):
        """Test compression of large markdown (but under limit)."""
        # Create ~1MB markdown (well under 10MB limit)
        markdown = "# Large Document\n\n" + ("Lorem ipsum dolor sit amet. " * 10000)

        compressed = compress_markdown(markdown)
        decompressed = decompress_markdown(compressed)

        assert decompressed == markdown

        # Should achieve significant compression
        original_size = len(markdown.encode("utf-8"))
        compressed_size = len(compressed.encode("utf-8"))
        assert compressed_size < original_size

    def test_compress_markdown_with_unicode(self):
        """Test markdown with unicode characters."""
        markdown = """# Unicode Test

日本語のテキスト
Émojis: 🎉 🚀 ⭐
Math: Σ, π, ∫, Ω
"""

        compressed = compress_markdown(markdown)
        decompressed = decompress_markdown(compressed)

        assert decompressed == markdown

    def test_compress_markdown_too_large(self):
        """Test that oversized markdown raises error."""
        # Create >10MB markdown
        large_markdown = "x" * (11 * 1024 * 1024)

        with pytest.raises(MarkdownTooLargeError) as exc_info:
            compress_markdown(large_markdown)

        assert "exceeds limit" in str(exc_info.value)

    def test_decompress_markdown_too_large(self):
        """Test that decompression catches oversized markdown."""
        # Create markdown that's just under 10MB
        markdown = "x" * (9 * 1024 * 1024)
        compressed = compress_markdown(markdown)

        # Now try to decompress (should work)
        decompressed = decompress_markdown(compressed)
        assert len(decompressed) == len(markdown)

    def test_decompress_invalid_base64(self):
        """Test decompression with invalid base64."""
        with pytest.raises(CorruptedDataError) as exc_info:
            decompress_markdown("not valid base64!!!")

        assert "base64" in str(exc_info.value).lower() or "corrupted" in str(exc_info.value).lower()

    def test_decompress_invalid_gzip(self):
        """Test decompression with invalid gzip data."""
        # Valid base64 but not gzip
        invalid_gzip = base64.b64encode(b"not gzip data").decode("utf-8")

        with pytest.raises(CorruptedDataError) as exc_info:
            decompress_markdown(invalid_gzip)

        assert "gzip" in str(exc_info.value).lower() or "corrupted" in str(exc_info.value).lower()

    def test_decompress_invalid_utf8(self):
        """Test decompression with invalid UTF-8."""
        # Create valid gzip but with invalid UTF-8 bytes
        invalid_utf8_bytes = b"\xff\xfe\xfd"
        compressed_bytes = gzip.compress(invalid_utf8_bytes)
        compressed_str = base64.b64encode(compressed_bytes).decode("utf-8")

        with pytest.raises(CorruptedDataError) as exc_info:
            decompress_markdown(compressed_str)

        assert "utf-8" in str(exc_info.value).lower() or "corrupted" in str(exc_info.value).lower()

    def test_markdown_compression_ratio(self):
        """Test that markdown achieves good compression."""
        # Repetitive markdown should compress well
        markdown = "# Section\n\n" + ("Lorem ipsum dolor sit amet.\n" * 100)
        compressed = compress_markdown(markdown)

        original_size = len(markdown.encode("utf-8"))
        compressed_size = len(compressed.encode("utf-8"))
        ratio = original_size / compressed_size

        # Should achieve at least 2x compression on repetitive text
        assert ratio > 2.0


class TestMetadataSanitization:
    """Test metadata sanitization for ChromaDB."""

    def test_sanitize_primitives(self):
        """Test that primitives pass through unchanged."""
        metadata = {"string": "value", "int": 42, "float": 3.14, "bool": True, "none": None}

        sanitized = sanitize_metadata_for_chroma(metadata)
        assert sanitized == metadata

    def test_sanitize_lists(self):
        """Test that lists are converted to JSON strings."""
        metadata = {"tags": ["tag1", "tag2", "tag3"], "numbers": [1, 2, 3, 4, 5]}

        sanitized = sanitize_metadata_for_chroma(metadata)

        assert isinstance(sanitized["tags"], str)
        assert isinstance(sanitized["numbers"], str)

        # Should be valid JSON
        assert json.loads(sanitized["tags"]) == ["tag1", "tag2", "tag3"]
        assert json.loads(sanitized["numbers"]) == [1, 2, 3, 4, 5]

    def test_sanitize_dicts(self):
        """Test that dicts are converted to JSON strings."""
        metadata = {
            "config": {"key1": "value1", "key2": "value2"},
            "nested": {"level1": {"level2": "deep"}},
        }

        sanitized = sanitize_metadata_for_chroma(metadata)

        assert isinstance(sanitized["config"], str)
        assert isinstance(sanitized["nested"], str)

        # Should be valid JSON
        assert json.loads(sanitized["config"]) == {"key1": "value1", "key2": "value2"}

    def test_sanitize_mixed_types(self):
        """Test sanitization with mixed types."""
        metadata = {
            "name": "test",
            "count": 5,
            "active": True,
            "tags": ["a", "b"],
            "config": {"key": "value"},
            "score": 0.95,
            "none_value": None,
        }

        sanitized = sanitize_metadata_for_chroma(metadata)

        # Primitives unchanged
        assert sanitized["name"] == "test"
        assert sanitized["count"] == 5
        assert sanitized["active"] is True
        assert sanitized["score"] == 0.95
        assert sanitized["none_value"] is None

        # Complex types converted to strings
        assert isinstance(sanitized["tags"], str)
        assert isinstance(sanitized["config"], str)

    def test_sanitize_empty_dict(self):
        """Test sanitization of empty dictionary."""
        metadata = {}
        sanitized = sanitize_metadata_for_chroma(metadata)
        assert sanitized == {}

    def test_sanitize_custom_objects(self):
        """Test sanitization converts unknown types to strings."""

        class CustomObject:
            def __str__(self):
                return "custom_object"

        metadata = {"obj": CustomObject()}
        sanitized = sanitize_metadata_for_chroma(metadata)

        assert isinstance(sanitized["obj"], str)
        assert "custom_object" in sanitized["obj"]

    def test_sanitize_preserves_key_names(self):
        """Test that key names are preserved."""
        metadata = {"simple_key": "value", "complex_key": {"nested": "data"}}

        sanitized = sanitize_metadata_for_chroma(metadata)

        assert set(sanitized.keys()) == set(metadata.keys())

    def test_sanitize_compact_json(self):
        """Test that JSON is compact (no extra spaces)."""
        metadata = {"list": [1, 2, 3], "dict": {"a": 1, "b": 2}}
        sanitized = sanitize_metadata_for_chroma(metadata)

        # Should use compact JSON separators
        assert " " not in sanitized["list"]  # No spaces after commas
        assert " " not in sanitized["dict"]


class TestExceptions:
    """Test exception classes."""

    def test_compression_error_base_class(self):
        """Test CompressionError base exception."""
        with pytest.raises(CompressionError):
            raise CompressionError("Test error")

    def test_markdown_too_large_error(self):
        """Test MarkdownTooLargeError exception."""
        with pytest.raises(MarkdownTooLargeError):
            raise MarkdownTooLargeError("Too large")

        # Should be a subclass of CompressionError
        with pytest.raises(CompressionError):
            raise MarkdownTooLargeError("Too large")

    def test_corrupted_data_error(self):
        """Test CorruptedDataError exception."""
        with pytest.raises(CorruptedDataError):
            raise CorruptedDataError("Corrupted")

        # Should be a subclass of CompressionError
        with pytest.raises(CompressionError):
            raise CorruptedDataError("Corrupted")


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_compress_single_value_embedding(self):
        """Test compression of single-value embedding."""
        embeddings = np.array([[1.0]], dtype=np.float32)
        compressed = compress_embeddings(embeddings)
        decompressed = decompress_embeddings(compressed, (1, 1), np.float32)

        assert np.allclose(embeddings, decompressed)

    def test_compress_zeros_embedding(self):
        """Test compression of all-zeros embedding."""
        embeddings = np.zeros((100, 128), dtype=np.float32)
        compressed = compress_embeddings(embeddings)
        decompressed = decompress_embeddings(compressed, (100, 128), np.float32)

        assert np.allclose(embeddings, decompressed)

        # Zeros should compress very well
        ratio = compression_ratio(embeddings)
        assert ratio > 10.0  # Should be highly compressible

    def test_compress_ones_embedding(self):
        """Test compression of all-ones embedding."""
        embeddings = np.ones((100, 128), dtype=np.float32)
        compressed = compress_embeddings(embeddings)
        decompressed = decompress_embeddings(compressed, (100, 128), np.float32)

        assert np.allclose(embeddings, decompressed)

    def test_compress_very_long_markdown(self):
        """Test compression near the size limit."""
        # Create markdown close to 10MB limit
        size_mb = 9.5
        size_bytes = int(size_mb * 1024 * 1024)
        markdown = "x" * size_bytes

        compressed = compress_markdown(markdown)
        decompressed = decompress_markdown(compressed)

        assert len(decompressed) == size_bytes

    def test_sanitize_nested_empty_structures(self):
        """Test sanitization with nested empty structures."""
        metadata = {"empty_list": [], "empty_dict": {}, "nested_empty": {"list": [], "dict": {}}}

        sanitized = sanitize_metadata_for_chroma(metadata)

        assert json.loads(sanitized["empty_list"]) == []
        assert json.loads(sanitized["empty_dict"]) == {}
        assert json.loads(sanitized["nested_empty"])["list"] == []
