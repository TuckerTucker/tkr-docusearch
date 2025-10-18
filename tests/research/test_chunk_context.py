"""
Unit tests for chunk_id extraction from ChromaDB metadata.

Tests the chunk_extractor module's ability to extract and transform
chunk_id from search results for bidirectional highlighting.
"""

import pytest

from src.research.chunk_extractor import extract_chunk_id, parse_chunk_id


class TestExtractChunkId:
    """Test chunk_id extraction from metadata"""

    def test_extract_from_text_result_integer(self):
        """Extract chunk_id from text result with integer chunk_id"""
        metadata = {
            "doc_id": "abc123",
            "chunk_id": 45,
            "filename": "report.pdf",
            "page": 1,
        }
        doc_id = "abc123"

        result = extract_chunk_id(metadata, doc_id)

        assert result == "abc123-chunk0045"

    def test_extract_from_text_result_string(self):
        """Extract chunk_id from text result with string chunk_id"""
        metadata = {
            "doc_id": "xyz789",
            "chunk_id": "123",
            "filename": "document.pdf",
            "page": 5,
        }
        doc_id = "xyz789"

        result = extract_chunk_id(metadata, doc_id)

        assert result == "xyz789-chunk0123"

    def test_extract_from_text_result_zero(self):
        """Extract chunk_id zero (first chunk)"""
        metadata = {
            "doc_id": "test-doc",
            "chunk_id": 0,
            "filename": "test.pdf",
            "page": 1,
        }
        doc_id = "test-doc"

        result = extract_chunk_id(metadata, doc_id)

        assert result == "test-doc-chunk0000"

    def test_extract_from_text_result_large_number(self):
        """Extract large chunk_id number"""
        metadata = {
            "doc_id": "large-doc",
            "chunk_id": 9999,
            "filename": "large.pdf",
            "page": 100,
        }
        doc_id = "large-doc"

        result = extract_chunk_id(metadata, doc_id)

        assert result == "large-doc-chunk9999"

    def test_extract_from_visual_result_no_chunk_id(self):
        """Visual result has no chunk_id field"""
        metadata = {
            "doc_id": "abc123",
            "page": 1,
            "filename": "report.pdf",
            "type": "visual",
        }
        doc_id = "abc123"

        result = extract_chunk_id(metadata, doc_id)

        assert result is None

    def test_extract_with_invalid_chunk_id_type(self):
        """Handle invalid chunk_id type gracefully"""
        metadata = {
            "doc_id": "abc123",
            "chunk_id": [1, 2, 3],  # Invalid type
            "filename": "test.pdf",
        }
        doc_id = "abc123"

        result = extract_chunk_id(metadata, doc_id)

        assert result is None

    def test_extract_with_invalid_string_chunk_id(self):
        """Handle non-numeric string chunk_id"""
        metadata = {
            "doc_id": "abc123",
            "chunk_id": "invalid",
            "filename": "test.pdf",
        }
        doc_id = "abc123"

        result = extract_chunk_id(metadata, doc_id)

        assert result is None

    def test_extract_with_negative_chunk_id(self):
        """Handle negative chunk_id (should still format but unlikely in practice)"""
        metadata = {
            "doc_id": "abc123",
            "chunk_id": -5,
            "filename": "test.pdf",
        }
        doc_id = "abc123"

        # Should format even if negative (though invalid in practice)
        result = extract_chunk_id(metadata, doc_id)

        # Python's format will handle negative, but this is edge case
        assert "abc123-chunk" in result

    def test_extract_with_special_characters_in_doc_id(self):
        """Handle doc_id with special characters"""
        metadata = {
            "doc_id": "doc_2024-10-17_v2.1",
            "chunk_id": 10,
            "filename": "test.pdf",
        }
        doc_id = "doc_2024-10-17_v2.1"

        result = extract_chunk_id(metadata, doc_id)

        assert result == "doc_2024-10-17_v2.1-chunk0010"


class TestParseChunkId:
    """Test parsing chunk_id strings into components"""

    def test_parse_valid_chunk_id(self):
        """Parse valid chunk_id string"""
        chunk_id = "abc123-chunk0045"

        result = parse_chunk_id(chunk_id)

        assert result == {"doc_id": "abc123", "chunk_num": 45}

    def test_parse_chunk_id_zero(self):
        """Parse chunk_id with zero"""
        chunk_id = "test-doc-chunk0000"

        result = parse_chunk_id(chunk_id)

        assert result == {"doc_id": "test-doc", "chunk_num": 0}

    def test_parse_chunk_id_large_number(self):
        """Parse chunk_id with large number"""
        chunk_id = "large-doc-chunk9999"

        result = parse_chunk_id(chunk_id)

        assert result == {"doc_id": "large-doc", "chunk_num": 9999}

    def test_parse_chunk_id_special_characters(self):
        """Parse chunk_id with special characters in doc_id"""
        chunk_id = "doc_2024-10-17_v2.1-chunk0010"

        result = parse_chunk_id(chunk_id)

        assert result == {"doc_id": "doc_2024-10-17_v2.1", "chunk_num": 10}

    def test_parse_invalid_format_no_chunk(self):
        """Invalid format without 'chunk' keyword"""
        chunk_id = "abc123-page0045"

        result = parse_chunk_id(chunk_id)

        assert result is None

    def test_parse_invalid_format_wrong_digits(self):
        """Invalid format with wrong number of digits"""
        chunk_id = "abc123-chunk045"  # Only 3 digits

        result = parse_chunk_id(chunk_id)

        assert result is None

    def test_parse_invalid_format_no_hyphen(self):
        """Invalid format without hyphen"""
        chunk_id = "abc123chunk0045"

        result = parse_chunk_id(chunk_id)

        assert result is None

    def test_parse_empty_string(self):
        """Handle empty string"""
        result = parse_chunk_id("")

        assert result is None

    def test_parse_none(self):
        """Handle None input"""
        result = parse_chunk_id(None)

        assert result is None


class TestChunkIdRoundTrip:
    """Test round-trip extraction and parsing"""

    def test_roundtrip_extract_and_parse(self):
        """Extract from metadata and parse back"""
        metadata = {
            "doc_id": "test-doc",
            "chunk_id": 42,
            "filename": "test.pdf",
        }
        doc_id = "test-doc"

        # Extract
        extracted = extract_chunk_id(metadata, doc_id)
        assert extracted == "test-doc-chunk0042"

        # Parse
        parsed = parse_chunk_id(extracted)
        assert parsed == {"doc_id": "test-doc", "chunk_num": 42}

    def test_roundtrip_multiple_chunks(self):
        """Round-trip for multiple chunk IDs"""
        test_cases = [
            ({"chunk_id": 0}, "doc1-chunk0000", 0),
            ({"chunk_id": 1}, "doc1-chunk0001", 1),
            ({"chunk_id": 100}, "doc1-chunk0100", 100),
            ({"chunk_id": 9999}, "doc1-chunk9999", 9999),
        ]

        for metadata_dict, expected_str, expected_num in test_cases:
            metadata = {"doc_id": "doc1", "filename": "test.pdf", **metadata_dict}

            extracted = extract_chunk_id(metadata, "doc1")
            assert extracted == expected_str

            parsed = parse_chunk_id(extracted)
            assert parsed["chunk_num"] == expected_num


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
